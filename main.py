import asyncio
import sys
import math
import pygame
from game.data import ROOT, load_content
from game.chat import Chat
from game.director import Director
from game.living_world import LivingWorld
from game.locations import Locations
from game.adventure import Adventure
from game.audio import AudioManager
from game.session_jobs import SessionJobs
from game.asset_sync import AssetSync
from game import i18n
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
        self.audio = AudioManager()
        self.reset()

    def reset(self):
        if hasattr(self,'assets'):self.assets.cancel()
        if hasattr(self,'jobs'):self.jobs.cancel()
        if hasattr(self, 'chat'):
            self.chat.cancel()
        if hasattr(self,"director"): self.director.cancel()
        selected_mock = self.director.mock_type if hasattr(self,"director") else "COLLECT"
        self.director = Director(self.scene)
        self.director.mock_type = selected_mock
        if hasattr(self,"locations"): self.locations.cancel()
        elif hasattr(self,"living"): self.living.cancel()
        self.chat = Chat()
        self.jobs=SessionJobs(self.chat.session_id)
        self.assets=AssetSync()
        self.locations=Locations(self.scene,self.chat.session_id)
        self.world=self.locations.worlds['corporate_street'];self.living=self.locations.livings['corporate_street'];self.background=self.locations.backgrounds['corporate_street']
        next(e for e in self.world.entities if e["id"]=="buddy")["position"]=[540,440]
        pygame.key.stop_text_input()
        self.player = Player(self.scene['player_spawn'])
        self.quest = Quest(self.quest_data)
        self.adventure = Adventure()
        self.adventure.audio = self.audio
        self.adventure.living=self.living
        self.adventure.livings=self.locations.livings
        self.dialogue = None
        self.line_index = 0

    def text_input(self, text):
        if self.director.answer_open:
            self.director.insert_answer(text)
        elif self.chat.open and not self.dialogue:
            self.chat.insert(text)

    def key(self, key):
        self.audio.unlock()
        if key==pygame.K_F2:
            i18n.set_language('pl' if i18n.language()=='en' else 'en');self.chat.language=i18n.language();return
        if key==pygame.K_m and not self.chat.open and not self.director.answer_open:
            self.audio.toggle_mute();return
        if self.locations.fade:return
        if self.jobs.open:
            if key in (pygame.K_j,pygame.K_ESCAPE):self.jobs.open=False
            return
        if key==pygame.K_j and not self.chat.open and not self.dialogue and not self.director.answer_open and not self.adventure.dead and not self.adventure.shop_open and not self.locations.map_open:
            self.jobs.open=True;return
        if key==pygame.K_t and not self.adventure.dead and not self.locations.map_open and not self.dialogue and not self.chat.open and not self.director.answer_open and not self.adventure.shop_open:
            actor=min(self.living.npcs.values(),key=lambda n:math.dist(n['position'],self.player.position))
            if math.dist(actor['position'],self.player.position)<=80 and actor.get('down_time',0)<=0:
                if self.chat.select_npc(actor,self.locations.id,self.adventure.credits):
                    actor['player_engaged']=True;pygame.key.start_text_input();self.audio.play('conversation')
            return
        if self.adventure.dead:
            if key==pygame.K_RETURN:self.adventure.respawn(self.player)
            return
        if self.adventure.shop_open:
            if key==pygame.K_ESCAPE:
                self.adventure.shop_open=False;self.audio.play('shop_close')
            elif key in (pygame.K_UP,pygame.K_w):self.adventure.selection=(self.adventure.selection-1)%3
            elif key in (pygame.K_DOWN,pygame.K_s):self.adventure.selection=(self.adventure.selection+1)%3
            elif key in (pygame.K_RETURN,pygame.K_e):self.adventure.buy(self.adventure.data['shop'][self.adventure.selection]['id'])
            return
        if self.locations.map_open:
            if key in (pygame.K_TAB,pygame.K_ESCAPE):self.locations.map_open=False
            return
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
            elif key == pygame.K_F3 and self.chat.error:
                self.chat.text = self.chat.last_message
                self.chat.cursor = len(self.chat.text)
            return
        if not self.dialogue and key==pygame.K_h:
            self.adventure.heal();return
        if not self.dialogue and key==pygame.K_SPACE:
            self.adventure.living=self.living
            self.adventure.attack(self.player.position,self.player.facing_left)
            return
        if key==pygame.K_TAB and not self.dialogue:
            self.locations.map_open=True
            return
        if key==pygame.K_f and not self.dialogue:
            if self.locations.travel(self.player.position):self.audio.play('door')
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
                if self.jobs.interact(self):return
                if self.adventure.interact(self):
                    self.locations.notice_ttl=0
                    return
                if self.locations.id!='corporate_street':
                    if not self.locations.interact(self.player.position,self.quest):
                        if self.living.player_interaction(self.player.position):
                            self.locations.notice_ttl=0;self.audio.play('conversation')
                    return
                if self.director.interact(self.player.position,self.quest):
                    if self.director.answer_open: pygame.key.start_text_input()
                    return
                result = interact(self.player.position,self.world.entities,self.quest)
                entity = conversation_entity(self.player.position,self.world.entities,self.quest)
                if result is None and entity and entity['id']=='buddy':
                    result = 'waiting'
                if entity and entity['id']=='buddy':
                    self.chat.select_npc(self.living.npcs['buddy'],self.locations.id,self.adventure.credits)
                    self.chat.open = True;self.audio.play('conversation')
                if not result and self.living.player_interaction(self.player.position):self.audio.play('conversation')
                if entity and entity['id']=='buddy': self.living.event('Gracz rozmawia z Buddy',("buddy",),'FALLBACK',True)
                if result:
                    self.dialogue = self.dialogues[result]
                    self.line_index = 0

    def update(self, dt, keys):
        self.jobs.update(self)
        self.assets.update(self,dt)
        self.locations.update(dt,self)
        self.adventure.living=self.living
        self.adventure.update(dt,self,keys)
        self.audio.update(dt,self.locations.id)
        if self.locations.id=='corporate_street':next(e for e in self.world.entities if e['id']=='buddy')['position']=list(self.living.npcs['buddy']['position'])
        self.chat.poll()
        if self.locations.id=='corporate_street':self.director.start(self.quest,self.chat.session_id,self.chat.language)
        self.director.poll(self.quest)
        if not self.dialogue and not self.chat.open and not self.director.answer_open and not self.locations.fade and not self.locations.map_open and not self.adventure.shop_open and not self.adventure.dead and not self.jobs.open:
            self.player.move(int(keys[pygame.K_d])-int(keys[pygame.K_a]),int(keys[pygame.K_s])-int(keys[pygame.K_w]),dt,self.world)

    def draw(self, screen):
        screen.blit(self.background,(0,0))
        self.locations.draw_scene(screen,self.ui)
        # Terminal aligns with the left doorway in the original street background.
        if self.locations.id=='corporate_street':pygame.draw.rect(screen,(9,36,45),(222,387,24,34))
        if self.locations.id=='corporate_street':pygame.draw.rect(screen,CYAN,(222,387,24,34),2)
        if self.locations.id=='corporate_street':pygame.draw.rect(screen,GOLD if self.quest.index==1 else CYAN,(228,394,12,8))
        if self.locations.id=='corporate_street':self.ui.text(screen,'CHESS CORP',(183,365),CYAN,True)
        # Reuse the four original animation frames, with visible role accents.
        actors=[]
        frame=self.frames[int(self.player.animation)%4 if self.player.moving else 0]
        if self.player.facing_left: frame=pygame.transform.flip(frame,True,False)
        actors.append((self.player.position,frame,None))
        for npc in self.living.npcs.values():
            custom=self.locations.sprite_cache.get(npc.get('sprite_prefix'))
            frames=custom or self.frames
            sprite=frames[int(npc['frame'])%4 if npc['moving'] else int(self.living.clock*3)%4 if custom else 0].copy()
            tint={'buddy':(160,235,255),'security':(130,255,170),'hacker':(255,140,235),'employee':(255,220,140)}.get(npc['id'],tuple(npc['color']))
            if not custom:sprite.fill((*tint,255),special_flags=pygame.BLEND_RGBA_MULT)
            if npc.get('down_time',0)>0:sprite.set_alpha(100)
            if npc['facing_left']:sprite=pygame.transform.flip(sprite,True,False)
            actors.append((npc['position'],sprite,npc))
        for (x,y),sprite,npc in sorted(actors,key=lambda a:a[0][1]):
            pygame.draw.ellipse(screen,(5,16,23),(x-22,y-7,44,10))
            bob=round(math.sin(self.living.clock*3+len(npc['id']))*1) if npc and not npc['moving'] else 0
            screen.blit(sprite,(round(x-sprite.get_width()/2),round(y-sprite.get_height()+bob)))
            if npc:
                pygame.draw.rect(screen,npc['color'],(int(x-12),int(y-62+bob),24,4))
                # Role colors identify NPCs; names and activity live in the fixed roster.
        self.adventure.draw_world(screen,self.ui,self)
        if self.locations.id=='corporate_street':pygame.draw.rect(screen,(10,35,45),(840,414,20,28))
        if self.locations.id=='corporate_street':pygame.draw.rect(screen,(239,117,226),(840,414,20,28),2)
        if self.locations.id=='corporate_street':self.ui.draw(screen,self.quest,conversation_entity(self.player.position,self.world.entities,self.quest),self.dialogue,self.line_index)
        if self.locations.id=='corporate_street' and not self.dialogue: self.director.draw(screen,self.ui,self.player.position)
        if self.locations.id=='corporate_street' and not self.dialogue and not self.chat.open and not self.director.answer_open:
            self.living.draw_overlay(screen,self.ui,self.director.state=="idle")
        if not self.dialogue and not self.chat.open:self.locations.draw_ui(screen,self.ui,self)
        self.adventure.draw_ui(screen,self.ui,self)
        if not self.chat.open and not self.dialogue:self.jobs.draw(screen,self.ui,self)
        if self.chat.open and not self.dialogue:
            self.ui.draw_chat(screen,self.chat)
        self.audio.draw_mute(screen,self.ui)
        self.ui.draw_language(screen)

async def main(frame_limit=None, screenshot=None):
    pygame.init()
    screen = pygame.display.set_mode((960,540))
    pygame.display.set_caption(i18n.translate('Chess Corp — Pierwszy dzień'))
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
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    game.audio.unlock()
                    if sys.platform=='emscripten':
                        i18n.initialize();game.chat.language=i18n.language()
                    elif event.button==1 and 30<=event.pos[0]<=100 and 80<=event.pos[1]<=103:
                        i18n.set_language('en' if event.pos[0]<64 else 'pl');game.chat.language=i18n.language()
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
        game.assets.cancel()
        game.jobs.cancel()
        game.locations.cancel()
        game.audio.stop()
        pygame.quit()
    return frames

if __name__ == '__main__':
    if '--smoke' in sys.argv:
        print('Rendered frames:',asyncio.run(main(12,str(ROOT/'docs/smoke.png'))))
    else:
        asyncio.run(main())
