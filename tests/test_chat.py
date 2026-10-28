import asyncio
import pytest
from game.chat import Chat
from game.data import load_content
from game.quests import Quest


def test_unicode_input_and_length_limit():
    chat=Chat()
    chat.insert('Zażółć gęślą jaźń')
    assert chat.text=='Zażółć gęślą jaźń'
    chat.cursor=2
    chat.insert('ą')
    assert chat.text.startswith('Zaążółć')
    chat.insert('\n\t'+'x'*1000)
    assert len(chat.text)==600 and '\n' not in chat.text


def test_client_pending_history_errors_and_reset_are_nonblocking(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER','dummy')
    import pygame
    from main import Game
    async def run():
        pygame.init(); screen=pygame.display.set_mode((960,540))
        try:
            g=Game(); g.player.x,g.player.y=540,440
            g.key(pygame.K_e)
            while g.dialogue: g.key(pygame.K_RETURN)
            assert g.chat.open
            captured=[]; ready=asyncio.Event()
            async def transport(payload):
                captured.append(payload)
                await ready.wait()
                return {'reply':'Zażółć gęślą jaźń. Przyznaję ci identyfikator!', 'provider':'mock','grant_item':'employee_badge','quest_status':'completed'}
            g.chat.transport=transport
            g.text_input('Gdzie wejść?')
            g.key(pygame.K_RETURN)
            await asyncio.sleep(0)
            assert g.chat.pending
            for _ in range(10):
                g.update(.016,pygame.key.get_pressed()); g.draw(screen)
            g.key(pygame.K_ESCAPE)
            assert not g.chat.open and g.chat.pending
            old_x=g.player.x
            from collections import defaultdict
            moving=defaultdict(bool,{pygame.K_d:True})
            g.update(.02,moving)
            assert g.player.x>old_x
            ready.set(); await asyncio.sleep(0)
            g.update(.016,pygame.key.get_pressed())
            assert not g.chat.pending and 'Zażółć' in g.chat.history[-1]['content']
            assert g.quest.index==1 and not g.quest.inventory
            assert captured[0]['context']['quest_status']=='in_progress'
            assert captured[0]['context']['has_badge'] is False
            old_session=g.chat.session_id
            g.key(pygame.K_r)
            assert g.chat.session_id!=old_session and not g.chat.history
            async def fail(payload): return {'error':'Brak połączenia'}
            g.chat.transport=fail; g.chat.open=True
            g.text_input('Test błędu');g.key(pygame.K_RETURN)
            await asyncio.sleep(0);g.chat.poll()
            assert g.chat.error=='Brak połączenia'
            g.key(pygame.K_F3)
            assert g.chat.text=='Test błędu'
            g.draw(screen)
        finally: pygame.quit()
    asyncio.run(run())


def test_single_long_word_wrap_does_not_overflow(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    import pygame
    from game.ui import UI
    pygame.font.init()
    try:
        ui=UI()
        for line in ui.wrap('W'*600,790):
            assert ui.font.size(line)[0]<=790
    finally: pygame.font.quit()
