import asyncio
import copy
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.director import mock_plan,MetaDirector,director_payload
from backend.director_models import parse_plan,load_rules,validate_scene,DirectorRequest
from game.director import Director,validate_plan
from game.data import load_content
from game.quests import Quest

BODY={'session_id':'director-test-session','context':{'quest_status':'completed','has_badge':True}}
OWNER='director-test-owner-0123456789abcdef'

class Fake:
    def __init__(self,value):self.value=value;self.calls=0
    async def generate(self,*args):self.calls+=1;return self.value

@pytest.mark.parametrize('slot',['east_side','west_side'])
def test_valid_scene_and_client(slot):
    rules,scene=load_rules();plan=mock_plan('test');plan['place_object']['spawn_point']=slot
    assert validate_scene(parse_plan(json.dumps(plan)),rules,scene)['position']==rules['spawn_points'][slot]
    assert validate_plan(plan,scene,rules)['position']==rules['spawn_points'][slot]
    blocked=copy.deepcopy(scene);blocked['blocked_areas']=[[36,422,924,482]]
    with pytest.raises(ValueError):validate_scene(parse_plan(json.dumps(plan)),rules,blocked)
    with pytest.raises(ValueError):validate_plan(plan,blocked,rules)

@pytest.mark.parametrize('mutation',[
 lambda p:p.update(code='exec(1)'),lambda p:p.update(schema_version=True),
 lambda p:p['place_object'].update(action='spawn_npc'),lambda p:p['place_object'].update(spawn_point='buddy'),
 lambda p:p['create_quest']['quest']['completion'].update(type='run_code'),
 lambda p:p['create_quest']['quest'].update(title='x'*65),lambda p:p['create_quest']['quest'].update(title='bad\ntext'),
 lambda p:p['place_object'].update(position=[1,2]),lambda p:p['place_object'].update(id='buddy'),
])
def test_reject_untrusted_plans(mutation):
    plan=mock_plan('test');mutation(plan);rules,scene=load_rules()
    with pytest.raises(ValueError):parse_plan(json.dumps(plan))
    with pytest.raises(ValueError):validate_plan(plan,scene,rules)

@pytest.mark.parametrize('raw',['```json\n{}\n```','null','{"schema_version":1,"schema_version":1}','x'*16001])
def test_invalid_json(raw):
    with pytest.raises(ValueError):parse_plan(raw)

def test_endpoint_and_inspector_idempotency():
    fake=Fake(json.dumps(mock_plan('test')))
    app=create_app(Settings(inspector_token=OWNER),director_provider=fake)
    with TestClient(app) as c:
        assert c.post('/api/director',json={**BODY,'context':{'quest_status':'in_progress'}}).status_code==409
        first=c.post('/api/director',json=BODY);assert first.status_code==200
        assert c.post('/api/director',json={**BODY,'retry':True}).json()['cached']
        assert fake.calls==1
        assert c.get('/admin/api/calls').status_code==401
        c.post('/admin/api/login',json={'token':OWNER})
        row=c.get('/admin/api/calls/'+first.json()['call_id']).json()
        assert row['kind']=='director' and row['validation']['valid'] and row['response_json']==first.json()['plan']
        jury=app.state.inspector.list(BODY['session_id'],jury=True)[0]
        assert 'request_payload' not in jury and 'response_json' not in jury and 'session_id' not in jury
        assert jury['validated_plan']==first.json()['plan']

def test_invalid_cached_until_explicit_retry():
    fake=Fake('{"code":"private-invalid-raw"}')
    app=create_app(Settings(),director_provider=fake)
    with TestClient(app) as c:
        assert c.post('/api/director',json=BODY).status_code==422
        assert c.post('/api/director',json=BODY).status_code==422
        assert fake.calls==1
        row=app.state.inspector.list(BODY['session_id'],jury=True)[0]
        assert row['validation']['valid'] is False and 'private-invalid' not in json.dumps(row)
        fake.value=json.dumps(mock_plan('test'))
        assert c.post('/api/director',json={**BODY,'retry':True}).status_code==200
        assert fake.calls==2

def test_meta_requires_separate_consent_and_structured_payload():
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:pytest.fail('No HTTP allowed'))) as client:
            settings=Settings(mode='meta',allow_paid_requests=True,api_key='fake-key')
            with pytest.raises(Exception,match='osobna zgoda'):
                await MetaDirector(settings,client).generate(DirectorRequest(**BODY),load_rules()[0])
            payload=director_payload(DirectorRequest(**BODY),settings,load_rules()[0])
            assert payload['response_format']['json_schema']['strict'] is True
            assert payload['response_format']['json_schema']['schema']['additionalProperties'] is False
    asyncio.run(run())

