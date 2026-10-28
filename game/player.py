from math import hypot

class Player:
    def __init__(self, position):
        self.x, self.y = map(float, position)
        self.facing_left = False
        self.animation = 0.0
        self.moving = False

    @property
    def position(self):
        return self.x, self.y

    def move(self, dx, dy, dt, world):
        length = hypot(dx, dy)
        self.moving = length > 0
        if not length:
            self.animation = 0
            return
        if dx:
            self.facing_left = dx < 0
        dt = min(max(dt, 0), 0.05)
        self.x, self.y = world.constrain(self.x, self.y, dx / length * 185 * dt, dy / length * 85 * dt)
        self.animation += dt * 8
