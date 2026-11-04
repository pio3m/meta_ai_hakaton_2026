"""Batched World AI route. Invalid/slow/over-budget calls fall back locally."""
import asyncio
import json
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from backend.world_models import WorldRequest,WorldExecutionRequest,WorldPresenceRequest,load_world_data,parse_world_plan
from backend.world_ai import WorldBudget,world_payload
from backend.providers import ProviderError
from backend.history import SessionCapacityError
from backend.inspector import active_call
from game.world_contract import local_world_plan


def register_world(app,settings,store):
    budget=WorldBudget(settings);app.state.world_budget=budget

    @app.post('/api/world/plan')
    async def plan(body:WorldRequest,request:Request):
        body._language="en" if request.headers.get("X-Chess-Language")=="en" else "pl"
        try:
            async with app.state.history.turn(body.session_id) as session:
                rules,scene=load_world_data(body.snapshot.location_id)
                if body.revision==session.world_revision and session.world_result:
                    if session.world_result.get('location_id','corporate_street')!=body.snapshot.location_id:return JSONResponse(status_code=409,content={'detail':'World revision belongs to another location.'})
                    return {**session.world_result,'cached':True}
                if body.revision!=session.world_revision+1:return JSONResponse(status_code=409,content={'detail':'Invalid world revision.'})
                cid=store.start(body,settings.world_ai_mode,settings.model,kind='world');token=active_call.set((store,cid));reserved=None
                provider=settings.world_ai_mode;stage='budget'
                try:
                    if provider=='meta':reserved=await budget.reserve(session,world_payload(body,settings,rules))
                    else:
                        if session.world_revision>=settings.world_ai_session_limit:raise ProviderError(429,'WORLD_SESSION_LIMIT')
                    stage='generation'
                    async with asyncio.timeout(settings.timeout):raw=await app.state.world_provider.generate(body,rules)
                    stage='validation'
                    store.update(cid,reply=raw[:16000] if isinstance(raw,str) else None,reply_truncated=isinstance(raw,str) and len(raw)>16000)
                    try:store.update(cid,response_json=json.loads(raw))
                    except (ValueError,TypeError):pass
                    parsed=parse_world_plan(raw).model_dump()
                    from game.world_contract import validate_world_plan
                    validate_world_plan(parsed,rules,scene)
                    store.update(cid,validation={'valid':True,'errors':[]},validated_plan=parsed,plan_source=provider.upper())
                    store.finish(cid,reply=raw)
                    error=''
                except asyncio.CancelledError:
                    store.finish(cid,error='Przerwane World AI.',status=499);raise
                except Exception as exc:
                    from game.i18n import localize_plan
                    provider='fallback';parsed=localize_plan(local_world_plan(body.revision,rules,body.snapshot.location_id),body.language)
                    error=exc.public_message if isinstance(exc,ProviderError) else 'World AI timeout.' if isinstance(exc,TimeoutError) else 'World AI: nieprawidłowy plan.' if isinstance(exc,(ValueError,RecursionError)) else 'World AI chwilowo niedostępne.'
                    code=exc.status_code if isinstance(exc,ProviderError) else 504 if isinstance(exc,TimeoutError) else 422 if isinstance(exc,ValueError) else 500
                    validation_errors=[error]
                    if isinstance(exc,ValidationError):validation_errors=[{'path':'.'.join(map(str,e['loc'])),'message':e['msg'][:180]} for e in exc.errors(include_input=False,include_context=False)[:12]]
                    elif isinstance(exc,ValueError):validation_errors=[str(exc)[:180]]
                    store.update(cid,validation={'valid':False,'stage':stage,'errors':validation_errors},fallback_plan=parsed,plan_source='FALLBACK')
                    store.finish(cid,error=error,status=code)
                finally:
                    if reserved is not None:
                        row=store.get(cid)
                        await budget.settle(reserved,row.get('usage') if row else None)
                    active_call.reset(token)
                limits=budget.limits(session)
                if settings.world_ai_mode=='mock':limits['remaining_calls']=max(0,settings.world_ai_session_limit-body.revision)
                result={'location_id':body.snapshot.location_id,'plan':parsed,'provider':provider,'validation':{'valid':True,'errors':[]},'error_detail':error,'call_id':cid,'limits':limits,'cached':False,'language':body.language}
                session.world_revision=body.revision;session.world_result=result
                store.update(cid,world_limits=limits,execution={'source':'client_telemetry','completed_actions':[]})
                return result
        except SessionCapacityError:return JSONResponse(status_code=503,content={'detail':'World session capacity reached.'})

    @app.post('/api/world/presence')
    async def presence(body:WorldPresenceRequest):
        try:
            async with app.state.history.turn(body.session_id):
                store.record_presence(body.session_id,body.snapshot.model_dump())
                return {'status':'ok'}
        except SessionCapacityError:return JSONResponse(status_code=503,content={'detail':'World session capacity reached.'})

    @app.post('/api/world/execution')
    async def execution(body:WorldExecutionRequest):
        try:
            async with app.state.history.turn(body.session_id) as session:
                # NPCs keep executing their room's accepted plan after travelling.
                # Resolve the bounded trace by its own session/location, not only the newest revision.
                row=store.get(body.call_id)
                if not row or row.get('kind')!='world' or row.get('session_id')!=body.session_id or row.get('context',{}).get('location_id','corporate_street')!=body.snapshot.location_id:
                    return JSONResponse(status_code=404,content={'detail':'Unknown world plan for session.'})
                accepted=row.get('validated_plan') or row.get('fallback_plan')
                if not accepted:return JSONResponse(status_code=404,content={'detail':'Unknown world plan for session.'})
                result={'plan':accepted,'provider':row.get('plan_source','FALLBACK')}
                selected={(d['npc_id'],a['action'],a['target_id']) for d in accepted['decisions'] for a in d['actions']}
                observations=[a.model_dump() for a in body.completed_actions if a.plan_id==body.call_id]
                if any((a['npc_id'],a['action'],a['target_id']) not in selected or a['source']!=result['provider'].upper() for a in observations):
                    return JSONResponse(status_code=422,content={'detail':'Action does not belong to world plan.'})
                previous=store.get(body.call_id) or {}
                accumulated={(a['npc_id'],a['action'],a['target_id'],a['status']):a for a in (previous.get('execution') or {}).get('completed_actions',[])}
                accumulated.update({(a['npc_id'],a['action'],a['target_id'],a['status']):a for a in observations})
                value={'location_id':body.snapshot.location_id,'source':'client_telemetry','completed_actions':list(accumulated.values())[-24:],'npc_states':body.snapshot.model_dump()['npcs'],'recent_events':body.snapshot.events}
                store.update(body.call_id,execution=value)
                return {'execution':value}
        except SessionCapacityError:return JSONResponse(status_code=503,content={'detail':'World session capacity reached.'})
