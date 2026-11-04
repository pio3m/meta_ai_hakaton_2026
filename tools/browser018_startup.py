"""Bounded startup check: one fresh session, no asset generation, no repeated model queries."""
import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/changes/018-npc-combat-chat-and-session-jobs/evidence'
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True)
  page=await browser.new_page(viewport={'width':1200,'height':760});jobs=[];chats=[];errors=[]
  async def response(r):
   if r.url.endswith('/api/director/jobs'):jobs.append({'status':r.status,'data':await r.json()})
   if r.url.endswith('/api/chat'):chats.append({'status':r.status,'data':await r.json()})
  page.on('response',response);page.on('pageerror',lambda e:errors.append(str(e)))
  try:
   await page.goto('http://localhost:8080/');await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000)
   for _ in range(75):
    if jobs:break
    await page.wait_for_timeout(400)
   assert jobs and jobs[0]['status']==200,jobs
   assert jobs[0]['data']['provider']=='meta' and len(jobs[0]['data']['plan']['jobs'])==2
   await page.keyboard.press('j');await page.wait_for_timeout(400);await page.screenshot(path=str(OUT/'new-session-jobs.png'));await page.keyboard.press('Escape')
   await page.wait_for_timeout(300);await page.keyboard.press('t');await page.wait_for_timeout(400);await page.keyboard.type('Kim jestes i czym zajmujesz sie w Chess Corp?',delay=20);await page.wait_for_timeout(250);await page.keyboard.press('Enter')
   for _ in range(85):
    if chats:break
    await page.wait_for_timeout(400)
   assert chats and chats[0]['status']==200,chats
   assert chats[0]['data']['provider']=='meta' and chats[0]['data']['npc_id']!='buddy',chats
   await page.screenshot(path=str(OUT/'npc-text-chat.png'))
   print('READY: 2 new META jobs and NPC text reply from',chats[0]['data']['npc_id'],flush=True)
  finally:
   (OUT/'startup-live.json').write_text(json.dumps({'jobs':jobs,'chats':chats,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8');await browser.close()
if __name__=='__main__':asyncio.run(main())
