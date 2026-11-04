import asyncio,copy,json
from collections import defaultdict
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.world_models import WorldRequest,GameplaySnapshot,load_world_data,parse_world_plan
from backend.world_ai import WorldBudget
from backend.history import Session
from backend.providers import ProviderError
from game.adventure import Adventure
from game.world_contract import local_world_plan
from tests.test_locations import game,travel


def kill_wave(a):
    for rat in a.rats:
        while rat['hp']:
            a.cooldown=0
            a.attack(rat['position'],False)


def test_two_contracts_rewards_and_no_duplicate_payout(game):
    a=game.adventure;a.bounty();assert len(a.rats)==3 and a.state=='active'
    kill_wave(a);assert a.kills==3 and a.state=='ready' and a.credits==6
    a.attack([740,450],True);assert a.credits==6
    a.bounty();assert a.credits==36 and a.claimed=={0}
    assert a.buy('weapon') and a.credits==18 and a.damage==2
    assert not a.buy('weapon') and a.credits==18
    a.bounty();assert a.contract==1 and len(a.rats)==5
    kill_wave(a);assert a.state=='ready' and a.credits==33
    a.bounty();assert a.credits==93 and a.claimed=={0,1}
    for _ in range(4):a.bounty()
    assert a.credits==93 and a.state=='claimed'
    assert a.buy('armor') and a.health==125 and a.max_health==125
    assert a.buy('medkit') and a.medkits==2
    assert GameplaySnapshot.model_validate(a.snapshot())


def test_rat_attack_facing_depth_and_cooldown(game):
    a=game.adventure;a.bounty();a.living=None;a.rats=a.rats[:1];r=a.rats[0];r['position']=[400,450]
    before=copy.deepcopy(game.living.npcs)
    assert not a.attack([340,450],True) and r['hp']==2
    a.cooldown=0;assert not a.attack([350,490],False)
    a.cooldown=0;assert a.attack([350,450],False) and r['hp']==1
    assert not a.attack([350,450],False) and r['hp']==1
    assert game.living.npcs==before


def test_health_heal_death_respawn_preserves_progress(game):
    a=game.adventure;a.bounty();a.health=80
    assert a.heal() and a.health==100 and a.medkits==0
    assert not a.heal()
    r=a.rats[0];a.cooldown=0;a.attack(r['position'],False);a.cooldown=0;a.attack(r['position'],False)
    killed=set(a.killed);a.credits=2;a.health=0
    assert not a.heal() and not a.attack(game.player.position,False)
    assert a.respawn(game.player) and a.health==100 and a.credits==0 and a.killed==killed
    assert not a.respawn(game.player)


def test_shop_no_free_purchase_and_stock_is_finite(game):
    a=game.adventure;assert not a.buy('weapon') and not a.weapon and a.credits==0
    assert not a.buy('invalid');a.credits=100
    for _ in range(3):assert a.buy('medkit')
    balance=a.credits;assert not a.buy('medkit') and a.credits==balance


def test_bounty_and_shop_keyboard_roundtrip_preserves_first_quest(game):
    import pygame
    q=game.quest;q.interact('buddy');travel(game,'bar')
    a=game.adventure
    game.living.npcs['bartender']['position']=[545,440]
    game.locations.notice_ttl=5
    game.player.x,game.player.y=545,440;game.key(pygame.K_e)
    assert game.locations.notice_ttl==0
    assert a.state=='active' and q.index==1
    travel(game,'corporate_street');assert game.adventure is a and len(a.rats)==3
    kill_wave(a);travel(game,'bar')
    game.player.x,game.player.y=game.living.npcs['bartender']['position'];game.key(pygame.K_e)
    assert a.state=='claimed' and a.credits==36
    game.player.x,game.player.y=game.living.npcs['merchant']['position'];game.key(pygame.K_e)
    assert a.shop_open;game.key(pygame.K_DOWN);game.key(pygame.K_RETURN)
    assert a.weapon and a.credits==18
    game.key(pygame.K_ESCAPE);assert not a.shop_open
    travel(game,'corporate_street');assert q.index==1 and a.weapon


def test_pause_combat_in_dialogue_and_rooms_and_attack_does_not_spawn_rats(game):
    import pygame
    a=game.adventure;a.attack([100,450],False);assert not a.rats
    a.bounty();r=a.rats[0];r['position']=list(game.player.position);r['bite_cd']=0
    game.dialogue={'lines':['x']};a.update(.1,game,defaultdict(bool));assert a.health==100
    game.dialogue=None;a.update(.1,game,defaultdict(bool));assert a.health==90
    travel(game,'bar');hp=a.health
    for _ in range(30):a.update(.1,game,defaultdict(bool))
    assert hp==a.health


