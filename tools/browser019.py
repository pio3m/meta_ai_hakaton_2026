"""Real keyboard localization QA against an isolated keyless mock Compose."""
import asyncio,json,sys
from pathlib import Path
import httpx
from playwright.async_api import async_playwright
import browser015
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/changes/019-en-pl-localization/evidence';browser015.EVIDENCE=OUT
BASE='http://localhost:8084'
class SafeDemo(browser015.Demo):
 async def move(self,x,y=452):
  for _ in range(3):
   await self.fresh()
   if self.snap['gameplay']['health']==0:await self.press('Enter');await self.fresh()
   await super().move(x,y)
   if self.snap['gameplay']['health']>0:return
  raise AssertionError('Could not move after combat respawn')
 async def travel(self,location):
  for _ in range(3):
   await self.move(900 if location=='bar' else 65)
   await self.press('f');await self.fresh()
   if self.snap['location_id']==location:return
  raise AssertionError('Door traversal failed: '+self.snap['location_id'])

async def main():
 with httpx.Client(base_url=BASE,trust_env=False) as c:
  c.post('/admin/api/login',json={'token':'localization-qa-owner-1234567890'}).raise_for_status()
  assert all(c.get('/admin/api/calls').json()[k]=='mock' for k in ('mode','director_mode','world_mode'))
  demo=c.post('/admin/api/demo').json()
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True)
  page=await browser.new_page(viewport={'width':1200,'height':760});d=SafeDemo(page);jobs=[];chat=[]
  page.on('request',d.request);page.on('response',d.response);page.on('pageerror',lambda e:d.errors.append({'page_error':str(e)}))
  async def response(r):
   if r.url.endswith('/api/director/jobs'):jobs.append(await r.json())
   if r.url.endswith('/api/chat'):chat.append(await r.json())
  page.on('response',response)
  try:
   await page.goto(BASE+demo['game_url']);await page.get_by_role('button',name='Play',exact=True).click(timeout=60000)
   await page.locator('#chess-start').wait_for(state='hidden',timeout=90000);await d.fresh()
   assert await page.evaluate('chessCorpGetLanguage()')=='en'
   assert jobs and jobs[0]['provider']=='mock' and jobs[0]['language']=='en',jobs
   await d.shot('01-en-street');await d.press('j');await d.shot('02-en-jobs');await d.press('Escape')
   await d.press('F2');assert await page.evaluate('chessCorpGetLanguage()')=='pl';await d.shot('03-pl-street')
   await d.press('F2');assert await page.evaluate('chessCorpGetLanguage()')=='en'
   await d.move(535,440);await d.press('e');await d.shot('04-en-buddy');await d.press('Enter');await d.press('Enter');await d.press('Escape')
   await d.move(234,440);await d.press('e');await d.press('Escape')
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape');await d.fresh()
   assert d.snap['first_quest_complete'];await d.shot('05-en-first-quest-complete')
   await d.travel('bar');await d.npc('bartender');await d.press('t');await page.keyboard.type('Who are you and what is your role in Chess Corp?',delay=10);await d.press('Enter');await page.wait_for_timeout(1200)
   assert chat and chat[-1]['provider']=='mock',chat
   await d.shot('06-en-bartender-chat');await d.press('Escape')
   await d.press('e');await d.fresh();assert d.snap['gameplay']['bounty_state']=='active';await d.shot('07-en-contract')
   await d.travel('corporate_street');await d.fight();await d.shot('08-en-combat-complete')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['credits']>=30
   await d.npc('merchant');await d.press('e');await d.shot('09-en-shop');await d.press('F2');await d.shot('10-pl-shop');await d.press('F2');await d.press('Enter');await d.shot('11-en-purchase');await d.press('Escape')
   await d.travel('corporate_street');credits=d.snap['gameplay']['credits']
   for loc,x in [('hacker_hideout',100),('corporate_lobby',700)]:
    await d.move(x);await d.press('f');await d.fresh();assert d.snap['location_id']==loc,d.snap['location_id'];await d.shot('12-en-'+loc)
    assert d.snap['first_quest_complete'] and d.snap['gameplay']['credits']>=credits
    await d.move(65);await d.press('f');await d.fresh();assert d.snap['location_id']=='corporate_street'
   await d.press('Tab');await d.shot('13-en-map');await d.press('Escape')
   jury=await browser.new_page();await jury.goto(BASE+'/admin/jury');await jury.locator('#token').fill(demo['jury_token']);await jury.locator('#login-form button').click();await jury.locator('#dashboard').wait_for(state='visible');await jury.wait_for_timeout(1500)
   assert await jury.evaluate('chessCorpGetLanguage()')=='en';await jury.screenshot(path=str(OUT/'14-en-jury.png'))
   assert await jury.locator('h2').first.inner_text()=='Inspector access'
   await jury.locator('#admin-language').select_option('pl');await jury.wait_for_timeout(200);await jury.locator('#admin-language').select_option('en');await jury.wait_for_timeout(200)
   await page.bring_to_front();await d.press('F2');assert await page.evaluate('chessCorpGetLanguage()')=='pl'
   await page.reload();await page.get_by_role('button',name='Graj',exact=True).click(timeout=60000);await page.locator('#chess-start').wait_for(state='hidden',timeout=90000)
   assert await page.evaluate('chessCorpGetLanguage()')=='pl';await d.press('F2');await page.reload();await page.get_by_role('button',name='Play',exact=True).click(timeout=60000);await page.locator('#chess-start').wait_for(state='hidden',timeout=90000)
   assert await page.evaluate('chessCorpGetLanguage()')=='en'
   print('PASS: English gameplay, first quest, four locations, combat, contract, shop, mock chat/jobs, jury and persisted language.',flush=True)
  finally:
   (OUT/'browser019.json').write_text(json.dumps({'checkpoints':d.checkpoints,'errors':d.errors,'jobs':jobs,'chat':chat,'director':d.plans},ensure_ascii=False,indent=2),encoding='utf-8')
   await page.screenshot(path=str(OUT/'browser-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
