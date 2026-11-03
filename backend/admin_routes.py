"""Local-owner login and a separate expiring, single-session jury capability."""
from collections import deque
from hashlib import sha256
from pathlib import Path
import secrets
from time import monotonic
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ASSETS = Path(__file__).parent/'admin'
OWNER_COOKIE = 'chess_inspector_owner'
JURY_COOKIE = 'chess_inspector_jury'

class Login(BaseModel):
    token: str = Field(min_length=20,max_length=256)

class Access:
    def __init__(self, token, clock=monotonic):
        self.token, self.clock = token, clock
        self.owners = {}
        self.attempts = deque(maxlen=20)
        self.demo = None

    def throttle(self):
        now = self.clock()
        while self.attempts and now-self.attempts[0]>=60:
            self.attempts.popleft()
        if len(self.attempts)>=20:
            raise HTTPException(429,'Zbyt wiele prób. Odczekaj minutę.')
        self.attempts.append(now)

    def login(self, token):
        self.throttle()
        if not self.token:
            raise HTTPException(503,'Ustaw ADMIN_TOKEN w lokalnym .env.')
        if not secrets.compare_digest(token.encode(),self.token.encode()):
            raise HTTPException(401,'Nieprawidłowy token.')
        now = self.clock()
        self.owners = {k:v for k,v in self.owners.items() if v>now}
        if len(self.owners)>=100:
            self.owners.pop(next(iter(self.owners)))
        session = 'owner_'+secrets.token_urlsafe(32)
        self.owners[sha256(session.encode()).hexdigest()] = now+8*3600
        return session

    def owner(self, request: Request):
        cookie = request.cookies.get(OWNER_COOKIE,'')
        if self.owners.get(sha256(cookie.encode()).hexdigest(),0)<=self.clock():
            raise HTTPException(401,'Zaloguj się do panelu właściciela.')

    def new_demo(self):
        token = 'jury_'+secrets.token_urlsafe(32)
        session_id = 'demo_'+secrets.token_hex(16)
        self.demo = dict(token_hash=sha256(token.encode()).hexdigest(),session_id=session_id,expires=self.clock()+1800)
        return dict(jury_token=token,game_url='/?demo_session='+session_id,jury_url='/admin/jury',expires_in_seconds=1800)

    def jury_session(self, token):
        if not self.demo or self.demo['expires']<=self.clock() or not secrets.compare_digest(sha256(token.encode()).hexdigest(),self.demo['token_hash']):
            raise HTTPException(401,'Dostęp jury wygasł lub został cofnięty.')
        return self.demo['session_id']


def register_inspector(app,settings,store):
    access = Access(settings.inspector_token.get_secret_value())
    app.state.inspector_access = access
    router = APIRouter(prefix='/admin',include_in_schema=False)

    @app.middleware('http')
    async def admin_security(request,call_next):
        if request.url.path.startswith('/admin'):
            origin=request.headers.get('origin')
            expected=str(request.base_url).rstrip('/')
            if request.method not in ('GET','HEAD','OPTIONS') and origin and origin!=expected:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=403,content={'detail':'Niedozwolone źródło żądania.'},headers={'Cache-Control':'no-store'})
        response=await call_next(request)
        if request.url.path.startswith('/admin'):
            response.headers.update({'Cache-Control':'no-store','Referrer-Policy':'no-referrer',
                'X-Content-Type-Options':'nosniff','X-Frame-Options':'DENY',
                'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    @router.get('')
    @router.get('/')
    @router.get('/jury')
    async def page():
        return FileResponse(ASSETS/'index.html')

    @router.get('/assets/{name}')
    async def asset(name: str):
        if name not in ('inspector.css','inspector.js'):
            raise HTTPException(404)
        return FileResponse(ASSETS/name)

    @router.post('/api/login')
    async def login(body: Login,request: Request,response: Response):
        token=access.login(body.token)
        response.set_cookie(OWNER_COOKIE,token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=8*3600,path='/admin')
        return {'status':'ok'}

    @router.post('/api/logout',dependencies=[Depends(access.owner)])
    async def logout(request: Request,response: Response):
        access.owners.pop(sha256(request.cookies.get(OWNER_COOKIE,'').encode()).hexdigest(),None)
        response.delete_cookie(OWNER_COOKIE,path='/admin')
        return {'status':'ok'}

    @router.get('/api/calls',dependencies=[Depends(access.owner)])
    async def calls():
        return {'calls':store.list(),'limit':200,'mode':settings.mode,'director_mode':settings.director_mode}

    @router.get('/api/calls/{call_id}',dependencies=[Depends(access.owner)])
    async def detail(call_id: str):
        row=store.get(call_id)
        if row is None:
            raise HTTPException(404,'Wywołanie nie jest już w buforze.')
        return row

    @router.post('/api/demo',dependencies=[Depends(access.owner)])
    async def demo():
        return access.new_demo()

    @router.post('/api/demo/revoke',dependencies=[Depends(access.owner)])
    async def revoke():
        access.demo=None
        return {'status':'ok'}

    @router.post('/jury/api/login')
    async def jury_login(body: Login,request: Request,response: Response):
        access.throttle()
        access.jury_session(body.token)
        response.set_cookie(JURY_COOKIE,body.token,httponly=True,samesite='strict',secure=request.url.scheme=='https',max_age=1800,path='/admin/jury')
        return {'status':'ok'}

    @router.get('/jury/api/calls')
    async def jury_calls(request: Request):
        session_id=access.jury_session(request.cookies.get(JURY_COOKIE,''))
        return {'calls':store.list(session_id=session_id,jury=True),'limit':200,'mode':settings.mode,'director_mode':settings.director_mode}

    @router.post('/jury/api/logout')
    async def jury_logout(response: Response):
        response.delete_cookie(JURY_COOKIE,path='/admin/jury')
        return {'status':'ok'}

    app.include_router(router)
