import json,wave
from pathlib import Path
import pygame,pytest
from game.audio import AudioManager,AMBIENTS,EFFECTS
from tests.test_locations import game,travel

class Channel:
    def __init__(self):self.busy=False;self.plays=[];self.volume=0;self.stops=0
    def play(self,sound,loops=0):self.busy=True;self.plays.append((sound,loops))
    def stop(self):self.busy=False;self.stops+=1
    def get_busy(self):return self.busy
    def set_volume(self,value):self.volume=value
class Mixer:
    def __init__(self,fail=False,bad=None):self.fail=fail;self.bad=bad;self.channels={};self.loads=0;self.inits=0
    def get_init(self):return None
    def init(self,**kwargs):
        self.inits+=1
        if self.fail:raise pygame.error('no audio device')
    def set_num_channels(self,n):self.count=n
    def set_reserved(self,n):self.reserved=n
    def Channel(self,n):return self.channels.setdefault(n,Channel())
    def Sound(self,path):
        self.loads+=1
        if self.bad and self.bad in path:raise pygame.error('decode failed')
        return path


def test_original_wavs_are_valid_and_nonempty_with_bounded_levels():
    folder=Path('assets/audio');manifest=json.loads((folder/'manifest.json').read_text())
    assert len(manifest)==14 and len({r['file'] for r in manifest})==14
    for row in manifest:
        with wave.open(str(folder/row['file'])) as f:
            assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,22050)
            assert f.getnframes()>1000
        assert 0<row['peak']<.95 and row['source']=='ORIGINAL_SYNTHESIS'


def test_gesture_gate_and_no_restart_or_disk_load_per_frame():
    mixer=Mixer();audio=AudioManager(mixer=mixer)
    for _ in range(60):audio.update(.1,'corporate_street')
    assert mixer.loads==0 and not audio.play('hit')
    audio.unlock()
    for _ in range(100):audio.update(.1,'corporate_street')
    assert mixer.loads==14 and audio.ambient_starts=={'corporate_street':1}
    assert mixer.channels[0].plays[0][1]==-1 and mixer.reserved==1


def test_location_fades_out_before_single_channel_replacement_and_no_overlap():
    mixer=Mixer();audio=AudioManager(mixer=mixer);audio.unlock()
    for _ in range(6):audio.update(.1,'corporate_street')
    audio.update(.1,'bar');assert len(mixer.channels[0].plays)==1
    for _ in range(10):audio.update(.1,'bar')
    assert audio.current=='bar' and len(mixer.channels[0].plays)==2
    assert audio.level==1 and len(mixer.channels)==9
    for _ in range(10):audio.update(.1,'corporate_street')
    assert audio.ambient_starts=={'corporate_street':2,'bar':1}


def test_muting_stops_all_audio_and_unmute_starts_only_current_location():
    mixer=Mixer();audio=AudioManager(mixer=mixer);audio.unlock();audio.update(.1,'corporate_street');assert audio.play('hit')
    assert audio.toggle_mute();assert not any(c.busy for c in mixer.channels.values())
    audio.update(.1,'bar');assert not audio.play('purchase')
    assert not audio.toggle_mute();audio.update(.1,'bar')
    assert audio.current=='bar' and audio.ambient_starts=={'corporate_street':1,'bar':1}


def test_missing_device_is_nonfatal_and_not_retried_every_frame():
    mixer=Mixer(fail=True);audio=AudioManager(mixer=mixer);audio.unlock()
    for _ in range(100):audio.unlock();audio.update(.1,'bar');assert not audio.play('hit')
    assert not audio.available and mixer.inits==1 and audio.errors


def test_decode_error_isolated_to_one_sound_and_effects_never_steal_ambient():
    mixer=Mixer(bad='hit.wav');audio=AudioManager(mixer=mixer);audio.unlock();audio.update(.1,'bar')
    assert audio.available and len(audio.sounds)==13 and not audio.play('hit')
    for effect in EFFECTS:audio.play(effect)
    assert len(mixer.channels[0].plays)==1 and audio.current=='bar'


def test_mixer_disappearing_during_game_does_not_crash():
    mixer=Mixer();audio=AudioManager(mixer=mixer);audio.unlock();audio.update(.1,'bar')
    def broken(*args):raise pygame.error('device lost')
    mixer.channels[0].set_volume=broken
    audio.update(.1,'bar');assert not audio.available
    audio.stop()


def test_native_pcm_plays_through_real_dummy_mixer_and_m_is_global_in_shop(game):
    a=game.audio;assert not a.unlocked
    game.key(pygame.K_m);assert a.available and a.muted and len(a.sounds)==14
    game.adventure.shop_open=True;game.key(pygame.K_m);assert not a.muted
    a.update(.1,'bar');assert a.status()['ambient_busy']
    assert a.play('purchase');assert a.sfx_played['purchase']==1
    a.stop()


def test_audio_events_follow_successful_game_actions_without_changing_rewards(game):
    from collections import Counter
    class Spy:
        def __init__(self):self.events=Counter()
        def play(self,name):self.events[name]+=1
    a=game.adventure;spy=Spy();a.audio=spy
    a.bounty()
    for r in a.rats:
        while r['hp']:
            a.cooldown=0;a.attack(r['position'],False)
    assert spy.events['hit']>=3 and spy.events['rat_down']==3 and spy.events['swing']>=3
    a.bounty();assert a.credits==36 and spy.events['credits']==1
    a.bounty();assert spy.events['credits']==1
    assert a.buy('weapon') and spy.events['purchase']==1
    assert not a.buy('weapon') and spy.events['purchase']==1
    a.health=50;assert a.heal() and spy.events['heal']==1


def test_doors_and_barman_shop_open_close_emit_only_actual_interactions(game):
    from collections import Counter
    class Spy:
        muted=False
        def __init__(self):self.events=Counter()
        def unlock(self):pass
        def play(self,name):self.events[name]+=1
        def update(self,*args):pass
    spy=Spy();game.audio=spy;game.adventure.audio=spy
    game.key(pygame.K_f);assert spy.events['door']==0
    travel(game,'bar');assert spy.events['door']==1
    game.player.x,game.player.y=game.living.npcs['bartender']['position'];game.key(pygame.K_e)
    assert spy.events['conversation']==1
    game.player.x,game.player.y=game.living.npcs['merchant']['position'];game.key(pygame.K_e)
    assert spy.events['shop_open']==1
    game.key(pygame.K_ESCAPE);assert spy.events['shop_close']==1
