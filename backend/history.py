import asyncio
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from time import monotonic
from typing import AsyncContextManager, Protocol
from backend.models import Message

class SessionCapacityError(Exception):
    pass

@dataclass
class Session:
    messages: deque
    updated_at: float
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    users: int = 0
    director_result: dict | None = None
    director_error: dict | None = None
    director_execution_events: list = field(default_factory=list)
    world_revision: int = 0
    world_result: dict | None = None
    world_paid_calls: int = 0
    world_last_started: float | None = None
    model_messages: deque = field(default_factory=deque)
    npc_threads: dict = field(default_factory=dict)
    session_jobs: dict | None = None
    session_jobs_attempted: bool = False
    session_job_events: list = field(default_factory=list)

class HistoryRepository(Protocol):
    def turn(self, session_id: str) -> AsyncContextManager[Session]: ...
    def append(self, session: Session, message: str, reply: str, *, for_model: bool = True) -> None: ...

class MemoryHistory:
    def __init__(self, pairs=10, max_sessions=100, ttl=3600, clock=monotonic):
        self.pairs, self.max_sessions, self.ttl = pairs, max_sessions, ttl
        self.clock = clock
        self.sessions = OrderedDict()

    @asynccontextmanager
    async def turn(self, session_id):
        now = self.clock()
        for key, session in list(self.sessions.items()):
            if not session.users and now-session.updated_at > self.ttl:
                del self.sessions[key]
        if session_id not in self.sessions:
            if len(self.sessions) >= self.max_sessions:
                victim = next((key for key,s in self.sessions.items() if not s.users), None)
                if victim is None:
                    raise SessionCapacityError()
                del self.sessions[victim]
            self.sessions[session_id] = Session(deque(maxlen=self.pairs*2), now, model_messages=deque(maxlen=self.pairs*2))
        session = self.sessions[session_id]
        self.sessions.move_to_end(session_id)
        session.users += 1
        try:
            async with session.lock:
                yield session
        finally:
            session.updated_at = self.clock()
            session.users -= 1

    def append(self, session, message, reply, *, for_model=True):
        pair=[Message(role='user', content=message), Message(role='assistant', content=reply)]
        session.messages.extend(pair)
        if for_model: session.model_messages.extend(pair)
