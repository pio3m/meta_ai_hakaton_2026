"""Pydantic boundary for batched World AI decisions and bounded telemetry."""
import json
from pathlib import Path
from typing import Literal,Annotated
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator,PrivateAttr
from game.world_contract import validate_world_plan,valid_position,parse_world_json

LocationId=Literal['corporate_street','bar','hacker_hideout','corporate_lobby']
NpcId=Literal['buddy','security','hacker','employee','bartender','merchant','bar_guest','hacker_woman','hacker_contact','receptionist','lobby_guard']
Location=Literal['buddy_post','buddy_left','buddy_right','security_gate','west_corner','center','badge_terminal','data_terminal','east_corner','bar_counter','bar_table','bar_door','bar_corner','bar_market','bar_storage','hack_terminal','archive_terminal','hack_door','hack_desk','reception','lobby_gate','lobby_door','corporate_terminal']
Target=Literal['none','player','buddy','security','hacker','employee','buddy_post','buddy_left','buddy_right','security_gate','west_corner','center','badge_terminal','data_terminal','east_corner','bar_counter','bar_table','bar_door','bar_corner','bar_market','bar_storage','hack_terminal','archive_terminal','hack_door','hack_desk','reception','lobby_gate','lobby_door','corporate_terminal','bartender','merchant','bar_guest','hacker_woman','hacker_contact','receptionist','lobby_guard']
ActionKind=Literal['MOVE_TO','PATROL','WAIT','TALK_TO','INSPECT_TERMINAL','REACT_TO_PLAYER']
Mood=Literal['calm','alert','curious','ambitious','suspicious']
Text120=Annotated[str,Field(max_length=120)]
Text140=Annotated[str,Field(max_length=140)]


def load_world_data(location_id='corporate_street'):
    root=Path(__file__).resolve().parent.parent/'content'
    if location_id!='corporate_street':
        room=json.loads((root/'locations.json').read_text(encoding='utf-8-sig'))['locations'][location_id]
        return room,room
    return json.loads((root/'world_ai.json').read_text(encoding='utf-8-sig')),json.loads((root/'scene.json').read_text(encoding='utf-8-sig'))


class Closed(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)

class WorldAction(Closed):
    action:ActionKind
    target_id:Target
    route:list[Location]=Field(max_length=3)
    duration_s:int=Field(ge=2,le=15)
    text:str=Field(max_length=90)

class NpcDecision(Closed):
    npc_id:NpcId
    goal:str=Field(min_length=3,max_length=100)
    mood:Mood
    actions:list[WorldAction]=Field(min_length=1,max_length=3)

class WorldPlan(Closed):
    schema_version:Literal[1]
    summary:str=Field(min_length=3,max_length=160)
    decisions:list[NpcDecision]=Field(min_length=4,max_length=4)

    @field_validator('schema_version',mode='before')
    @classmethod
    def version(cls,value):
        if type(value) is not int:raise ValueError('Invalid world version')
        return value

    @model_validator(mode='after')
    def contract(self):
        validate_world_plan(self.model_dump(),*load_world_data())
        return self

class WorldPlanV2(Closed):
    schema_version:Literal[2]
    location_id:LocationId
    summary:str=Field(min_length=3,max_length=160)
    decisions:list[NpcDecision]=Field(min_length=1,max_length=4)

    @field_validator('schema_version',mode='before')
    @classmethod
    def version(cls,value):
        if type(value) is not int:raise ValueError('Invalid world version')
        return value

    @model_validator(mode='after')
    def contract(self):
        validate_world_plan(self.model_dump(),*load_world_data(self.location_id))
        return self

class NpcSnapshot(Closed):
    npc_id:NpcId
    source:Literal['META','MOCK','FALLBACK']
    position:list[float]=Field(min_length=2,max_length=2)
    state:ActionKind
    goal:str=Field(min_length=3,max_length=100)
    mood:Mood
    memory:list[Text120]=Field(max_length=6)

    @model_validator(mode='after')
    def location(self):valid_position(self.position,load_world_data()[1]);return self

