"""Existing Director client, extended with deterministic v2 quest transitions."""
import asyncio
from math import dist
from game.data import read_json
from game.chat import send_request
from game.director_contract import objects_for_plan, quest_kind, initial_execution, execute_event, puzzle_question


def validate_plan(plan, scene, rules):
    objects = objects_for_plan(plan,scene,rules)
    return objects[0] if plan['schema_version']==1 else objects


class Director:
    def __init__(self, scene, transport=send_request):
        self.scene,self.transport,self.rules=scene,transport,read_json('director_rules.json')
        self.state='idle';self.task=None;self.plan=None;self.object=None;self.objects=[]
        self.error='';self.provider='';self.collected=set();self.mock_type='COLLECT'
        self.execution=initial_execution();self.trace=[];self.execution_task=None;self.execution_pending=None
        self.execution_error='';self.call_id=None;self.session_id=None
        self.answer_open=False;self.answer='';self.notice=''

    @property
    def quest_type(self): return quest_kind(self.plan) if self.plan else self.mock_type

    @staticmethod
    def eligible(quest): return quest.complete and 'employee_badge' in quest.inventory

    def start(self, quest, session_id, language='pl', retry=False):
        if not self.eligible(quest) or self.state not in (('error',) if retry else ('idle',)): return False
        try: loop=asyncio.get_running_loop()
        except RuntimeError: return False
        body={'session_id':session_id,'language':language,'context':{'quest_id':'first_day','quest_status':'completed','has_badge':True},'retry':retry,'mock_type':self.mock_type}
        self.session_id=session_id
        self.task=loop.create_task(self.transport(body,'/api/director'));self.state='pending';self.error=''
        return True

    def poll(self, quest):
        self._poll_execution()
        if not self.task or not self.task.done(): return
        try:
            data=self.task.result()
            if data.get('error'): raise ValueError(str(data['error'])[:180])
            if data.get('validation',{}).get('valid') is not True or not self.eligible(quest): raise ValueError('Plan niezatwierdzony')
            objects=objects_for_plan(data['plan'],self.scene,self.rules)
            self.plan=data['plan'];self.objects=objects
            self.object=objects[0] if self.quest_type=='COLLECT' else None
            self.provider=data.get('provider','mock');self.call_id=data.get('call_id');self.state='active'
        except (Exception,asyncio.CancelledError) as error:
            self.state='error';self.error=str(error)[:180] or 'Nie udało się odczytać planu.'
        finally: self.task=None

    def nearby(self, position):
        return next((o for o in self.objects if dist(position,o['position'])<=o['interaction_radius']),None)

    def interact(self, position, quest):
        if self.state!='active' or not self.eligible(quest): return False
        obj=self.nearby(position)
        if not obj: return False
        if self.quest_type=='LOGIC_PUZZLE':
            self.answer_open=True;self.answer=''
        else:
            self._apply({'action':'interact','object_id':obj['id'],'position':list(position),'answer':''})
        return True

    def collect(self, position, quest):
        return self.interact(position,quest) if self.quest_type=='COLLECT' else False

    def insert_answer(self, value):
        self.answer += ''.join(c for c in value if '0' <= c <= '9')[:32-len(self.answer)]

    def submit_answer(self, position, quest):
        if not self.answer_open or self.state!='active' or not self.eligible(quest): return False
        obj=self.nearby(position)
        if not obj: return False
        self._apply({'action':'answer','object_id':obj['id'],'position':list(position),'answer':self.answer})
        self.answer=''
        if self.state=='completed': self.answer_open=False
        return True

    def _apply(self, event):
        if len(self.trace)>=100:
            self.notice='Limit 100 prób tej sesji. R: nowa rozgrywka.';return
        self.execution=execute_event(self.execution,self.plan,self.objects,event,self.scene)
        self.trace.append(event);self.notice=self.execution['message']
        if self.execution['status']=='completed':
            self.state='completed'
            if self.quest_type=='COLLECT': self.collected.add(self.object['id']);self.object=None
        if self.call_id:
            self.execution_pending={'session_id':self.session_id,'call_id':self.call_id,'events':list(self.trace)}
            self._poll_execution()

    def _poll_execution(self):
        if self.execution_task and self.execution_task.done():
            try:
                result=self.execution_task.result()
                self.execution_error=str(result.get('error',''))[:180]
            except (Exception,asyncio.CancelledError): self.execution_error='Brak potwierdzenia wykonania w Inspectorze.'
            self.execution_task=None
        if self.execution_pending and self.execution_task is None:
            try: loop=asyncio.get_running_loop()
            except RuntimeError: return
            self.execution_task=loop.create_task(self.transport(self.execution_pending,'/api/director/execution'))
            self.execution_pending=None

    def context(self):
        if self.state not in ('active','completed'): return None
        q=self.plan['create_quest']['quest']
        return {'id':q['id'],'title':q['title'],'objective':q['objective'],'status':self.state,'quest_type':self.quest_type}

    def cancel(self):
        for name in ('task','execution_task'):
            task=getattr(self,name)
            if task: task.cancel();setattr(self,name,None)
        self.execution_pending=None

    def draw(self, screen, ui, position):
        import pygame
        from game.ui import CYAN,GOLD
        if self.state=='idle':
            ui.text(screen,'F4: scenariusz mock — '+self.mock_type+' (wybierz przed końcem pierwszego questu)',(34,122),CYAN,True)
            return
        kind=self.quest_type
        for obj in self.objects:
            if kind=='COLLECT' and self.state=='completed': continue
            x,y=obj['position'];is_terminal=kind!='COLLECT'
            accepted=kind=='SEQUENCE' and obj['id'] in self.plan['sequence'][:self.execution['progress']]
            color=GOLD if accepted or self.state=='completed' else CYAN
            pygame.draw.ellipse(screen,(5,16,23),(x-18,y-5,36,10))
            pygame.draw.rect(screen,(10,40,52),(x-13,y-(40 if is_terminal else 23),26,39 if is_terminal else 22))
            pygame.draw.rect(screen,color,(x-13,y-(40 if is_terminal else 23),26,39 if is_terminal else 22),2)
            pygame.draw.rect(screen,GOLD,(x-6,y-(33 if is_terminal else 17),12,8))
            label=obj['id'][-1].upper() if kind=='SEQUENCE' else '?' if is_terminal else ''
            if label: ui.text(screen,label,(x-5,y-65),color)
            if self.state=='active' and dist(position,obj['position'])<=obj['interaction_radius']:
                hint='[E] Odbierz nośnik' if kind=='COLLECT' else '[E] Rozwiąż zagadkę' if kind=='LOGIC_PUZZLE' else '[E] Aktywuj '+label
                ui.text(screen,hint,(max(20,min(750,x-75)),y-94),color,True)
        ui.panel(screen,(18,118,924,128))
        ui.text(screen,'02 / DIRECTOR  •  '+(self.provider or 'oczekiwanie').upper()+'  /  '+kind,(34,130),CYAN,True)
        if self.state=='pending': lines=['Director przygotowuje kolejny quest… Możesz chodzić po ulicy.']
        elif self.state=='error': lines=ui.wrap(self.error,880)[:3]+['G: ponów generowanie     R: nowa sesja']
        else:
            q=self.plan['create_quest']['quest']
            lines=[('UKOŃCZONE: ' if self.state=='completed' else '')+q['title']]
            lines+=ui.wrap(q['completion_message'] if self.state=='completed' else q['objective'],880)[:1]
            if self.state=='active':
                if kind=='SEQUENCE':
                    order=' > '.join(t[-1].upper() for t in self.plan['sequence'])
                    hint='Kolejność silnika: '+order+f"   Postęp: {self.execution['progress']}/3"
                else:
                    placements=[self.plan['place_object']] if self.plan['schema_version']==1 else self.plan['place_objects']
                    side={'east_side':'PRAWA','west_side':'LEWA','center_side':'ŚRODEK'}[placements[0]['spawn_point']]
                    hint='Cel silnika: '+side+' strona / miejsce — podejdź do obiektu i naciśnij E.'
                lines += [hint,self.notice or ('Błędny terminal zeruje kolejność.' if kind=='SEQUENCE' else '')]
        for i,line in enumerate(lines[:4]): ui.text(screen,line,(34,152+i*20),GOLD if self.state=='completed' else CYAN)
        if self.answer_open:
            ui.panel(screen,(95,270,770,214));ui.text(screen,'TERMINAL ZAGADKI — wpisz samą liczbę',(115,282),CYAN)
            for i,line in enumerate(ui.wrap(puzzle_question(self.plan['puzzle']),725)[:4]): ui.text(screen,line,(115,309+i*21))
            pygame.draw.rect(screen,CYAN,(112,402,730,36),1);ui.text(screen,self.answer+'|',(123,412),GOLD)
            ui.text(screen,(self.notice or 'Enter: sprawdź odpowiedź     Esc: zamknij')[:95],(115,452),GOLD,True)
