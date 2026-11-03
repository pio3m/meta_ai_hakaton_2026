"""Only data: a closed schema and scene-aware validation for Director plans."""
import json
from pathlib import Path
from typing import Literal
from math import dist
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from backend.models import GameContext

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid',strict=True,str_strip_whitespace=True)

class CompletionCondition(StrictModel):
    type: Literal['collect_object']
    target: Literal['director_package']

class GeneratedQuest(StrictModel):
    id: Literal['director_delivery']
    title: str = Field(min_length=3,max_length=64)
    description: str = Field(min_length=3,max_length=240)
    objective: str = Field(min_length=3,max_length=100)
    completion_message: str = Field(min_length=3,max_length=160)
    completion: CompletionCondition

class CreateQuest(StrictModel):
    action: Literal['create_quest']
    quest: GeneratedQuest

class PlaceObject(StrictModel):
    action: Literal['place_object']
    id: Literal['director_package']
    label: str = Field(min_length=3,max_length=40)
    spawn_point: Literal['east_side','west_side']
    appearance: Literal['data_chip']

class DirectorPlan(StrictModel):
    schema_version: Literal[1]
    create_quest: CreateQuest
    place_object: PlaceObject

    @field_validator('schema_version',mode='before')
    @classmethod
    def version_type(cls,value):
        if type(value) is not int: raise ValueError('Invalid version type')
        return value

    @model_validator(mode='after')
    def links(self):
        if type(self.schema_version) is not int:
            raise ValueError('Invalid schema version')
        if self.create_quest.quest.completion.target != self.place_object.id:
            raise ValueError('Completion target missing')
        texts=[self.create_quest.quest.title,self.create_quest.quest.description,self.create_quest.quest.objective,
               self.create_quest.quest.completion_message,self.place_object.label]
        if any(not text.isprintable() for text in texts):
            raise ValueError('Control characters not allowed')
        return self

class DirectorRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    scene_id: Literal['corporate_street'] = 'corporate_street'
    language: Literal['pl','en'] = 'pl'
    context: GameContext
    retry: bool = Field(default=False,strict=True)
    mock_type: Literal['COLLECT','SEQUENCE','LOGIC_PUZZLE'] | None = None

    @property
    def npc_id(self): return 'game_director'

    @property
    def message(self): return 'Wygeneruj pierwszy dynamiczny quest po ukończeniu pierwszego dnia.'


def load_rules():
    root=Path(__file__).resolve().parent.parent
    return (json.loads((root/'content/director_rules.json').read_text(encoding='utf-8-sig')),
            json.loads((root/'content/scene.json').read_text(encoding='utf-8-sig')))


def validate_scene(plan, rules, scene):
    if rules['allowed_actions']!=['create_quest','place_object']:
        raise ValueError('Invalid server action configuration')
    if plan.schema_version==2:
        from game.director_contract import objects_for_plan
        return objects_for_plan(plan.model_dump(),scene,rules)
    position=rules['spawn_points'][plan.place_object.spawn_point]
    left,top,right,bottom=scene['walkable_bounds']
    x,y=position
    if not left+24<=x<=right-24 or not top<=y<=bottom:
        raise ValueError('Spawn outside walkable area')
    if any(a-24<=x<=c+24 and b-12<=y<=d+12 for a,b,c,d in scene.get('blocked_areas',[])):
        raise ValueError('Blocked spawn point')
    if any(dist(position,e['position'])<e['interaction_radius']+rules['interaction_radius']+12 for e in scene['entities']):
        raise ValueError('Spawn conflicts with existing interaction')
    return {'id':plan.place_object.id,'type':'collectible','label':plan.place_object.label,
            'position':position,'appearance':plan.place_object.appearance,'interaction_radius':rules['interaction_radius']}


def parse_plan(raw):
    if not isinstance(raw,str) or len(raw)>16000:
        raise ValueError('Invalid JSON length')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    value=json.loads(raw,object_pairs_hook=unique)
    if not isinstance(value,dict) or type(value.get("schema_version")) is not int: raise ValueError("Invalid version")
    if value["schema_version"]==1: return DirectorPlan.model_validate(value)
    if value["schema_version"]==2: return DirectorPlanV2.model_validate(value)
    raise ValueError("Unsupported schema version")


class CompletionV2(StrictModel):
    type: Literal['collect_object','activate_sequence','solve_puzzle']
    target: Literal['director_package','terminals','puzzle_terminal']

class QuestV2(GeneratedQuest):
    completion: CompletionV2

class CreateQuestV2(StrictModel):
    action: Literal['create_quest']
    quest: QuestV2

class ObjectV2(StrictModel):
    action: Literal['place_object']
    id: Literal['director_package','terminal_a','terminal_b','terminal_c','puzzle_terminal']
    label: str = Field(min_length=3,max_length=40)
    spawn_point: Literal['west_side','center_side','east_side']
    appearance: Literal['data_chip','terminal']

class PuzzleSpec(StrictModel):
    template: Literal['SUM','DIFFERENCE','NEXT_NUMBER']
    a: int = Field(ge=1,le=20)
    b: int = Field(ge=1,le=9)
    flavor: str = Field(min_length=3,max_length=100)

class DirectorPlanV2(StrictModel):
    schema_version: Literal[2]
    quest_type: Literal['COLLECT','SEQUENCE','LOGIC_PUZZLE']
    create_quest: CreateQuestV2
    place_objects: list[ObjectV2] = Field(min_length=1,max_length=3)
    sequence: list[Literal['terminal_a','terminal_b','terminal_c']] = Field(max_length=3)
    puzzle: PuzzleSpec | None

    @field_validator('schema_version',mode='before')
    @classmethod
    def version_type(cls,value):
        if type(value) is not int: raise ValueError('Invalid version type')
        return value

    @model_validator(mode='after')
    def contract(self):
        from game.director_contract import validate_contract
        validate_contract(self.model_dump())
        return self


class ExecutionEvent(StrictModel):
    action: Literal['interact','answer']
    object_id: Literal['director_package','terminal_a','terminal_b','terminal_c','puzzle_terminal']
    position: list[float] = Field(min_length=2,max_length=2)
    answer: str = Field(max_length=32)

    @field_validator('position',mode='before')
    @classmethod
    def coordinates(cls,value):
        from math import isfinite
        if not isinstance(value,list) or len(value)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in value):
            raise ValueError('Invalid position')
        return value

class ExecutionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    session_id: str = Field(min_length=8,max_length=80,pattern=r'^[a-zA-Z0-9_-]+$')
    call_id: str = Field(pattern=r'^[a-f0-9]{32}$')
    events: list[ExecutionEvent] = Field(min_length=1,max_length=100)
