"""Shared closed action vocabulary. World decisions are data, never code."""
import json
from math import isfinite

STREET_NPC_IDS=('buddy','security','hacker','employee')
NPC_IDS=STREET_NPC_IDS+('bartender','merchant','bar_guest','hacker_woman','hacker_contact','receptionist','lobby_guard')
ACTIONS=('MOVE_TO','PATROL','WAIT','TALK_TO','INSPECT_TERMINAL','REACT_TO_PLAYER')
MOODS=('calm','alert','curious','ambitious','suspicious')
LOCATIONS=('buddy_post','buddy_left','buddy_right','security_gate','west_corner','center','badge_terminal','data_terminal','east_corner','bar_counter','bar_table','bar_door','bar_corner','bar_market','bar_storage','hack_terminal','archive_terminal','hack_door','hack_desk','reception','lobby_gate','lobby_door','corporate_terminal')


def exact(value,fields):
    if not isinstance(value,dict) or set(value)!=set(fields): raise ValueError('Unexpected world fields')


def short_text(value,limit,minimum=0):
    if not isinstance(value,str) or not minimum<=len(value)<=limit or (value and not value.isprintable()): raise ValueError('Invalid world text')


def valid_position(position,scene):
    if not isinstance(position,(list,tuple)) or len(position)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in position): raise ValueError('Invalid world position')
    x,y=position;l,t,r,b=scene['walkable_bounds']
    if not l<=x<=r or not t<=y<=b or any(a<=x<=c and z<=y<=d for a,z,c,d in scene.get('blocked_areas',[])): raise ValueError('World position outside scene')


def validate_world_plan(plan,rules,scene):
    version=plan.get('schema_version') if isinstance(plan,dict) else None
    if type(version) is not int or version not in (1,2):raise ValueError('Unsupported world schema')
    exact(plan,('schema_version','summary','decisions') if version==1 else ('schema_version','location_id','summary','decisions'))
    location_id=scene.get('id','corporate_street')
    if version==1 and location_id!='corporate_street':raise ValueError('Legacy world plans belong to the street')
    if version==2 and plan['location_id']!=location_id:raise ValueError('World plan location mismatch')
    expected={n['id'] for n in rules['npcs']}
    short_text(plan['summary'],160,3)
    decisions=plan['decisions']
    if not isinstance(decisions,list) or len(decisions)!=len(expected): raise ValueError('Plan needs all location NPCs')
    ids=[]
    for decision in decisions:
        exact(decision,('npc_id','goal','mood','actions'))
        if decision['npc_id'] not in expected or decision['mood'] not in MOODS: raise ValueError('Unknown NPC/mood')
        ids.append(decision['npc_id']);short_text(decision['goal'],100,3)
        actions=decision['actions']
        if not isinstance(actions,list) or not 1<=len(actions)<=3: raise ValueError('Invalid action count')
        for item in actions:
            exact(item,('action','target_id','route','duration_s','text'))
            kind=item['action'];target=item['target_id'];route=item['route']
            if kind not in ACTIONS or type(item['duration_s']) is not int or not 2<=item['duration_s']<=15: raise ValueError('Invalid action/duration')
            short_text(item['text'],90)
            if not isinstance(route,list): raise ValueError('Invalid patrol route')
            if kind=='PATROL':
                if target!='none' or not 2<=len(route)<=3 or any(p not in LOCATIONS for p in route) or len(set(route))!=len(route): raise ValueError('Invalid patrol')
            elif route: raise ValueError('Only patrol accepts a route')
            if kind=='MOVE_TO' and target not in LOCATIONS: raise ValueError('Invalid destination')
            if kind=='WAIT' and target!='none': raise ValueError('WAIT has no target')
            if kind=='TALK_TO' and (target not in expected or target==decision['npc_id'] or not item['text']): raise ValueError('Invalid conversation')
            if kind=='INSPECT_TERMINAL' and target not in rules['terminals']: raise ValueError('Invalid terminal')
            if kind=='REACT_TO_PLAYER' and (target!='player' or not item['text']): raise ValueError('Invalid player reaction')
            points=route if kind=='PATROL' else [target] if kind in ('MOVE_TO','INSPECT_TERMINAL') else []
            for point in points:
                if point not in rules['locations']:raise ValueError('Destination belongs to another location')
                valid_position(rules['locations'][point],scene)
    if set(ids)!=expected: raise ValueError('Duplicate NPC decisions')
    return plan


def action(kind,target='none',route=None,duration=6,text=''):
    return {'action':kind,'target_id':target,'route':route or [],'duration_s':duration,'text':text}


def local_world_plan(revision=1,rules=None,location_id='corporate_street'):
    """Identical vocabulary for the local mock/fallback. Never labels itself Meta."""
    if location_id!='corporate_street':
        if not rules:raise ValueError('Location rules required')
        return {'schema_version':2,'location_id':location_id,'summary':'Lokalny rytm: '+rules['name'],
                'decisions':[{'npc_id':n['id'],'goal':n['goal'],'mood':n['mood'],'actions':n['local_actions']} for n in rules['npcs']]}
    plans={
      'buddy':[action('PATROL',route=['buddy_left','buddy_right'],duration=6),action('REACT_TO_PLAYER','player',text='Spokojnie, rekrucie. Papierologia nie gryzie.',duration=4),action('WAIT',duration=3)],
      'security':[action('PATROL',route=['security_gate','east_corner'],duration=8),action('TALK_TO','hacker',text='Widzę cię. Od terminala trzy kroki wstecz.',duration=12),action('WAIT',duration=3)],
      'hacker':[action('INSPECT_TERMINAL','data_terminal',text='Ten terminal skrywa więcej niż raporty.',duration=13),action('TALK_TO','security',text='Ja tylko czytam regulamin. Bardzo dokładnie.',duration=6),action('MOVE_TO','west_corner',duration=12)],
      'employee':[action('MOVE_TO','center',duration=4),action('TALK_TO','buddy',text='Kto dziś zatwierdza awanse? Pytam dla kolegi.',duration=8),action('INSPECT_TERMINAL','badge_terminal',text='Raport gotowy. Teraz niech ktoś to doceni.',duration=8)]}
    moods=['calm','alert','curious','ambitious']
    goals=['Pomóc rekrutowi.','Utrzymać porządek.','Znaleźć trop danych.','Zasłużyć na awans.']
    return {'schema_version':1,'summary':'Lokalny rytm ulicy: patrol, dane i korporacyjne ambicje.',
            'decisions':[{'npc_id':n,'goal':goals[i],'mood':moods[i],'actions':plans[n]} for i,n in enumerate(STREET_NPC_IDS)]}


def parse_world_json(raw):
    if not isinstance(raw,str) or len(raw)>24000: raise ValueError('Invalid world response length')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result: raise ValueError('Duplicate world key')
            result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=unique)
