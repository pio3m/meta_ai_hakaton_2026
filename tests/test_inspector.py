import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.inspector import CallStore, active_call
from backend.models import ChatRequest
from backend.providers import MetaProvider
from backend.admin_routes import Access

OWNER='inspector-test-owner-0123456789abcdef'
API_SECRET='api-secret-canary-abcdef0123456789'

def config(**kwargs):
    return Settings(inspector_token=OWNER,**kwargs)

def body(session='private-session-one',message='Gdzie odebrać identyfikator?'):
    return {'session_id':session,'npc_id':'buddy','message':message,'language':'pl','context':{'quest_id':'first_day','quest_status':'in_progress','has_badge':False}}

def login(client):
    response=client.post('/admin/api/login',json={'token':OWNER})
    assert response.status_code==200
    return response


def test_owner_auth_cookie_logout_and_no_cache():
    with TestClient(create_app(config())) as client:
        for path in ['/admin/api/calls','/admin/api/calls/anything']:
            assert client.get(path).status_code==401
        shell=client.get('/admin')
        assert shell.status_code==200 and OWNER not in shell.text
        assert shell.headers['cache-control']=='no-store'
        assert "frame-ancestors 'none'" in shell.headers['content-security-policy']
        assert client.post('/admin/api/login',json={'token':'incorrect-token-0123456789'}).status_code==401
        response=login(client)
        cookie=response.headers['set-cookie'].lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie
        assert client.get('/admin/api/calls').status_code==200
        assert client.post('/admin/api/logout').status_code==200
        assert client.get('/admin/api/calls').status_code==401


def test_admin_disabled_without_token_and_csrf_rejected():
    with TestClient(create_app(Settings())) as client:
        assert client.post('/admin/api/login',json={'token':OWNER}).status_code==503
    with TestClient(create_app(config())) as client:
        login(client)
        assert client.post('/admin/api/demo',headers={'Origin':'https://evil.example'}).status_code==403
        assert client.post('/admin/api/demo',headers={'Origin':'http://testserver'}).status_code==200


def test_records_limit_and_redaction():
    store=CallStore(secrets=(API_SECRET,OWNER))
    for i in range(205):
        cid=store.start(ChatRequest(**body(message=f'{API_SECRET} {OWNER} Bearer abcdef123456 password=hello {i}')),'meta','muse-spark-1.3')
        store.finish(cid,reply='Authorization Bearer topsecret')
    rows=store.list()
    assert len(rows)==200
    text=json.dumps(rows)
    assert API_SECRET not in text and OWNER not in text and 'abcdef123456' not in text and 'password=hello' not in text
    assert 'topsecret' not in text
    assert rows[0]['message'].endswith('204') and rows[-1]['message'].endswith('5')
    assert store.get('missing') is None


def test_real_payload_tokens_model_reply_and_elapsed_captured_using_fake_http():
    captured=[]
    store=CallStore(secrets=(API_SECRET,OWNER))
    request=ChatRequest(**body())
    async def run():
        def handler(req):
            captured.append(json.loads(req.content))
            return httpx.Response(200,json={'model':'muse-spark-1.3-server','usage':{'prompt_tokens':123,'completion_tokens':45,'total_tokens':168,'unsafe':'not logged'},'choices':[{'message':{'content':'Odbierz identyfikator przy terminalu.'}}]})
        cid=store.start(request,'meta','muse-spark-1.3')
        token=active_call.set((store,cid))
        try:
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
                reply=await MetaProvider(config(mode='meta',api_key=API_SECRET,allow_paid_requests=True),client).reply(request,[])
            store.finish(cid,reply=reply)
        finally:
            active_call.reset(token)
        row=store.get(cid)
        assert row['request_payload']==captured[0]
        assert row['sent_to_model'] is True
        assert row['model']=='muse-spark-1.3-server'
        assert row['usage']=={'prompt_tokens':123,'completion_tokens':45,'total_tokens':168}
        assert row['upstream_status']==200 and row['elapsed_ms']>=0
        assert row['reply']==reply
        assert 'Authorization' not in json.dumps(row)
    asyncio.run(run())


def test_error_is_recorded_without_internal_exception_or_secret():
    class Broken:
        async def reply(self,request,history):
            raise RuntimeError(API_SECRET)
    with TestClient(create_app(config(api_key=API_SECRET),provider=Broken())) as client:
        assert client.post('/api/chat',json=body()).status_code==500
        login(client)
        rows=client.get('/admin/api/calls').json()['calls']
        assert rows[0]['state']=='error' and rows[0]['error']
        assert API_SECRET not in json.dumps(rows)


