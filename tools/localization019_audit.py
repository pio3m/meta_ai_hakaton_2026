"""Offline render audit of modal screens; never starts network or model calls."""
import os,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
os.environ.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',CHESS_CORP_WORLD_NETWORK='false')
import pygame
pygame.init();screen=pygame.display.set_mode((960,540))
from main import Game
from game import i18n
from backend.director import mock_plan_v2
from game.director import validate_plan
from game.director_contract import initial_execution
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/changes/019-en-pl-localization/evidence'
g=Game()
for kind in ['SEQUENCE','LOGIC_PUZZLE']:
 d=g.director;d.plan=i18n.localize_plan(mock_plan_v2('offline-localization',kind,'en'),'en');d.plan_language='en';d.state='active';d.objects=validate_plan(d.plan,g.scene,d.rules);d.execution=initial_execution();d.answer_open=kind=='LOGIC_PUZZLE'
 g.draw(screen);pygame.image.save(screen,str(OUT/('native-en-'+kind.lower()+'.png')))
g.director.state='idle';g.director.objects=[];g.director.answer_open=False
g.adventure.shop_open=True;g.draw(screen)
g.adventure.shop_open=False;g.locations.map_open=True;g.draw(screen)
g.locations.map_open=False;g.adventure.bounty();g.draw(screen)
g.adventure.health=0;g.draw(screen)
(OUT/'render-untranslated.json').write_text(json.dumps(i18n.missing(),ensure_ascii=False,indent=2),encoding='utf-8')
print('Render audit complete; missing authored strings:',i18n.missing())
pygame.quit()
