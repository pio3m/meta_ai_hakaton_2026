"""Two fresh LLM jobs per new game session, using the existing adapter and Inspector."""
import asyncio,json,uuid
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel,ConfigDict,Field,model_validator
from typing import Literal
from backend.inspector import active_call
from backend.providers import MetaProvider
from game.job_contract import POINTS,validate_jobs,replay_jobs

class Closed(BaseModel):model_config=ConfigDict(extra='forbid',strict=True)
class Placement(Closed):
 location_id:Literal['corporate_street','bar','hacker_hideout','corporate_lobby']
 slot:Literal['A','B']
class Job(Closed):
 id:Literal['job_a','job_b']
 title:str=Field(min_length=3,max_length=60)
 description:str=Field(min_length=3,max_length=180)
 item_label:str=Field(min_length=3,max_length=28)
 reward:int=Field(ge=15,le=45)
 placements:list[Placement]=Field(min_length=1,max_length=2)
class JobPlan(Closed):
 schema_version:Literal[1]
 jobs:list[Job]=Field(min_length=2,max_length=2)
 @model_validator(mode='after')
 def contract(self):validate_jobs(self.model_dump());return self
class Context(BaseModel):run_id:str
class JobRequest(BaseModel):
 model_config=ConfigDict(extra='forbid')
 session_id:str=Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
 language:Literal['pl','en']='pl'
 @property
 def npc_id(self):return 'session_director'
 @property
 def message(self):return 'Dwa nowe zlecenia zbierackie bieżącej sesji'
 @property
 def context(self):return Context(run_id=self.session_id)
class CollectEvent(Closed):
 object_id:str=Field(pattern=r'^job_[ab]_[01]$')
 location_id:Literal['corporate_street','bar','hacker_hideout','corporate_lobby']
 position:list[float]=Field(min_length=2,max_length=2)
class JobExecution(JobRequest):
 call_id:str=Field(pattern=r'^[a-f0-9]{32}$')
 events:list[CollectEvent]=Field(max_length=4)

