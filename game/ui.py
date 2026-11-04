import pygame
from game.data import ROOT
from game import i18n

CYAN = (100, 224, 239)
WHITE = (218, 237, 240)
GOLD = (245, 201, 117)

class UI:
    def __init__(self):
        i18n.initialize()
        self.font = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 16)
        self.small = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 13)
        self.title = pygame.font.Font(str(ROOT / 'assets/processed/font.ttf'), 23)

    def text(self, screen, text, pos, color=WHITE, small=False):
        screen.blit((self.small if small else self.font).render(i18n.translate(text), False, color), pos)

    @property
    def language(self):return i18n.language()

    def translate(self,text):return i18n.translate(text)

    def ai_text(self,text,source_language):return i18n.original(text,source_language)

    def draw_language(self,screen):
        self.text(screen,'EN',(34,84),GOLD if self.language=='en' else WHITE,True)
        self.text(screen,'/',(56,84),WHITE,True)
        self.text(screen,'PL',(67,84),GOLD if self.language=='pl' else WHITE,True)

    def panel(self, screen, rect):
        pygame.draw.rect(screen, (8, 22, 34), rect)
        pygame.draw.rect(screen, (49, 120, 143), rect, 2)
        x,y,w,h = rect
        pygame.draw.line(screen, CYAN, (x,y), (x+35,y), 3)

    def wrap(self, text, width):
        # Character fallback also wraps a single very long word.
        text=i18n.translate(text)
        lines, line = [], ''
        for word in text.split():
            candidate = (line+' '+word).strip()
            if self.font.size(candidate)[0] <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            line = ''
            for char in word:
                if line and self.font.size(line+char)[0] > width:
                    lines.append(line)
                    line = ''
                line += char
        return [i18n.OriginalText(x) for x in lines+[line]] if isinstance(text,i18n.OriginalText) else lines+[line]

    def draw(self, screen, quest, target, dialogue, line_index):
        self.panel(screen, (18,16,924,86))
        screen.blit(self.title.render('CHESS CORP',False,CYAN), (34,28))
        self.text(screen, '01 / PIERWSZY DZIEŃ', (34,62), small=True)
        objective = 'Pierwszy dzień zaliczony!' if quest.complete else quest.objective
        self.text(screen, objective, (310,34), GOLD if quest.complete else WHITE)
        self.text(screen, 'Identyfikator: ' + ('ODEBRANY' if 'employee_badge' in quest.inventory else 'brak'), (310,67), CYAN, True)
        self.draw_controls(screen)
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

    def draw_controls(self,screen):
        self.panel(screen,(18,502,924,29))
        self.text(screen,'WASD Ruch  E Akcja  T Czat  F Drzwi  Spacja Cios  H Leczenie  J Questy  Tab Mapa  M Audio  R Restart',(30,510),small=True)

    def draw_chat(self,screen,chat):
        self.panel(screen,(60,126,840,364))
        provider = chat.provider or 'tryb ustala serwer'
        self.text(screen,f'{chat.npc_name} | {provider} | {chat.language.upper()}',(78,138),CYAN)
        self.text(screen,'Enter: wyślij | Esc: zamknij | F2: PL/EN | PgUp/PgDn: historia',(78,164),small=True)
        lines=[]
        for entry_index,entry in enumerate(chat.history):
            label = 'Ty: ' if entry['role']=='user' else chat.npc_name+': '
            color = WHITE if entry['role']=='user' else CYAN
            lines.extend((line,color) for line in self.wrap(label+(self.ai_text(entry['content'],chat.history_languages[entry_index] if entry_index<len(chat.history_languages) else 'und') if entry['role']=='assistant' else i18n.OriginalText(entry['content'])),790))
            lines.append(('',WHITE))
        if not lines:
            lines=[('Zapytaj '+chat.npc_name+' o Chess Corp lub jego sprawy.',WHITE)]
        visible=8
        chat.scroll=min(chat.scroll,max(0,len(lines)-visible))
        end=len(lines)-chat.scroll
        for i,(line,color) in enumerate(lines[max(0,end-visible):end]):
            self.text(screen,line,(78,190+i*20),color)
        if chat.pending:
            self.text(screen,'Buddy pisze...',(78,354),GOLD)
        elif chat.error:
            self.text(screen,self.wrap(chat.error,790)[0],(78,354),GOLD)
            self.text(screen,'F3: przywróć wiadomość do ponowienia',(78,375),GOLD,True)
        else:
            self.text(screen,'Wpisz wiadomość. Zmiany questu wykonuje wyłącznie gra.',(78,354),small=True)
        self.panel(screen,(76,399,807,74))
        before=chat.text[:chat.cursor]
        after=chat.text[chat.cursor:]
        input_lines=self.wrap(before+'|'+after,780)[-3:]
        for i,line in enumerate(input_lines):
            self.text(screen,line,(88,408+i*19))
        self.text(screen,f'{len(chat.text)}/600',(817,476),small=True)
