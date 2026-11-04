import asyncio
import copy
import json
from collections import deque
import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.history import Session
from backend.inspector import active_call
from backend.providers import ProviderError
from backend.settings import Settings
from backend.world_ai import MetaWorldProvider, WorldBudget, world_payload
from backend.world_models import WorldPlan, WorldRequest, load_world_data, parse_world_plan
from game.living_world import LivingWorld
from game.world_contract import action, local_world_plan, validate_world_plan

RULES, SCENE = load_world_data()

def request_body(session='world-test-one', revision=1):
    world=LivingWorld(SCENE,session,network_enabled=False)
    return dict(session_id=session,revision=revision,reason='interval',snapshot=world.snapshot([350,440],False))

@pytest.mark.parametrize('mutation',[
    lambda p:p.update(schema_version=True),
    lambda p:p.update(code='print(1)'),
    lambda p:p['decisions'].pop(),
    lambda p:p['decisions'][0].update(npc_id='hacker'),
    lambda p:p['decisions'][0].update(mood='violent'),
    lambda p:p['decisions'][0]['actions'][0].update(action='EXECUTE'),
    lambda p:p['decisions'][0]['actions'][0].update(duration_s=True),
    lambda p:p['decisions'][0]['actions'][0].update(route=['outside','center']),
    lambda p:p['decisions'][0]['actions'][0].update(route=['center','center']),
    lambda p:p['decisions'][0].update(actions=[action('TALK_TO','buddy',text='Self')]),
    lambda p:p['decisions'][0].update(actions=[action('INSPECT_TERMINAL','buddy_post')]),
    lambda p:p['decisions'][0].update(actions=[action('MOVE_TO','player')]),
    lambda p:p['decisions'][0].update(actions=[action('REACT_TO_PLAYER','player')]),
    lambda p:p['decisions'][0].update(goal='bad\ncontrol'),
])
def test_invalid_world_plans_rejected_on_both_boundaries(mutation):
    p=local_world_plan();mutation(p)
    with pytest.raises(ValueError):validate_world_plan(p,RULES,SCENE)
    with pytest.raises(ValueError):WorldPlan.model_validate(p)

def test_closed_json_no_duplicate_keys_or_markdown():
    for raw in ['{"schema_version":1,"schema_version":1}', '```json\n{}\n```', 'x'*24001]:
        with pytest.raises(ValueError):parse_world_plan(raw)
    assert parse_world_plan(json.dumps(local_world_plan())).schema_version==1

def test_snapshot_rejects_outside_scene_and_duplicate_npcs():
    for change in ['player','npc','duplicate','buddy']:
        b=request_body()
        if change=='player':b['snapshot']['player_position']=[-1,440]
        elif change=='npc':b['snapshot']['npcs'][2]['position']=[200,float('nan')]
        elif change=='duplicate':b['snapshot']['npcs'][0]['npc_id']='hacker'
        else:b['snapshot']['npcs'][0]['position']=[100,440]
        with pytest.raises(ValueError):WorldRequest.model_validate(b)

def test_four_npcs_move_without_player_and_keep_buddy_available():
    w=LivingWorld(SCENE,'local-world',network_enabled=False)
    before={n:list(a['position']) for n,a in w.npcs.items()}
    for _ in range(200):w.update(.1,[36,422],False)
    assert all(w.npcs[n]['position']!=before[n] for n in before)
    assert 515<=w.npcs['buddy']['position'][0]<=565
    assert len(w.events)<=12 and all(len(a['memory'])<=6 for a in w.npcs.values())
    assert any(a['bubble_ttl'] for a in w.npcs.values())
    assert {'PATROL','TALK_TO','MOVE_TO','INSPECT_TERMINAL'}<={a['action'] for a in w.completed}
    assert all(a['source']=='FALLBACK' for a in w.completed)

def test_atomic_invalid_plan_and_buddy_freezes_only_during_chat():
    w=LivingWorld(SCENE,'local-world',network_enabled=False)
    before=copy.deepcopy(w.npcs);bad=local_world_plan();bad['decisions'][-1]['goal']=''
    with pytest.raises(ValueError):w.apply_plan(bad,'META')
    assert w.npcs==before
    for _ in range(20):w.update(.1,[350,440],False,True)
    assert w.npcs['buddy']['position']==before['buddy']['position']
    assert w.npcs['security']['position']!=before['security']['position']

