from pathlib import Path
from PIL import Image
import shutil
p=Path('assets/processed')
Image.open('grafika/Background/Tło(1).png').resize((960,540),Image.Resampling.NEAREST).save(p/'street.png')
im=Image.open('grafika/Dude/Dude_white.png').convert('RGBA')
# Four consecutive side-facing poses; shared crop preserves the ground anchor.
for i,(x,y) in enumerate([(1,3),(2,3),(0,4),(1,4)]):
 im.crop((x*256+48,y*256+68,x*256+192,y*256+248)).resize((72,90),Image.Resampling.NEAREST).save(p/f'player_{i}.png')
Image.open('grafika/Dude/Dude2.png').crop((48,68,192,248)).resize((72,90),Image.Resampling.NEAREST).save(p/'buddy.png')
# Bundle pygame's redistributable default font so rendering works offline and on web.
import pygame
shutil.copy(Path(pygame.__file__).parent/'freesansbold.ttf',p/'font.ttf')
