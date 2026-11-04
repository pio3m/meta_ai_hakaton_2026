"""Final browser verification of the rebuilt localization, no real model access."""
import asyncio,json,httpx
from pathlib import Path
from playwright.async_api import async_playwright
from browser019 import SafeDemo
import browser015
OUT=Path(__file__).resolve().parent.parent/'docs/changes/019-en-pl-localization/evidence';browser015.EVIDENCE=OUT
BASE='http://localhost:8084'
async def main():
 with httpx.Client(base_url=BASE,trust_env=False) as c:
  c.post('/admin/api/login',json={'token':'localization-qa-owner-1234567890'}).raise_for_status();demo=c.post('/admin/api/demo').json()
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True);page=await browser.new_page(viewport={'width':1200,'height':760});d=SafeDemo(page);page.on('request',d.request);page.on('response',d.response)
  try:
   await page.goto(BASE+demo['game_url']);await page.get_by_role('button',name='Play',exact=True).click(timeout=60000);await page.locator('#chess-start').wait_for(state='hidden',timeout=90000);await d.fresh()
   await d.press('F2');assert await page.evaluate('chessCorpGetLanguage()')=='pl'
   await page.reload();await page.get_by_role('button',name='Graj',exact=True).click(timeout=60000);await page.locator('#chess-start').wait_for(state='hidden',timeout=90000);assert await page.evaluate('chessCorpGetLanguage()')=='pl'
   await d.press('F2');assert await page.evaluate('chessCorpGetLanguage()')=='en'
   await page.reload();await page.get_by_role('button',name='Play',exact=True).click(timeout=60000);await page.locator('#chess-start').wait_for(state='hidden',timeout=90000);assert await page.evaluate('chessCorpGetLanguage()')=='en';await d.fresh()
   await page.mouse.click(92,151);await page.wait_for_timeout(500)
   click_ok=await page.evaluate('chessCorpGetLanguage()')=='pl';print('Visible language switch click:',click_ok,flush=True)
   if not click_ok:raise AssertionError('Visible language selector click failed')
   await d.press('F2');await d.travel('bar');await d.npc('merchant');await d.press('e');await d.shot('final-en-shop');await d.press('F2');await d.shot('final-pl-shop');await d.press('F2');await d.press('Escape')
   await d.npc('bartender');await d.press('t');await page.keyboard.type('Who are you?',delay=20);await d.press('Enter');await page.wait_for_timeout(1000);await d.shot('final-en-bartender-chat');await d.press('Escape')
   jury=await browser.new_page();await jury.goto(BASE+'/admin/jury');await jury.locator('#token').fill(demo['jury_token']);await jury.locator('#login-form button').click();await jury.locator('#dashboard').wait_for(state='visible');await jury.wait_for_timeout(1200)
   assert await jury.evaluate('chessCorpGetLanguage()')=='en'
   states=await jury.locator('.npc-state').all_text_contents();assert all(not any(x in s for x in ['Patroluje','Reaguje','Rozmawia','Bada','Obserwuje']) for s in states),states
   await jury.screenshot(path=str(OUT/'final-en-jury.png'))
   await jury.locator('#admin-language').select_option('pl');await jury.wait_for_timeout(250);await jury.locator('#admin-language').select_option('en');await jury.wait_for_timeout(250)
   (OUT/'browser019-final.json').write_text(json.dumps({'passed':True,'selector_click':click_ok,'persistence':['EN','PL reload','EN reload'],'npc_states':states,'errors':d.errors,'paid_calls':0},indent=2),encoding='utf-8');print('FINAL BROWSER PASS',flush=True)
  finally:
   await page.screenshot(path=str(OUT/'final-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
