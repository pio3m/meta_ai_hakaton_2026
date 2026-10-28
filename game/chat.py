import asyncio
import json
import os
import sys
import uuid

MAX_MESSAGE = 600

async def send_chat(payload):
    if sys.platform == 'emscripten':
        import platform
        request_id = str(platform.window.chessCorpChatSend(json.dumps(payload,ensure_ascii=True)))
        for _ in range(800):
            result = str(platform.window.chessCorpChatPoll(request_id))
            if result:
                return json.loads(result)
            await asyncio.sleep(0.05)
        return {'error':'Buddy nie odpowiedział na czas. Spróbuj ponownie.'}
    # Native desktop: urllib runs on a worker, never inside the frame loop.
    return await asyncio.to_thread(_native_request,payload)

def _native_request(payload):
    import urllib.request
    import urllib.error
    url = os.getenv('CHESS_CORP_API_URL','http://127.0.0.1:8080').rstrip('/')+'/api/chat'
    request = urllib.request.Request(url,data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json'})
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
        self.transport = transport
        self.open = False
        self.text = ''
        self.cursor = 0
        self.language = 'pl'
        self.history = []
        self.task = None
        self.error = ''
        self.provider = ''
        self.scroll = 0
        self.last_message = ''

    @property
    def pending(self):
        return self.task is not None

    def insert(self,text):
        text = ''.join(c for c in text if c.isprintable())
        text = text[:MAX_MESSAGE-len(self.text)]
        self.text = self.text[:self.cursor]+text+self.text[self.cursor:]
        self.cursor += len(text)

    def submit(self,quest):
        if self.pending or not self.text.strip():
            return
        message = self.text.strip()
        payload = {'session_id':self.session_id,'npc_id':'buddy','message':message,'language':self.language,
                   'context':{'quest_id':quest.data['id'],'quest_status':'completed' if quest.complete else 'in_progress' if quest.index else 'not_started',
                              'has_badge':'employee_badge' in quest.inventory}}
        self.error = ''
        self.last_message = message
        self.text = ''
        self.cursor = 0
        self.history.append({'role':'user','content':message})
        self.history = self.history[-20:]
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
                if isinstance(history,list) and all(isinstance(m,dict) and m.get('role') in ('user','assistant') and isinstance(m.get('content'),str) for m in history):
                    self.history = [{'role':m['role'],'content':m['content'][:2000]} for m in history[-20:]]
                else:
                    self.history.append({'role':'assistant','content':reply[:2000]})
                self.provider = 'mock' if data.get('provider')=='mock' else 'Meta'
        except (Exception, asyncio.CancelledError):
            self.error = 'Nie udało się odczytać odpowiedzi. Spróbuj ponownie.'
        finally:
            self.task = None

    def cancel(self):
        if self.task:
            self.task.cancel()
            self.task = None
