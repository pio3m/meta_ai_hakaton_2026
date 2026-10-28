import asyncio
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from backend.settings import Settings
from backend.models import ChatRequest, ChatResponse
from backend.history import MemoryHistory, SessionCapacityError
from backend.providers import MockProvider, MetaProvider, ProviderError


def create_app(settings=None, provider=None, repository=None):
    settings = settings or Settings.from_env()
    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(follow_redirects=False, trust_env=False) as client:
            app.state.provider = provider or (MockProvider() if settings.mode=='mock' else MetaProvider(settings,client))
            yield
    app = FastAPI(title='Chess Corp Buddy API', lifespan=lifespan)
    app.state.history = repository or MemoryHistory(settings.history_pairs, settings.max_sessions, settings.session_ttl)
    app.state.settings = settings

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc):
        return JSONResponse(status_code=422,content={'detail':'Nieprawidłowe dane rozmowy (sesja, NPC, język lub długość wiadomości).'})

    @app.get('/health')
    async def health():
        return {'status':'ok', 'mode':settings.mode}

    @app.post('/api/chat', response_model=ChatResponse)
    async def chat(body: ChatRequest):
        try:
            async with asyncio.timeout(settings.timeout+1):
                async with app.state.history.turn(body.session_id) as session:
                    reply = await app.state.provider.reply(body,list(session.messages))
                    app.state.history.append(session,body.message,reply)
                    return ChatResponse(session_id=body.session_id, reply=reply,provider=settings.mode,history=list(session.messages))
        except ProviderError as error:
            return JSONResponse(status_code=error.status_code,content={'detail':error.public_message})
        except TimeoutError:
            return JSONResponse(status_code=504,content={'detail':'Buddy nie odpowiedział na czas. Spróbuj ponownie.'})
        except SessionCapacityError:
            return JSONResponse(status_code=503,content={'detail':'Buddy ma teraz zbyt wiele rozmów. Spróbuj później.'})
        except Exception:
            return JSONResponse(status_code=500,content={'detail':'Rozmowa jest chwilowo niedostępna. Możesz kontynuować grę.'})
    return app

app = create_app()
