import asyncio
import sys
import pygame
from game.data import ROOT, load_content
from game.chat import Chat
from game.director import Director
from game.player import Player
from game.world import World
from game.quests import Quest
from game.interactions import nearest_entity, conversation_entity, interact
from game.ui import UI, CYAN, GOLD

class Game:
    def __init__(self):
        self.scene, self.quest_data, self.dialogues = load_content()
        self.world = World(self.scene)
        self.ui = UI()
        self.background = pygame.image.load(str(ROOT / self.scene['background'])).convert()
        self.frames = [pygame.image.load(str(ROOT / f'assets/processed/player_{i}.png')).convert_alpha() for i in range(4)]
        self.buddy_sprite = pygame.image.load(str(ROOT / 'assets/processed/buddy.png')).convert_alpha()
        self.reset()

    def reset(self):
        if hasattr(self, 'chat'):
            self.chat.cancel()
        if hasattr(self,"director"): self.director.cancel()
        selected_mock = self.director.mock_type if hasattr(self,"director") else "COLLECT"
        self.director = Director(self.scene)
        self.director.mock_type = selected_mock
        self.chat = Chat()
        pygame.key.stop_text_input()
        self.player = Player(self.scene['player_spawn'])
        self.quest = Quest(self.quest_data)
        self.dialogue = None
        self.line_index = 0

    def text_input(self, text):
        if self.director.answer_open:
            self.director.insert_answer(text)
        elif self.chat.open and not self.dialogue:
            self.chat.insert(text)

    def key(self, key):
        if key == pygame.K_ESCAPE:
            self.director.answer_open = False
            self.dialogue = None
            self.chat.open = False
            pygame.key.stop_text_input()
            return
        if self.director.answer_open:
            if key == pygame.K_BACKSPACE: self.director.answer = self.director.answer[:-1]
            elif key == pygame.K_RETURN:
                self.director.submit_answer(self.player.position,self.quest)
                if not self.director.answer_open: pygame.key.stop_text_input()
            return
        if self.chat.open and not self.dialogue:
            if key == pygame.K_RETURN:
                self.chat.submit(self.quest,self.director.context())
            elif key == pygame.K_BACKSPACE and self.chat.cursor:
                i = self.chat.cursor
                self.chat.text = self.chat.text[:i-1]+self.chat.text[i:]
                self.chat.cursor -= 1
            elif key == pygame.K_DELETE:
                i = self.chat.cursor
                self.chat.text = self.chat.text[:i]+self.chat.text[i+1:]
            elif key == pygame.K_LEFT:
                self.chat.cursor = max(0,self.chat.cursor-1)
            elif key == pygame.K_RIGHT:
                self.chat.cursor = min(len(self.chat.text),self.chat.cursor+1)
            elif key == pygame.K_HOME:
                self.chat.cursor = 0
            elif key == pygame.K_END:
                self.chat.cursor = len(self.chat.text)
            elif key == pygame.K_PAGEUP:
                self.chat.scroll += 5
            elif key == pygame.K_PAGEDOWN:
                self.chat.scroll = max(0,self.chat.scroll-5)
            elif key == pygame.K_F2 and not self.chat.pending:
                self.chat.language = 'en' if self.chat.language=='pl' else 'pl'
            elif key == pygame.K_F3 and self.chat.error:
                self.chat.text = self.chat.last_message
                self.chat.cursor = len(self.chat.text)
            return
        if key == pygame.K_r and not self.dialogue:
            self.reset()
        elif key == pygame.K_F4 and not self.dialogue and self.director.state=='idle':
            kinds=('COLLECT','SEQUENCE','LOGIC_PUZZLE')
            self.director.mock_type=kinds[(kinds.index(self.director.mock_type)+1)%3]
        elif key == pygame.K_g and not self.dialogue:
            self.director.start(self.quest,self.chat.session_id,self.chat.language,retry=True)
        elif key == pygame.K_ESCAPE:
            self.dialogue = None
        elif key in (pygame.K_e, pygame.K_RETURN):
            if self.dialogue:
                self.line_index += 1
                if self.line_index >= len(self.dialogue['lines']):
                    self.dialogue = None
                    if self.chat.open:
                        pygame.key.start_text_input()
            elif key == pygame.K_e:
                if self.director.interact(self.player.position,self.quest):
                    if self.director.answer_open: pygame.key.start_text_input()
                    return
                result = interact(self.player.position,self.world.entities,self.quest)
                entity = conversation_entity(self.player.position,self.world.entities,self.quest)
                if result is None and entity and entity['id']=='buddy':
                    result = 'waiting'
                if entity and entity['id']=='buddy':
                    self.chat.open = True
                if result:
                    self.dialogue = self.dialogues[result]
                    self.line_index = 0

    def update(self, dt, keys):
        self.chat.poll()
        self.director.start(self.quest,self.chat.session_id,self.chat.language)
        self.director.poll(self.quest)
        if not self.dialogue and not self.chat.open and not self.director.answer_open:
            self.player.move(int(keys[pygame.K_d])-int(keys[pygame.K_a]),int(keys[pygame.K_s])-int(keys[pygame.K_w]),dt,self.world)

    def draw(self, screen):
        screen.blit(self.background,(0,0))
        # Terminal aligns with the left doorway in the original street background.
        pygame.draw.rect(screen,(9,36,45),(222,387,24,34))
        pygame.draw.rect(screen,CYAN,(222,387,24,34),2)
        pygame.draw.rect(screen,GOLD if self.quest.index==1 else CYAN,(228,394,12,8))
        self.ui.text(screen,'CHESS CORP',(183,365),CYAN,True)
        buddy = next(e for e in self.world.entities if e['id']=='buddy')
        frame = self.frames[int(self.player.animation)%4 if self.player.moving else 0]
        if self.player.facing_left:
            frame = pygame.transform.flip(frame,True,False)
        actors=[(buddy['position'],self.buddy_sprite),(self.player.position,frame)]
        for (x,y),sprite in sorted(actors,key=lambda a:a[0][1]):
            pygame.draw.ellipse(screen,(5,16,23),(x-22,y-7,44,10))
            screen.blit(sprite,(round(x-36),round(y-90)))
        self.ui.text(screen,'Buddy',(buddy['position'][0]-23,buddy['position'][1]-106),CYAN,True)
        self.ui.draw(screen,self.quest,conversation_entity(self.player.position,self.world.entities,self.quest),self.dialogue,self.line_index)
        if not self.dialogue: self.director.draw(screen,self.ui,self.player.position)
        if self.chat.open and not self.dialogue:
            self.ui.draw_chat(screen,self.chat)

