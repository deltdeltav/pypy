import pygame
import random
import math

class Particle:
    def __init__(self, x, y, color, speed, life, size):
        self.x, self.y = x, y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size *= 0.96

    def draw(self, screen):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            screen.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = str(text)
        self.color = color
        self.life = 40
        self.vy = -1.5
        self.font = pygame.font.SysFont('consolas', 18, bold=True)

    def update(self):
        self.y += self.vy
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            surf = self.font.render(self.text, True, self.color)
            screen.blit(surf, (self.x - surf.get_width()//2, self.y))

class Lightning:
    def __init__(self, x1, y1, x2, y2, color, life=6):
        self.segments = []
        steps = 5
        for i in range(steps):
            t1, t2 = i/steps, (i+1)/steps
            x1_j = x1 + (x2-x1)*t1 + random.uniform(-6, 6)
            y1_j = y1 + (y2-y1)*t1 + random.uniform(-6, 6)
            x2_j = x1 + (x2-x1)*t2 + random.uniform(-6, 6)
            y2_j = y1 + (y2-y1)*t2 + random.uniform(-6, 6)
            self.segments.append(((x1_j, y1_j), (x2_j, y2_j)))
        self.color = color
        self.life = life

    def draw(self, screen):
        if self.life > 0:
            for p1, p2 in self.segments:
                pygame.draw.line(screen, self.color, p1, p2, 3)
            self.life -= 1

class TargetZone:
    def __init__(self, x, y, radius, life=60):
        self.x, self.y = x, y
        self.radius = radius
        self.life = life
        self.max_life = life

    def update(self):
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 150)
            s = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 0, alpha), (self.radius, self.radius), self.radius, 3)
            pygame.draw.line(s, (255, 0, 0, alpha), (0, self.radius), (self.radius*2, self.radius), 2)
            pygame.draw.line(s, (255, 0, 0, alpha), (self.radius, 0), (self.radius, self.radius*2), 2)
            screen.blit(s, (int(self.x - self.radius), int(self.y - self.radius)))

class DelayedStrike:
    def __init__(self, x, y, dmg, enemies_list, delay=60):
        self.x, self.y = x, y
        self.dmg = dmg
        self.enemies_list = enemies_list
        self.delay = delay
        self.active = True

    def update(self, fx):
        self.delay -= 1
        if self.delay <= 0 and self.active:
            self.active = False
            for e in self.enemies_list:
                if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 80:
                    e.take_damage(self.dmg, fx)
            fx.spawn_explosion(self.x, self.y, (255, 255, 255), count=50)
            fx.add_shake(15)
            return True
        return False

    def draw(self, screen):
        if self.delay <= 10 and self.active:
             for i in range(-40, 41, 10):
                 start_y = -100
                 end_y = self.y
                 start_x = self.x + i
                 pygame.draw.line(screen, (255, 50, 50, 150), (start_x, start_y), (start_x + (i*0.1), end_y), 4)

class EffectsManager:
    def __init__(self):
        self.particles = []
        self.texts = []
        self.lightnings = []
        self.target_zones = []
        self.delayed_strikes = []
        self.shake = 0
        self.shake_decay = 0.9

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, random.uniform(1, 5), random.randint(20, 40), random.randint(3, 8)))

    def spawn_flame_stream(self, x1, y1, x2, y2):
        steps = 5
        for i in range(steps):
            t = i / steps
            px = x1 + (x2 - x1) * t + random.uniform(-5, 5)
            py = y1 + (y2 - y1) * t + random.uniform(-5, 5)
            r, g = 255, random.randint(100, 200)
            self.particles.append(Particle(px, py, (r, g, 0), random.uniform(1, 3), random.randint(10, 20), random.randint(3, 6)))

    def spawn_damage(self, x, y, dmg):
        self.texts.append(FloatingText(x, y, f"-{dmg}", (255, 255, 255)))

    def spawn_gold_sparks(self, x, y, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, (255, 215, 0), random.uniform(1, 3), random.randint(10, 20), random.randint(2, 4)))

    def spawn_lightning(self, x1, y1, x2, y2, color=(100, 220, 255), life=6):
        self.lightnings.append(Lightning(x1, y1, x2, y2, color, life))

    def spawn_target_zone(self, x, y, radius):
        self.target_zones.append(TargetZone(x, y, radius))

    def add_delayed_strike(self, x, y, dmg, enemies_list):
        self.delayed_strikes.append(DelayedStrike(x, y, dmg, enemies_list))

    def add_shake(self, amount):
        self.shake = max(self.shake, amount)

    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        self.texts = [t for t in self.texts if t.life > 0]
        self.lightnings = [l for l in self.lightnings if l.life > 0]
        self.target_zones = [z for z in self.target_zones if z.life > 0]
        
        for strike in self.delayed_strikes[:]:
            if strike.update(self):
                self.delayed_strikes.remove(strike)

        for p in self.particles: p.update()
        for t in self.texts: t.update()
        for z in self.target_zones: z.update()
        
        if self.shake > 0.5: self.shake *= self.shake_decay
        else: self.shake = 0

    def draw(self, screen):
        for z in self.target_zones: z.draw(screen)
        for p in self.particles: p.draw(screen)
        for t in self.texts: t.draw(screen)
        for l in self.lightnings: l.draw(screen)
        for strike in self.delayed_strikes: strike.draw(screen)

    def get_shake_offset(self):
        if self.shake > 0:
            return random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)
        return 0, 0
