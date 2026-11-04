"""Small mixer-only audio layer. Cached assets, one ambient channel, silent failure."""
from collections import Counter
import json
import sys
import pygame
from game.data import ROOT

AMBIENTS={'corporate_street':'ambient_street','bar':'ambient_bar','hacker_hideout':'ambient_hideout','corporate_lobby':'ambient_lobby'}
EFFECTS=('conversation','shop_open','shop_close','purchase','credits','swing','hit','rat_down','heal','door')

class AudioManager:
    def __init__(self,mixer=None,root=None):
        self.mixer=mixer if mixer is not None else pygame.mixer
        self.root=root or ROOT/'assets/audio'
        self.unlocked=False;self.attempted=False;self.available=False;self.muted=False
        self.sounds={};self.channels=[];self.ambient_channel=None
        self.desired='corporate_street';self.current=None;self.level=0.;self.clock=0.;self.report_due=0.
        self.last_effect={};self.ambient_starts=Counter();self.sfx_played=Counter();self.errors=[]

    def _error(self,error):
        self.errors=(self.errors+[str(error)[:120]])[-4:]

    def unlock(self):
        self.unlocked=True
        if self.attempted:return
        self.attempted=True
        try:
            if not self.mixer.get_init():self.mixer.init(frequency=22050,size=-16,channels=2,buffer=512)
            self.mixer.set_num_channels(9);self.mixer.set_reserved(1)
            self.ambient_channel=self.mixer.Channel(0)
            self.channels=[self.mixer.Channel(i) for i in range(1,9)]
            for name in (*AMBIENTS.values(),*EFFECTS):
                try:self.sounds[name]=self.mixer.Sound(str(self.root/(name+'.wav')))
                except (pygame.error,OSError,ValueError) as error:self._error(error)
            self.available=True
        except (pygame.error,OSError,AttributeError,ValueError) as error:
            self.available=False;self._error(error)

    def play(self,name):
        if not self.available or self.muted or name not in self.sounds:return False
        if self.clock-self.last_effect.get(name,-100)<.045:return False
        try:
            channel=next((c for c in self.channels if not c.get_busy()),None)
            if channel is None:return False
            channel.set_volume(.32);channel.play(self.sounds[name])
            self.last_effect[name]=self.clock;self.sfx_played[name]+=1
            return True
        except (pygame.error,OSError) as error:self._error(error);self.available=False;return False

    def toggle_mute(self):
        self.muted=not self.muted
        if self.muted:self.stop()
        return self.muted

    def stop(self):
        for channel in ([self.ambient_channel] if self.ambient_channel is not None else [])+self.channels:
            try:channel.set_volume(0);channel.stop()
            except (pygame.error,OSError):pass
        self.current=None;self.level=0.

    def update(self,dt,location):
        dt=max(0,min(.1,dt));self.clock+=dt
        if location in AMBIENTS:self.desired=location
        if sys.platform=='emscripten' and not self.unlocked:
            try:
                import platform
                if str(platform.window.chessCorpAudioGestureSeen()).lower() in ('true','1'):self.unlock()
            except (AttributeError,TypeError):pass
        if self.available and not self.muted:
            try:
                if self.current!=self.desired:
                    self.level=max(0.,self.level-dt/.25)
                    self.ambient_channel.set_volume(.22*self.level)
                    if self.level==0:
                        self.ambient_channel.stop();self.current=None
                        name=AMBIENTS[self.desired]
                        if name in self.sounds:
                            self.ambient_channel.play(self.sounds[name],loops=-1)
                            self.current=self.desired;self.ambient_starts[self.current]+=1
                else:
                    self.level=min(1.,self.level+dt/.45)
                    self.ambient_channel.set_volume(.22*self.level)
            except (pygame.error,OSError) as error:self._error(error);self.available=False
        # Read-only, bounded local diagnostics for browser QA. No network or game UI.
        if sys.platform=='emscripten' and self.clock>=self.report_due:
            self.report_due=self.clock+.5
            try:
                import platform
                platform.window.chessCorpAudioReport(json.dumps(self.status()))
            except (AttributeError,TypeError):pass

    def status(self):
        try:busy=bool(self.available and self.ambient_channel and self.ambient_channel.get_busy())
        except pygame.error:busy=False
        return {'available':self.available,'unlocked':self.unlocked,'muted':self.muted,'ambient':self.current,'ambient_busy':busy,
                'ambient_starts':dict(self.ambient_starts),'sfx_played':dict(self.sfx_played),'loaded_sounds':len(self.sounds),'errors':list(self.errors)}

    def draw_mute(self,screen,ui):
        if self.muted:ui.text(screen,'M: wyciszono',(822,484),(155,184,194),True)
