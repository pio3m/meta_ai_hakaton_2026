from math import dist

def nearest_entity(position, entities, quest):
    target = 'buddy' if quest.complete else quest.current['target']
    candidates = [e for e in entities if e['id'] == target and dist(position, e['position']) <= e['interaction_radius']]
    return min(candidates, key=lambda e: dist(position, e['position']), default=None)

def interact(position, entities, quest):
    entity = nearest_entity(position, entities, quest)
    if entity is None:
        return None
    return 'complete' if quest.complete else quest.interact(entity['id'])


def conversation_entity(position, entities, quest):
    # Keep quest priority, but Buddy can still chat while the terminal is the goal.
    active = nearest_entity(position,entities,quest)
    if active:
        return active
    return next((e for e in entities if e['id']=='buddy' and dist(position,e['position']) <= e['interaction_radius']),None)