def test_jury_only_sees_demo_session_not_prompt_or_other_history():
    app=create_app(config())
    with TestClient(app) as owner, TestClient(app) as jury:
        login(owner)
        grant=owner.post('/admin/api/demo').json()
        session=grant['game_url'].split('=',1)[1]
        owner.post('/api/chat',json=body('private-session-other','PRIVATE CANARY'))
        owner.post('/api/chat',json=body(session,'DEMO QUESTION'))
        assert jury.get('/admin/jury/api/calls').status_code==401
        assert jury.post('/admin/jury/api/login',json={'token':grant['jury_token']}).status_code==200
        result=jury.get('/admin/jury/api/calls').json()
        assert len(result['calls'])==1
        assert result['calls'][0]['message']=='DEMO QUESTION'
        assert 'PRIVATE CANARY' not in json.dumps(result)
        assert 'session_id' not in result['calls'][0]
        assert 'request_payload' not in result['calls'][0]
        assert 'messages' not in result['calls'][0]
        assert jury.get('/admin/api/calls').status_code==401
        row_id=result['calls'][0]['id']
        assert jury.get('/admin/api/calls/'+row_id).status_code==401
        assert jury.post('/admin/api/demo').status_code==401
        assert len(owner.get('/admin/api/calls').json()['calls'])==2
        assert owner.post('/admin/api/demo/revoke').status_code==200
        assert jury.get('/admin/jury/api/calls').status_code==401


def test_jury_expiry_and_new_demo_revoke_previous_access():
    now=[0.0]
    access=Access(OWNER,clock=lambda:now[0])
    first=access.new_demo()
    assert access.jury_session(first['jury_token'])
    access.new_demo()
    from fastapi import HTTPException
    with pytest.raises(HTTPException): access.jury_session(first['jury_token'])
    last=access.new_demo();now[0]=1801
    with pytest.raises(HTTPException): access.jury_session(last['jury_token'])


def test_mock_labels_and_no_estimated_tokens():
    with TestClient(create_app(config())) as client:
        client.post('/api/chat',json=body())
        login(client)
        row=client.get('/admin/api/calls').json()['calls'][0]
        assert row['provider']=='mock' and row['usage'] is None and row['sent_to_model'] is False
        detail=client.get('/admin/api/calls/'+row['id']).json()
        assert detail['request_payload']['messages'][0]['role']=='developer'
        assert 'context=' not in detail['request_payload']['messages'][0]['content']
        assert any(m['role']=='user' and 'GAME_CONTEXT_DATA' in m['content'] for m in detail['request_payload']['messages'])


def test_pending_call_visible_before_reply():
    async def run():
        entered=asyncio.Event();release=asyncio.Event()
        class Slow:
            async def reply(self,request,history):
                entered.set();await release.wait();return 'Done'
        app=create_app(config(),provider=Slow())
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver') as client:
                await client.post('/admin/api/login',json={'token':OWNER})
                task=asyncio.create_task(client.post('/api/chat',json=body()))
                await entered.wait()
                rows=(await client.get('/admin/api/calls')).json()['calls']
                assert rows[0]['state']=='pending' and rows[0]['elapsed_ms'] is None
                release.set();await task
                rows=(await client.get('/admin/api/calls')).json()['calls']
                assert rows[0]['state']=='ok'
    asyncio.run(run())


def test_login_rate_limit_and_session_expiration():
    now=[0.0];access=Access(OWNER,clock=lambda:now[0])
    from fastapi import HTTPException
    for _ in range(20):
        with pytest.raises(HTTPException): access.login('invalid-token')
    with pytest.raises(HTTPException) as error: access.login(OWNER)
    assert error.value.status_code==429
    now[0]=61
    cookie=access.login(OWNER)
    now[0]+=8*3600+1
    from starlette.requests import Request
    request=Request({'type':'http','headers':[(b'cookie',('chess_inspector_owner='+cookie).encode())]})
    with pytest.raises(HTTPException): access.owner(request)

def test_concurrent_call_contexts_do_not_mix_prompts():
    from backend.inspector import record_request
    async def run():
        store=CallStore()
        async def one(session,message):
            cid=store.start(ChatRequest(**body(session,message)),'mock','mock')
            token=active_call.set((store,cid))
            try:
                await asyncio.sleep(.01)
                record_request({'messages':[{'role':'user','content':message}]},sent=False)
                await asyncio.sleep(.01)
                store.finish(cid,reply=message)
            finally: active_call.reset(token)
            return store.get(cid)
        a,b=await asyncio.gather(one('session-one','FIRST'),one('session-two','SECOND'))
        assert a['request_payload']['messages'][0]['content']=='FIRST' and a['reply']=='FIRST'
        assert b['request_payload']['messages'][0]['content']=='SECOND' and b['reply']=='SECOND'
    asyncio.run(run())


def test_jury_cannot_change_scope_using_query_or_owner_login():
    app=create_app(config())
    with TestClient(app) as owner,TestClient(app) as jury:
        login(owner)
        grant=owner.post('/admin/api/demo').json()
        demo=grant['game_url'].split('=',1)[1]
        owner.post('/api/chat',json=body(demo,'Public demo'))
        owner.post('/api/chat',json=body('session-private','Do not disclose'))
        assert jury.post('/admin/jury/api/login',json={'token':grant['jury_token']}).status_code==200
        assert jury.post('/admin/api/login',json={'token':grant['jury_token']}).status_code==401
        data=jury.get('/admin/jury/api/calls?session_id=session-private').json()
        assert len(data['calls'])==1 and data['calls'][0]['message']=='Public demo'
