import pytest
from game.data import load_content
from game.quests import Quest
from game.interactions import interact, nearest_entity
from game.player import Player
from game.world import World

@pytest.fixture
def content():
    return load_content()

def test_content_references(content):
    scene,quest,dialogues=content
    assert len(quest['steps'])==3
    assert all(step['id'] in dialogues for step in quest['steps'])
    assert len(scene['entities'])==2

def test_quest_sequence_and_no_duplicate_reward(content):
    q=Quest(content[1])
    assert q.interact('corporate_entrance') is None
    assert not q.inventory
    assert q.interact('buddy')=='meet_buddy'
    assert q.interact('buddy') is None
    assert q.interact('corporate_entrance')=='collect_badge'
    assert q.interact('corporate_entrance') is None
    assert not q.complete
    assert q.interact('buddy')=='return_to_buddy'
    for _ in range(100):
        q.interact('buddy'); q.interact('corporate_entrance')
    assert q.complete and q.reward_count==1
    assert q.inventory=={'employee_badge'}

def test_interaction_range_and_priority(content):
    scene,data,_=content
    q=Quest(data)
    entities=scene['entities']
    assert interact((0,0),entities,q) is None
    assert interact((235,432),entities,q) is None
    assert interact((605,440),entities,q)=='meet_buddy'
    assert nearest_entity((540,440),entities,q) is None
    assert interact((296,432),entities,q) is None
    assert interact((295,432),entities,q)=='collect_badge'
    assert interact((540,440),entities,q)=='return_to_buddy'

def test_movement_bounds_and_delta_time(content):
    w=World(content[0]); p=Player((350,440))
    p.move(1,0,0.02,w)
    assert p.x==pytest.approx(353.7)
    for _ in range(1000): p.move(1,1,0.05,w)
    assert p.position==(924,482)
    for _ in range(1000): p.move(-1,-1,0.05,w)
    assert p.position==(36,422)

def test_blocked_area():
    w=World({'walkable_bounds':[0,0,100,100],'blocked_areas':[[40,40,60,60]],'entities':[]})
    assert w.constrain(39,50,5,0)==(39,50)

def test_keyboard_quest_and_render(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER','dummy')
    import pygame
    from main import Game
    pygame.init(); screen=pygame.display.set_mode((960,540))
    try:
        g=Game()
        for position in [(540,440),(235,432),(540,440)]:
            g.player.x,g.player.y=position
            g.key(pygame.K_e)
            assert g.dialogue
            g.draw(screen)
            # Movement is blocked while reading.
            before=g.player.position
            g.update(.02,pygame.key.get_pressed())
            assert g.player.position==before
            while g.dialogue: g.key(pygame.K_RETURN)
        assert g.quest.complete and g.quest.reward_count==1
        for _ in range(100): g.key(pygame.K_e)
        g.key(pygame.K_ESCAPE)
        g.key(pygame.K_r)
        assert g.quest.index==0 and not g.quest.inventory
        g.draw(screen)
    finally: pygame.quit()
