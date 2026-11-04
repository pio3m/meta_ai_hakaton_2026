
import pytest

@pytest.fixture(autouse=True)
def disable_real_world_network(monkeypatch):
    monkeypatch.setenv('CHESS_CORP_WORLD_NETWORK','false')

@pytest.fixture(autouse=True)
def isolate_asset_cache(tmp_path,monkeypatch):
    monkeypatch.setenv("ASSET_AI_CACHE_DIR",str(tmp_path/"generated"))
