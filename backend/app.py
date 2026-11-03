import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.settings import Settings
from backend.inspector import CallStore, active_call
from backend.admin_routes import register_inspector
from backend.models import ChatRequest, ChatResponse
from backend.history import MemoryHistory, SessionCapacityError
from backend.providers import MockProvider, MetaProvider, ProviderError


def create_app(settings=None, provider=None, repository=None, director_provider=None):
    settings = settings or Settings.from_env()
    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(follow_redirects=False, trust_env=False) as client:
            app.state.provider = provider or (MockProvider() if settings.mode=='mock' else MetaProvider(settings,client))
            from backend.director import MockDirector, MetaDirector
            app.state.director = director_provider or (MockDirector(settings) if settings.director_mode=="mock" else MetaDirector(settings,client))
            yield
    app = FastAPI(title='Chess Corp Buddy API', lifespan=lifespan)
    app.state.history = repository or MemoryHistory(settings.history_pairs, settings.max_sessions, settings.session_ttl)
    app.state.settings = settings
    store=CallStore(secrets=(settings.api_key.get_secret_value(),settings.inspector_token.get_secret_value()))
    app.state.inspector=store
    register_inspector(app,settings,store)
    from backend.director_routes import register_director
    register_director(app,settings,store)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc):
        return JSONResponse(status_code=422,content={'detail':'Nieprawidłowe dane rozmowy (sesja, NPC, język lub długość wiadomości).'})

    @app.get('/health')
    async def health():
        return {'status':'ok', 'mode':settings.mode}

    @app.post('/api/chat', response_model=ChatResponse)
    async def chat(body: ChatRequest):
        call_id=None
        trace_token=None
        try:
            async with asyncio.timeout(settings.timeout+1):
                async with app.state.history.turn(body.session_id) as session:
                    call_id=store.start(body,settings.mode,settings.model)
                    trace_token=active_call.set((store,call_id))
                    reply = await app.state.provider.reply(body,list(session.messages))
                    store.finish(call_id,reply=reply)
                    app.state.history.append(session,body.message,reply)
                    return ChatResponse(session_id=body.session_id, reply=reply,provider=settings.mode,history=list(session.messages))
        except ProviderError as error:
            store.finish(call_id,error=error.public_message,status=error.status_code)
            return JSONResponse(status_code=error.status_code,content={'detail':error.public_message})
        except TimeoutError:
            store.finish(call_id,error='Przekroczony czas odpowiedzi.',status=504)
            return JSONResponse(status_code=504,content={'detail':'Buddy nie odpowiedział na czas. Spróbuj ponownie.'})
        except SessionCapacityError:
            store.finish(call_id,error='Osiągnięto limit sesji.',status=503)
            return JSONResponse(status_code=503,content={'detail':'Buddy ma teraz zbyt wiele rozmów. Spróbuj później.'})
        except asyncio.CancelledError:
            store.finish(call_id,error='Przerwane żądanie.',status=499)
            raise
        except Exception:
            store.finish(call_id,error='Wewnętrzny błąd rozmowy.',status=500)
            return JSONResponse(status_code=500,content={'detail':'Rozmowa jest chwilowo niedostępna. Możesz kontynuować grę.'})
        finally:
            if trace_token is not None:
                active_call.reset(trace_token)
    return app

app = create_app()
