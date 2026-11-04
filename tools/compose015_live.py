"""Create/start an isolated, capped Compose from resolved local configuration.
Secrets stay in a private temporary file, never stdout or evidence.
"""
import json,subprocess,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
if sys.argv[1:]!=['--start-capped-live']:raise SystemExit('Manual use only')
data=json.loads(subprocess.run(['docker','compose','config','--format','json'],cwd=ROOT,capture_output=True,text=True,check=True).stdout)
data['name']='chess-corp-stage015-live'
data['networks']={'default':{'name':'chess-corp-stage015-live_default'}}
for name,service in data['services'].items():
 service.pop('build',None);service['image']='chess-corp-'+name+':latest'
data['services']['game']['ports']=[{'target':80,'published':'8082','host_ip':'127.0.0.1','protocol':'tcp'}]
env=data['services']['backend']['environment'];env.update(WORLD_AI_MODE='meta',WORLD_AI_ALLOW_PAID_REQUESTS='true',WORLD_AI_SESSION_LIMIT='3',WORLD_AI_GLOBAL_LIMIT='3',WORLD_AI_MAX_OUTPUT_TOKENS='2400',WORLD_AI_TOKEN_BUDGET='150000',WORLD_AI_LEDGER_PATH='/app/assets/generated/.world-ai-stage-015.json',WORLD_AI_MIN_INTERVAL_SECONDS='30',BUDDY_MODE='mock',DIRECTOR_MODE='mock',DIRECTOR_ALLOW_PAID_REQUESTS='false',META_ALLOW_PAID_REQUESTS='false',ASSET_AI_MODE='mock',ASSET_AI_ALLOW_PAID_REQUESTS='false',ASSET_AI_GLOBAL_LIMIT='3')
path=Path(tempfile.gettempdir())/'chess-corp-stage015-live-compose.json';path.write_text(json.dumps(data),encoding='utf-8')
subprocess.run(['docker','compose','-p',data['name'],'-f',str(path),'up','-d','--force-recreate'],cwd=ROOT,check=True)
print('Isolated test ready: localhost:8082, hard cap 3 World calls; Buddy/Quest/image paid disabled.')
