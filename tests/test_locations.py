import asyncio
import copy
import json
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.world_models import load_world_data,parse_world_plan,WorldRequest
from backend.world_ai import world_payload
from game.data import load_content
from game.living_world import LivingWorld
from game.world_contract import local_world_plan,validate_world_plan

ROOMS=['bar','hacker_hideout','corporate_lobby']

@pytest.mark.parametrize('location',ROOMS)
def test_location_v2_contract_client_backend_and_schema_only_current_targets(location):
    rules,scene=load_world_data(location);p=local_world_plan(1,rules,location)
    validate_world_plan(p,rules,scene);assert parse_world_plan(json.dumps(p)).location_id==location
    w=LivingWorld(scene,'location-test',rules=rules,network_enabled=False)
    body=WorldRequest.model_validate(dict(session_id='location-test',revision=1,reason='event',snapshot=w.snapshot([110,455],False)))
    payload=world_payload(body,Settings(),rules)
    assert payload['response_format']['json_schema']['schema']['$defs']['NpcDecision']['properties']['npc_id']['enum']==[n['id'] for n in rules['npcs']]
    bad=copy.deepcopy(p);bad['location_id']='corporate_street'
    with pytest.raises(ValueError):validate_world_plan(bad,rules,scene)
    bad=copy.deepcopy(p);bad['decisions'][0]['actions']=[dict(action='MOVE_TO',target_id='buddy_post',route=[],duration_s=5,text='')]
    with pytest.raises(ValueError):validate_world_plan(bad,rules,scene)

@pytest.mark.parametrize('location',ROOMS)
def test_room_npcs_move_and_can_be_stopped_to_talk(location):
    rules,scene=load_world_data(location);w=LivingWorld(scene,'room-npcs',rules=rules,network_enabled=False)
    before={n:list(a['position']) for n,a in w.npcs.items()}
    for _ in range(150):w.update(.1,[36,482],False)
    assert all(w.npcs[n]['position']!=before[n] for n in before)
    a=next(iter(w.npcs.values()));position=list(a['position'])
    w.update(.1,[position[0]+30,position[1]])
    assert a['player_engaged'] and a['position']==position
    assert w.player_interaction(position)


def test_api_cross_room_revision_and_presence_are_scoped_without_llm_cost():
    app=create_app(Settings(inspector_token='test-owner-token-more-than-20'))
    with TestClient(app) as c,TestClient(app) as jury:
        c.post('/admin/api/login',json={'token':'test-owner-token-more-than-20'})
        demo=c.post('/admin/api/demo').json();sid=demo['game_url'].split('=')[1]
        jury.post('/admin/jury/api/login',json={'token':demo['jury_token']})
        for revision,location in enumerate(ROOMS,1):
            rules,scene=load_world_data(location);w=LivingWorld(scene,sid,rules=rules,network_enabled=False)
            body=dict(session_id=sid,revision=revision,reason='event',snapshot=w.snapshot([110,455],False))
            response=c.post('/api/world/plan',json=body);assert response.status_code==200,response.text
            data=response.json();assert data['provider']=='mock' and data['location_id']==location and data['plan']['schema_version']==2
            assert c.post('/api/world/presence',json={'session_id':sid,'snapshot':body['snapshot']}).status_code==200
            assert jury.get('/admin/jury/api/calls').json()['world_state']['location_id']==location
            bad=copy.deepcopy(body);bad['snapshot']['location_id']='corporate_street'
            assert c.post('/api/world/plan',json=bad).status_code==422
        private=copy.deepcopy(body);private['session_id']='private-session'
        c.post('/api/world/presence',json={'session_id':'private-session','snapshot':private['snapshot']})
        assert jury.get('/admin/jury/api/calls').json()['world_state']['location_id']==ROOMS[-1]
        assert all(not row['sent_to_model'] for row in app.state.inspector.list())

@pytest.fixture
def game(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy');monkeypatch.setenv('SDL_AUDIODRIVER','dummy')
    import pygame
    from main import Game
    pygame.init();pygame.display.set_mode((960,540));g=Game()
    yield g
    g.locations.cancel();g.chat.cancel();g.director.cancel();pygame.quit()


def travel(game,target):
    import pygame
    if target=='corporate_street':point=game.locations.rooms[game.locations.id]['exit_position']
    else:point=game.locations.rooms[target]['street_entry']
    game.player.x,game.player.y=point;game.key(pygame.K_f)
    assert game.locations.fade
    for _ in range(6):game.update(.1,pygame.key.get_pressed())
    assert game.locations.id==target
    assert game.world is game.locations.worlds[target] and game.living is game.locations.livings[target]


def test_all_rooms_roundtrip_preserves_quest_inventory_chat_npcs_and_planner(game):
    import pygame
    q=game.quest;chat=game.chat;director=game.director
    game.quest.interact('buddy');game.chat.history=[{'role':'user','content':'Historia sesji'}]
    game.living.event('Ważny trop.',('buddy',))
    street=game.living
    for target in ROOMS:
        travel(game,target)
        obj=game.locations.rooms[target]['interactable'];game.player.x,game.player.y=obj['position'];game.key(pygame.K_e)
        assert obj['item'] in q.inventory
        assert game.living.planner is street.planner
        assert game.quest is q and q.index==1 and game.chat is chat and game.director is director
        assert 'employee_badge' not in q.inventory
        travel(game,'corporate_street')
        assert game.living is street and 'Ważny trop.' in street.npcs['buddy']['memory']
    assert len(q.inventory)==3 and game.chat.history[0]['content']=='Historia sesji'
    assert len(game.locations.visited)==4


def test_fade_blocks_extra_keypresses_and_unreachable_portal_does_nothing(game):
    import pygame
    game.key(pygame.K_f);assert game.locations.fade is None
    game.player.x,game.player.y=game.locations.rooms['bar']['street_entry'];game.key(pygame.K_f)
    before=game.quest;game.key(pygame.K_r);game.key(pygame.K_f)
    assert game.quest is before and game.locations.fade[0]=='bar'


def test_room_movement_continues_while_player_visits_another_location(game):
    import pygame
    bar=game.locations.livings['bar'];before=list(bar.npcs['bartender']['position'])
    for _ in range(25):game.update(.1,pygame.key.get_pressed())
    assert bar.npcs['bartender']['position']!=before


def test_closest_npc_takes_priority_over_more_distant_bar_counter(game):
    travel(game,'bar')
    game.living.npcs['bartender']['position']=[435,452]
    game.living.npcs['bar_guest']['position']=[800,465]
    assert not game.locations.interact([445,452],game.quest)
    assert game.living.player_interaction([445,452])
    assert game.living.visible_speaker=='bartender'
    assert game.locations.interact([400,452],game.quest)
    assert 'bar_receipt' in game.quest.inventory


def test_local_conversation_pause_is_not_reported_as_meta_action():
    scene=load_content()[0];w=LivingWorld(scene,'source-test',network_enabled=False)
    w.apply_plan(local_world_plan(),'META','a'*32)
    w.update(.1,[540,440])
    buddy=next(n for n in w.snapshot([540,440],False)['npcs'] if n['npc_id']=='buddy')
    assert buddy['source']=='FALLBACK' and buddy['state']=='WAIT'
    w.update(.1,[350,440])
    assert w.action_source(w.npcs['buddy'])=='META'
