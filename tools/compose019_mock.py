"""Isolated localization QA: no API key, no paid permission, no shared ledgers."""
import json,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
config=json.loads(subprocess.run(['docker','compose','config','--format','json'],cwd=root,capture_output=True,text=True,check=True).stdout)
config['name']='chess-corp-i18n-test';config['networks']={'default':{'name':'chess-corp-i18n-test_default'}}
for name,service in config['services'].items():
 service.pop('build',None);service['image']='chess-corp-'+name+':latest'
config['services']['game']['ports']=[{'target':80,'published':'8084','host_ip':'127.0.0.1','protocol':'tcp'}]
b=config['services']['backend'];b.pop('volumes',None)
b['environment'].update(MODEL_API_KEY='',ADMIN_TOKEN='localization-qa-owner-1234567890',BUDDY_MODE='mock',DIRECTOR_MODE='mock',WORLD_AI_MODE='mock',ASSET_AI_MODE='mock',META_ALLOW_PAID_REQUESTS='false',DIRECTOR_ALLOW_PAID_REQUESTS='false',WORLD_AI_ALLOW_PAID_REQUESTS='false',ASSET_AI_ALLOW_PAID_REQUESTS='false',WORLD_AI_LEDGER_PATH='')
path=Path(tempfile.gettempdir())/'chess-corp-i18n-test-compose.json';path.write_text(json.dumps(config),encoding='utf-8')
subprocess.run(['docker','compose','-p',config['name'],'-f',str(path),'up','-d','--force-recreate'],cwd=root,check=True)
print('Isolated mock QA available on localhost:8084; no key or shared writable volumes.')
