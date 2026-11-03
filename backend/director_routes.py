"""One validated plan per in-memory game session; no automatic retries."""
import asyncio
import json
from fastapi.responses import JSONResponse
from backend.director_models import DirectorRequest, load_rules, parse_plan, validate_scene, ExecutionRequest
from backend.inspector import active_call
from backend.providers import ProviderError
from backend.history import SessionCapacityError


def register_director(app, settings, store):
    rules, scene = load_rules()

    @app.post('/api/director')
    async def generate(body: DirectorRequest):
        if body.context.quest_status != 'completed' or not body.context.has_badge:
            return JSONResponse(status_code=409, content={'detail': 'Najpierw ukończ pierwszy quest.'})
        try:
            async with app.state.history.turn(body.session_id) as session:
                if session.director_result:
                    return {**session.director_result, 'cached': True}
                if session.director_error and not body.retry:
                    return JSONResponse(**session.director_error)
                call_id = store.start(body, settings.director_mode, settings.model, kind='director')
                token = active_call.set((store, call_id))
                stage = 'generation'
                try:
                    async with asyncio.timeout(settings.timeout):
                        raw = await app.state.director.generate(body, rules)
                        stage = 'validation'
                        store.update(call_id, reply=raw[:16000] if isinstance(raw, str) else None)
                        if isinstance(raw, str) and len(raw) <= 16000:
                            try:
                                store.update(call_id, response_json=json.loads(raw))
                            except (ValueError, RecursionError):
                                pass
                        plan = parse_plan(raw)
                        validate_scene(plan, rules, scene)
                    result = {'plan': plan.model_dump(), 'provider': settings.director_mode,
                              'validation': {'valid': True, 'errors': []}, 'call_id': call_id, 'cached': False}
                    store.update(call_id, validation=result['validation'], validated_plan=result['plan'],
                                 quest_type=result['plan'].get('quest_type','COLLECT'),
                                 execution={'status':'active','progress':0,'mistakes':0,'attempts':0,'events':0,'source':'client_events_replayed'})
                    store.finish(call_id, reply=raw)
                    session.director_result = result
                    session.director_error = None
                    return result
                except asyncio.CancelledError:
                    store.finish(call_id, error='Przerwane żądanie.', status=499)
                    raise
                except Exception as error:
                    if isinstance(error, (ValueError, RecursionError)):
                        status, message = 422, 'Director zwrócił nieprawidłowy plan. Nic nie zmieniono. G: ponów.'
                    elif isinstance(error, ProviderError):
                        status, message = error.status_code, error.public_message
                    elif isinstance(error, TimeoutError):
                        status, message = 504, 'Director nie odpowiedział na czas. G: ponów.'
                    else:
                        status, message = 500, 'Błąd Directora. Nic nie zmieniono. G: ponów.'
                    store.update(call_id, validation={'valid': False, 'stage': stage, 'errors': [message]})
                    store.finish(call_id, error=message, status=status)
                    # Cache failures under the same lock, so concurrent requests cannot silently retry.
                    session.director_error = {'status_code': status, 'content': {'detail': message}}
                    return JSONResponse(**session.director_error)
                finally:
                    active_call.reset(token)
        except SessionCapacityError:
            return JSONResponse(status_code=503, content={'detail': 'Osiągnięto limit sesji. Spróbuj później.'})


    @app.post('/api/director/execution')
    async def execution(body: ExecutionRequest):
        from game.director_contract import objects_for_plan, initial_execution, execute_event
        try:
            async with app.state.history.turn(body.session_id) as session:
                result=session.director_result
                if not result or result['call_id']!=body.call_id:
                    return JSONResponse(status_code=404,content={'detail':'Brak planu tej sesji.'})
                events=[event.model_dump() for event in body.events]
                previous=session.director_execution_events
                if events[:len(previous)]!=previous:
                    return JSONResponse(status_code=409,content={'detail':'Nie można zmieniać historii wykonania.'})
                plan=result['plan'];objects=objects_for_plan(plan,scene,rules)
                state=initial_execution()
                try:
                    for event in events: state=execute_event(state,plan,objects,event,scene)
                except ValueError:
                    return JSONResponse(status_code=422,content={'detail':'Nieprawidłowy przebieg zadania.'})
                session.director_execution_events=events
                summary={**state,'events':len(events),'source':'client_events_replayed'}
                store.update(body.call_id,execution=summary)
                return {'execution':summary}
        except SessionCapacityError:
            return JSONResponse(status_code=503,content={'detail':'Osiągnięto limit sesji.'})
