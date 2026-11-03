"""Closed data contracts and deterministic puzzle rules, shared by API and WASM."""
from math import dist, isfinite
import copy

KINDS = ('COLLECT', 'SEQUENCE', 'LOGIC_PUZZLE')
TERMINALS = ('terminal_a', 'terminal_b', 'terminal_c')
SLOTS = ('west_side', 'center_side', 'east_side')
TEMPLATES = ('SUM', 'DIFFERENCE', 'NEXT_NUMBER')


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Nieprawidłowe pola planu')


def text(value, maximum, minimum=3):
    if not isinstance(value, str) or not minimum <= len(value) <= maximum or not value.isprintable():
        raise ValueError('Nieprawidłowy tekst')


def quest_kind(plan):
    return 'COLLECT' if plan['schema_version'] == 1 else plan['quest_type']


def validate_contract(plan):
    if not isinstance(plan, dict) or type(plan.get('schema_version')) is not int:
        raise ValueError('Nieprawidłowa wersja')
    version = plan['schema_version']
    if version == 1:
        keys(plan, ['schema_version', 'create_quest', 'place_object'])
        placements = [plan['place_object']]
        kind = 'COLLECT'
    elif version == 2:
        keys(plan, ['schema_version', 'quest_type', 'create_quest', 'place_objects', 'sequence', 'puzzle'])
        kind = plan['quest_type']
        if kind not in KINDS or not isinstance(plan['place_objects'], list):
            raise ValueError('Nieprawidłowy typ zadania')
        placements = plan['place_objects']
        if not isinstance(plan['sequence'], list): raise ValueError('Nieprawidłowa sekwencja')
        if kind == 'SEQUENCE':
            if len(plan['sequence']) != 3 or any(not isinstance(x, str) for x in plan['sequence']) or set(plan['sequence']) != set(TERMINALS):
                raise ValueError('Sekwencja musi być permutacją trzech terminali')
        elif plan['sequence']:
            raise ValueError('Sekwencja nie dotyczy tego typu')
        if kind == 'LOGIC_PUZZLE':
            p = plan['puzzle']
            keys(p, ['template', 'a', 'b', 'flavor'])
            if p['template'] not in TEMPLATES or type(p['a']) is not int or type(p['b']) is not int:
                raise ValueError('Nieprawidłowy szablon zagadki')
            if not 1 <= p['a'] <= 20 or not 1 <= p['b'] <= 9 or (p['template'] == 'DIFFERENCE' and p['a'] < p['b']):
                raise ValueError('Parametry zagadki poza zakresem')
            text(p['flavor'], 100)
        elif plan['puzzle'] is not None:
            raise ValueError('Zagadka nie dotyczy tego typu')
    else:
        raise ValueError('Nieobsługiwana wersja schematu')
    create = plan['create_quest']
    keys(create, ['action', 'quest'])
    if create['action'] != 'create_quest': raise ValueError('Niedozwolona akcja')
    q = create['quest']
    keys(q, ['id', 'title', 'description', 'objective', 'completion_message', 'completion'])
    if q['id'] != 'director_delivery': raise ValueError('Nieprawidłowe ID zadania')
    for field, limit in [('title',64),('description',240),('objective',100),('completion_message',160)]: text(q[field], limit)
    condition = {'COLLECT': ('collect_object','director_package'), 'SEQUENCE': ('activate_sequence','terminals'), 'LOGIC_PUZZLE': ('solve_puzzle','puzzle_terminal')}[kind]
    if q['completion'] != {'type':condition[0], 'target':condition[1]}: raise ValueError('Niespójny warunek ukończenia')
    expected_ids = set(TERMINALS) if kind == 'SEQUENCE' else {'director_package' if kind == 'COLLECT' else 'puzzle_terminal'}
    if len(placements) != len(expected_ids): raise ValueError('Nieprawidłowa liczba obiektów')
    ids, slots = [], []
    for obj in placements:
        keys(obj, ['action','id','label','spawn_point','appearance'])
        if obj['action'] != 'place_object': raise ValueError('Niedozwolona akcja obiektu')
        text(obj['label'],40)
        if obj['id'] not in expected_ids or obj['spawn_point'] not in (('east_side','west_side') if version == 1 else SLOTS): raise ValueError('Nieprawidłowy obiekt lub miejsce')
        if obj['appearance'] != ('data_chip' if kind == 'COLLECT' else 'terminal'): raise ValueError('Nieprawidłowy wygląd')
        ids.append(obj['id']);slots.append(obj['spawn_point'])
    if len(set(ids)) != len(ids) or set(ids) != expected_ids or len(set(slots)) != len(slots): raise ValueError('Powtórzone ID lub miejsca')
    return placements


