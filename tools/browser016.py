"""UI-only browser regression. Requires mock; no paid calls."""
import asyncio,json,sys
from pathlib import Path
from playwright.async_api import async_playwright
import browser015 as b
b.EVIDENCE=b.ROOT/'docs/changes/016-unobstructed-game-ui/evidence'
async def main():
 b.require_mock()
 values=dict(l.split('=',1) for l in (b.ROOT/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'))
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  context=await browser.new_context(viewport={'width':1200,'height':760});page=await context.new_page();d=b.Demo(page)
  page.on('request',d.request);page.on('response',d.response);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  try:
   await page.goto('http://localhost:8080/');await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000);await d.fresh();await d.shot('browser-clear-street')
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape')
   await d.move(234,440);await d.press('e');await d.press('Escape')
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape');await d.fresh();assert d.snap['first_quest_complete'];await d.shot('browser-compact-quest')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await page.wait_for_timeout(1000);await d.shot('browser-explicit-barman');await d.fresh();assert d.snap['gameplay']['bounty_state']=='active'
   await context.request.post('http://localhost:8080/admin/api/login',data={'token':values['ADMIN_TOKEN']})
   admin=await context.new_page();await admin.goto('http://localhost:8080/admin');await admin.locator('#dashboard').wait_for(state='visible');await admin.locator('.npc-card').nth(2).wait_for(state='visible');assert await admin.locator('.npc-card').count()==3
   assert 'merchant' in await admin.locator('#npc-roster').inner_text();await admin.locator('#npc-roster').screenshot(path=str(b.EVIDENCE/'admin-npc-status-cards.png'))
   assert not d.errors,d.errors;print('UI BROWSER PASSED: clear scene, first quest, compact Director, explicit Barman, live admin roster.',flush=True)
  finally:
   (b.EVIDENCE/'browser-results.json').write_text(json.dumps({'checkpoints':d.checkpoints,'errors':d.errors},ensure_ascii=False,indent=2),encoding='utf-8');await browser.close()
if __name__=='__main__':asyncio.run(main())
