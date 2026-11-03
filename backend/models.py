from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class DirectorContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Literal['director_delivery']
    title: str = Field(min_length=3,max_length=64)
    objective: str = Field(min_length=3,max_length=100)
    status: Literal['active','completed']
    quest_type: Literal['COLLECT','SEQUENCE','LOGIC_PUZZLE'] = 'COLLECT'

class GameContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    quest_id: Literal['first_day'] = 'first_day'
    quest_status: Literal['not_started', 'in_progress', 'completed'] = 'not_started'
    has_badge: bool = False
    director_quest: DirectorContext | None = None

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    npc_id: Literal['buddy'] = 'buddy'
    message: str = Field(min_length=1, max_length=600)
    language: Literal['pl', 'en'] = 'pl'
    context: GameContext = Field(default_factory=GameContext)

    @field_validator('message')
    @classmethod
    def nonblank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Message cannot be empty')
        return value

class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str

class ChatResponse(BaseModel):
    session_id: str
    npc_id: Literal['buddy'] = 'buddy'
    reply: str
    status: Literal['ok'] = 'ok'
    provider: Literal['mock', 'meta']
    history: list[Message]
