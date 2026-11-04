"""Final build regression: original quest, COLLECT, combat/shop, all four rooms."""
import asyncio,json
from playwright.async_api import async_playwright
from browser015 import Demo,EVIDENCE,require_mock
async def main():
 require_mock()
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  page=await browser.new_page(viewport={'width':1200,'height':760});d=Demo(page);execution=[]
  async def response(res):
   await d.response(res)
   if res.url.endswith('/api/director/execution'):execution.append(await res.json())
  page.on('request',d.request);page.on('response',response);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  try:
   await page.goto('http://localhost:8080/');await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000);await d.fresh()
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape')
   await d.move(234,440);await d.press('e');await d.press('Escape')
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape');await d.fresh();assert d.snap['first_quest_complete']
   assert d.plans;plan=d.plans[-1]['plan'];obj=plan['place_objects'][0];pos={'east_side':[780,452],'west_side':[100,452],'center_side':[385,452]}[obj['spawn_point']]
   await d.move(*pos);await d.press('e');await d.fresh();await d.shot('final-browser-collect')
   assert execution, 'No director execution report'
   print('COLLECT execution',json.dumps(execution[-1]),flush=True)
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['target']==3;await d.shot('final-browser-bounty')
   await d.travel('corporate_street');await d.shot('final-browser-rats');await d.fight();await d.shot('final-browser-first-wave')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['credits']==36
   await d.npc('merchant');await d.press('e');await d.press('ArrowDown');await d.press('Enter');await d.fresh();assert d.snap['gameplay']['weapon_upgrade'];await d.shot('final-browser-shop');await d.press('Escape')
   await d.travel('corporate_street')
   for location,x in [('hacker_hideout',100),('corporate_lobby',700)]:
    await d.move(x);await d.press('f');await d.fresh();assert d.snap['location_id']==location
    assert d.snap['first_quest_complete'] and d.snap['gameplay']['weapon_upgrade'] and d.snap['gameplay']['claimed_contracts']==[0]
    await d.shot('final-browser-'+location);await d.travel('corporate_street')
   await d.shot('final-browser-street');assert not d.errors,d.errors
   print('FINAL BUILD BROWSER PASSED',flush=True)
  finally:
   (EVIDENCE/'final-browser-results.json').write_text(json.dumps({'checkpoints':d.checkpoints,'director_execution':execution,'errors':d.errors,'last_state':d.snap},ensure_ascii=False,indent=2),encoding='utf-8');await page.screenshot(path=str(EVIDENCE/'final-browser-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
