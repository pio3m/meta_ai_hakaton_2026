from tools.build_web import patch_html
import pytest

def test_web_startup_uses_bundled_wheel_and_visible_status():
    source='<title>web_app</title>\n    await shell.source(main, callback=ui_callback)\n</body>'
    html=patch_html(source)
    assert 'repo["-CDN-"] = str(platform.window.location.origin) + "/runtime/"' in html
    assert 'pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl' in html
    assert 'window.chessCorpStarted=' in html
    assert 'window.chessCorpFailed=' in html
    assert 'id="chess-play"' in html
    assert 'role="status"' in html

def test_web_template_change_fails_build():
    with pytest.raises(ValueError,match='Unsupported pygbag template'):
        patch_html('<html></html>')

def test_runtime_cache_is_verified_and_avoids_download(monkeypatch,tmp_path):
    import hashlib
    from tools import build_web
    payload=b'PK-test-runtime'
    monkeypatch.setattr(build_web,'SHA256',hashlib.sha256(payload).hexdigest())
    monkeypatch.setenv('CHESS_CORP_RUNTIME_CACHE',str(tmp_path))
    cache=tmp_path / build_web.Path(build_web.WHEEL_PATH).name
    cache.write_bytes(payload)
    def no_network(*args,**kwargs):
        raise AssertionError('Cached runtime must not be downloaded again')
    monkeypatch.setattr(build_web.urllib.request,'urlopen',no_network)
    assert build_web.fetch_runtime()==payload


def test_runtime_download_retries_incomplete_read(monkeypatch,tmp_path):
    import hashlib
    import io
    import http.client
    from tools import build_web
    payload=b'PK-test-runtime'
    monkeypatch.setattr(build_web,'SHA256',hashlib.sha256(payload).hexdigest())
    monkeypatch.setenv('CHESS_CORP_RUNTIME_CACHE',str(tmp_path))
    calls=[]
    def download(*args,**kwargs):
        calls.append(1)
        if len(calls)==1:
            raise http.client.IncompleteRead(b'PK',13)
        return io.BytesIO(payload)
    monkeypatch.setattr(build_web.urllib.request,'urlopen',download)
    assert build_web.fetch_runtime()==payload
    assert len(calls)==2
