"""Owner-only, persistent one-shot Meta image generation. No startup inference."""
import asyncio
import base64
from datetime import datetime,timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
from time import monotonic
from typing import Literal
from fastapi import Depends,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from pydantic import BaseModel,ConfigDict,Field,model_validator
from PIL import Image
from backend.inspector import active_call,record_request,record_status

MODEL='muse-image-1.0'
ASSET_ID='hacker_emblem'
PROMPT=('Create one decorative wall poster for the fictional pixel-art game Chess Corp. '
        'Square flat front-facing sign, dark navy background, luminous cyan and magenta circuit-board fox emblem. '
        'Crisp chunky pixel art, limited 16-color palette, hard edges, no gradients, no photographic detail. '
        'Center the emblem with generous dark padding. No text, no letters, no brands, no real people. '
        'It hangs on the wall of a cyberpunk hacker hideout. One single image, not a sprite sheet.')

SPRITE_PROMPT=('For the fictional 2D cyberpunk pixel-art game Chess Corp, draw exactly ONE isolated full-body side-view character, facing right, centered with ample padding. Flat PURE BRIGHT GREEN background RGB(0,255,0), no ground, no shadow, no scenery, no letters, no UI, no sprite sheet, no other characters. Crisp chunky pixel art, limited dark navy/cyan/magenta palette, hard edges, no gradients. Do not use green anywhere on the character. ')
ASSETS={
    'hacker_emblem':{'prompt':PROMPT,'location':'hacker_hideout','size':(128,128)},
    'cyber_rat':{'prompt':SPRITE_PROMPT+'A small aggressive cybernetic sewer rat: low horizontal quadruped silhouette, grey-purple fur, long segmented mechanical tail, four short legs, glowing red eye and cyan metal spine. Entire tail and paws visible. Cute sinister arcade enemy, readable at 80 pixels wide.','location':'corporate_street','size':(80,48)},
    'merchant':{'prompt':SPRITE_PROMPT+'Nyx, a futuristic equipment merchant: full standing biped character, dark purple hooded coat, gold tool belt and small satchel, cyan visor, fingerless gloves, boots. Face in profile. Relaxed confident stance. Clear silhouette, entire body and boots visible. Readable at 72 pixels tall.','location':'bar','size':(64,96)},
}

def payload(asset_id=ASSET_ID):
    return {'model':MODEL,'prompt':ASSETS[asset_id]['prompt'],'n':1,'size':'1024x1024','output_format':'png','response_format':'b64_json',
            'reasoning_strength':'low','tool_enablement':{'enable_image_search':False,'enable_web_search':False,'enable_shell':False}}

class AssetContext(BaseModel):
    location_id:str='hacker_hideout'
    asset_id:str=ASSET_ID

class AssetRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    session_id:str=Field(default='asset-owner-session',min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    asset_id:Literal['hacker_emblem','cyber_rat','merchant']=ASSET_ID
    refresh:bool=False
    request_id:str | None=Field(default=None,pattern=r'^[a-f0-9]{32}$')
    @model_validator(mode='after')
    def refresh_id(self):
        if self.refresh and not self.request_id:raise ValueError('Refresh requires unique request_id')
        return self
    @property
    def npc_id(self):return 'asset_generator'
    @property
    def language(self):return 'pl'
    @property
    def message(self):return self.asset_id+' / Muse Image'
    @property
    def context(self):return AssetContext(location_id=ASSETS[self.asset_id]['location'],asset_id=self.asset_id)

class AssetGenerator:
    def __init__(self,settings,client,store):
        self.settings=settings;self.client=client;self.store=store;self.root=Path(settings.asset_cache_dir);self.lock=asyncio.Lock()
        self.manifest=self.root/(ASSET_ID+'.json');self.image=self.root/(ASSET_ID+'.png')
        self.claim=self.root/('.'+ASSET_ID+'-paid-attempt.json')
        self.import_cache()

    def paths(self,asset_id):
        return (self.root/(asset_id+('.json' if asset_id==ASSET_ID else '.private.json')),self.root/(asset_id+'.png'),self.root/('.'+asset_id+'-paid-attempt.json'))

    def cached(self,asset_id=ASSET_ID):
        manifest,image,_=self.paths(asset_id)
        try:
            data=json.loads(manifest.read_text(encoding='utf-8'))
            if data.get('id')!=asset_id or data.get('source')!='META' or data.get('model')!=MODEL:return None
            if hashlib.sha256(image.read_bytes()).hexdigest()!=data.get('sha256'):return None
            return data
        except (OSError,ValueError,TypeError):return None

    @staticmethod
    def public(data):return {k:data[k] for k in ('id','source','model','sha256','generation_ms','preview_url')}

    def import_cache(self):
        for asset_id in ASSETS:
            data=self.cached(asset_id)
            if data:
                cid=self.store.start(AssetRequest(session_id='asset-cache-session',asset_id=asset_id),'meta',MODEL,kind='asset')
                self.store.update(cid,provider='cache',asset={**self.public(data),'cached':True},usage=data.get('usage'),request_payload=data.get('request_payload'),sent_to_model=False)
                self.store.finish(cid,reply='Wczytano istniejący asset Meta z cache. Bez generacji.')

    def write_image(self,raw,asset_id=ASSET_ID):
        if len(raw)>20*1024*1024:raise ValueError('Image too large')
        with Image.open(BytesIO(raw)) as image:
            if image.width*image.height>16000000:raise ValueError('Image dimensions too large')
            original={'size':list(image.size),'format':image.format}
            image=image.convert('RGBA')
            if asset_id==ASSET_ID:
                image=image.resize((64,64),Image.Resampling.NEAREST).resize((128,128),Image.Resampling.NEAREST)
            else:
                # Chroma key supplied explicitly in the generation prompt; never assumes black=alpha.
                pixels=[]
                for r,g,b,a in image.get_flattened_data():
                    pixels.append((r,g,b,0 if g>85 and g>r*1.25 and g>b*1.25 else a))
                image.putdata(pixels)
                box=image.getbbox()
                if not box:raise ValueError('Empty sprite')
                image=image.crop(box);w,h=ASSETS[asset_id]['size'];image.thumbnail((w-4,h-4),Image.Resampling.NEAREST)
                canvas=Image.new('RGBA',(w,h));canvas.alpha_composite(image,((w-image.width)//2,h-image.height-2));image=canvas
                # Derived local animation, not four independently generated poses.
                for i in range(4):
                    frame=Image.new('RGBA',(w,h));frame.alpha_composite(image,(0,-(i%2)))
                    frame.save(self.root/(asset_id+'_'+str(i)+'.png'))
            temp=self.root/(asset_id+'.pending.png');image.save(temp);temp.replace(self.paths(asset_id)[1])
        return original

    async def generate(self,body):
        async with self.lock:
            asset_id=body.asset_id
            manifest,image,claim=self.paths(asset_id)
            cached=self.cached(asset_id)
            if cached and not body.refresh:
                cid=self.store.start(body,'meta',MODEL,kind='asset');self.store.update(cid,provider='cache',asset={**self.public(cached),'cached':True},usage=cached.get('usage'),request_payload=cached.get('request_payload'),sent_to_model=False)
                self.store.finish(cid,reply='Asset z cache. Bez wywołania Meta.')
                return {'asset':{**self.public(cached),'cached':True},'call_id':cid}
            if self.settings.asset_ai_mode!='meta' or not self.settings.asset_ai_allow_paid_requests:
                raise HTTPException(503,'Generowanie obrazów jest wyłączone. Gra używa oryginalnych zasobów.')
            if not self.settings.api_key.get_secret_value():raise HTTPException(503,'Brak klucza Meta.')
            self.root.mkdir(parents=True,exist_ok=True)
            if body.refresh:
                claim=self.root/('.'+asset_id+'-refresh-'+body.request_id+'-paid-attempt.json')
                if claim.exists():raise HTTPException(409,'Ta próba regeneracji została już wykorzystana. Bez powtórzenia kosztu.')
                budget=self.root/'.asset-refresh-spend.json'
                try:used=json.loads(budget.read_text())['calls'] if budget.exists() else 0
                except (OSError,ValueError,KeyError):raise HTTPException(503,'Nieprawidłowy licznik regeneracji. Nie wyzerowano go.')
                if used>=self.settings.asset_ai_global_limit:raise HTTPException(429,'Limit ręcznych regeneracji z konfiguracji został wykorzystany.')
                with claim.open('x',encoding='utf-8') as f:json.dump({'attempt':1,'model':MODEL,'request_id':body.request_id},f)
                tmp=budget.with_suffix('.pending.json');tmp.write_text(json.dumps({'calls':used+1}));tmp.replace(budget)
            else:
                if len(list(self.root.glob('.*-paid-attempt.json')))>=self.settings.asset_ai_global_limit:
                    raise HTTPException(429,'Globalny limit prób generacji obrazów został wykorzystany.')
                try:
                    with claim.open('x',encoding='utf-8') as f:json.dump({'attempt':1,'model':MODEL,'started_at':datetime.now(timezone.utc).isoformat()},f)
                except FileExistsError:raise HTTPException(429,'Próba generacji wykorzystana. Użyj jawnej regeneracji w adminie.')
            cid=self.store.start(body,'meta',MODEL,kind='asset');token=active_call.set((self.store,cid));started=monotonic()
            try:
                req=payload(asset_id)
                if body.refresh:req['prompt']+=' Produce a fresh visual variation, keeping the required style and silhouette. Variation seed: '+body.request_id
                record_request(req)
                response=await self.client.post(self.settings.base_url+'/images/generations',json=req,
                    headers={'Authorization':'Bearer '+self.settings.api_key.get_secret_value()},timeout=self.settings.asset_ai_timeout_seconds)
                record_status(response.status_code);response.raise_for_status()
                data=response.json()
                if not isinstance(data.get('data'),list) or len(data['data'])!=1:raise ValueError('Expected exactly one image')
                encoded=data['data'][0]['b64_json']
                if not isinstance(encoded,str) or len(encoded)>28*1024*1024:raise ValueError('Invalid image payload')
                raw=base64.b64decode(encoded,validate=True)
                original=await asyncio.to_thread(self.write_image,raw,asset_id)
                usage={}
                for src,dst in [('input_tokens','prompt_tokens'),('output_tokens','completion_tokens'),('total_tokens','total_tokens')]:
                    value=data.get('usage',{}).get(src)
                    if type(value) is int and value>=0:usage[dst]=value
                info={'id':asset_id,'source':'META','model':MODEL,'prompt':ASSETS[asset_id]['prompt'],'request_payload':req,
                      'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'generation_ms':round((monotonic()-started)*1000,2),
                      'preview_url':'/api/assets/'+asset_id+'.png','usage':usage,'original':original,'processed_size':list(ASSETS[asset_id]['size']),
                      'generated_at':datetime.now(timezone.utc).isoformat()}
                temp=self.root/(asset_id+'.pending.json');temp.write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(manifest)
                public=self.public(info);(self.root/(asset_id+'.public.json')).write_text(json.dumps(public,indent=2),encoding='utf-8')
                self.store.update(cid,asset={**public,'cached':False},usage=usage,response_json={'image_saved':True,'original':original,'usage':data.get('usage')},validation={'valid':True,'errors':[]})
                self.store.finish(cid,reply='Wygenerowano i zapisano dekorację kryjówki, 128x128 PNG.')
                return {'asset':{**public,'cached':False},'call_id':cid}
            except asyncio.CancelledError:
                self.store.finish(cid,error='Generacja przerwana. Próba wykorzystana; bez ponowienia.',status=499);raise
            except Exception:
                self.store.update(cid,validation={'valid':False,'errors':['Generacja lub dekodowanie obrazu nie powiodło się.']})
                self.store.finish(cid,error='Meta Image: generacja nie powiodła się; próba wykorzystana, bez ponowienia.',status=502)
                return JSONResponse(status_code=502,content={'detail':'Meta Image: generacja nie powiodła się; próba wykorzystana, bez ponowienia.','call_id':cid})
            finally:active_call.reset(token)


def register_assets(app,settings,store):
    @app.post('/admin/api/asset/generate',dependencies=[Depends(app.state.inspector_access.owner)])
    async def generate(body:AssetRequest):return await app.state.asset_generator.generate(body)

    @app.get('/api/assets/{asset_id}.png')
    async def image(asset_id:str):
        if asset_id not in ASSETS:raise HTTPException(404,'Unknown asset')
        generator=app.state.asset_generator
        if not generator.cached(asset_id):raise HTTPException(404,'Brak wygenerowanego obrazu. Gra korzysta z oryginałów.')
        return FileResponse(generator.paths(asset_id)[1],media_type='image/png',headers={'Cache-Control':'no-store'})

    @app.get('/api/assets/catalog')
    async def catalog():
        g=app.state.asset_generator
        return {'assets':[g.public(data) for key in ASSETS if (data:=g.cached(key))],'fallback_source':'ORIGINAL','automatic_generation':False}

    @app.post('/admin/api/asset/clear',dependencies=[Depends(app.state.inspector_access.owner)])
    async def clear(body:AssetRequest):
        g=app.state.asset_generator
        async with g.lock:
            manifest,image,_=g.paths(body.asset_id)
            files=[manifest,image,g.root/(body.asset_id+'.public.json')]+[g.root/(body.asset_id+'_'+str(i)+'.png') for i in range(4)]
            for path in files:path.unlink(missing_ok=True)
        return {'removed':body.asset_id,'spending_ledgers_preserved':True}

    @app.post('/api/assets/updates')
    async def updates(body:dict):
        versions=body.get('versions',{})
        if set(body)!={'versions'} or not isinstance(versions,dict) or len(versions)>3 or any(k not in ASSETS or not isinstance(v,str) or len(v)>64 for k,v in versions.items()):raise HTTPException(422,'Invalid asset versions')
        g=app.state.asset_generator;available={};changed=[]
        for key in ASSETS:
            data=g.cached(key)
            if not data:continue
            available[key]=data['sha256']
            if versions.get(key)!=data['sha256']:
                changed.append({'id':key,'sha256':data['sha256'],'model':data['model'],'png_base64':base64.b64encode(g.paths(key)[1].read_bytes()).decode()})
        return {'versions':available,'assets':changed,'removed':[key for key in versions if key not in available]}