def test_all_six_actions_execute_and_are_traced_with_actual_source():
    w=LivingWorld(SCENE,'local-world',network_enabled=False)
    w.npcs['security']['position']=[550,440]
    w.npcs['employee']['position']=[235,432]
    p=local_world_plan()
    p['decisions'][0]['actions']=[action('REACT_TO_PLAYER','player',duration=3,text='Witaj!'),action('WAIT',duration=2),action('PATROL',route=['buddy_left','buddy_right'],duration=2)]
    p['decisions'][1]['actions']=[action('TALK_TO','buddy',duration=3,text='Raport!')]
    p['decisions'][2]['actions']=[action('MOVE_TO','west_corner',duration=3)]
    p['decisions'][3]['actions']=[action('INSPECT_TERMINAL','badge_terminal',duration=6,text='Raport gotowy.')]
    w.apply_plan(p,'META','a'*32)
    for _ in range(90):w.update(.1,[350,422],False)
    observed=[a for a in w.completed if a['plan_id']=='a'*32]
    assert {a['action'] for a in observed}=={'MOVE_TO','PATROL','WAIT','TALK_TO','INSPECT_TERMINAL','REACT_TO_PLAYER'}
    assert all(a['source']=='META' for a in observed)
    assert all(a['status']=='completed' for a in observed)
    w.player_interaction(w.npcs['security']['position'])
    assert w.npcs['security']['bubble_source']=='FALLBACK'

def test_budget_is_global_bounded_paced_and_unknown_tokens_reserved():
    async def run():
        now=[0.];s=Settings(world_ai_mode='meta',world_ai_allow_paid_requests=True,api_key='test',world_ai_global_limit=2)
        b=WorldBudget(s,clock=lambda:now[0]);one=Session(deque(),0);two=Session(deque(),0)
        r=await b.reserve(one,{})
        with pytest.raises(ProviderError,match='WORLD_MIN_INTERVAL'):await b.reserve(two,{})
        await b.settle(r,None);assert b.tokens==r
        now[0]=31;r2=await b.reserve(two,{})
        await b.settle(r2,{'total_tokens':100});assert b.tokens==r+100
        now[0]=62
        with pytest.raises(ProviderError,match='WORLD_GLOBAL_LIMIT'):await b.reserve(Session(deque(),0),{})
        assert b.calls==2 and one.world_paid_calls==two.world_paid_calls==1
    asyncio.run(run())

@pytest.mark.parametrize('patch,reason',[
    ({'world_ai_allow_paid_requests':False},'WORLD_PAID_DISABLED'),
    ({'api_key':''},'WORLD_KEY_MISSING'),
    ({'world_ai_token_budget':1000},'WORLD_TOKEN_BUDGET'),
])
def test_paid_gates_before_http(patch,reason):
    async def run():
        s=Settings(**({'world_ai_mode':'meta','world_ai_allow_paid_requests':True,'api_key':'test'}|patch))
        budget=WorldBudget(s)
        with pytest.raises(ProviderError,match=reason):await budget.reserve(Session(deque(),0),{})
        assert budget.calls==0
    asyncio.run(run())

def test_api_mock_idempotency_execution_validation_and_owner_inspector():
    app=create_app(Settings(inspector_token='owner-test-token-long-enough'))
    with TestClient(app) as c:
        b=request_body();r=c.post('/api/world/plan',json=b);assert r.status_code==200,r.text
        data=r.json();assert data['provider']=='mock' and data['validation']['valid']
        assert c.post('/api/world/plan',json=b).json()['cached']
        assert len(app.state.inspector.calls)==1
        trace=dict(session_id=b['session_id'],call_id=data['call_id'],snapshot=b['snapshot'],completed_actions=[])
        assert c.post('/api/world/execution',json=trace).status_code==200
        trace['completed_actions']=[dict(npc_id='buddy',action='PATROL',target_id='none',status='completed',source='MOCK',plan_id=data['call_id'])]
        assert c.post('/api/world/execution',json=trace).status_code==200
        empty_trace={**trace,'completed_actions':[]}
        assert len(c.post('/api/world/execution',json=empty_trace).json()['execution']['completed_actions'])==1
        trace['completed_actions'][0]['action']='INSPECT_TERMINAL'
        assert c.post('/api/world/execution',json=trace).status_code==422
        trace['session_id']='another-session'
        assert c.post('/api/world/execution',json=trace).status_code==404
        assert c.get('/admin/api/calls').status_code==401
        assert c.post('/admin/api/login',json={'token':'owner-test-token-long-enough'}).status_code==200
        detail=c.get('/admin/api/calls/'+data['call_id']).json()
        assert detail['kind']=='world' and detail['validation']['valid']
        assert detail['request_payload']['response_format']['json_schema']['strict']
        assert not detail['sent_to_model']
        assert c.get('/admin/api/calls').json()['world_mode']=='mock'