class AssetReference(Closed):
    id:str=Field(min_length=1,max_length=40,pattern=r'^[a-zA-Z0-9_-]+$')
    source:Literal['ORIGINAL','META']
    model:str=Field(default='',max_length=120)

class EnemySnapshot(Closed):
    id:str=Field(pattern=r'^rat-[01]-[0-4]$')
    position:list[float]=Field(min_length=2,max_length=2)
    hp:int=Field(ge=0,le=3)
    max_hp:int=Field(ge=2,le=3)
    @model_validator(mode='after')
    def valid(self):
        valid_position(self.position,load_world_data()[1])
        if self.hp>self.max_hp:raise ValueError('Enemy hp exceeds max')
        return self

class GameplaySnapshot(Closed):
    health:int=Field(ge=0,le=125)
    max_health:int=Field(ge=100,le=125)
    credits:int=Field(ge=0,le=1000)
    medkits:int=Field(ge=0,le=4)
    weapon_upgrade:bool
    armor:bool
    bounty_state:Literal['available','active','ready','claimed']
    contract_index:int=Field(ge=-1,le=1)
    kills:int=Field(ge=0,le=5)
    target:int=Field(ge=0,le=5)
    claimed_contracts:list[Literal[0,1]]=Field(max_length=2)
    enemies:list[EnemySnapshot]=Field(max_length=5)
    events:list[Text140]=Field(max_length=8)
    @model_validator(mode='after')
    def consistent(self):
        if self.health>self.max_health or self.kills>self.target:raise ValueError('Inconsistent gameplay counters')
        if len({e.id for e in self.enemies})!=len(self.enemies):raise ValueError('Duplicate enemies')
        return self

class WorldSnapshot(Closed):
    gameplay:GameplaySnapshot | None = None
    asset_sources:list[AssetReference]=Field(default_factory=list,max_length=8)
    location_id:LocationId='corporate_street'
    journey_events:list[Text140]=Field(default_factory=list,max_length=8)
    player_position:list[float]=Field(min_length=2,max_length=2)
    first_quest_complete:bool
    npcs:list[NpcSnapshot]=Field(min_length=1,max_length=4)
    events:list[Text140]=Field(max_length=8)

    @model_validator(mode='after')
    def world(self):
        valid_position(self.player_position,load_world_data()[1])
        rules,scene=load_world_data(self.location_id)
        if {n.npc_id for n in self.npcs}!={n['id'] for n in rules['npcs']} or len({n.npc_id for n in self.npcs})!=len(self.npcs):raise ValueError('Invalid snapshot NPCs for location')
        for n in self.npcs:
            if self.location_id=='corporate_street' and not self.first_quest_complete and n.npc_id=='buddy' and not 515<=n.position[0]<=565:raise ValueError('Buddy outside quest zone')
        return self

class WorldRequest(Closed):
    _language:str=PrivateAttr(default="pl")
    session_id:str=Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    revision:int=Field(ge=1,le=1000)
    reason:Literal['event','interval']
    snapshot:WorldSnapshot

    @property
    def npc_id(self):return 'world_director'
    @property
    def language(self):return self._language
    @property
    def message(self):return f'World AI / runda {self.revision} / {self.reason}'
    @property
    def context(self):return self.snapshot

class CompletedAction(Closed):
    npc_id:NpcId
    action:ActionKind
    target_id:Target
    status:Literal['completed','expired']
    source:Literal['META','MOCK','FALLBACK']
    plan_id:Annotated[str,Field(max_length=32)]|None

class WorldPresenceRequest(Closed):
    session_id:str=Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    snapshot:WorldSnapshot

class WorldExecutionRequest(Closed):
    session_id:str=Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    call_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    snapshot:WorldSnapshot
    completed_actions:list[CompletedAction]=Field(max_length=24)


def parse_world_plan(raw):
    value=parse_world_json(raw)
    return (WorldPlanV2 if value.get('schema_version')==2 else WorldPlan).model_validate(value)
