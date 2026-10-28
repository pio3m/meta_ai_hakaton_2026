from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'web_app'
DEST.mkdir(exist_ok=True)
shutil.copy2(ROOT/'main.py',DEST/'main.py')
for name in ['game','content','assets']:
 shutil.copytree(ROOT/name,DEST/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
print('Web source:',DEST)
