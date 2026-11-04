"""Build pygbag and make its startup reliable on localhost static hosting."""
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request
import http.client
import os
import time

ROOT = Path(__file__).resolve().parent.parent
WHEEL_PATH = 'cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl'
CDN = 'https://pygame-web.github.io/cdn/'

SHA256 = '4f2caa3020592950565f3649c41e2eeacd001be93da892d60e5a4a43d893a323'


def fetch_runtime():
    cache = Path(os.getenv('CHESS_CORP_RUNTIME_CACHE',str(ROOT/'.cache/runtime')))/Path(WHEEL_PATH).name
    if cache.is_file():
        payload = cache.read_bytes()
        if hashlib.sha256(payload).hexdigest() == SHA256:
            return payload
    for attempt in range(3):
        try:
            started = time.monotonic()
            chunks = []
            size = 0
            with urllib.request.urlopen(CDN+WHEEL_PATH,timeout=15) as response:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    size += len(chunk)
                    if time.monotonic()-started > 60 or size > 5000000:
                        raise TimeoutError('Runtime download exceeded limit')
            payload = b''.join(chunks)
            if hashlib.sha256(payload).hexdigest() != SHA256:
                raise ValueError('Pygame WASM wheel checksum mismatch')
            cache.parent.mkdir(parents=True,exist_ok=True)
            cache.write_bytes(payload)
            return payload
        except (OSError,http.client.HTTPException,ValueError):
            if attempt == 2:
                raise
            print('Runtime download interrupted; retrying',attempt+2,flush=True)


def patch_html(html):
    marker = '    await shell.source(main, callback=ui_callback)'
    if html.count(marker) != 1:
        raise ValueError('Unsupported pygbag template: source marker missing or duplicated')
    replacement = '''    # pygbag 0.9.3 treats localhost as its development package proxy.
    # This is a static server: use the WASM wheel bundled during the build.
    import aio.pep0723
    for repo in aio.pep0723.Config.pkg_repolist:
        if "pygame" in repo:
            repo["-CDN-"] = str(platform.window.location.origin) + "/runtime/"
            repo["pygame"] = "''' + WHEEL_PATH + '''"
    try:
        await shell.source(main, callback=ui_callback)
    except Exception as error:
        platform.window.chessCorpFailed(str(error))
        raise
'''
    html = html.replace(marker, replacement)
    html = html.replace('<title>web_app</title>', '<title>Chess Corp</title>')
    html = html.replace('</head>', '<script src="chat_bridge.js"></script></head>')
    overlay = '''
<style>
#chess-start {position:fixed;inset:0;z-index:1000000;display:grid;place-content:center;text-align:center;background:#081622;color:#daedf0;font:18px Arial;padding:24px}
#chess-start[hidden]{display:none}
#chess-start h1{color:#64e0ef;letter-spacing:3px}
#chess-start button{background:#64e0ef;color:#081622;border:0;padding:14px 36px;font-size:20px;cursor:pointer;margin:18px auto}
#chess-start p{max-width:640px;line-height:1.5}
#infobox{display:none!important}
html,body{margin:0;background:#081622;overflow:hidden}
canvas.emscripten{image-rendering:pixelated;object-fit:contain;position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;border:0;outline:none;background:#081622}
</style>
<section id="chess-start" aria-label="Uruchamianie gry">
<h1>CHESS CORP</h1>
<p id="chess-message" role="status">Ładowanie gry i środowiska Python… Pierwszy start może potrwać kilkadziesiąt sekund.</p>
<button id="chess-play" type="button">Graj</button>
<p>WASD — ruch · E — rozmowa · Enter — dalej<br>Po załadowaniu kliknij Graj, aby rozpocząć.</p>
<button id="chess-retry" type="button" hidden>Spróbuj ponownie</button>
</section>
<script>
(() => {
 const ui=()=>({panel:document.getElementById('chess-start'),message:document.getElementById('chess-message'),play:document.getElementById('chess-play'),retry:document.getElementById('chess-retry')});
 let started=false, failed=false;
 window.chessCorpStarted=()=>{const {panel}=ui();started=true;panel.hidden=true;document.getElementById('canvas').focus();};
 window.chessCorpFailed=(error)=>{const {panel,message,retry}=ui();if(started)return;failed=true;panel.hidden=false;message.textContent='Nie udało się uruchomić gry: '+error;retry.hidden=false;};
 document.addEventListener('click',event=>{const {message,play}=ui();if(event.target.id==='chess-retry')location.reload();if(event.target.id==='chess-play'){message.textContent='Uruchamianie gry…';play.textContent='Uruchamianie…';}},true);
 window.addEventListener('error',event=>{if(event.message)window.chessCorpFailed(event.message);});
 window.addEventListener('unhandledrejection',event=>window.chessCorpFailed(String(event.reason)));
 setInterval(()=>{
  const {message,play}=ui();
  if(started||failed)return;
  const status=document.getElementById('infobox')?.textContent||'';
  if(status.includes('Ready to start')){message.textContent='Gra jest gotowa. Kliknij Graj.';play.textContent='Graj';}
  else if(status.includes('installing'))message.textContent='Przygotowywanie Pygame…';
 },500);
 setTimeout(()=>{const {message,retry}=ui();if(!started&&!failed){message.textContent='Ładowanie trwa dłużej niż zwykle. Kliknij Graj. Jeśli ekran się nie zmieni, sprawdź połączenie z Internetem i spróbuj ponownie.';retry.hidden=false;}},60000);
})();
</script>
'''
    return html.replace('</body>', '<script src="/audio_bridge.js"></script>'+overlay + '<script src="/locale.js"></script></body>')


def main():
    subprocess.run([sys.executable, str(ROOT/'tools/package_web.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-m', 'pygbag', '--build', '--no_opt', '--disable-sound-format-error', 'web_app'], cwd=ROOT, check=True)
    build = ROOT/'web_app/build/web'
    import shutil
    shutil.copy2(ROOT/'web/chat_bridge.js', build/'chat_bridge.js')
    shutil.copy2(ROOT/'web/audio_bridge.js', build/'audio_bridge.js')
    shutil.copy2(ROOT/'web/locale_bridge.js', build/'locale.js')
    shutil.copy2(ROOT/'content/i18n/catalog.json', build/'i18n.json')
    target = build/'runtime'/WHEEL_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_runtime()
    target.write_bytes(payload)
    print('Bundled pygame WASM SHA256:', hashlib.sha256(payload).hexdigest())
    index = build/'index.html'
    index.write_text(patch_html(index.read_text(encoding='utf-8')),encoding='utf-8')

if __name__ == '__main__':
    if '--fetch-runtime' in sys.argv:
        fetch_runtime()
    else:
        main()