@pytest.mark.parametrize('failure',['invalid','timeout','provider'])
def test_failed_world_generation_no_retry_and_clear_fallback(failure):
    class Broken:
        calls=0
        async def generate(self,*args):
            self.calls+=1
            if failure=='timeout':raise TimeoutError()
            if failure=='provider':raise ProviderError(502,'Upstream unavailable')
            return '{"schema_version":99}'
    broken=Broken();app=create_app(Settings(),world_provider=broken)
    with TestClient(app) as c:
        b=request_body();d=c.post('/api/world/plan',json=b).json()
        assert d['provider']=='fallback' and d['validation']['valid'] and d['error_detail']
        WorldPlan.model_validate(d['plan'])
        assert c.post('/api/world/plan',json=b).json()['cached']
        assert broken.calls==1
        row=app.state.inspector.get(d['call_id'])
        assert row['state']=='error' and not row['validation']['valid'] and row['plan_source']=='FALLBACK'

def test_real_adapter_contract_uses_fake_http_only_no_other_llm():
    async def run():
        calls=[]
        def handler(req):
            payload=json.loads(req.content);calls.append(payload)
            assert payload['model']=='muse-spark-1.3'
            assert payload['response_format']['json_schema']['schema']['additionalProperties'] is False
            assert 'short memories' in payload['messages'][0]['content']
            return httpx.Response(200,json={'model':'muse-spark-1.3','choices':[{'message':{'content':json.dumps(local_world_plan())}}],'usage':{'total_tokens':1500}})
        s=Settings(world_ai_mode='meta',world_ai_allow_paid_requests=True,api_key='fake-only')
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as h:
            raw=await MetaWorldProvider(s,h).generate(WorldRequest.model_validate(request_body()),RULES)
            WorldPlan.model_validate(json.loads(raw))
        assert len(calls)==1
    asyncio.run(run())

def test_client_mock_async_batch_and_telemetry_without_per_frame_requests():
    async def run():
        calls=[]
        async def transport(body,path):
            calls.append((body,path))
            if path.endswith('execution'):return {'ok':True}
            return dict(plan=local_world_plan(),provider='mock',validation={'valid':True},call_id='a'*32,limits={'session_limit':1,'remaining_calls':0})
        w=LivingWorld(SCENE,'async-test',transport=transport,network_enabled=True)
        for _ in range(400):w.update(.1,[350,440]);await asyncio.sleep(0)
        assert sum(p.endswith('/plan') for _,p in calls)==1
        assert any(p.endswith('/execution') for _,p in calls)
        assert w.last_source=='MOCK'
        assert all(a['source']=='MOCK' for a in w.completed)
        w.cancel()
    asyncio.run(run())

def test_api_paid_attempts_count_failures_cache_and_cross_session_budget():
    class Fake:
        calls=0
        async def generate(self,*args):self.calls+=1;raise TimeoutError()
    fake=Fake();s=Settings(world_ai_mode='meta',world_ai_allow_paid_requests=True,api_key='fake',world_ai_global_limit=1)
    app=create_app(s,world_provider=fake)
    with TestClient(app) as c:
        first=c.post('/api/world/plan',json=request_body()).json()
        assert first['provider']=='fallback' and first['limits']['global_paid_calls']==1
        assert c.post('/api/world/plan',json=request_body()).json()['cached']
        second=c.post('/api/world/plan',json=request_body('other-world')).json()
        assert second['provider']=='fallback' and second['error_detail']=='WORLD_GLOBAL_LIMIT'
        assert fake.calls==1

