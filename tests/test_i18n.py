import copy,json
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.world_models import WorldRequest,load_world_data
from game import i18n
from game.living_world import LivingWorld

@pytest.fixture(autouse=True)
def reset_language():
 i18n.set_language('en');yield;i18n.set_language('en')

def test_default_en_switch_and_exact_template():
 assert i18n.initialize()=='en'
 assert i18n.translate("Porozmawiaj z Buddy'm")=='Talk to Buddy'
 i18n.set_language('pl');assert i18n.translate("Porozmawiaj z Buddy'm")=="Porozmawiaj z Buddy'm"
 i18n.set_language('en');assert i18n.translate('Nieprawidłowa pozycja')=='Invalid position'

def test_ai_original_is_never_falsely_translated():
 value=i18n.original('Porozmawiaj z Buddy\'m','pl')
 assert value.startswith('[PL original]') and i18n.translate(value)==value
 assert i18n.original('Unknown stored output','und').startswith('[Original / language unknown]')
 i18n.set_language('pl');assert i18n.original('Hello','en')=='[EN oryginał] Hello'

def test_mock_translation_keeps_contract_fields_and_ids():
 raw={'schema_version':2,'quest_type':'COLLECT','create_quest':{'quest':{'title':"Porozmawiaj z Buddy'm",'id':'quest_01'}},'place_objects':[{'id':'obj_a','spawn_point':'east_side','label':'Bateria'}]}
 before=copy.deepcopy(raw);out=i18n.localize_plan(raw,'en')
 assert raw==before and out['quest_type']=='COLLECT' and out['place_objects'][0]['spawn_point']=='east_side'
 assert out['create_quest']['quest']['title']=='Talk to Buddy'

def test_mock_world_language_header_does_not_change_json_schema():
 rules,scene=load_world_data();w=LivingWorld(scene,'localization-world',network_enabled=False)
 payload={'session_id':'localization-world','revision':1,'reason':'interval','snapshot':w.snapshot([350,440],False)}
 assert 'language' not in WorldRequest.model_json_schema()['properties']
 with TestClient(create_app(Settings())) as c:
  r=c.post('/api/world/plan',json=payload,headers={'X-Chess-Language':'en'});assert r.status_code==200,r.text
  data=r.json();assert data['provider']=='mock' and data['language']=='en' and data['validation']['valid']
  assert data['plan']['decisions'][0]['npc_id']=='buddy'
  assert not any(x in data['plan']['decisions'][0]['goal'] for x in 'ąćęłńóśźż')

def test_mock_session_jobs_in_english_without_paid_permission():
 with TestClient(create_app(Settings())) as c:
  r=c.post('/api/director/jobs',json={'session_id':'localization-jobs','language':'en'})
  assert r.status_code==200,r.text
  d=r.json();assert d['provider']=='mock' and d['language']=='en' and len(d['plan']['jobs'])==2
  assert d['plan']['jobs'][0]['title']=='Batteries for Nyx'

def test_admin_locale_resources_public_but_calls_protected():
 with TestClient(create_app(Settings())) as c:
  assert c.get('/admin/assets/locale.js').status_code==200
  assert c.get('/admin/assets/i18n.json').status_code==200
  assert c.get('/admin/jury/api/calls').status_code==401
  assert c.get('/admin/api/calls').status_code==401
@pytest.mark.parametrize('kind',['COLLECT','SEQUENCE','LOGIC_PUZZLE'])
@pytest.mark.parametrize('lang',['en','pl'])
def test_all_mock_director_types_and_languages_validate(kind,lang):
 from backend.director_models import parse_plan,validate_scene,load_rules
 from game.director import validate_plan
 with TestClient(create_app(Settings())) as c:
  r=c.post('/api/director',json={'session_id':'locale-'+kind+'-'+lang,'language':lang,'context':{'quest_status':'completed','has_badge':True},'mock_type':kind})
  assert r.status_code==200,r.text
  data=r.json();assert data['language']==lang and data['plan']['quest_type']==kind
  rules,scene=load_rules();validate_scene(parse_plan(json.dumps(data['plan'])),rules,scene);validate_plan(data['plan'],scene,rules)
  if lang=='en':assert not any(x in data['plan']['create_quest']['quest']['title'] for x in 'ąćęłńóśźż')
def test_original_ai_text_stays_original_after_wrapping_and_prefixes(monkeypatch):
 import pygame
 from game.ui import UI
 pygame.font.init();ui=UI();i18n.set_language('en')
 value='Buddy: '+i18n.original("Porozmawiaj z Buddy'm",'pl')
 assert isinstance(value,i18n.OriginalText)
 lines=ui.wrap(value,150)
 assert all(isinstance(x,i18n.OriginalText) and i18n.translate(x)==x for x in lines)
 assert 'Talk to Buddy' not in ' '.join(lines)

def test_old_remote_chat_history_has_unknown_source_not_current_language():
 import asyncio
 from game.chat import Chat
 async def run():
  chat=Chat();chat.pending_language='en'
  task=asyncio.create_task(asyncio.sleep(0,result={'reply':'Hello recruit','history':[{'role':'user','content':'Czesc'},{'role':'assistant','content':'Witaj rekrucie'},{'role':'user','content':'Hello'},{'role':'assistant','content':'Hello recruit'}],'provider':'mock'}))
  await task;chat.task=task;chat.poll()
  assert chat.history_languages==['und','und','und','en']
 asyncio.run(run())
@pytest.mark.parametrize('source,expected',[
 ('> Apteczka / 8 KR','> Medkit / 8 CR'),
 ('  Pałka impulsowa +1 / 18 KR','  Pulse baton +1 / 18 CR'),
 ('  Pancerz uliczny / 22 KR','  Street armour / 22 CR'),
 ('Barman | mock | EN','Bartender | mock | EN'),
 ('Ty: ','You: '),
])
def test_composed_shop_and_chat_labels(source,expected):
 assert i18n.translate(source,'en')==expected