async def main(frame_limit=None, screenshot=None):
    pygame.init()
    screen = pygame.display.set_mode((960,540))
    pygame.display.set_caption('Chess Corp — Pierwszy dzień')
    clock = pygame.time.Clock()
    game = Game()
    running, frames = True, 0
    try:
        while running:
            dt = clock.tick(60)/1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    game.key(event.key)
                elif event.type == pygame.TEXTINPUT:
                    game.text_input(event.text)
                elif event.type == pygame.MOUSEWHEEL and game.chat.open and not game.dialogue:
                    game.chat.scroll = max(0,game.chat.scroll+event.y*3)
            game.update(dt,pygame.key.get_pressed())
            game.draw(screen)
            pygame.display.flip()
            if frames == 0 and sys.platform == "emscripten":
                import platform
                platform.window.chessCorpStarted()
            frames += 1
            if frame_limit and frames >= frame_limit:
                if screenshot:
                    pygame.image.save(screen,screenshot)
                running = False
            await asyncio.sleep(0)
    finally:
        game.chat.cancel()
        game.director.cancel()
        pygame.quit()
    return frames

if __name__ == '__main__':
    if '--smoke' in sys.argv:
        print('Rendered frames:',asyncio.run(main(12,str(ROOT/'docs/smoke.png'))))
    else:
        asyncio.run(main())
