import asyncio,json,copy
from collections import defaultdict
from types import SimpleNamespace
import httpx,pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.models import ChatRequest
from backend.providers import build_messages
from backend.asset_generator import AssetGenerator,AssetRequest
from backend.inspector import CallStore
from game.job_contract import validate_jobs,replay_jobs,objects_for_jobs
from tests.test_locations import game
from tests.test_asset_generator import encoded_image

PLAN={'schema_version':1,'jobs':[{'id':'job_a','title':'Ogniwa dla Nyx','description':'Odbierz ogniwo dla ulicznych łowców.','item_label':'Ogniwo','reward':20,'placements':[{'location_id':'bar','slot':'A'}]},{'id':'job_b','title':'Audyt nośników','description':'Zbierz plik audytu z ulicy.','item_label':'Plik audytu','reward':25,'placements':[{'location_id':'corporate_street','slot':'B'}]}]}

def test_provocation_attacks_outside_rat_contract_and_guard_retaliates(game):
    import pygame
    game.player.x,game.player.y=660,450;guard=game.living.npcs['security'];guard['position']=[700,450]
    game.adventure.weapon=True;game.key(pygame.K_SPACE)
    assert guard['hostile'] and guard['combat_hp']==22 and game.adventure.state=='available'
    for _ in range(12):game.update(.1,defaultdict(bool))
    assert game.adventure.health<100
    for _ in range(11):game.adventure.cooldown=0;game.adventure.attack(guard['position'],False)
    assert guard['down_time']==12 and not guard['hostile']
    for _ in range(125):game.living.update(.1,[40,440],False)
    assert guard['combat_hp']==24 and guard['down_time']==0

def test_each_npc_chat_has_identity_and_separate_history():
    class Echo:
        async def reply(self,request,history):return 'Postać '+request.npc_id+', pamięć '+str(len(history))+'.'
    app=create_app(Settings(),provider=Echo())
    with TestClient(app) as c:
        def ask(npc):return c.post('/api/chat',json={'session_id':'npc-history-test','npc_id':npc,'message':'Kim jesteś w Chess Corp?'}).json()
        assert ask('buddy')['npc_id']=='buddy'
        assert len(ask('security')['history'])==2
        assert len(ask('security')['history'])==4
        assert len(ask('merchant')['history'])==2
        assert len(ask('buddy')['history'])==4
    req=ChatRequest(session_id='identity-test',npc_id='security',message='Co pilnujesz?')
    prompt=build_messages(req,[])[0]['content']
    assert 'Security' in prompt and 'Never identify yourself as Buddy' in prompt

def test_session_jobs_local_rewards_are_once_only_and_bad_positions_rejected(game):
    jobs=game.jobs;jobs.plan=copy.deepcopy(PLAN);jobs.objects=objects_for_jobs(PLAN);jobs.state='active'
    game.locations.id='bar';game.player.x,game.player.y=830,430
    assert jobs.interact(game) and game.adventure.credits==20
    assert not jobs.interact(game) and game.adventure.credits==20
    with pytest.raises(ValueError):replay_jobs(PLAN,[{'object_id':'job_b_0','location_id':'bar','position':[620,478]}])

def test_new_session_produces_new_request_and_same_session_does_not_double_charge(tmp_path):
    async def unused():pass
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200,json={'model':'muse-spark-1.3','choices':[{'message':{'content':json.dumps(PLAN)}}]})
    settings=Settings(director_mode='meta',director_allow_paid_requests=True,allow_paid_requests=True,api_key='fake',asset_cache_dir=str(tmp_path))
    app=create_app(settings)
    with TestClient(app) as c:
        app.state.asset_generator.client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        one=c.post('/api/director/jobs',json={'session_id':'jobs-session-one'});assert one.status_code==200,one.text
        same=c.post('/api/director/jobs',json={'session_id':'jobs-session-one'});assert same.json()['generation']=='accepted-session-state'
        two=c.post('/api/director/jobs',json={'session_id':'jobs-session-two'});assert two.status_code==200,two.text
        assert len(calls)==2 and calls[0]['messages'][-1]!=calls[1]['messages'][-1]
        assert json.loads((tmp_path/'.session-jobs-spend.json').read_text())['calls']==2

def test_manual_asset_regeneration_bypasses_cached_image_once_per_unique_request(tmp_path):
    async def run():
        calls=[]
        def handler(request):calls.append(request);return httpx.Response(200,json={'data':[{'b64_json':encoded_image()}]})
        s=Settings(asset_ai_mode='meta',asset_ai_allow_paid_requests=True,api_key='fake',asset_cache_dir=str(tmp_path))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            g=AssetGenerator(s,client,CallStore())
            await g.generate(AssetRequest())
            body=AssetRequest(asset_id='hacker_emblem',refresh=True,request_id='a'*32)
            assert not (await g.generate(body))['asset']['cached'] and len(calls)==2
            from fastapi import HTTPException
            with pytest.raises(HTTPException):await g.generate(body)
            assert len(calls)==2 and (tmp_path/'.asset-refresh-spend.json').exists()
    asyncio.run(run())
