"""One bounded LIVE browser test: at most three World calls in isolated Compose."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
from browser015 import Demo,EVIDENCE,ROOT
BASE='http://localhost:8082'
async def main():
 values={}
 for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
  if '=' in line and not line.startswith('#'):
   k,v=line.split('=',1);values[k.strip()]=v.strip().strip('"').strip("'")
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  context=await browser.new_context(viewport={'width':1200,'height':760})
  response=await context.request.post(BASE+'/admin/api/login',data={'token':values['ADMIN_TOKEN']});assert response.status==200
  demo=await (await context.request.post(BASE+'/admin/api/demo')).json()
  existing=await (await context.request.get(BASE+'/admin/api/calls')).json()
  prior=[r for r in existing['calls'] if r['kind']=='world' and r['sent_to_model']]
  game_url='/?demo_session='+prior[-1]['session_id'] if prior else demo['game_url']
  page=await context.new_page();d=Demo(page);world_results=[]
  async def collect(res):
   await d.response(res)
   if res.url.endswith('/api/world/plan'):
    result=await res.json();world_results.append(result);print('LIVE WORLD',len(world_results),result.get('provider'),result.get('error_detail'),flush=True)
  page.on('request',d.request);page.on('response',collect);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  try:
   await page.goto(BASE+game_url);await page.get_by_role('button',name='Graj',exact=False).click()
   await page.locator('#chess-start').wait_for(state='hidden',timeout=60000);await d.fresh()
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh()
   assert d.snap['gameplay']['bounty_state']=='active'
   await d.shot('live-bar-bounty')
   # Let generated plans execute with the player away from the NPCs.
   await d.move(110,455)
   for _ in range(95):
    if len(world_results)>=3:break
    await page.wait_for_timeout(1000)
   assert len(world_results)==3,'Expected 3 controlled World plans'
   await page.wait_for_timeout(16000);await d.fresh();await d.shot('live-bar-meta')
   assert all(r['provider']=='meta' for r in world_results),[(r['provider'],r.get('error_detail')) for r in world_results]
   await d.npc('merchant');await d.press('e');await d.shot('live-nyx-shop');await d.press('Escape')
   records=await (await context.request.get(BASE+'/admin/api/calls')).json()
   calls=[]
   for row in records['calls']:
    if row['kind']=='world':
     detail=await (await context.request.get(BASE+'/admin/api/calls/'+row['id'])).json()
     calls.append({k:detail.get(k) for k in ['id','model','provider','sent_to_model','upstream_status','elapsed_ms','usage','validated_plan','validation','execution','world_limits','error']})
   assert len(calls)==3 and all(row['sent_to_model'] and row['validation']['valid'] for row in calls)
   assert any((r['execution'] or {}).get('completed_actions') for r in calls),'No model actions executed'
   inspector=await context.new_page();await inspector.goto(BASE+'/admin');await inspector.locator('#dashboard').wait_for(state='visible')
   await inspector.locator('#call-list button').filter(has_text='[World AI').first.click();await inspector.screenshot(path=str(EVIDENCE/'live-inspector-world.png'),full_page=False)
   await inspector.locator('#call-list button').filter(has_text='merchant / Muse').first.click();await inspector.locator('#asset-preview').wait_for(state='visible');await inspector.locator('#asset-section').screenshot(path=str(EVIDENCE/'live-inspector-merchant.png'))
   jury=await browser.new_context(viewport={'width':1200,'height':760});await jury.request.post(BASE+'/admin/jury/api/login',data={'token':demo['jury_token']})
   jury_data=await (await jury.request.get(BASE+'/admin/jury/api/calls')).json()
   assert all('request_payload' not in row and 'session_id' not in row for row in jury_data['calls'])
   assert jury_data['world_state'] is None and not jury_data['calls'], 'Other session leaked to jury'
   jp=await jury.new_page();await jp.goto(BASE+'/admin/jury');await jp.locator('#dashboard').wait_for(state='visible');await jp.screenshot(path=str(EVIDENCE/'live-inspector-jury.png'))
   evidence={'world_calls':calls,'assets':[r['asset'] for r in records['calls'] if r['kind']=='asset'],'world_state':records['world_state'],'errors':d.errors,'jury_scoped':True}
   (EVIDENCE/'live-results.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
   print('LIVE PASSED',json.dumps([{'model':r['model'],'usage':r['usage'],'actions':[a['action'] for n in r['validated_plan']['decisions'] for a in n['actions']]} for r in calls],ensure_ascii=False),flush=True)
  finally:
   (EVIDENCE/'live-browser-checkpoints.json').write_text(json.dumps({'checkpoints':d.checkpoints,'errors':d.errors,'world_results':world_results},ensure_ascii=False,indent=2),encoding='utf-8')
   await page.screenshot(path=str(EVIDENCE/'live-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
