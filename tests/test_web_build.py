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
