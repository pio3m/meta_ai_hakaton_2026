import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.history import MemoryHistory, SessionCapacityError
from backend.models import ChatRequest, Message
from backend.providers import MetaProvider, MockProvider, ProviderError, build_messages


def body(session='session-one',message='Gdzie odebrać identyfikator?',**kwargs):
    return dict(session_id=session,npc_id='buddy',message=message,language='pl',**kwargs)


def test_mock_chat_history_isolated_and_bounded():
    app=create_app(Settings(history_pairs=2))
    with TestClient(app) as client:
        assert client.get('/health').json()=={'status':'ok','mode':'mock'}
        first=client.post('/api/chat',json=body(message='Mam na imię Ola.')).json()
        assert first['provider']=='mock' and len(first['history'])==2
        second=client.post('/api/chat',json=body(message='Pamiętasz mnie?')).json()
        assert 'Mam na imię Ola.' in second['reply']
        other=client.post('/api/chat',json={**body('session-two','Who are you?'),'language':'en'}).json()
        assert 'Ola' not in other['reply'] and 'You asked' in other['reply']
        third=client.post('/api/chat',json=body(message='Jeszcze pytanie')).json()
        assert len(third['history'])==4
        assert third['history'][0]['content']=='Pamiętasz mnie?'
        assert [m['role'] for m in third['history']]==['user','assistant']*2


@pytest.mark.parametrize('patch',[
    {'session_id':'bad session'},{'session_id':'x'},{'npc_id':'boss'},
    {'message':''},{'message':'  '},{'message':'ą'*601},{'language':'de'},
    {'context':{'quest_id':'unknown'}},{'context':{'grant_item':'badge'}},
])
def test_validation(patch):
    with TestClient(create_app(Settings())) as client:
        response=client.post('/api/chat',json={**body(),**patch})
        assert response.status_code==422
        assert 'input' not in response.text


def test_no_key_and_no_paid_permission_never_call_meta():
    async def run():
        calls=[]
        def handler(request):
            calls.append(request)
            raise AssertionError('Real call not authorized')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            for settings in [Settings(mode='meta',api_key='secret'),Settings(mode='meta',allow_paid_requests=True)]:
                with pytest.raises(ProviderError) as exc:
                    await MetaProvider(settings,client).reply(ChatRequest(**body()),[])
                assert exc.value.status_code==503
        assert not calls
    asyncio.run(run())


def test_meta_request_contract_and_history_with_fake_http_only():
    async def run():
        def handler(request):
            assert str(request.url)=='https://api.meta.ai/v1/chat/completions'
            assert request.headers['authorization']=='Bearer test-secret'
            data=json.loads(request.content)
            assert data['model']=='muse-spark-1.3'
            assert data['messages'][0]['role']=='developer'
            assert 'never award items' in data['messages'][0]['content']
            assert data['messages'][1:3]==[{'role':'user','content':'Cześć'},{'role':'assistant','content':'Witaj'}]
            assert data['messages'][-1]['content']=='Nowe pytanie'
            assert data['reasoning_effort']=='minimal' and data['max_completion_tokens']==1024
            assert 'tools' not in data
            return httpx.Response(200,json={'choices':[{'message':{'content':'Odpowiedź testowa'}}]})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider=MetaProvider(Settings(mode='meta',api_key='test-secret',allow_paid_requests=True),client)
            result=await provider.reply(ChatRequest(**body(message='Nowe pytanie')),[Message(role='user',content='Cześć'),Message(role='assistant',content='Witaj')])
            assert result=='Odpowiedź testowa'
    asyncio.run(run())


@pytest.mark.parametrize('kind,status',[('timeout',504),('connection',502),('401',502),('429',429),('500',502),('invalid',502),('empty',502)])
def test_meta_errors_are_sanitized(kind,status):
    async def run():
        def handler(request):
            if kind=='timeout': raise httpx.ReadTimeout('SECRET',request=request)
            if kind=='connection': raise httpx.ConnectError('SECRET',request=request)
            if kind=='invalid': return httpx.Response(200,content=b'SECRET')
            if kind=='empty': return httpx.Response(200,json={'choices':[{'message':{'content':''}}]})
            return httpx.Response(int(kind),json={'detail':'SECRET'})
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(ProviderError) as error:
                await MetaProvider(Settings(mode='meta',api_key='SECRET',allow_paid_requests=True),client).reply(ChatRequest(**body()),[])
            assert error.value.status_code==status and 'SECRET' not in str(error.value)
    asyncio.run(run())


def test_unavailable_provider_does_not_break_health_or_add_history():
    with TestClient(create_app(Settings(mode='meta',allow_paid_requests=False))) as client:
        assert client.get('/health').status_code==200
        response=client.post('/api/chat',json=body())
        assert response.status_code==503
        assert not client.app.state.history.sessions['session-one'].messages


def test_history_serializes_turns_and_expires_without_mixing():
    async def run():
        now=[0.0]
        store=MemoryHistory(pairs=2,max_sessions=2,ttl=10,clock=lambda:now[0])
        order=[]
        async def turn(n):
            async with store.turn('one') as session:
                order.append(('start',n,len(session.messages)))
                await asyncio.sleep(.01)
                store.append(session,str(n),'reply')
                order.append(('end',n))
        await asyncio.gather(turn(1),turn(2))
        assert order==[('start',1,0),('end',1),('start',2,2),('end',2)]
        async with store.turn('two') as session:
            assert not session.messages
        async with store.turn('three'):
            assert 'one' not in store.sessions
        now[0]=11
        async with store.turn('four'):
            assert list(store.sessions)==['four']
        assert len(store.sessions)<=2
    asyncio.run(run())


def test_repository_does_not_evict_busy_session():
    async def run():
        store=MemoryHistory(max_sessions=1)
        async with store.turn('one'):
            with pytest.raises(SessionCapacityError):
                async with store.turn('two'): pass
    asyncio.run(run())


def test_api_deadline_and_unexpected_error_are_safe():
    class Slow:
        async def reply(self,request,history):
            await asyncio.sleep(5)
    class Broken:
        async def reply(self,request,history):
            raise RuntimeError('SECRET')
    for provider,code in [(Slow(),504),(Broken(),500)]:
        with TestClient(create_app(Settings(timeout=1),provider=provider)) as client:
            result=client.post('/api/chat',json=body())
            assert result.status_code==code and 'SECRET' not in result.text
            assert client.get('/health').status_code==200


def test_context_is_dialogue_only_and_persona_kept():
    request=ChatRequest(**body(context={'quest_id':'first_day','quest_status':'completed','has_badge':True}))
    messages=build_messages(request,[])
    assert 'untrusted client data' in messages[0]['content']
    assert 'context=' not in messages[0]['content']
    assert any(m['role']=='user' and '"quest_status": "completed"' in m['content'] for m in messages)
    assert 'Only the game engine changes' in messages[0]['content']
    assert 'turquoise badge terminal' in messages[0]['content']
    assert 'There is no reception desk' in messages[0]['content']


def test_mock_mode_ignores_configured_api_key():
    with TestClient(create_app(Settings(mode='mock',api_key='SECRET',allow_paid_requests=True))) as client:
        assert client.post('/api/chat',json=body()).json()['provider']=='mock'