def test_merchant_and_combat_context_are_valid_and_visible_in_mock_api(game):
    travel(game,'bar');game.adventure.bounty(game.living)
    game.update(.1,defaultdict(bool));snap=game.living.snapshot(game.player.position,False)
    assert 'merchant' in [n['npc_id'] for n in snap['npcs']]
    assert snap['gameplay']['target']==3 and snap['gameplay']['bounty_state']=='active'
    body=dict(session_id='combat-api-test',revision=1,reason='event',snapshot=snap)
    assert WorldRequest.model_validate(body)
    app=create_app(Settings(inspector_token='combat-owner-token-very-long'))
    with TestClient(app) as c:
        response=c.post('/api/world/plan',json=body);assert response.status_code==200,response.text
        plan=response.json()['plan'];assert parse_world_plan(json.dumps(plan))
        assert {d['npc_id'] for d in plan['decisions']}=={'bartender','bar_guest','merchant'}
        row=app.state.inspector.get(response.json()['call_id'])
        assert row['context']['gameplay']['target']==3 and not row['sent_to_model']


@pytest.mark.parametrize('field,value',[('credits',-1),('health',126),('medkits',5),('kills',6),('contract_index',2)])
def test_gameplay_boundary_rejects_invalid_state(game,field,value):
    data=game.adventure.snapshot();data[field]=value
    with pytest.raises(ValueError):GameplaySnapshot.model_validate(data)


def test_world_budget_survives_restart_and_corruption_fails_closed(tmp_path):
    async def run():
        path=tmp_path/'ledger.json'
        s=Settings(world_ai_allow_paid_requests=True,api_key='fake',world_ai_global_limit=1,world_ai_ledger_path=str(path))
        b=WorldBudget(s);session=Session(messages=[],updated_at=0);reserved=await b.reserve(session,{'messages':[]});await b.settle(reserved,{'total_tokens':123})
        b2=WorldBudget(s);assert b2.calls==1 and b2.tokens==123
        with pytest.raises(ProviderError):await b2.reserve(Session(messages=[],updated_at=0),{})
        path.write_text('broken');b3=WorldBudget(s);assert b3.calls==1 and b3.tokens==s.world_ai_token_budget
    asyncio.run(run())
def test_next_world_plan_waits_full_cooldown_after_slow_response():
    async def run():
        from game.living_world import LivingWorld
        from game.data import load_content
        now=[0.];starts=[]
        async def transport(body,path):
            if not path.endswith('/plan'):return {}
            starts.append(now[0]);await asyncio.sleep(0);now[0]=10.
            return dict(plan=local_world_plan(),provider='mock',validation={'valid':True},call_id='a'*32,limits={'session_limit':3,'remaining_calls':2,'min_interval_seconds':30})
        w=LivingWorld(load_content()[0],'slow-plan-test',transport=transport,network_enabled=True,network_clock=lambda:now[0])
        for _ in range(8):w.update(.1,[350,440]);await asyncio.sleep(0)
        now[0]=31.;w.update(.1,[350,440]);await asyncio.sleep(0);assert starts==[0.]
        now[0]=41.;w.update(.1,[350,440]);await asyncio.sleep(0);assert starts==[0.]
        now[0]=42.;w.update(.1,[350,440]);await asyncio.sleep(0);assert starts==[0.,42.]
        w.cancel()
    asyncio.run(run())
def test_explicit_barman_contract_is_not_overwritten_by_nearby_auto_greeting(game):
    travel(game,'bar');a=game.adventure;w=game.living
    a.bounty(w);offer=w.visible_utterance
    w._player_reply(w.npcs['bar_guest'],opening=True)
    assert w.visible_speaker=='bartender' and w.visible_utterance==offer
    w.clock+=8;w._player_reply(w.npcs['bar_guest'],opening=True)
    assert w.visible_speaker=='bar_guest'
def test_previous_location_plan_execution_remains_valid_after_new_plan_in_another_room():
    from game.living_world import LivingWorld
    from game.data import load_content
    app=create_app(Settings())
    with TestClient(app) as c:
        street=LivingWorld(load_content()[0],'travel-trace',network_enabled=False)
        snap=street.snapshot([350,440],False)
        first=c.post('/api/world/plan',json=dict(session_id='travel-trace',revision=1,reason='event',snapshot=snap)).json()
        room,_=load_world_data('bar');bar=LivingWorld(room,'travel-trace',rules=room,network_enabled=False)
        assert c.post('/api/world/plan',json=dict(session_id='travel-trace',revision=2,reason='event',snapshot=bar.snapshot([110,455],False))).status_code==200
        trace=dict(session_id='travel-trace',call_id=first['call_id'],snapshot=snap,completed_actions=[])
        assert c.post('/api/world/execution',json=trace).status_code==200
        trace['session_id']='foreign-session'
        assert c.post('/api/world/execution',json=trace).status_code==404
        trace['session_id']='travel-trace';trace['snapshot']=bar.snapshot([110,455],False)
        assert c.post('/api/world/execution',json=trace).status_code==404
