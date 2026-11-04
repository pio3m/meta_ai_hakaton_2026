"""Actual Chrome audio + gameplay check. Uses configured real LLM; no audio APIs.
Only reads emitted game audio diagnostics and samples the real Web Audio mixer output.
"""
import asyncio,base64,json
from pathlib import Path
from playwright.async_api import async_playwright
import browser015 as b
ROOT=b.ROOT;EVIDENCE=ROOT/'docs/changes/017-cyberpunk-sound-design/evidence'
b.EVIDENCE=EVIDENCE
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,ignore_default_args=['--mute-audio'],args=['--autoplay-policy=document-user-activation-required'])
  context=await browser.new_context(viewport={'width':1200,'height':760});await context.add_init_script(path=str(ROOT/'tools/audio_qa.js'))
  page=await context.new_page();d=b.Demo(page);samples=[];world_results=[]
  async def response(res):
   await d.response(res)
   if res.url.endswith('/api/world/plan'):world_results.append(await res.json())
  page.on('request',d.request);page.on('response',response);page.on('pageerror',lambda error:d.errors.append({'page_error':str(error)}))
  async def audio(label):
   await page.wait_for_timeout(700)
   state=await page.evaluate('({audio:window.chessCorpAudioStatus,meter:window.__audioQA.measure()})');state['label']=label;samples.append(state)
   print('AUDIO',label,json.dumps(state,ensure_ascii=False),flush=True);return state
  try:
   await page.goto('http://localhost:8080/');before=await page.evaluate('({report:window.chessCorpAudioStatus??null,meter:window.__audioQA.measure()})')
   assert before['meter']['rms']==0,'Audio before user gesture'
   await page.wait_for_timeout(1500)
   baseline_intervals=await page.evaluate('window.__audioQA.frames')
   baseline_hz=1000/(sum(baseline_intervals)/len(baseline_intervals))
   await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000)
   await page.wait_for_function('window.chessCorpAudioStatus?.unlocked',timeout=30000)
   state=await audio('after-play-click');assert state['audio']['available'] and state['audio']['loaded_sounds']==14 and not state['audio']['errors'],state
   assert state['meter']['rms']>.0001 and 'running' in state['meter']['contexts'],state
   assert await page.evaluate('window.__audioQA.startRecording()')
   await page.wait_for_timeout(2500);state=await audio('street-no-duplicate');assert state['audio']['ambient_starts']=={'corporate_street':1}
   await d.press('m');state=await audio('muted');assert state['audio']['muted'] and not state['audio']['ambient_busy'] and state['meter']['rms']<.00001
   await d.shot('browser-muted')
   await d.press('m');await page.wait_for_timeout(500);state=await audio('unmuted');assert not state['audio']['muted'] and state['meter']['rms']>.0001
   await d.fresh();await d.travel('bar');state=await audio('bar');assert state['audio']['ambient']=='bar' and state['audio']['ambient_starts']['bar']==1
   await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['bounty_state']=='active'
   state=await audio('barman');assert state['audio']['sfx_played']['conversation']>=1
   await d.npc('merchant');await d.press('e');await d.press('Escape');state=await audio('shop-open-close');assert state['audio']['sfx_played']['shop_open']>=1 and state['audio']['sfx_played']['shop_close']>=1
   await d.travel('corporate_street');state=await audio('street-return');assert state['audio']['ambient']=='corporate_street'
   if d.snap['gameplay']['health']<100:await d.press('h')
   await d.fight();state=await audio('combat');assert all(state['audio']['sfx_played'].get(name,0)>0 for name in ['swing','hit','rat_down'])
   if d.snap['gameplay']['health']<100 and d.snap['gameplay']['medkits']>0:await d.press('h')
   await d.travel('bar');await d.npc('bartender');await d.press('e');await d.fresh();assert d.snap['gameplay']['credits']==36
   state=await audio('contract-credits');assert state['audio']['sfx_played'].get('credits',0)==1
   await d.npc('merchant');await d.press('e');await d.press('ArrowDown');await d.press('Enter');await d.fresh();assert d.snap['gameplay']['weapon_upgrade']
   state=await audio('purchase');assert state['audio']['sfx_played']['purchase']>=1;await d.press('Escape')
   assert state['audio']['sfx_played'].get('heal',0)>=1,'Apteczka not used'
   await d.shot('browser-audio-shop')
   await d.travel('corporate_street')
   for location,x in [('hacker_hideout',100),('corporate_lobby',700)]:
    await d.move(x);await d.press('f');await d.fresh();state=await audio(location);assert state['audio']['ambient']==location
    await d.travel('corporate_street')
   state=await audio('final-street');assert state['audio']['sfx_played']['door']>=8 and not state['audio']['errors']
   stats=await page.evaluate('({samples:window.__audioQA.samples,frameIntervals:window.__audioQA.frames})')
   frames=stats['frameIntervals'];fps=1000/(sum(frames)/len(frames))
   assert fps>=baseline_hz*.85,(fps,baseline_hz)
   encoded=await page.evaluate('window.__audioQA.finishRecording()');(EVIDENCE/'browser-live-audio.webm').write_bytes(base64.b64decode(encoded))
   assert not d.errors,d.errors
   (EVIDENCE/'browser-audio-results.json').write_text(json.dumps({'success':True,'before_gesture':before,'checkpoints':samples,'audio_samples':stats['samples'],'observed_browser_refresh_hz':round(fps,2),'baseline_browser_refresh_hz':round(baseline_hz,2),'api_errors':d.errors,'world_providers':[r['provider'] for r in world_results],'last_game_state':d.snap},ensure_ascii=False,indent=2),encoding='utf-8')
   print('BROWSER AUDIO PASSED, FPS',round(fps,2),'real PCM, M silence, 4 ambients, all effects, real gameplay.',flush=True)
  finally:
   (EVIDENCE/'browser-audio-progress.json').write_text(json.dumps({'audio_checkpoints':samples,'api_errors':d.errors,'world_results':world_results,'last_state':d.snap},ensure_ascii=False,indent=2),encoding='utf-8')
   await page.screenshot(path=str(EVIDENCE/'browser-audio-last.png'));await browser.close()
if __name__=='__main__':asyncio.run(main())
