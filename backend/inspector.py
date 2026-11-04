"""Bounded, process-local LLM call recorder. Never stores HTTP headers or keys."""
from collections import OrderedDict
from contextvars import ContextVar
from datetime import datetime, timezone
from time import monotonic
import copy
import base64
import re
import uuid

active_call = ContextVar('inspector_call', default=None)

class CallStore:
    def __init__(self, secrets=(), limit=200, clock=monotonic):
        raw_secrets=tuple(s for s in secrets if s)
        self.secrets=tuple(dict.fromkeys(raw_secrets+tuple(base64.b64encode(s.encode()).decode() for s in raw_secrets)+tuple(base64.urlsafe_b64encode(s.encode()).decode() for s in raw_secrets)))
        self.limit, self.clock = limit, clock
        self.calls = OrderedDict()
        self.world_states=OrderedDict()

    def clean(self, value):
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, '[REDACTED]')
            value = re.sub(r'(?i)Bearer\s+[^\s"\']+', 'Bearer [REDACTED]', value)
            value = re.sub(r'\b(?:owner_|jury_|admin_)[A-Za-z0-9_-]{20,}', '[REDACTED]', value)
            value = re.sub(r'(?i)\b(api[_-]?key|password|secret)\s*[:=]\s*[^\s,;]+', r'\1=[REDACTED]', value)
            return value
        if isinstance(value, (list,tuple)):
            return [self.clean(v) for v in value]
        if isinstance(value, dict):
            return {k: '[REDACTED]' if k.lower() in ('authorization','api_key','model_api_key','admin_token','cookie') else self.clean(v) for k,v in value.items()}
        return value

    def record_presence(self,session_id,snapshot):
        self.world_states.pop(session_id,None)
        self.world_states[session_id]=(self.clock(),self.clean(snapshot))
        while len(self.world_states)>100:self.world_states.popitem(last=False)

    def latest_presence(self,session_id=None):
        now=self.clock()
        for key,(updated,_) in list(self.world_states.items()):
            if now-updated>3600:self.world_states.pop(key,None)
        matches=[snapshot for key,(_,snapshot) in self.world_states.items() if session_id is None or key==session_id]
        return copy.deepcopy(matches[-1]) if matches else None

    def presentation_languages(self,session_id=None):
        # Infer provenance only from recorded, validated plans of this same session.
        self.latest_presence(session_id)
        if session_id is None and self.world_states:session_id=next(reversed(self.world_states))
        known={}
        def collect(value,lang):
            if isinstance(value,dict):
                for key,item in value.items():
                    if key in ('goal','summary','text') and isinstance(item,str) and item:
                        known.setdefault(item,set()).add(lang)
                        known.setdefault(item[:120],set()).add(lang)
                    elif isinstance(item,(dict,list)):collect(item,lang)
            elif isinstance(value,list):
                for item in value:collect(item,lang)
        for row in self.calls.values():
            if row['session_id']==session_id and row.get('validated_plan'):collect(row['validated_plan'],row.get('language','und'))
        return {text:next(iter(langs)) for text,langs in known.items() if len(langs)==1}

    def start(self, body, mode, model, kind="buddy"):
        call_id = uuid.uuid4().hex
        self.calls[call_id] = self.clean(dict(
            guard_status=None, guard=None, delivered_reply=None, kind=kind, quest_type=None, execution=None, validation=None, response_json=None, validated_plan=None, id=call_id, session_id=body.session_id, npc_id=body.npc_id,
            started_at=datetime.now(timezone.utc).isoformat(), state='pending',
            provider=mode, model=model if mode=='meta' else 'mock', requested_model=model if mode=='meta' else None,
            context=body.context.model_dump(), language=body.language, message=body.message,
            request_payload=None, sent_to_model=False, reply=None, usage=None,
            upstream_status=None, error=None, elapsed_ms=None, reply_truncated=False,
        ))
        self.calls[call_id]['_start'] = self.clock()
        while len(self.calls)>self.limit:
            self.calls.popitem(last=False)
        return call_id

    def update(self, call_id, **values):
        if call_id in self.calls:
            self.calls[call_id].update(self.clean(values))

    def finish(self, call_id, reply=None, error=None, status=None):
        if call_id not in self.calls:
            return
        row = self.calls[call_id]
        self.update(call_id, state='error' if error else 'ok', error=error,
                    http_status=status or (500 if error else 200),
                    elapsed_ms=round((self.clock()-row['_start'])*1000,2))
        if row['reply'] is None and reply is not None:
            self.update(call_id,reply=reply[:16000],reply_truncated=len(reply)>16000)

    def get(self, call_id):
        row = self.calls.get(call_id)
        return copy.deepcopy({k:v for k,v in row.items() if k!='_start'}) if row else None

    def list(self, session_id=None, jury=False):
        allowed = ('id','started_at','state','provider','model','message','reply','context','language',
                   'elapsed_ms','usage','error','sent_to_model','upstream_status','reply_truncated','kind','validation','validated_plan','quest_type','execution','guard_status','guard','delivered_reply','plan_source','world_limits','asset')
        # Project before copying so polling does not duplicate every full prompt.
        rows=[]
        for row in reversed(self.calls.values()):
            if session_id is not None and row['session_id']!=session_id: continue
            value=copy.deepcopy({k:v for k,v in row.items() if (k in allowed if jury else k not in ('_start','request_payload','response_json','validated_plan','fallback_plan'))})
            if jury and row.get('kind')=='buddy' and row.get('guard') is not None:
                value['reply']=row.get('delivered_reply')
                value['reply_truncated']=False
            if jury and row.get('kind') in ('director','world'):
                value['reply']='Plan zatwierdzony' if row.get('validation') and row['validation'].get('valid') else 'Brak zatwierdzonego planu'
            rows.append(value)
        return rows




def record_request(payload, sent=True):
    current = active_call.get()
    if current:
        store, call_id = current
        store.update(call_id, request_payload=payload, sent_to_model=sent)


def record_response(response):
    current = active_call.get()
    if not current:
        return
    store, call_id = current
    values = {}
    if isinstance(response.get('model'),str):
        values['model'] = response['model'][:120]
    usage = response.get('usage')
    if isinstance(usage,dict):
        usage = {k:v for k,v in usage.items() if k in ('prompt_tokens','completion_tokens','total_tokens') and isinstance(v,int) and not isinstance(v,bool) and v>=0}
        if usage:
            values['usage'] = usage
    try:
        reply = response['choices'][0]['message']['content']
        if isinstance(reply,str):
            values.update(reply=reply[:16000], reply_truncated=len(reply)>16000)
    except (KeyError,IndexError,TypeError):
        pass
    store.update(call_id,**values)


def record_status(status):
    current = active_call.get()
    if current:
        current[0].update(current[1],upstream_status=status)
