"""Reproducible original Chess Corp audio. Standard library only; no samples/API.
Generated audio and this synthesizer are dedicated under CC0-1.0 (assets/audio/LICENSE.md).
Run manually during development, never in the frame loop or on game startup.
"""
from array import array
import hashlib,json,math,random,sys,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
RATE=22050
TAU=2*math.pi

def ambient(kind,seconds=8):
    rng=random.Random(1700+kind);out=[];low=0.;slow=0.
    for i in range(int(seconds*RATE)):
        t=i/RATE;white=rng.uniform(-1,1);low+=.08*(white-low);slow+=.008*(white-slow)
        if kind==0: # rain, ventilation rumble, distant city oscillators
            value=.19*(white-low)+.24*low+.045*math.sin(TAU*55*t)+.015*math.sin(TAU*110*t)
            value*=.85+.15*math.sin(TAU*.25*t)
        elif kind==1: # muffled club heard from the bar, 90 BPM / exactly twelve beats
            beat=t% (2/3);kick=math.sin(TAU*(48*t+1.5*(1-math.exp(-beat*20))))*math.exp(-beat*13)
            pad=sum(math.sin(TAU*f*t) for f in (110,137.5,165))/3
            value=.11*kick+.05*math.sin(TAU*55*t)*(.5+.5*math.exp(-beat*6))+.035*pad+.07*low
            value+=.014*(white-low)*math.exp(-((t+1/3)%(2/3))*35)
        elif kind==2: # rack fans, electrical hum, occasional quiet circuit bleeps
            tick=t%2;beep=math.sin(TAU*880*t)*math.exp(-tick*35)*.012
            value=.21*low+.055*math.sin(TAU*90*t)+.018*math.sin(TAU*180*t)+beep
        else: # low HVAC and spacious calm sustained chord
            pad=sum(math.sin(TAU*f*t) for f in (110,165,220))/3
            value=.25*slow+.12*low+.04*pad*(.8+.2*math.sin(TAU*.125*t))
        # A 6 ms zero boundary prevents clicks at the cached loop seam.
        edge=min(1,t/.006,(seconds-t)/.006);out.append(value*max(0,edge))
    return out

def effect(name,seconds):
    rng=random.Random(name);out=[];low=0.
    notes={'conversation':[660,880],'purchase':[880,1100,1320],'credits':[660,880,1100,1320],
           'heal':[440,550,660,880]}
    for i in range(int(seconds*RATE)):
        t=i/RATE;u=t/seconds;white=rng.uniform(-1,1);low+=.15*(white-low)
        edge=min(1,t/.006,(seconds-t)/.025);env=max(0,edge)
        if name in notes:
            tones=notes[name];index=min(len(tones)-1,int(u*len(tones)));freq=tones[index]
            value=.23*math.sin(TAU*freq*t)+.055*math.sin(TAU*freq*2*t)
            value*=.8+.2*math.cos(TAU*(u*len(tones)%1))
        elif name=='swing':value=(.40*(white-low)+.08*math.sin(TAU*(180*t+1200*t*t)))*math.sin(math.pi*u)
        elif name=='hit':value=(.32*low+.22*math.sin(TAU*(100*t-180*t*t))+.08*white)*math.exp(-u*5)
        elif name=='rat_down':value=(.22*math.sin(TAU*(640*t-900*t*t))+.08*low)*(1-u)
        elif name=='door':value=.20*low*math.sin(math.pi*u)+.12*math.sin(TAU*(150*t+180*t*t))*(1-u)
        elif name=='shop_open':value=.17*math.sin(TAU*(250*t+1500*t*t))+.045*low
        elif name=='shop_close':value=.17*math.sin(TAU*(1000*t-1700*t*t))+.045*low
        else:raise ValueError(name)
        out.append(value*env)
    return out

def write(name,samples,folder):
    # Fixed moderate levels, no normalization that would amplify subtle ambient.
    values=array('h',(round(max(-.95,min(.95,x))*32767) for x in samples))
    if sys.byteorder!='little':values.byteswap()
    path=folder/(name+'.wav')
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE);wav.writeframes(values.tobytes())
    return {'file':name+'.wav','sample_rate':RATE,'channels':1,'bits':16,'duration_s':round(len(samples)/RATE,4),
            'peak':round(max(abs(x) for x in samples),4),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source':'ORIGINAL_SYNTHESIS','license':'CC0-1.0'}

def main():
    folder=ROOT/'assets/audio';folder.mkdir(parents=True,exist_ok=True);manifest=[]
    for kind,name in enumerate(('street','bar','hideout','lobby')):manifest.append(write('ambient_'+name,ambient(kind),folder))
    for name,seconds in {'conversation':.16,'shop_open':.22,'shop_close':.18,'purchase':.28,'credits':.48,'swing':.14,'hit':.14,'rat_down':.25,'heal':.44,'door':.32}.items():
        manifest.append(write(name,effect(name,seconds),folder))
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Generated',len(manifest),'original local PCM WAVs /',sum((folder/x['file']).stat().st_size for x in manifest),'bytes')
if __name__=='__main__':main()
