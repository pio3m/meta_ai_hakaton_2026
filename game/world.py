import copy

class World:
    def __init__(self, scene):
        self.bounds = scene['walkable_bounds']
        self.blocked = scene.get('blocked_areas', [])
        self.entities = copy.deepcopy(scene['entities'])

    def constrain(self, x, y, dx, dy):
        left, top, right, bottom = self.bounds
        nx = max(left, min(right, x + dx))
        ny = max(top, min(bottom, y + dy))
        def blocked(px, py):
            return any(a <= px <= c and b <= py <= d for a,b,c,d in self.blocked)
        if not blocked(nx, y):
            x = nx
        if not blocked(x, ny):
            y = ny
        return x, y
