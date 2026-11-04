"""Focused final browser regression for room-plan traces and dialogue priority."""
import asyncio,json
from playwright.async_api import async_playwright
from browser015 import Demo,EVIDENCE,require_mock
async def main():
 require_mock()
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  page=await browser.new_page(viewport={'width':1200,'height':760});d=Demo(page);plans=[]
  async def response(res):
   await d.response(res)
   if res.url.endswith('/api/world/plan'):plans.append(await res.json())
  page.on('request',d.request);page.on('response',response);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  try:
   await page.goto('http://localhost:8080/');await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000);await d.fresh()
   await d.travel('bar')
   while len(plans)<2:await page.wait_for_timeout(1000)
   await d.fresh();await d.travel('corporate_street');await d.fresh()
   for location,x in [('hacker_hideout',100),('corporate_lobby',700)]:
    await d.move(x);await d.press('f');await d.fresh();assert d.snap['location_id']==location
    await d.shot('verified-'+location);await d.travel('corporate_street');await d.fresh()
   await d.shot('verified-return-street')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await page.wait_for_timeout(2200);await d.shot('verified-barman-offer');await d.fresh();assert d.snap['gameplay']['bounty_state']=='active'
   await d.npc('merchant');await d.press('e');await d.press('Enter');await d.shot('verified-shop-no-free-item');await d.press('Escape');await d.fresh()
   assert d.snap['gameplay']['credits']==0 and d.snap['gameplay']['medkits']==1
   assert not d.errors,d.errors;assert len(plans)==3
   print('TARGETED BROWSER PASSED: 4 rooms, old plan execution accepted, dialogue readable, shop rejects unaffordable item.',flush=True)
  finally:
   (EVIDENCE/'targeted-browser-results.json').write_text(json.dumps({'checkpoints':d.checkpoints,'plans':plans,'errors':d.errors},ensure_ascii=False,indent=2),encoding='utf-8');await browser.close()
if __name__=='__main__':asyncio.run(main())
