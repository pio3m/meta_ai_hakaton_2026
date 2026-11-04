"""Manual, bounded stage-015 assets. Never runs at startup; no retries."""
import asyncio,json,sys
from pathlib import Path
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from backend.settings import Settings
from backend.asset_generator import AssetGenerator,AssetRequest
from backend.inspector import CallStore
ROOT=Path(__file__).resolve().parent.parent
async def run():
    if sys.argv[1:]!=['--generate-two-approved-assets']:raise SystemExit('Manual use only')
    values={}
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);values[k.strip()]=v.strip().strip('"').strip("'")
    settings=Settings(api_key=values.get('MODEL_API_KEY',''),asset_ai_mode='meta',asset_ai_allow_paid_requests=True,asset_ai_global_limit=3,asset_cache_dir=str(ROOT/'assets/generated'),base_url=values.get('META_API_BASE_URL','https://api.meta.ai/v1'))
    results=[]
    async with httpx.AsyncClient(trust_env=False) as client:
        generator=AssetGenerator(settings,client,CallStore(secrets=(settings.api_key.get_secret_value(),)))
        for asset_id in ['cyber_rat','merchant']:
            try:
                result=await generator.generate(AssetRequest(session_id='stage015-asset-test',asset_id=asset_id))
                if not isinstance(result,dict):
                    print(asset_id,'FAILED, no retry',flush=True);break
                results.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
            except Exception as error:
                print(asset_id,type(error).__name__,'NO RETRY',flush=True);break
    (ROOT/'docs/changes/015-rat-bounties-and-merchant/evidence/asset-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':asyncio.run(run())
