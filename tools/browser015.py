"""End-to-end keyboard playthrough in Chrome. No state injection, no fake model replies."""
import asyncio,json,math,sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parent.parent
EVIDENCE=ROOT/'docs/changes/015-rat-bounties-and-merchant/evidence'
def require_mock():
 import httpx
 values=dict(l.split('=',1) for l in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines() if '=' in l and not l.startswith('#'))
 with httpx.Client(base_url='http://localhost:8080',trust_env=False) as c:
  c.post('/admin/api/login',json={'token':values.get('ADMIN_TOKEN','').strip().strip('"')}).raise_for_status()
  data=c.get('/admin/api/calls').json()
  if any(data.get(k)!='mock' for k in ('mode','director_mode','world_mode')):
   raise SystemExit('Browser mock test requires Buddy, Director and World in mock mode; no paid calls started.')

class Demo:
 def __init__(self,page):self.page=page;self.snap=None;self.plans=[];self.errors=[];self.checkpoints=[];self.seen_at=0
 def request(self,req):
  if req.url.endswith(('/api/world/presence','/api/world/plan')):
   try:self.snap=req.post_data_json['snapshot'];self.seen_at=asyncio.get_running_loop().time()
   except Exception:pass
 async def response(self,res):
  if res.url.endswith('/api/director'):
   try:self.plans.append(await res.json())
   except Exception:pass
  if '/api/' in res.url and res.status>=400:self.errors.append({'url':res.url,'status':res.status,'body':(await res.text())[:300]})
 async def shot(self,name):
  await self.page.screenshot(path=str(EVIDENCE/(name+'.png')))
  self.checkpoints.append({'name':name,'state':self.snap});print(name,json.dumps(self.snap.get('gameplay') if self.snap else None,ensure_ascii=False),flush=True)
 async def fresh(self):
  before=self.seen_at
  for _ in range(450):
   await self.page.wait_for_timeout(100)
   if self.snap and self.seen_at>before:return self.snap
  raise AssertionError('No fresh game telemetry')
 async def hold(self,key,seconds):
  await self.page.keyboard.down(key);await self.page.wait_for_timeout(int(seconds*1000));await self.page.keyboard.up(key)
 async def move(self,x,y=452):
  await self.fresh();px,py=self.snap['player_position']
  if abs(py-y)>8:await self.hold('s' if y>py else 'w',abs(y-py)/85)
  if abs(px-x)>8:await self.hold('d' if x>px else 'a',abs(x-px)/185)
  await self.fresh()
 async def npc(self,ident):
  for _ in range(4):
   a=next(n for n in self.snap['npcs'] if n['npc_id']==ident)
   if math.dist(a['position'],self.snap['player_position'])<=12:return
   await self.move(*a['position'])
  raise AssertionError('Could not approach '+ident)
 async def press(self,key):await self.page.keyboard.press(key);await self.page.wait_for_timeout(250)
 async def travel(self,location):
  await self.move(900 if location=='bar' else 65)
  await self.press('f');await self.fresh()
  assert self.snap['location_id']==location,self.snap['location_id']
 async def fight(self):
  await self.page.keyboard.down('Space')
  try:
   for _ in range(15):
    await self.fresh();state=self.snap['gameplay']
    if state['bounty_state']=='ready':return
    if state['health']==0:await self.press('Enter');continue
    if state['health']<65:await self.press('h')
    enemies=[r for r in state['enemies'] if r['hp']>0]
    target=min(enemies,key=lambda r:math.dist(r['position'],self.snap['player_position']))
    await self.move(*target['position'])
    # Face toward the approaching enemy, then continue automatic local melee.
    dx=target['position'][0]-self.snap['player_position'][0]
    await self.hold('d' if dx>=0 else 'a',.04)
   raise AssertionError('Combat did not finish')
  finally:await self.page.keyboard.up('Space')

async def main():
 require_mock()
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
  page=await browser.new_page(viewport={'width':1200,'height':760});d=Demo(page)
  page.on('request',d.request);page.on('response',d.response);page.on('pageerror',lambda error:d.errors.append({'page_error':str(error)}))
  try:
   await page.goto('http://localhost:8080/');await page.get_by_role('button',name='Graj',exact=False).click()
   await page.locator('#chess-start').wait_for(state='hidden',timeout=60000);await d.fresh()
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape')
   await d.move(234,440);await d.press('e');await d.press('Escape')
   await d.move(535,440);await d.press('e');await d.press('Enter');await d.press('Enter');await d.press('Escape');await d.fresh()
   assert d.snap['first_quest_complete'],'First quest incomplete'
   await d.shot('browser-first-quest')
   if d.plans:
    plan=d.plans[-1]['plan'];obj=plan['place_objects'][0];obj['position']={'east_side':[780,452],'west_side':[100,452],'center_side':[385,452]}[obj['spawn_point']]
    if obj:
     await d.move(*obj['position']);await d.press('e');await d.fresh();await d.shot('browser-collect')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh()
   assert d.snap['gameplay']['bounty_state']=='active';await d.shot('browser-bounty-accepted')
   await d.travel('corporate_street');await d.shot('browser-rats');await d.fight();await d.shot('browser-first-wave-complete')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh()
   assert d.snap['gameplay']['credits']==36;await d.shot('browser-first-payout')
   await d.npc('merchant');await d.press('e');await d.press('ArrowDown');await d.press('Enter');await d.press('ArrowUp');await d.press('Enter');await d.fresh()
   assert d.snap['gameplay']['weapon_upgrade'] and d.snap['gameplay']['credits']==10
   await d.shot('browser-shop');await d.press('Escape')
   await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['contract_index']==1
   await d.travel('corporate_street');await d.fight();await d.shot('browser-second-wave-complete')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh()
   assert d.snap['gameplay']['claimed_contracts']==[0,1] and d.snap['first_quest_complete']
   await d.npc('merchant');await d.press('e');await d.press('ArrowDown');await d.press('ArrowDown');await d.press('Enter');await d.fresh()
   assert d.snap['gameplay']['armor'];await d.shot('browser-armor-and-both-contracts')
   await d.press('Escape');await d.travel('corporate_street');await d.shot('browser-final-street')
   print('BROWSER PLAYTHROUGH PASSED',flush=True)
  finally:
   (EVIDENCE/'browser-playthrough.json').write_text(json.dumps({'checkpoints':d.checkpoints,'api_errors':d.errors,'last_state':d.snap},ensure_ascii=False,indent=2),encoding='utf-8')
   await page.screenshot(path=str(EVIDENCE/'browser-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
