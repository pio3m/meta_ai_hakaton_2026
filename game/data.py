import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def read_json(name):
    with (ROOT / 'content' / name).open(encoding='utf-8-sig') as stream:
        return json.load(stream)

def load_content():
    scene = read_json('scene.json')
    quest = read_json('quest_first_day.json')
    dialogues = read_json('dialogues.json')
    bounds = scene['walkable_bounds']
    if len(bounds) != 4 or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        raise ValueError('Invalid walkable bounds')
    ids = [e['id'] for e in scene['entities']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate entity id')
    for e in scene['entities']:
        if e['interaction_radius'] <= 0 or len(e['position']) != 2:
            raise ValueError('Invalid interaction entity')
    for step in quest['steps']:
        if step['target'] not in ids or step['id'] not in dialogues:
            raise ValueError('Unresolved quest reference')
        if not dialogues[step['id']]['lines']:
            raise ValueError('Empty dialogue')
    if not (ROOT / scene['background']).is_file():
        raise ValueError('Background missing')
    return scene, quest, dialogues
