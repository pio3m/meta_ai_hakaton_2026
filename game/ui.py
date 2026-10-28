import pygame
from game.data import ROOT

CYAN = (100, 224, 239)
WHITE = (218, 237, 240)
GOLD = (245, 201, 117)

class UI:
    def __init__(self):
        self.font = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 16)
        self.small = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 13)
        self.title = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 23)

    def text(self, screen, text, pos, color=WHITE, small=False):
        screen.blit((self.small if small else self.font).render(text, False, color), pos)

    def panel(self, screen, rect):
        pygame.draw.rect(screen, (8, 22, 34), rect)
        pygame.draw.rect(screen, (49, 120, 143), rect, 2)
        x,y,w,h = rect
        pygame.draw.line(screen, CYAN, (x,y), (x+35,y), 3)

    def wrap(self, text, width):
        lines, line = [], ''
        for word in text.split():
            candidate = (line + ' ' + word).strip()
            if self.font.size(candidate)[0] > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        return lines + [line]

    def draw(self, screen, quest, target, dialogue, line_index):
        self.panel(screen, (18,16,924,95))
        screen.blit(self.title.render('CHESS CORP',False,CYAN), (34,28))
        self.text(screen, '01 / PIERWSZY DZIEŃ', (34,62), small=True)
        objective = 'Pierwszy dzień zaliczony!' if quest.complete else quest.objective
        self.text(screen, objective, (310,34), GOLD if quest.complete else WHITE)
        self.text(screen, 'Identyfikator: ' + ('ODEBRANY' if quest.inventory else 'brak'), (310,67), CYAN, True)
        for i in range(3):
            pygame.draw.rect(screen, CYAN if i < quest.index else (35,62,76), (820+i*33,70,25,6))
        self.panel(screen, (18,502,924,29))
        self.text(screen, 'WASD  Ruch     E  Interakcja     Enter  Dalej     Esc  Zamknij dialog     R  Nowy start', (30,510), small=True)
        if target and not dialogue:
            prompt = '[E] Rozmawiaj' if target['id']=='buddy' else '[E] Odbierz identyfikator'
            x,y=target['position']
            width=self.small.size(prompt)[0]+20
            x=max(20,min(940-width,x-width//2))
            self.panel(screen,(x,y-124,width,28))
            self.text(screen,prompt,(x+10,y-117),CYAN,True)
        if dialogue:
            self.panel(screen,(95,287,770,116))
            self.text(screen,dialogue['speaker'],(115,299),CYAN)
            for i,line in enumerate(self.wrap(dialogue['lines'][line_index],725)):
                self.text(screen,line,(115,326+i*21))
            self.text(screen,f"{line_index+1}/{len(dialogue['lines'])}    E / Enter: dalej    Esc: zamknij",(115,382),GOLD,True)
        elif quest.complete:
            self.panel(screen,(250,154,460,58))
            self.text(screen,'ZADANIE UKOŃCZONE — witaj w zespole!',(270,166),GOLD)
            self.text(screen,'R: rozpocznij ponownie lub zwiedzaj ulicę',(290,190),small=True)