def register_jobs(app,settings,store):
 lock=asyncio.Lock();ledger=Path(settings.asset_cache_dir)/'.session-jobs-spend.json'
 @app.post('/api/director/jobs')
 async def generate(body:JobRequest):
  async with app.state.history.turn(body.session_id) as session:
   if session.session_jobs:return {**session.session_jobs,'generation':'accepted-session-state'}
   if session.session_jobs_attempted:return JSONResponse(status_code=409,content={'detail':'Ta sesja ma już wykorzystaną próbę generacji. R rozpoczyna nową sesję.'})
   session.session_jobs_attempted=True
   cid=store.start(body,settings.director_mode,settings.model,kind='director');token=active_call.set((store,cid))
   try:
    if settings.director_mode=='mock':
     from game.i18n import localize_plan
     from backend.inspector import record_request
     plan=localize_plan({'schema_version':1,'jobs':[
      {'id':'job_a','title':'Baterie dla Nyx','description':'Odbierz baterię przy barze. Nagroda zostanie wypłacona automatycznie.','item_label':'Bateria','reward':25,'placements':[{'location_id':'bar','slot':'A'}]},
      {'id':'job_b','title':'Archiwum kuriera','description':'Odbierz paczkę z kryjówki hakerów. Nagroda zostanie wypłacona automatycznie.','item_label':'Paczka kuriera','reward':30,'placements':[{'location_id':'hacker_hideout','slot':'A'}]}]},body.language)
     validate_jobs(plan);record_request({'model':'mock','language':body.language,'purpose':'session_jobs'},sent=False)
     result={'plan':plan,'provider':'mock','call_id':cid,'generation':'fresh-session','language':body.language,'validation':{'valid':True,'errors':[]}}
     session.session_jobs=result;store.update(cid,quest_type='SESSION_JOBS',validated_plan=plan,response_json=plan,validation=result['validation'],execution=replay_jobs(plan,[]));store.finish(cid,reply=json.dumps(plan,ensure_ascii=False));return result
    if not settings.director_allow_paid_requests or not settings.allow_paid_requests:raise ValueError('Generowanie nowych zleceń jest wyłączone.')
    async with lock:
     used=json.loads(ledger.read_text())['calls'] if ledger.exists() else 0
     if used>=settings.session_jobs_global_limit:raise ValueError('Limit generacji zleceń z konfiguracji został wykorzystany. Nie zresetowano licznika.')
     ledger.parent.mkdir(parents=True,exist_ok=True);tmp=ledger.with_suffix('.pending.json');tmp.write_text(json.dumps({'calls':used+1}));tmp.replace(ledger)
    payload={'model':settings.model,'messages':[{'role':'developer','content':
       'You are the Chess Corp Game Director. Return strict JSON only. Generate TWO genuinely different short collectible errands for a fresh game run. '
       'Use ids job_a and job_b. Vary titles, fiction, items, locations and amounts between sessions; the unique run nonce is inspiration, not code. '
       'Do not repeat the starter badge quest, rat bounties or the generic lost data package. Invent concrete cyberpunk items and motivations. '
       'Each job rewards 15..45 credits automatically after collecting its 1..2 objects. The ENGINE grants rewards, never dialogue. '
       'Use only listed location_id/slot pairs, unique across both jobs; no free coordinates, code, expressions, extra objectives or invented NPCs. '
       f'Keep descriptions honest about automatic completion. All displayed text MUST be in {body.language}. Locations: street, bar, hacker hideout, corporate lobby.'},
       {'role':'user','content':json.dumps({'run_nonce':body.session_id+'-'+uuid.uuid4().hex,'approved_slots':POINTS})}],
       'max_completion_tokens':1600,'reasoning_effort':'minimal','response_format':{'type':'json_schema','json_schema':{'name':'ChessCorpSessionJobs','strict':True,'schema':JobPlan.model_json_schema()}}}
    provider=MetaProvider(settings.model_copy(update={'allow_paid_requests':True}),app.state.asset_generator.client)
    async with asyncio.timeout(settings.timeout):raw=await provider.complete(payload)
    plan=JobPlan.model_validate_json(raw).model_dump();validate_jobs(plan)
    result={'plan':plan,'provider':'meta','call_id':cid,'generation':'fresh-session','language':body.language,'validation':{'valid':True,'errors':[]}}
    session.session_jobs=result;store.update(cid,quest_type='SESSION_JOBS',validated_plan=plan,response_json=plan,validation=result['validation'],execution=replay_jobs(plan,[]));store.finish(cid,reply=raw)
    return result
   except asyncio.CancelledError:store.finish(cid,error='Przerwane zlecenia sesji.',status=499);raise
   except Exception as error:
    store.update(cid,validation={'valid':False,'errors':[str(error)[:180]]});store.finish(cid,error='Nowe zlecenia nie zostały zastosowane.',status=502)
    return JSONResponse(status_code=502,content={'detail':'Nie udało się wygenerować poprawnych nowych zleceń. Bez automatycznego ponowienia.','call_id':cid})
   finally:active_call.reset(token)
 @app.post('/api/director/jobs/execution')
 async def execution(body:JobExecution):
  async with app.state.history.turn(body.session_id) as session:
   result=session.session_jobs
   if not result or result['call_id']!=body.call_id:raise HTTPException(404,'Nieznane zlecenia tej sesji.')
   events=[e.model_dump() for e in body.events]
   if events[:len(session.session_job_events)]!=session.session_job_events:raise HTTPException(409,'Nie można cofać wykonania.')
   try:state=replay_jobs(result['plan'],events)
   except ValueError:raise HTTPException(422,'Nieprawidłowe zbieranie przedmiotów.')
   session.session_job_events=events;store.update(body.call_id,execution={**state,'source':'client_events_replayed'})
   return {'execution':state}
