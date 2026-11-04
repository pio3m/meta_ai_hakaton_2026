import asyncio
import json
import os
import sys
import uuid
from game.i18n import language

MAX_MESSAGE = 600

async def send_chat(payload):
    return await send_request(payload)

async def send_request(payload,path="/api/chat"):
    if path not in ("/api/chat","/api/director","/api/director/execution","/api/director/jobs","/api/director/jobs/execution","/api/assets/updates","/api/world/plan","/api/world/execution","/api/world/presence"): raise ValueError("Invalid endpoint")
    if sys.platform == 'emscripten':
        import platform
        request_id = str(platform.window.chessCorpRequestSend(json.dumps(payload,ensure_ascii=True),path))
        for _ in range(800):
            result = str(platform.window.chessCorpChatPoll(request_id))
            if result:
                return json.loads(result)
            await asyncio.sleep(0.05)
        return {'error':'Buddy nie odpowiedział na czas. Spróbuj ponownie.'}
    # Native desktop: urllib runs on a worker, never inside the frame loop.
    return await asyncio.to_thread(_native_request,payload,path)

def _native_request(payload,path="/api/chat"):
    import urllib.request
    import urllib.error
    url = os.getenv('CHESS_CORP_API_URL','http://127.0.0.1:8080').rstrip('/')+path
    request = urllib.request.Request(url,data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json','X-Chess-Language':language()})
    try:
        with urllib.request.urlopen(request,timeout=35) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return {'error':json.load(error).get('detail','Buddy jest chwilowo niedostępny.')}
        except (ValueError,AttributeError):
            return {'error':'Backend jest chwilowo niedostępny. Możesz kontynuować grę.'}
    except (OSError, ValueError):
        return {'error':'Brak połączenia z Buddy’m. Możesz kontynuować grę.'}

class Chat:
    def __init__(self,transport=send_chat):
        self.session_id = uuid.uuid4().hex
        if sys.platform == 'emscripten':
            import platform
            demo_session=str(platform.window.chessCorpDemoSession())
            if demo_session:
                self.session_id=demo_session
        self.npc_id='buddy';self.npc_name='Buddy';self.threads={}
        self.npc_context=None;self.location_id='corporate_street';self.credits=0
        self.transport = transport
        self.open = False
        self.text = ''
        self.cursor = 0
        self.language = language()
        self.history_languages=[];self.thread_languages={};self.pending_language=self.language
        self.history = []
        self.task = None
        self.error = ''
        self.provider = ''
        self.guard_status = ''
        self.scroll = 0
        self.last_message = ''

    def select_npc(self,actor,location_id,credits=0):
        if self.pending:return False
        self.threads[self.npc_id]=list(self.history)
        self.thread_languages[self.npc_id]=list(self.history_languages)
        self.npc_id=actor['id'];self.npc_name=actor['name'];self.location_id=location_id;self.credits=credits
        self.history=list(self.threads.get(self.npc_id,[]));self.history_languages=list(self.thread_languages.get(self.npc_id,[]));self.error='';self.text='';self.cursor=0;self.scroll=0
        self.npc_context={'goal':actor['goal'],'mood':actor['mood'],'memory':list(actor['memory'])[-6:],'hostile':bool(actor.get('hostile')),'health':actor.get('combat_hp',24)}
        self.open=True
        return True

    @property
    def pending(self):
        return self.task is not None

    def insert(self,text):
        text = ''.join(c for c in text if c.isprintable())
        text = text[:MAX_MESSAGE-len(self.text)]
        self.text = self.text[:self.cursor]+text+self.text[self.cursor:]
        self.cursor += len(text)

    def submit(self,quest,director_context=None):
        if self.pending or not self.text.strip():
            return
        message = self.text.strip()
        payload = {'session_id':self.session_id,'npc_id':self.npc_id,'message':message,'language':self.language,
                   'context':{'quest_id':quest.data['id'],'quest_status':'completed' if quest.complete else 'in_progress' if quest.index else 'not_started',
                              'has_badge':'employee_badge' in quest.inventory}}
        payload['context'].update(location_id=self.location_id,npc=self.npc_context,credits=self.credits)
        if director_context: payload['context']['director_quest']=director_context
        self.error = ''
        self.last_message = message
        self.text = ''
        self.cursor = 0
        self.pending_language=self.language
        self.history_languages.append(self.language)
        self.history.append({'role':'user','content':message})
        self.history = self.history[-20:]
        self.history_languages=self.history_languages[-20:]
        self.scroll = 0
        self.task = asyncio.create_task(self.transport(payload))

    def poll(self):
        if self.task is None or not self.task.done():
            return
        try:
            data = self.task.result()
            if data.get('error'):
                self.error = str(data['error'])[:300]
            else:
                reply = data.get('reply')
                history = data.get('history')
                if not isinstance(reply,str) or not reply.strip():
                    raise ValueError('Empty reply')
                sources={(m['role'],m['content']):self.history_languages[i] if i<len(self.history_languages) else 'und' for i,m in enumerate(self.history)}
                if isinstance(history,list) and all(isinstance(m,dict) and m.get('role') in ('user','assistant') and isinstance(m.get('content'),str) for m in history):
                    self.history = [{'role':m['role'],'content':m['content'][:2000]} for m in history[-20:]]
                else:
                    self.history.append({'role':'assistant','content':reply[:2000]})
                self.history_languages=[self.pending_language if m['role']=='assistant' and i==len(self.history)-1 else sources.get((m['role'],m['content']),'und') for i,m in enumerate(self.history)]
                self.provider = {'mock':'mock','meta':'Meta','guard':'Guard (lokalnie)'}.get(data.get('provider'),'Meta')
                self.guard_status = data.get('guard_status','ALLOWED')
        except (Exception, asyncio.CancelledError):
            self.error = 'Nie udało się odczytać odpowiedzi. Spróbuj ponownie.'
        finally:
            self.task = None

    def cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None
