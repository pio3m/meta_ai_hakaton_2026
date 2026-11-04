"""Connected rooms reuse World and LivingWorld; transitions never reset the session."""
import json
import math
from collections import deque
from pathlib import Path
import pygame
from game.data import ROOT,read_json
from game.living_world import LivingWorld
from game.world import World
from game.ui import CYAN,GOLD,WHITE


class Locations:
    def __init__(self,street,session_id):
        self.rooms=read_json('locations.json')['locations']
        self.scenes={'corporate_street':{**street,'name':'ULICA CHESS CORP'},**self.rooms}
        self.worlds={key:World(scene) for key,scene in self.scenes.items()}
        first=LivingWorld(street,session_id)
        self.livings={'corporate_street':first}
        for key,room in self.rooms.items():self.livings[key]=LivingWorld(room,session_id,rules=room,planner=first.planner)
        self.backgrounds={key:pygame.image.load(str(ROOT/scene['background'])).convert() for key,scene in self.scenes.items()}
        self.visited={'corporate_street'};self.events=deque(maxlen=8);self.id='corporate_street'
        self.fade=None;self.elapsed=0.;self.switched=False;self.title_ttl=0.;self.notice=None;self.notice_ttl=0.;self.map_open=False
        self.sprite_cache={}
        for room in self.rooms.values():
            for npc in room['npcs']:
                prefix=npc.get('sprite_prefix')
                if prefix and prefix not in self.sprite_cache:
                    folder='assets/generated' if prefix=='merchant' and (ROOT/'assets/generated/merchant.public.json').is_file() else 'assets/processed'
                    fallback='bar_guest' if prefix=='merchant' and folder=='assets/processed' else prefix
                    self.sprite_cache[prefix]=[pygame.image.load(str(ROOT/f'{folder}/{fallback}_{i}.png')).convert_alpha() for i in range(4)]
        self.decor=pygame.image.load(str(ROOT/'assets/processed/original_hologram.png')).convert_alpha();self.decor_source='ORYGINAŁ'
        manifest=ROOT/'assets/generated/hacker_emblem.public.json';image=ROOT/'assets/generated/hacker_emblem.png'
        if manifest.is_file() and image.is_file():
            try:
                info=json.loads(manifest.read_text(encoding='utf-8'));self.decor=pygame.image.load(str(image)).convert_alpha();self.decor_source=info['source']+' / '+info['model']
            except (ValueError,KeyError,pygame.error):pass

    def cancel(self):
        for living in self.livings.values():living.cancel()

    def portals(self):
        if self.id=='corporate_street':return [(key,room['street_entry'],{'bar':'BAR','hacker_hideout':'KRYJÓWKA','corporate_lobby':'LOBBY'}[key]) for key,room in self.rooms.items()]
        return [('corporate_street',self.rooms[self.id]['exit_position'],'ULICA')]

    def nearest_portal(self,position):return min((p for p in self.portals() if math.dist(position,p[1])<=65),key=lambda p:math.dist(position,p[1]),default=None)

    def travel(self,position):
        portal=self.nearest_portal(position)
        if portal and self.fade is None:
            target=portal[0];spawn=self.rooms[self.id]['return_position'] if target=='corporate_street' else self.rooms[target]['spawn']
            self.fade=(target,spawn);self.elapsed=0.;self.switched=False
            return True
        return False

    def update(self,dt,game):
        dt=max(0,min(dt,.1));self.title_ttl=max(0,self.title_ttl-dt);self.notice_ttl=max(0,self.notice_ttl-dt)
        if self.fade:
            self.elapsed+=dt
            if self.elapsed>=.22 and not self.switched:
                target,spawn=self.fade;self.id=target;self.visited.add(target);self.switched=True
                game.world=self.worlds[target];game.living=self.livings[target];game.background=self.backgrounds[target]
                game.player.x,game.player.y=spawn;game.player.moving=False;self.title_ttl=1.7
                event='Gracz odwiedził: '+self.scenes[target]['name'];self.events.append(event)
                game.living.event(event,tuple(game.living.npcs),'FALLBACK',True)
                self.notice=None;self.notice_ttl=0
            if self.elapsed>=.44:self.fade=None
        for key,living in self.livings.items():
            active=key==self.id;living.journey_events=self.events
            living.gameplay=game.adventure.snapshot() if hasattr(game,'adventure') else None
            living.asset_sources=[{'id':'scene_original','source':'ORIGINAL','model':''}]
            if key=='hacker_hideout' and self.decor_source.startswith('META'):living.asset_sources.append({'id':'hacker_emblem','source':'META','model':'muse-image-1.0'})
            if key=='corporate_street' and hasattr(game,'adventure') and game.adventure.asset_source=='META':living.asset_sources.append({'id':'cyber_rat','source':'META','model':'muse-image-1.0'})
            if key=='bar' and ('merchant' in self.live_asset_versions if hasattr(self,'live_asset_versions') else (ROOT/'assets/generated/merchant.public.json').is_file()):living.asset_sources.append({'id':'merchant','source':'META','model':'muse-image-1.0'})
            living.update(dt,game.player.position if active else [-1000,-1000],game.quest.complete,bool(active and (game.dialogue or game.chat.open)),active=active)

    def interact(self,position,quest):
        if self.id=='corporate_street':return False
        obj=self.rooms[self.id]['interactable']
        distance=math.dist(position,obj['position'])
        if distance>58:return False
        if any(math.dist(position,npc['position'])<distance for npc in self.livings[self.id].npcs.values()):return False
        fresh=obj['item'] not in quest.inventory;quest.inventory.add(obj['item'])
        text=obj['text'] if fresh else 'Ten wpis jest już w twoim ekwipunku. '+obj['text']
        self.notice=(obj['label'],text);self.notice_ttl=6.
        self.livings[self.id].event(text,tuple(self.livings[self.id].npcs),'FALLBACK',True)
        return True

    def draw_scene(self,screen,ui):
        for _,(x,y),_ in self.portals():
            pygame.draw.rect(screen,(9,26,36),(int(x-21),int(y-85),42,65));pygame.draw.rect(screen,CYAN,(int(x-21),int(y-85),42,65),2)
        if self.id=='corporate_street':return
        if self.id=='hacker_hideout':
            screen.blit(self.decor,(740,280))
            ui.panel(screen,(740,280,128,20));ui.text(screen,'OBRAZ / '+('META' if self.decor_source.startswith('META') else 'ORYGINAŁ'),(746,284),GOLD,True)
        room=self.rooms[self.id];obj=room['interactable'];x,y=obj['position']
        pygame.draw.rect(screen,(9,36,45),(int(x-15),int(y-42),30,36));pygame.draw.rect(screen,CYAN,(int(x-15),int(y-42),30,36),2)
        pygame.draw.rect(screen,GOLD,(int(x-8),int(y-35),16,10));ui.text(screen,obj['label'],(max(30,min(730,x-72)),y-65),CYAN,True)
        if self.id=='corporate_lobby':ui.text(screen,'CHESS CORP / RECEPCJA',(360,286),CYAN)

    def draw_ui(self,screen,ui,game):
        if self.id!='corporate_street':
            ui.panel(screen,(18,16,924,86));ui.text(screen,self.scenes[self.id]['name'],(34,30),CYAN)
            ui.text(screen,'Pierwszy dzień: '+('ukończony' if game.quest.complete else game.quest.objective),(34,62),WHITE,True)
            ui.text(screen,'Przedmioty: '+str(len(game.quest.inventory)),(760,34),GOLD,True);ui.draw_controls(screen)
            game.living.draw_overlay(screen,ui,True)
            if self.notice_ttl and self.notice:
                ui.panel(screen,(18,108,612,96));ui.text(screen,self.notice[0],(34,120),GOLD)
                for i,line in enumerate(ui.wrap(self.notice[1],570)[:3]):ui.text(screen,line,(34,147+i*18),WHITE)
        for target,position,label in self.portals():
            x,y=position;near=math.dist(game.player.position,position)<=65
            color=GOLD if near else CYAN
            text=('[F] ' if near else '')+label;w=ui.small.size(text)[0]+12;bx=max(18,min(942-w,x-w/2))
            ui.panel(screen,(int(bx),int(y-112),w,23));ui.text(screen,text,(bx+6,y-107),color,True)
        if self.map_open:
            ui.panel(screen,(140,160,680,270));ui.text(screen,'CHESS CORP / MAPA',(164,180),CYAN)
            for i,(key,scene) in enumerate(self.scenes.items()):
                marker='>' if key==self.id else '+' if key in self.visited else ' '
                ui.text(screen,marker+' '+scene['name'],(175,222+i*34),GOLD if key==self.id else WHITE)
            ui.text(screen,'Z ulicy: lewo — Kryjówka / środek — Lobby / prawo — Bar',(164,375),CYAN,True)
            ui.text(screen,'Przy drzwiach F. Tab / Esc: zamknij mapę.',(164,399),WHITE,True)
        if self.fade:
            alpha=int(255*max(0,1-abs(self.elapsed-.22)/.22));overlay=pygame.Surface((960,540));overlay.fill((5,13,23));overlay.set_alpha(alpha);screen.blit(overlay,(0,0))
        if self.title_ttl:
            text=ui.translate(self.scenes[self.id]['name']);w=ui.title.size(text)[0]
            ui.panel(screen,(int(480-w/2-18),289,w+36,44));screen.blit(ui.title.render(text,False,CYAN),(int(480-w/2),300))