def objects_for_plan(plan, scene, rules):
    placements = validate_contract(plan)
    result = []
    radius = rules['interaction_radius']
    for obj in placements:
        position = rules['spawn_points'][obj['spawn_point']]
        x,y = position; left,top,right,bottom = scene['walkable_bounds']
        if not left+24 <= x <= right-24 or not top <= y <= bottom: raise ValueError('Obiekt poza obszarem ruchu')
        if any(a-24 <= x <= c+24 and b-12 <= y <= d+12 for a,b,c,d in scene.get('blocked_areas',[])): raise ValueError('Obiekt zablokowany')
        if any(dist(position,e['position']) < e['interaction_radius']+radius+12 for e in scene['entities']): raise ValueError('Kolizja ze starą interakcją')
        if any(dist(position,e['position']) < 2*radius+12 for e in result): raise ValueError('Kolizja nowych interakcji')
        result.append({'id':obj['id'],'label':obj['label'],'position':list(position),'interaction_radius':radius})
    return result


def puzzle_question(p):
    a,b = p['a'],p['b']
    question = f'Ile wynosi {a} + {b}?' if p['template']=='SUM' else f'Ile wynosi {a} - {b}?' if p['template']=='DIFFERENCE' else f'Podaj następną liczbę: {a}, {a+b}, {a+2*b}, ? (stały przyrost).'
    return p['flavor']+' '+question


def puzzle_answer(p):
    return p['a']+p['b'] if p['template']=='SUM' else p['a']-p['b'] if p['template']=='DIFFERENCE' else p['a']+3*p['b']


def initial_execution():
    return {'status':'active','progress':0,'mistakes':0,'attempts':0,'message':''}


def execute_event(state, plan, objects, event, scene):
    """Pure transition: no network, LLM, inventory or scene mutation."""
    keys(event, ['action','object_id','position','answer'])
    if event['action'] not in ('interact','answer') or not isinstance(event['answer'],str) or len(event['answer'])>32: raise ValueError('Nieprawidłowa próba')
    pos=event['position']
    if not isinstance(pos,list) or len(pos)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in pos): raise ValueError('Nieprawidłowa pozycja')
    l,t,r,b=scene['walkable_bounds']
    if not l<=pos[0]<=r or not t<=pos[1]<=b: raise ValueError('Gracz poza sceną')
    obj=next((o for o in objects if o['id']==event['object_id']),None)
    if obj is None or dist(pos,obj['position'])>obj['interaction_radius']: raise ValueError('Obiekt poza zasięgiem')
    result=copy.deepcopy(state)
    if result['status']=='completed': return result
    kind=quest_kind(plan)
    if kind=='COLLECT':
        if event['action']!='interact' or event['answer']: raise ValueError('Nieprawidłowa akcja COLLECT')
        result.update(status='completed',progress=1,message='Nośnik odebrany.')
    elif kind=='SEQUENCE':
        if event['action']!='interact' or event['answer']: raise ValueError('Nieprawidłowa akcja SEQUENCE')
        result['attempts']+=1
        if event['object_id']==plan['sequence'][result['progress']]:
            result['progress']+=1;result['message']=f"Terminal zatwierdzony: {result['progress']}/3."
            if result['progress']==3: result['status']='completed'
        else:
            result['progress']=0;result['mistakes']+=1;result['message']='Błędna kolejność. Sekwencja wyzerowana — zacznij od początku.'
    else:
        if event['action']!='answer': raise ValueError('Zagadka wymaga odpowiedzi')
        result['attempts']+=1
        answer=event['answer'].strip()
        if answer and answer.isascii() and answer.isdecimal() and int(answer)==puzzle_answer(plan['puzzle']):
            result.update(status='completed',progress=1,message='Poprawna odpowiedź.')
        else:
            result['mistakes']+=1;result['message']='Błędna odpowiedź. Spróbuj ponownie; wpisz samą liczbę.'
    return result
