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

class HistoryRepository(Protocol):
    def turn(self, session_id: str) -> AsyncContextManager[Session]: ...
    def append(self, session: Session, message: str, reply: str) -> None: ...

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
            self.sessions[session_id] = Session(deque(maxlen=self.pairs*2), now)
        session = self.sessions[session_id]
        self.sessions.move_to_end(session_id)
        session.users += 1
        try:
            async with session.lock:
                yield session
        finally:
            session.updated_at = self.clock()
            session.users -= 1

    def append(self, session, message, reply):
        session.messages.extend([Message(role='user', content=message), Message(role='assistant', content=reply)])
