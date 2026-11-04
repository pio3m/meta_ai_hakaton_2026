"""Final controlled World call after two successful paid calls. No retries."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from browser015 import Demo,EVIDENCE,ROOT
BASE='http://localhost:8082'
async def main():
 ledger=json.loads((ROOT/'assets/generated/.world-ai-stage-015.json').read_text());assert ledger['calls']==2,'No extra test calls permitted'
 values=dict(l.split('=',1) for l in (ROOT/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  context=await browser.new_context(viewport={'width':1200,'height':760});await context.request.post(BASE+'/admin/api/login',data={'token':values['ADMIN_TOKEN']})
  demo=await (await context.request.post(BASE+'/admin/api/demo')).json()
  page=await context.new_page();d=Demo(page);results=[]
  async def collect(res):
   await d.response(res)
   if res.url.endswith('/api/world/plan'):results.append(await res.json())
  page.on('request',d.request);page.on('response',collect);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  try:
   await page.goto(BASE+demo['game_url']);await page.get_by_role('button',name='Graj',exact=False).click()
   await page.locator('#chess-start').wait_for(state='hidden',timeout=60000)
   await d.fresh()
   for _ in range(40):
    if results:break
    await page.wait_for_timeout(1000)
   assert len(results)==1 and results[0]['provider']=='meta',results
   await page.wait_for_timeout(15000);await d.fresh();await d.shot('live-final-meta-street')
   data=await (await context.request.get(BASE+'/admin/api/calls')).json();calls=[];blocked=[]
   for row in data['calls']:
    if row['kind']=='world':
     detail=await (await context.request.get(BASE+'/admin/api/calls/'+row['id'])).json()
     safe={k:detail.get(k) for k in ['id','started_at','model','provider','sent_to_model','upstream_status','elapsed_ms','usage','context','validated_plan','validation','execution','world_limits','error']}
     (calls if row['sent_to_model'] else blocked).append(safe)
   assert len(calls)==3 and all(r['validation']['valid'] for r in calls)
   assert any(r['context']['location_id']=='bar' and any(n['npc_id']=='merchant' for n in r['validated_plan']['decisions']) and r['execution']['completed_actions'] for r in calls)
   owner=await context.new_page();await owner.goto(BASE+'/admin');await owner.locator('#dashboard').wait_for(state='visible')
   await owner.locator('#call-list button').filter(has_text='[World AI META]').first.click();await owner.screenshot(path=str(EVIDENCE/'live-inspector-world.png'))
   await owner.locator('#call-list button').filter(has_text='merchant / Muse').first.click();await owner.locator('#asset-preview').wait_for(state='visible');await owner.locator('#asset-section').screenshot(path=str(EVIDENCE/'live-inspector-merchant.png'))
   jury=await browser.new_context(viewport={'width':1200,'height':760});await jury.request.post(BASE+'/admin/jury/api/login',data={'token':demo['jury_token']})
   jd=await (await jury.request.get(BASE+'/admin/jury/api/calls')).json()
   assert len(jd['calls'])==1 and jd['calls'][0]['sent_to_model'] and all('request_payload' not in r and 'session_id' not in r for r in jd['calls'])
   assert jd['world_state']['location_id']=='corporate_street'
   jp=await jury.new_page();await jp.goto(BASE+'/admin/jury');await jp.locator('#dashboard').wait_for(state='visible');await jp.screenshot(path=str(EVIDENCE/'live-inspector-jury.png'))
   (EVIDENCE/'live-results.json').write_text(json.dumps({'world_calls':calls,'blocked_without_payment':blocked,'errors':d.errors,'jury_scoped':True,'world_state':data['world_state']},ensure_ascii=False,indent=2),encoding='utf-8')
   print('LIVE PASSED: 3 paid valid plans total; merchant Meta actions executed; jury scoped; no extra generation.',flush=True)
  finally:await browser.close()
if __name__=='__main__':asyncio.run(main())
