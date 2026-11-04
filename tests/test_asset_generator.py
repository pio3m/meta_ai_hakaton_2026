import asyncio
import base64
from io import BytesIO
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from backend.app import create_app
from backend.asset_generator import AssetGenerator,AssetRequest,MODEL,payload
from backend.inspector import CallStore
from backend.settings import Settings


def encoded_image():
    data=BytesIO();Image.new('RGB',(256,256),(30,90,120)).save(data,format='PNG');return base64.b64encode(data.getvalue()).decode()


def test_image_owner_auth_and_mock_never_generate():
    app=create_app(Settings(inspector_token='asset-owner-token-very-long'))
    with TestClient(app) as c:
        assert c.post('/admin/api/asset/generate',json={}).status_code==401
        c.post('/admin/api/login',json={'token':'asset-owner-token-very-long'})
        assert c.post('/admin/api/asset/generate',json={}).status_code==503
        assert c.get('/api/assets/catalog').json()['automatic_generation'] is False
        assert c.get('/api/assets/hacker_emblem.png').status_code==404
        assert not app.state.inspector.calls


def test_image_fake_http_generates_once_cache_survives_restart_and_private_prompt_not_public(tmp_path):
    async def run():
        calls=[]
        def handler(req):
            calls.append(json.loads(req.content));assert str(req.url)=='https://api.meta.ai/v1/images/generations'
            assert calls[-1]['n']==1 and calls[-1]['model']==MODEL and calls[-1]['response_format']=='b64_json'
            return httpx.Response(200,json={'data':[{'b64_json':encoded_image()}],'output_format':'png','usage':{'input_tokens':20,'output_tokens':80,'total_tokens':100}})
        s=Settings(asset_ai_mode='meta',asset_ai_allow_paid_requests=True,api_key='fake-secret',asset_cache_dir=str(tmp_path))
        store=CallStore(secrets=('fake-secret',))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            g=AssetGenerator(s,c,store);first=await g.generate(AssetRequest(session_id='asset-test-one'))
            assert first['asset']['source']=='META' and not first['asset']['cached']
            assert Image.open(tmp_path/'hacker_emblem.png').size==(128,128)
            assert 'prompt' not in first['asset'] and 'prompt' not in json.loads((tmp_path/'hacker_emblem.public.json').read_text())
            assert store.get(first['call_id'])['sent_to_model']
            assert store.get(first['call_id'])['usage']['total_tokens']==100
            assert (await g.generate(AssetRequest()))['asset']['cached']
            restarted=AssetGenerator(s,c,CallStore());assert (await restarted.generate(AssetRequest()))['asset']['cached']
        assert len(calls)==1
    asyncio.run(run())

@pytest.mark.parametrize('failure',['http','malformed','bad-image'])
def test_image_failed_attempt_is_durable_no_automatic_retry(tmp_path,failure):
    async def run():
        calls=[]
        def handler(req):
            calls.append(req)
            if failure=='http':return httpx.Response(503,json={'error':'unavailable'})
            if failure=='malformed':return httpx.Response(200,json={'data':[]})
            return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(b'bad').decode()}]})
        s=Settings(asset_ai_mode='meta',asset_ai_allow_paid_requests=True,api_key='fake',asset_cache_dir=str(tmp_path))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            g=AssetGenerator(s,c,CallStore());assert (await g.generate(AssetRequest())).status_code==502
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as error:await AssetGenerator(s,c,CallStore()).generate(AssetRequest())
            assert error.value.status_code==429 and len(calls)==1
    asyncio.run(run())
@pytest.mark.parametrize('asset_id',['cyber_rat','merchant'])
def test_generated_sprite_alpha_frames_cache_and_public_route(tmp_path,asset_id):
    async def run():
        raw=BytesIO();im=Image.new('RGB',(256,256),(0,255,0))
        from PIL import ImageDraw
        ImageDraw.Draw(im).rectangle((70,50,185,220),fill=(130,40,180));im.save(raw,format='PNG')
        count=[]
        def handler(req):count.append(req);return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(raw.getvalue()).decode()}]})
        s=Settings(asset_ai_mode='meta',asset_ai_allow_paid_requests=True,asset_ai_global_limit=3,api_key='fake',asset_cache_dir=str(tmp_path))
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as c:
            g=AssetGenerator(s,c,CallStore());body=AssetRequest(asset_id=asset_id)
            result=await g.generate(body);assert result['asset']['id']==asset_id
            with Image.open(tmp_path/(asset_id+'.png')) as sprite:
                assert sprite.mode=='RGBA' and sprite.getpixel((0,0))[3]==0
            assert all((tmp_path/f'{asset_id}_{i}.png').exists() for i in range(4))
            assert (tmp_path/(asset_id+'.private.json')).exists()
            assert (await AssetGenerator(s,c,CallStore()).generate(body))['asset']['cached']
            assert len(count)==1
    asyncio.run(run())


def test_asset_global_limit_includes_other_assets_and_survives_restart(tmp_path):
    async def run():
        (tmp_path/'.hacker_emblem-paid-attempt.json').write_text('{}')
        s=Settings(asset_ai_mode='meta',asset_ai_allow_paid_requests=True,api_key='fake',asset_cache_dir=str(tmp_path))
        def unexpected(req):raise AssertionError('No HTTP permitted')
        async with httpx.AsyncClient(transport=httpx.MockTransport(unexpected)) as c:
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as e:await AssetGenerator(s,c,CallStore()).generate(AssetRequest(asset_id='cyber_rat'))
            assert e.value.status_code==429
    asyncio.run(run())