def test_world_jury_is_scoped_and_no_full_payload_or_raw_invalid_output():
    s=Settings(inspector_token='long-enough-test-admin-token');app=create_app(s)
    with TestClient(app) as owner, TestClient(app) as jury:
        owner.post('/admin/api/login',json={'token':'long-enough-test-admin-token'})
        demo=owner.post('/admin/api/demo').json()
        jury.post('/admin/jury/api/login',json={'token':demo['jury_token']})
        owner.post('/api/world/plan',json=request_body('private-world'))
        result=owner.post('/api/world/plan',json=request_body(demo['game_url'].split('=')[1])).json()
        rows=jury.get('/admin/jury/api/calls').json()['calls']
        assert len(rows)==1 and rows[0]['id']==result['call_id']
        assert all(k not in rows[0] for k in ('request_payload','session_id','response_json','fallback_plan'))
        assert rows[0]['reply']=='Plan zatwierdzony'
        assert jury.get('/admin/api/calls').status_code==401

def test_next_planning_payload_includes_short_memory_after_events():
    w=LivingWorld(SCENE,'memory-test',network_enabled=False)
    w.event('Security ostrzegł Hackera przy terminalu.',('security','hacker'),'META',True)
    body=WorldRequest.model_validate(dict(session_id='memory-test',revision=2,reason='event',snapshot=w.snapshot([350,440],False)))
    payload=world_payload(body,Settings(),RULES)
    state=json.loads(payload['messages'][1]['content'])['world']
    assert 'Security ostrzegł Hackera przy terminalu.' in state['npcs'][2]['memory']
    assert state['events'][-1]=='Security ostrzegł Hackera przy terminalu.'

def test_client_real_clock_spacing_has_network_margin_even_with_fast_frames():
    async def run():
        now=[0.];calls=[]
        async def transport(body,path):
            if not path.endswith('/plan'):return {}
            calls.append(now[0]);return dict(plan=local_world_plan(),provider='mock',validation={'valid':True},call_id='a'*32,limits={'session_limit':3,'remaining_calls':2,'min_interval_seconds':30})
        w=LivingWorld(SCENE,'pace-test',transport=transport,network_enabled=True,network_clock=lambda:now[0])
        for _ in range(400):w.update(.1,[350,440]);await asyncio.sleep(0)
        assert calls==[0.] # Simulation time alone cannot spend another call.
        now[0]=30.;w.update(.1,[350,440]);await asyncio.sleep(0)
        assert calls==[0.]
        now[0]=31.;w.update(.1,[350,440]);await asyncio.sleep(0)
        assert calls==[0.]
        now[0]=32.;w.update(.1,[350,440]);await asyncio.sleep(0)
        assert calls==[0.,32.]
        w.cancel()
    asyncio.run(run())

def test_pinned_buddy_can_greet_stationary_recruit_without_losing_first_quest():
    w=LivingWorld(SCENE,'react-test',network_enabled=False);p=local_world_plan()
    p['decisions'][0]['actions']=[action('REACT_TO_PLAYER','player',duration=4,text='Witaj, rekrucie!')]
    w.apply_plan(p,'META','a'*32)
    for _ in range(25):w.update(.1,[350,440],False)
    assert any(a['npc_id']=='buddy' and a['action']=='REACT_TO_PLAYER' and a['status']=='completed' for a in w.completed)
    assert 515<=w.npcs['buddy']['position'][0]<=565


@pytest.mark.parametrize('npc_id',['buddy','security','hacker','employee'])
def test_approach_pauses_npc_faces_player_and_resumes_with_hysteresis(npc_id):
    w=LivingWorld(SCENE,'approach-test',network_enabled=False)
    a=w.npcs[npc_id];position=list(a['position'])
    player=[position[0]-50,position[1]]
    for _ in range(40):w.update(.1,player)
    assert a['position']==position and a['player_engaged'] and not a['moving']
    assert a['facing_left'] and a['state']=='WAIT' and a['bubble_ttl']>0
    assert a['elapsed']==0 # A paused action does not expire during conversation.
    w.update(.1,[position[0]-80,position[1]])
    assert a['player_engaged'] and a['position']==position
    for _ in range(2):w.update(.1,[36,422] if npc_id!='hacker' else [924,482])
    assert not a['player_engaged'] and a['moving']


def test_e_chooses_nearest_npc_and_conversation_is_visible_without_llm():
    w=LivingWorld(SCENE,'conversation-test',network_enabled=False)
    w.npcs['employee']['position']=[420,460]
    w.npcs['security']['position']=[470,460]
    assert w.player_interaction([415,460])
    assert w.visible_speaker=='employee'
    assert w.npcs['employee']['player_engaged']
    first=w.visible_utterance
    assert w.player_interaction([415,460]) and w.visible_utterance!=first
    assert not w.npcs['security'].get('player_engaged')
    assert w.requests_sent==0
