"""Four deterministic actors, short memories and a paced async planning client."""
import asyncio
import copy
import math
import os
from collections import deque
from time import monotonic
from types import SimpleNamespace
from game.data import read_json
from game.chat import send_request
from game.world_contract import NPC_IDS,local_world_plan,validate_world_plan


class LivingWorld:
    def __init__(self,scene,session_id,transport=send_request,network_enabled=None,network_clock=monotonic,rules=None,planner=None):
        self.network_clock=network_clock
        self.scene=scene;self.location_id=scene.get('id','corporate_street');self.rules=rules or read_json('world_ai.json');
        self.planner=planner or SimpleNamespace(revision=0,requests_sent=0,max_requests=3,interval=30.,next_due=0.,last_started=-1000.)
        self.session_id=session_id;self.transport=transport
        self.network_enabled=os.getenv('CHESS_CORP_WORLD_NETWORK','true').lower()!='false' if network_enabled is None else network_enabled
        self.npcs={p['id']:{**copy.deepcopy(p),'state':'WAIT','memory':deque(maxlen=6),'queue':[],'current':None,'elapsed':0.,'hold':0.,'route_index':0,'frame':0.,'moving':False,'facing_left':False,'bubble':'','bubble_ttl':0.,'source':'FALLBACK'} for p in self.rules['npcs']}
        self.clock=0.;self.events=deque(maxlen=12);self.task=None
        self.last_source='FALLBACK';self.last_error='';self.last_call_id=None;self.plan_cached=False
        self.completed=deque(maxlen=48);self.report_task=None;self.report_due=0.;self.last_react={};self.important=False
        self.apply_plan(self.local_plan(),'FALLBACK')
        self.event('Lokalny start: '+self.location_id,source='FALLBACK')

    @property
    def requests_sent(self):return self.planner.requests_sent

    def local_plan(self):return local_world_plan(self.planner.revision,self.rules,self.location_id)

    def event(self,text,actors=(),source='FALLBACK',important=False):
        text=text[:140]
        self.events.append({'time_s':round(self.clock,1),'text':text,'source':source})
        for ident in actors:
            if ident in self.npcs:self.npcs[ident]['memory'].append(text[:120])
        self.important=self.important or important

    def apply_plan(self,plan,source,plan_id=None):
        validate_world_plan(plan,self.rules,self.scene)
        for decision in plan['decisions']:
            actor=self.npcs[decision['npc_id']]
            actor.update(goal=decision['goal'],mood=decision['mood'],queue=copy.deepcopy(decision['actions']),current=None,elapsed=0.,hold=0.,source=source,plan_id=plan_id)
        self.last_source=source
        self.event(plan['summary'],tuple(self.npcs),source)

    def action_source(self,actor):
        if actor.get('hostile') or actor.get('down_time',0)>0:return 'FALLBACK'
        if actor.get('player_engaged'):return 'MOCK' if self.last_source=='MOCK' else 'FALLBACK'
        return actor['source']

    def snapshot(self,player,first_complete):
        return {'gameplay':getattr(self,'gameplay',None),'asset_sources':getattr(self,'asset_sources',[]),'location_id':self.location_id,'journey_events':list(getattr(self,'journey_events',[]))[-8:],'player_position':list(player),'first_quest_complete':bool(first_complete),
                'npcs':[{'npc_id':n,'source':self.action_source(a),'position':[round(v,1) for v in a['position']],'state':a['state'],'goal':a['goal'],'mood':a['mood'],'memory':list(a['memory'])} for n,a in self.npcs.items()],
                'events':[e['text'] for e in self.events][-8:]}

    def _walk(self,actor,target,dt,pinned):
        x,y=target;l,t,r,b=self.scene['walkable_bounds']
        if self.location_id=='corporate_street' and actor['id']=='buddy' and pinned: x=max(515,min(565,x));y=440
        x=max(l+24,min(r-24,x));y=max(t,min(b,y))
        px,py=actor['position'];dx,dy=x-px,y-py;distance=math.hypot(dx,dy)
        if distance<=3:return True
        step=min(distance,actor['speed']*dt)
        nx,ny=px+dx/distance*step,py+dy/distance*step
        if any(a<=nx<=c and z<=ny<=d for a,z,c,d in self.scene.get('blocked_areas',[])):return False
        actor['position']=[nx,ny];actor['moving']=True;actor['facing_left']=dx<0;actor['frame']+=dt*8
        return distance<=step+3

    def _speak(self,actor,text,other=None,source=None):
        actor['bubble']=text[:90];actor['bubble_ttl']=5.;actor['bubble_source']=source or actor['source']
        actors=(actor['id'],other) if other else (actor['id'],)
        self.event(actor['name']+': '+text,actors,source or actor['source'],important=True)
        if other in self.npcs and not self.npcs[other].get('player_engaged'):
            target=self.npcs[other]
            target['bubble']='Słyszę cię. Zapamiętam to.';target['bubble_ttl']=3.;target['bubble_source']='FALLBACK'

    def update(self,dt,player,first_complete=False,buddy_busy=False,active=True):
        dt=max(0.,min(float(dt),.1));self.clock+=dt;self.player_position=list(player)
        self._network(player,first_complete,active)
        for ident,actor in self.npcs.items():
            actor['moving']=False;actor['bubble_ttl']=max(0.,actor['bubble_ttl']-dt)
            if actor.get('down_time',0)>0:
                actor['down_time']=max(0,actor['down_time']-dt);actor['state']='WAIT';actor['player_engaged']=False
                if actor['down_time']==0:
                    actor.update(combat_hp=actor.get('combat_max_hp',14),hostile=False)
                    self.event(actor['name']+' dochodzi do siebie.',(ident,),'FALLBACK',True)
                continue
            if actor.get('hostile'):
                actor['player_engaged']=False;actor['state']='WAIT'
                if active and not buddy_busy and math.dist(actor['position'],player)>34:
                    actor['state']='MOVE_TO';self._walk(actor,player,dt,self.location_id=='corporate_street' and ident=='buddy' and not first_complete)
                continue
            distance=math.dist(actor['position'],player)
            engaged=actor.get('player_engaged',False)
            if engaged and distance>100:actor['player_engaged']=False;engaged=False
            if not engaged and distance<=65:
                actor['player_engaged']=True;engaged=True
                self._player_reply(actor,opening=True)
            if engaged or (ident=='buddy' and buddy_busy):
                actor['state']='WAIT';actor['facing_left']=player[0]<actor['position'][0]
                if engaged:actor['bubble_ttl']=max(1.,actor['bubble_ttl'])
                continue
            if actor['current'] is None:
                if not actor['queue']:
                    fallback=next(d for d in self.local_plan()['decisions'] if d['npc_id']==ident)
                    actor['queue']=copy.deepcopy(fallback['actions']);actor['source']='MOCK' if self.last_source=='MOCK' else 'FALLBACK';actor['plan_id']=None
                actor['current']=actor['queue'].pop(0);actor['elapsed']=0.;actor['hold']=0.;actor['route_index']=0
                actor['state']=actor['current']['action']
            current=actor['current'];actor['state']=current['action'];kind=current['action'];target=current['target_id'];actor['elapsed']+=dt;done=False
            if kind=='WAIT':done=actor['elapsed']>=current['duration_s']
            elif kind=='PATROL':
                route=current['route'];point=route[actor['route_index']%len(route)]
                if self._walk(actor,self.rules['locations'][point],dt,not first_complete):actor['route_index']+=1
                done=actor['elapsed']>=current['duration_s']
            elif kind=='MOVE_TO':done=self._walk(actor,self.rules['locations'][target],dt,not first_complete)
            else:
                target_pos=player if target=='player' else self.npcs[target]['position'] if target in self.npcs else self.rules['locations'][target]
                reach=210 if kind=='REACT_TO_PLAYER' else 90 if kind=='TALK_TO' else 26
                if math.dist(actor['position'],target_pos)>reach:self._walk(actor,target_pos,dt,not first_complete)
                else:
                    if actor['hold']==0:self._speak(actor,current['text'] or 'Sprawdzam terminal. Wszystko zostaje w raporcie.',target if target in self.npcs else None,source=None if current['text'] else 'FALLBACK')
                    actor['hold']+=dt;done=actor['hold']>=2
            expired=actor['elapsed']>=current['duration_s'] and not done
            if done or expired:
                status='expired' if expired else 'completed'
                self.completed.append({'npc_id':ident,'action':kind,'target_id':target,'status':status,'source':actor['source'],'plan_id':actor.get('plan_id')})
                self.event(actor['name']+' '+kind+' / '+status,(ident,),actor['source'],important=kind=='INSPECT_TERMINAL')
                actor['current']=None
            if math.dist(actor['position'],player)<75 and self.clock-self.last_react.get(ident,-100)>18:
                self.last_react[ident]=self.clock
                self.event('Gracz w pobliżu '+actor['name'],(ident,),'FALLBACK',True)

    def _player_reply(self,actor,opening=False):
        lines={
            'buddy':['Hej, rekrucie! Podejdź, porozmawiajmy.','Jestem tu. Co chcesz wiedzieć?'],
            'security':['Stój na chwilę. Wszystko w porządku?','Pilnuję terminali. Z Hackerem lepiej ostrożnie.','Masz identyfikator? W takim razie spokojnego dnia.'],
            'hacker':['Cicho, pogadajmy. Tylko bez Security.','Szukam danych. Korporacja ma sporo tajemnic.','Jeśli ktoś pyta, rozmawialiśmy o regulaminie.'],
            'employee':['Masz chwilę? Chodzi o mój awans.','Mój raport jest gotowy. Zarząd musi go zauważyć.','Jeśli spotkasz szefa, wspomnij o mnie, dobrze?']}
        index=0 if opening else actor.get('player_line',0)+1
        actor['player_line']=index
        choices=lines.get(actor['id'],actor.get('player_lines',[actor['goal']]))
        text=choices[index%len(choices)]
        origin='MOCK' if self.last_source=='MOCK' else 'FALLBACK'
        actor.update(bubble=text,bubble_ttl=6.,bubble_source=origin)
        self.event(actor['name']+': '+text,(actor['id'],),origin,True)
        if opening and self.clock<getattr(self,'conversation_priority_until',0.):return
        if not opening:self.conversation_priority_until=self.clock+5.
        self.visible_speaker=actor['id'];self.speaker_until=self.clock+5.
        self.visible_utterance=text;self.visible_origin=origin

    def player_interaction(self,position):
        nearby=min((a for n,a in self.npcs.items() if n!='buddy' and a.get('down_time',0)<=0 and math.dist(a['position'],position)<=70),
                   key=lambda a:math.dist(a['position'],position),default=None)
        if nearby:
            nearby['player_engaged']=True;nearby['moving']=False;nearby['state']='WAIT'
            self._player_reply(nearby)
            return True
        return False

    def _network(self,player,first_complete,active=True):
        now=self.network_clock()
        if self.task and self.task.done():
            try:
                data=self.task.result()
                if data.get('error'):raise ValueError(str(data['error']))
                if data.get('location_id',self.location_id)!=self.location_id:raise ValueError('World response belongs to another location')
                source=data.get('provider','fallback').upper()
                if source not in ('META','MOCK','FALLBACK'):raise ValueError('Invalid world source')
                if not data.get('validation',{}).get('valid'):raise ValueError('Invalid world plan')
                self.plan_cached=bool(data.get('cached',False));self.last_call_id=data.get('call_id');self.report_due=0.;self.apply_plan(data['plan'],source,self.last_call_id)
                self.last_error=data.get('error_detail','')[:140]
                limits=data.get('limits',{});self.planner.interval=max(20.,float(limits.get('min_interval_seconds',30)))
                self.planner.max_requests=min(100,int(limits.get('session_limit',3)))
                if limits.get('remaining_calls')==0:self.planner.max_requests=self.planner.requests_sent
            except (Exception,asyncio.CancelledError) as error:
                self.last_call_id=None;self.apply_plan(self.local_plan(),'FALLBACK');self.last_error=str(error)[:140]
            self.task=None;self.planner.next_due=now+self.planner.interval+2.
        if self.report_task and self.report_task.done():
            try:self.report_task.result()
            except (Exception,asyncio.CancelledError):pass
            self.report_task=None
        if not self.network_enabled or not active:return
        try:loop=asyncio.get_running_loop()
        except RuntimeError:return
        if self.task is None and self.planner.requests_sent<self.planner.max_requests and now>=self.planner.next_due:
            self.planner.revision+=1;self.planner.requests_sent+=1;self.planner.last_started=now;self.planner.next_due=now+self.planner.interval+1.
            payload={'session_id':self.session_id,'revision':self.planner.revision,'reason':'event' if self.important else 'interval','snapshot':self.snapshot(player,first_complete)}
            self.important=False
            self.task=loop.create_task(self.transport(payload,'/api/world/plan'))
        if self.report_task is None and now>=self.report_due:
            self.report_due=now+4
            report={'session_id':self.session_id,'snapshot':self.snapshot(player,first_complete),'call_id':self.last_call_id,'completed_actions':list(self.completed)[-24:]}
            self.report_task=loop.create_task(self._report_world(report))

    async def _report_world(self,report):
        await self.transport({'session_id':report['session_id'],'snapshot':report['snapshot']},'/api/world/presence')
        if report['call_id']:return await self.transport(report,'/api/world/execution')
        return {}

    def cancel(self):
        for task in (self.task,self.report_task):
            if task:task.cancel()

    def draw_overlay(self,screen,ui,show_feed=True):
        from game.ui import CYAN,WHITE
        # AI state, sources and roster belong exclusively to the authenticated Inspector.
        engaged=[a for a in self.npcs.values() if a.get('player_engaged') and a['id']!='buddy']
        nearest=min(engaged,key=lambda a:math.dist(a['position'],self.player_position),default=None)
        if nearest:
            text='[E] / [T] '+nearest['name'];width=ui.small.size(text)[0]+16
            x=max(18,min(942-width,nearest['position'][0]-width/2));y=nearest['position'][1]-112
            ui.panel(screen,(int(x),int(y),width,23));ui.text(screen,text,(x+8,y+5),CYAN,True)
        # Automatic greetings stay in NPC memory; only an explicit conversation opens UI.
        if self.clock>=getattr(self,'conversation_priority_until',0.):return
        actor=self.npcs.get(getattr(self,'visible_speaker',None))
        if not actor or not actor.get('player_engaged') or actor['bubble_ttl']<=0:return
        y=212 if not show_feed else 108
        ui.panel(screen,(18,y,612,96))
        ui.text(screen,actor['name']+'   [E] Rozmawiaj',(34,y+12),actor['color'])
        for i,line in enumerate(ui.wrap(self.visible_utterance,570)[:3]):
            ui.text(screen,line,(34,y+39+i*18),WHITE)
