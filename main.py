import asyncio
import sys
import pygame
from game.data import ROOT, load_content
from game.player import Player
from game.world import World
from game.quests import Quest
from game.interactions import nearest_entity, interact
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
        self.player = Player(self.scene['player_spawn'])
        self.quest = Quest(self.quest_data)
        self.dialogue = None
        self.line_index = 0

    def key(self, key):
        if key == pygame.K_r and not self.dialogue:
            self.reset()
        elif key == pygame.K_ESCAPE:
            self.dialogue = None
        elif key in (pygame.K_e, pygame.K_RETURN):
            if self.dialogue:
                self.line_index += 1
                if self.line_index >= len(self.dialogue['lines']):
                    self.dialogue = None
            elif key == pygame.K_e:
                result = interact(self.player.position,self.world.entities,self.quest)
                if result:
                    self.dialogue = self.dialogues[result]
                    self.line_index = 0

    def update(self, dt, keys):
        if not self.dialogue:
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
        self.ui.draw(screen,self.quest,nearest_entity(self.player.position,self.world.entities,self.quest),self.dialogue,self.line_index)

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
        pygame.quit()
    return frames

if __name__ == '__main__':
    if '--smoke' in sys.argv:
        print('Rendered frames:',asyncio.run(main(12,str(ROOT/'docs/smoke.png'))))
    else:
        asyncio.run(main())
