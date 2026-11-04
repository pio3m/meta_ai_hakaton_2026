"""Poll only local asset versions; regenerated images appear without a web rebuild."""
import asyncio,base64,json,os
from io import BytesIO
import pygame
from game.data import ROOT
from game.chat import send_request
class AssetSync:
 def __init__(self):
  self.versions={};self.task=None;self.clock=0.;self.next_due=0.
  for key in ('hacker_emblem','cyber_rat','merchant'):
   try:self.versions[key]=json.loads((ROOT/f'assets/generated/{key}.public.json').read_text())['sha256']
   except (OSError,ValueError,KeyError):pass
 def cancel(self):
  if self.task:self.task.cancel()
 def update(self,game,dt):
  if os.getenv('CHESS_CORP_WORLD_NETWORK','true').lower()=='false':return
  self.clock+=max(0,min(.1,dt))
  if self.task and self.task.done():
   try:
    data=self.task.result()
    if data.get('error'):raise ValueError('Asset update unavailable')
    for key in data.get('removed',[]):
     if key=='cyber_rat':game.adventure.frames=[];game.adventure.asset_source='ORIGINAL'
     elif key=='merchant':
      game.locations.sprite_cache['merchant']=[pygame.image.load(str(ROOT/f'assets/processed/bar_guest_{i}.png')).convert_alpha() for i in range(4)];game.adventure.portrait=None
     elif key=='hacker_emblem':game.locations.decor=pygame.image.load(str(ROOT/'assets/processed/original_hologram.png')).convert_alpha();game.locations.decor_source='ORYGINAŁ'
    for item in data.get('assets',[]):
     key=item['id']
     if key not in ('cyber_rat','merchant','hacker_emblem'):continue
     raw=base64.b64decode(item['png_base64']);image=pygame.image.load(BytesIO(raw),'asset.png').convert_alpha()
     if key=='hacker_emblem':game.locations.decor=image;game.locations.decor_source='META / '+item['model']
     else:
      frames=[]
      for i in range(4):
       frame=pygame.Surface(image.get_size(),pygame.SRCALPHA);frame.blit(image,(0,-(i%2)));frames.append(frame)
      if key=='cyber_rat':game.adventure.frames=frames;game.adventure.asset_source='META'
      else:game.locations.sprite_cache['merchant']=frames;game.adventure.portrait=image
    self.versions=data['versions'];game.locations.live_asset_versions=dict(self.versions)
   except (ValueError,KeyError,TypeError,pygame.error):pass
   self.task=None;self.next_due=self.clock+10
  if self.task is None and self.clock>=self.next_due:
   try:self.task=asyncio.get_running_loop().create_task(send_request({'versions':dict(self.versions)},'/api/assets/updates'))
   except RuntimeError:self.next_due=self.clock+10