def test_complete_first_and_generated_quest_via_real_mock_endpoint():
    scene,data,_=load_content();quest=Quest(data)
    with TestClient(create_app(Settings())) as client:
        async def transport(body,path):return await asyncio.to_thread(lambda:client.post(path,json=body).json())
        async def run():
            d=Director(scene,transport)
            assert not d.start(quest,'integration-session')
            for target in ['buddy','corporate_entrance','buddy']:quest.interact(target)
            assert quest.complete and quest.reward_count==1
            assert d.start(quest,'integration-session')
            await d.task;d.poll(quest)
            assert d.state=='active' and not d.collect((500,440),quest)
            pos=d.object['position'];assert d.collect(pos,quest)
            assert not d.collect(pos,quest) and d.collected=={'director_package'}
            assert quest.reward_count==1 and quest.inventory=={'employee_badge'}
            assert d.context()['status']=='completed'
            assert not d.start(quest,'integration-session',retry=True)
        asyncio.run(run())

def test_client_rejects_atomically_and_cancel():
    scene,data,_=load_content();q=Quest(data)
    for target in ['buddy','corporate_entrance','buddy']:q.interact(target)
    async def transport(*args):return {'plan':{'code':'bad'},'validation':{'valid':True}}
    async def run():
        d=Director(scene,transport);d.start(q,'invalid-session');await d.task;d.poll(q)
        assert d.state=='error' and d.object is None and d.plan is None
        d.start(q,'invalid-session',retry=True);task=d.task;d.cancel()
        await asyncio.sleep(0)
        assert task.cancelled() and d.task is None
    asyncio.run(run())


def test_meta_http_adapter_with_fake_upstream():
    from backend.inspector import CallStore, active_call
    from backend.director_models import DirectorRequest
    async def run():
        captured=[]
        def upstream(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200,json={'model':'muse-spark-1.3','usage':{'prompt_tokens':100,'completion_tokens':80,'total_tokens':180},'choices':[{'message':{'content':json.dumps(mock_plan('test'))}}]})
        settings=Settings(director_mode='meta',allow_paid_requests=True,director_allow_paid_requests=True,api_key='synthetic-key')
        request=DirectorRequest(**BODY);store=CallStore();cid=store.start(request,'meta',settings.model,kind='director')
        token=active_call.set((store,cid))
        try:
            async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
                raw=await MetaDirector(settings,client).generate(request,load_rules()[0])
                assert parse_plan(raw).schema_version==1
        finally:active_call.reset(token)
        assert captured[0]['response_format']['type']=='json_schema'
        assert store.get(cid)['usage']['total_tokens']==180 and store.get(cid)['sent_to_model']
    asyncio.run(run())


def test_timeout_is_cached_and_inspected():
    class Slow:
        calls=0
        async def generate(self,*args):
            self.calls+=1
            await asyncio.sleep(2)
    slow=Slow();app=create_app(Settings(timeout=1),director_provider=slow)
    with TestClient(app) as client:
        assert client.post('/api/director',json=BODY).status_code==504
        assert client.post('/api/director',json=BODY).status_code==504
        assert slow.calls==1
        row=app.state.inspector.list()[0]
        assert row['state']=='error' and row['validation']['stage']=='generation'


def test_concurrent_generation_is_single_and_reset_cancels():
    from concurrent.futures import ThreadPoolExecutor
    app=create_app(Settings())
    with TestClient(app) as client:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:client.post('/api/director',json=BODY).json(),range(2)))
        assert sorted(r['cached'] for r in results)==[False,True]
        assert len(app.state.inspector.list())==1
    import os
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from main import Game
    pygame.init();pygame.display.set_mode((960,540))
    try:
        game=Game();old=game.director;session=game.chat.session_id
        game.reset()
        assert game.director is not old and game.director.state=='idle'
        assert game.chat.session_id!=session and not game.quest.complete
    finally:pygame.quit()


@pytest.mark.parametrize('status',['active','completed'])
def test_buddy_receives_director_context(status):
    from backend.models import ChatRequest
    from backend.providers import build_messages,MockProvider
    body={**BODY,'message':'Co teraz?','context':{**BODY['context'],'director_quest':{'id':'director_delivery','title':'Nośnik danych','objective':'Odbierz nośnik po lewej.','status':status}}}
    request=ChatRequest(**body)
    messages=build_messages(request,[])
    assert 'director_delivery' not in messages[0]['content']
    assert any(m['role']=='user' and 'director_delivery' in m['content'] for m in messages)
    reply=asyncio.run(MockProvider().reply(request,[]))
    assert ('ukończone' if status=='completed' else 'Odbierz nośnik po lewej.') in reply
