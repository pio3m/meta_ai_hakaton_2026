"""Local deterministic combat and economy; model decisions never award money."""
import math
from collections import deque
import pygame
from game.data import ROOT, read_json
from game.ui import CYAN, GOLD, WHITE

class Adventure:
    def __init__(self):
        self.data=read_json('adventure.json')
        self.credits=0; self.health=100; self.max_health=100; self.medkits=1
        self.weapon=False; self.armor=False; self.contract=-1; self.state='available'
        self.rats=[]; self.killed=set(); self.claimed=set(); self.stock={'medkit':3,'weapon':1,'armor':1}
        self.shop_open=False; self.selection=0; self.shop_message='E / Enter: kup. Esc: zamknij.'
        self.clock=0.; self.cooldown=0.; self.attack_ttl=0.; self.hurt_ttl=0.; self.effects=[]
        self.events=deque(maxlen=8); self.frames=[]; self.asset_source='ORIGINAL'; self.portrait=None
        if (ROOT/'assets/generated/cyber_rat.public.json').exists():
            try:
                self.frames=[pygame.image.load(str(ROOT/f'assets/generated/cyber_rat_{i}.png')).convert_alpha() for i in range(4)]
                self.asset_source='META'
            except (OSError,pygame.error): self.frames=[]
        try: self.portrait=pygame.image.load(str(ROOT/'assets/generated/merchant.png')).convert_alpha()
        except (OSError,pygame.error): pass

    @property
    def dead(self): return self.health<=0
    @property
    def kills(self): return sum(r['id'] in self.killed for r in self.rats)
    @property
    def damage(self): return 2 if self.weapon else 1

    def _sound(self,name):
        audio=getattr(self,'audio',None)
        if audio:audio.play(name)

    def event(self,text,living=None):
        self.events.append(text[:140])
        if living: living.event(text,tuple(living.npcs),'FALLBACK',True)

    def talk(self,living,npc,text):
        actor=living.npcs[npc]; origin='MOCK' if living.last_source=='MOCK' else 'FALLBACK'
        actor.update(player_engaged=True,moving=False,state='WAIT',bubble=text,bubble_ttl=7.,bubble_source=origin)
        living.conversation_priority_until=living.clock+7.; living.visible_speaker=npc; living.speaker_until=living.clock+7.; living.visible_utterance=text; living.visible_origin=origin
        self.event(actor['name']+': '+text,living)
        if npc!='merchant':self._sound('conversation')

    def bounty(self,living=None):
        if self.state=='ready':
            if self.contract in self.claimed: return False
            reward=self.data['contracts'][self.contract]['reward']; self.credits+=reward; self.claimed.add(self.contract)
            self._sound('credits')
            self.state='claimed'; text=f'Kontrakt zamknięty. +{reward} KR! Sprzęt kupisz u Nyx po prawej.'
        elif self.state in ('available','claimed') and self.contract+1<len(self.data['contracts']):
            self.contract+=1; contract=self.data['contracts'][self.contract]; self.state='active'; self.rats=[]
            for i,pos in enumerate(contract['spawns']):
                self.rats.append({'id':f'rat-{self.contract}-{i}','position':list(map(float,pos)),'home':list(pos),'hp':contract['hp'],'max_hp':contract['hp'],'bite_cd':.8+i*.15,'flash':0.,'facing_left':False,'phase':i*1.7})
            text=f"{contract['name']}: pokonaj {len(self.rats)} szczury na ulicy. Nagroda {contract['reward']} KR + łup. Spacja: cios. H: apteczka."
        elif self.state=='active': text=f'Na ulicy zostało {len(self.rats)-self.kills} szczurów. Wróć po nagrodę. Nyx sprzedaje sprzęt.'
        else: text='Oba kontrakty rozliczone. Dobra robota, łowco!'
        if living: self.talk(living,'bartender',text)
        return True

    def interact(self,game):
        if game.locations.id!='bar': return False
        nearby=min(game.living.npcs.values(),key=lambda n:math.dist(n['position'],game.player.position))
        if math.dist(nearby['position'],game.player.position)>70 or nearby.get('hostile') or nearby.get('down_time',0)>0: return False
        obj=game.locations.rooms['bar']['interactable']
        if math.dist(obj['position'],game.player.position)<math.dist(nearby['position'],game.player.position): return False
        if nearby['id']=='bartender': return self.bounty(game.living)
        if nearby['id']=='merchant':
            self._sound('shop_open')
            self.shop_open=True; self.shop_message='E / Enter: kup. Esc: zamknij.'
            self.talk(game.living,'merchant','Witaj u Nyx. Wybierz sprzęt — płacisz kredytami z kontraktów.'); return True
        return False

    def buy(self,kind):
        item=next((i for i in self.data['shop'] if i['id']==kind),None)
        if not item or self.stock.get(kind,0)<=0: self.shop_message='Wyprzedane / ulepszenie już posiadasz.'; return False
        if self.credits<item['price']: self.shop_message='Za mało kredytów. Barman płaci za kontrakty.'; return False
        self.credits-=item['price']; self.stock[kind]-=1
        if kind=='medkit': self.medkits+=1
        elif kind=='weapon': self.weapon=True
        elif kind=='armor': self.armor=True; self.max_health=125; self.health=min(125,self.health+25)
        self._sound('purchase')
        self.shop_message='Kupiono: '+item['name']; self.event(self.shop_message); return True

    def heal(self):
        if not self.dead and self.health<self.max_health and self.medkits:
            self.medkits-=1; self.health=min(self.max_health,self.health+45); self.event('Użyto apteczki: +45 HP'); self._sound('heal'); return True
        return False

    def respawn(self,player):
        if not self.dead: return False
        self.credits=max(0,self.credits-5); self.health=self.max_health; self.hurt_ttl=2.; player.x,player.y=820.,452.
        for rat in self.rats:
            if rat['id'] not in self.killed: rat['position']=list(rat['home']); rat['hp']=rat['max_hp']; rat['bite_cd']=2.
        for living in getattr(self,'livings',{}).values():
            for actor in living.npcs.values():actor.update(hostile=False,down_time=0.,combat_hp=actor.get('combat_max_hp',14))
        self.event('Ratunek: do 5 KR. Postęp kontraktu zachowany.'); return True

    def attack(self,position,facing_left):
        if self.cooldown>0 or self.dead: return []
        self._sound('swing')
        self.cooldown=.32; self.attack_ttl=.16; self.attack_left=facing_left; self.attack_position=tuple(position); hits=[]
        living=getattr(self,'living',None)
        for rat in self.rats if living is None or living.location_id=='corporate_street' else []:
            if rat['id'] in self.killed: continue
            dx=rat['position'][0]-position[0]; dy=abs(rat['position'][1]-position[1])
            if abs(dx)<=88 and dy<=32 and (abs(dx)<=25 or (dx<0)==facing_left):
                self._sound('hit')
                rat['hp']=max(0,rat['hp']-self.damage); rat['flash']=.16
                rat['position'][0]=max(42,min(918,rat['position'][0]+(-22 if facing_left else 22)))
                hits.append(rat['id']); self.effects.append([list(rat['position']),'-'+str(self.damage),.7,CYAN])
                if rat['hp']==0:
                    self._sound('rat_down')
                    self.killed.add(rat['id']); loot=self.data['contracts'][self.contract]['loot']; self.credits+=loot
                    self.effects.append([list(rat['position']),f'+{loot} KR',1.,GOLD]); self.event('Zlikwidowano '+rat['id']+f' / +{loot} KR')
        living=getattr(self,'living',None)
        if living:
            for actor in living.npcs.values():
                dx=actor['position'][0]-position[0];dy=abs(actor['position'][1]-position[1])
                if actor.get('down_time',0)>0 or abs(dx)>78 or dy>32 or (abs(dx)>25 and (dx<0)!=facing_left):continue
                maximum=24 if actor['id'] in ('security','lobby_guard') else 14
                actor['combat_max_hp']=maximum;actor['combat_hp']=max(0,actor.get('combat_hp',maximum)-self.damage)
                actor.update(hostile=True,player_engaged=False,mood='alert',goal='Bronić się przed agresją gracza.',bubble_ttl=0.)
                living.event('Gracz uderzył '+actor['name']+'. NPC broni się.',(actor['id'],),'FALLBACK',True)
                self._sound('hit');hits.append(actor['id'])
                self.effects.append([list(actor['position']),'-'+str(self.damage),.7,CYAN])
                if actor['combat_hp']==0:
                    actor.update(hostile=False,down_time=12.,state='WAIT',moving=False)
                    living.event(actor['name']+' jest ogłuszony. Wróci do siebie.',(actor['id'],),'FALLBACK',True)
        if self.rats and self.kills==len(self.rats): self.state='ready'; self.event('Ulica oczyszczona. Wróć do Barmana po wypłatę.')
        return hits

    def update(self,dt,game,keys):
        dt=max(0,min(.1,dt)); self.clock+=dt
        self.effects=[e for e in self.effects if e[2]>0]
        for e in self.effects: e[2]-=dt; e[0][1]-=dt*20
        self.cooldown=max(0,self.cooldown-dt); self.attack_ttl=max(0,self.attack_ttl-dt)
        paused=game.dialogue or game.chat.open or game.director.answer_open or game.locations.fade or game.locations.map_open or self.shop_open or game.jobs.open
        if paused or self.dead: return
        self.hurt_ttl=max(0,self.hurt_ttl-dt)
        if keys[pygame.K_SPACE]: self.attack(game.player.position,game.player.facing_left)
        for rat in self.rats if game.locations.id=='corporate_street' else []:
            if rat['id'] in self.killed: continue
            rat['flash']=max(0,rat['flash']-dt); rat['bite_cd']=max(0,rat['bite_cd']-dt)
            x,y=rat['position']; px,py=game.player.position; distance=math.dist((x,y),(px,py))
            if distance<245: tx,ty=px,py
            else: tx,ty=rat['home'][0]+math.sin(self.clock*.8+rat['phase'])*45,rat['home'][1]
            dx,dy=tx-x,ty-y; dist=math.hypot(dx,dy)
            if dist>15:
                step=min(dist,(74 if distance<245 else 30)*dt)
                rat['position']=[max(42,min(918,x+dx/dist*step)),max(424,min(480,y+dy/dist*step))]; rat['facing_left']=dx<0
            if distance<29 and rat['bite_cd']==0 and self.hurt_ttl==0:
                damage=max(1,(10 if self.contract==0 else 14)-(3 if self.armor else 0))
                self.health=max(0,self.health-damage); rat['bite_cd']=1.; self.hurt_ttl=.65
                self.effects.append([[px,py-65],'-'+str(damage)+' HP',.7,(255,110,135)])
                if self.dead: self.event('Gracz pokonany. Enter: ratunek.'); break

        for actor in game.living.npcs.values():
            if not actor.get('hostile') or actor.get('down_time',0)>0:continue
            actor['attack_cd']=max(0,actor.get('attack_cd',0)-dt)
            if math.dist(actor['position'],game.player.position)<42 and actor['attack_cd']==0 and self.hurt_ttl==0:
                damage=max(1,(12 if actor['id'] in ('security','lobby_guard') else 6)-(3 if self.armor else 0))
                self.health=max(0,self.health-damage);self.hurt_ttl=.65;actor['attack_cd']=.9
                self.effects.append([[game.player.x,game.player.y-65],'-'+str(damage)+' HP',.7,(255,110,135)])
                self._sound('hit')
                if self.dead:self.event('Gracz pokonany przez '+actor['name']);break

    def snapshot(self):
        return {'health':self.health,'max_health':self.max_health,'credits':self.credits,'medkits':self.medkits,'weapon_upgrade':self.weapon,'armor':self.armor,
                'bounty_state':self.state,'contract_index':self.contract,'kills':self.kills,'target':len(self.rats),'claimed_contracts':sorted(self.claimed),
                'enemies':[{'id':r['id'],'position':[round(v,1) for v in r['position']],'hp':r['hp'],'max_hp':r['max_hp']} for r in self.rats], 'events':list(self.events)}

    def draw_world(self,screen,ui,game):
        for actor in game.living.npcs.values():
            if actor.get('hostile') or actor.get('down_time',0)>0:
                x,y=actor['position'];hp=actor.get('combat_hp',14);maximum=actor.get('combat_max_hp',14)
                pygame.draw.rect(screen,(45,18,28),(int(x-22),int(y-114),44,5))
                pygame.draw.rect(screen,(255,105,120),(int(x-22),int(y-114),int(44*hp/maximum),5))
                if actor.get('down_time',0)>0:ui.text(screen,'Ogłuszony',(x-30,y-131),GOLD,True)
        for r in sorted(self.rats if game.locations.id=='corporate_street' else [],key=lambda r:r['position'][1]):
            if r['id'] in self.killed: continue
            x,y=r['position']; pygame.draw.ellipse(screen,(5,12,20),(x-27,y-5,54,9))
            if self.frames:
                sprite=self.frames[int(self.clock*9+r['phase'])%4].copy()
                if r['facing_left']: sprite=pygame.transform.flip(sprite,True,False)
                if r['flash']: sprite.fill((120,120,120,0),special_flags=pygame.BLEND_RGBA_ADD)
                screen.blit(sprite,(round(x-sprite.get_width()/2),round(y-sprite.get_height())))
            else:
                pygame.draw.ellipse(screen,(147,80,167),(x-20,y-23,39,22)); pygame.draw.line(screen,CYAN,(x-20,y-5),(x-39,y-15),3); pygame.draw.circle(screen,(255,85,95),(int(x+15),int(y-17)),3)
            pygame.draw.rect(screen,(48,24,45),(int(x-20),int(y-53),40,4)); pygame.draw.rect(screen,(255,104,141),(int(x-20),int(y-53),int(40*r['hp']/r['max_hp']),4))
        if self.attack_ttl:
            x,y=self.attack_position; left=self.attack_left
            pygame.draw.arc(screen,CYAN,(int(x-85),int(y-65),170,80),math.pi/2 if left else -math.pi/2,3*math.pi/2 if left else math.pi/2,5)
        for pos,text,ttl,color in self.effects: ui.text(screen,text,pos,color,True)

    def draw_ui(self,screen,ui,game):
        modal=game.dialogue or game.chat.open or game.director.answer_open or game.locations.map_open or game.locations.fade
        if not modal:
            y=67
            pygame.draw.rect(screen,(45,38,56),(620,y+3,45,7)); pygame.draw.rect(screen,(100,224,175),(620,y+3,int(45*self.health/self.max_health),7))
            ui.text(screen,f'{self.health}/{self.max_health} HP | {self.credits} KR | H: {self.medkits}',(675,y),GOLD,True)
            if self.state in ('active','ready'): text=f'SZCZURY {self.kills}/{len(self.rats)} | '+('WRÓĆ DO BARMANA PO NAGRODĘ' if self.state=='ready' else 'SPACJA: CIOS / H: APTECZKA')
            elif self.state=='claimed': text='BARMAN: kolejny kontrakt | NYX: sklep'
            else: text='BAR: kontrakty u Barmana / sklep Nyx'
            ui.text(screen,text,(310,84),CYAN,True)
        if self.shop_open:
            ui.panel(screen,(155,145,650,342)); ui.text(screen,'NYX / SPRZĘT DLA ŁOWCÓW',(180,166),CYAN); ui.text(screen,f'{self.credits} KR',(685,166),GOLD)
            if self.portrait: screen.blit(pygame.transform.scale(self.portrait,(96,144)),(185,214))
            else: ui.text(screen,'NYX',(195,250),GOLD)
            for i,item in enumerate(self.data['shop']):
                y=215+i*65
                if i==self.selection: pygame.draw.rect(screen,(22,53,65),(300,y-7,479,59))
                label=('> ' if i==self.selection else '  ')+item['name']+f" / {item['price']} KR"
                ui.text(screen,label,(310,y),GOLD if i==self.selection else WHITE)
                ui.text(screen,item['description']+f" [zapas {self.stock[item['id']]}]",(326,y+24),CYAN,True)
            for i,line in enumerate(ui.wrap(self.shop_message,590)[:2]): ui.text(screen,line,(180,417+i*22),GOLD,True)
            ui.text(screen,'Góra/dół: wybór   Enter / E: kup   Esc: wyjdź',(180,463),WHITE,True)
        if self.dead:
            ui.panel(screen,(195,200,570,180)); ui.text(screen,'SYSTEM RATUNKOWY CHESS CORP',(220,224),(255,110,135))
            ui.text(screen,'Pokonały cię cyber-szczury. Kontrakt zachowany.',(220,267),WHITE)
            ui.text(screen,'Enter: wróć na ulicę (koszt do 5 KR)',(220,310),GOLD)
