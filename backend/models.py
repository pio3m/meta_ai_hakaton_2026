from typing import Literal,Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator

NpcId = Literal['buddy','security','hacker','employee','bartender','bar_guest','merchant','hacker_woman','hacker_contact','receptionist','lobby_guard']

class NpcContext(BaseModel):
    model_config=ConfigDict(extra='forbid')
    goal:str=Field(default='',max_length=100)
    mood:str=Field(default='',max_length=30)
    memory:list[Annotated[str,Field(max_length=120)]]=Field(default_factory=list,max_length=6)
    hostile:bool=False
    health:int=Field(default=24,ge=0,le=30)

class DirectorContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Literal['director_delivery']
    title: str = Field(min_length=3,max_length=64)
    objective: str = Field(min_length=3,max_length=100)
    status: Literal['active','completed']
    quest_type: Literal['COLLECT','SEQUENCE','LOGIC_PUZZLE'] = 'COLLECT'

class GameContext(BaseModel):
    model_config = ConfigDict(extra='forbid')
    location_id:Literal['corporate_street','bar','hacker_hideout','corporate_lobby']='corporate_street'
    npc:NpcContext | None=None
    credits:int=Field(default=0,ge=0,le=10000)
    quest_id: Literal['first_day'] = 'first_day'
    quest_status: Literal['not_started', 'in_progress', 'completed'] = 'not_started'
    has_badge: bool = False
    director_quest: DirectorContext | None = None

class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')
    npc_id: NpcId = 'buddy'
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
    npc_id: NpcId = 'buddy'
    reply: str
    status: Literal['ok'] = 'ok'
    provider: Literal['mock', 'meta', 'guard']
    guard_status: Literal['ALLOWED','OUT_OF_SCOPE','BLOCKED'] = 'ALLOWED'
    guard_reason: str = 'WORLD_DIALOGUE'
    history: list[Message]
