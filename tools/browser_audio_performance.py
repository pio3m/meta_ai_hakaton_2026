"""Real browser audio output and relative performance check, no model substitutes."""
import asyncio,json,base64
from playwright.async_api import async_playwright
from browser015 import ROOT
OUT=ROOT/'docs/changes/017-cyberpunk-sound-design/evidence'
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(channel='chrome',headless=True,ignore_default_args=['--mute-audio'],args=['--autoplay-policy=document-user-activation-required'])
  context=await browser.new_context(viewport={'width':1200,'height':760});await context.add_init_script(path=str(ROOT/'tools/audio_qa.js'))
  page=await context.new_page();results={}
  async def measure(label):
   await page.evaluate('window.__audioQA.frames=[]');await page.wait_for_timeout(4000)
   item=await page.evaluate('({audio:window.chessCorpAudioStatus??null,meter:window.__audioQA.measure(),intervals:window.__audioQA.frames})')
   frames=item.pop('intervals');item['browser_raf_hz']=round(1000/(sum(frames)/len(frames)),2);results[label]=item;print(label,json.dumps(item),flush=True);return item
  try:
   await page.goto('http://localhost:8080/');before=await measure('before-play')
   assert before['meter']['rms']==0
   await page.get_by_role('button',name='Graj',exact=False).click();await page.locator('#chess-start').wait_for(state='hidden',timeout=60000)
   await page.wait_for_function('window.chessCorpAudioStatus?.available',timeout=30000);assert await page.evaluate('window.__audioQA.startRecording()')
   on=await measure('audio-on');assert on['meter']['rms']>.0001
   await page.keyboard.press('m');await page.wait_for_timeout(800);off=await measure('audio-muted');assert off['audio']['muted'] and off['meter']['rms']==0
   await page.keyboard.press('m');await page.wait_for_timeout(800);again=await measure('audio-restored');assert again['meter']['rms']>.0001 and not again['audio']['errors']
   assert on['browser_raf_hz']>=off['browser_raf_hz']*.85
   assert again['browser_raf_hz']>=off['browser_raf_hz']*.85
   encoded=await page.evaluate('window.__audioQA.finishRecording()');(OUT/'browser-live-audio.webm').write_bytes(base64.b64decode(encoded))
   results['success']=True
   print('AUDIO PERFORMANCE PASSED: no relative refresh-rate regression, actual output and mute confirmed.',flush=True)
  finally:
   (OUT/'browser-audio-performance.json').write_text(json.dumps(results,indent=2),encoding='utf-8');await browser.close()
if __name__=='__main__':asyncio.run(main())
