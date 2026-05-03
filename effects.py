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

class EffectsManager:
    def __init__(self):
        self.particles = []
        self.texts = []
        self.shake = 0
        self.shake_decay = 0.9

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, random.uniform(1, 5), random.randint(20, 40), random.randint(3, 8)))
    
    def spawn_gold_sparks(self, x, y, count=10):
        """Эффект золотых искр"""
        for _ in range(count):
            # Цвет золота: (255, 215, 0)
            self.particles.append(Particle(x, y, (255, 215, 0), random.uniform(1, 3), random.randint(10, 20), random.randint(2, 4)))
    
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

    def add_shake(self, amount):
        self.shake = max(self.shake, amount)

    def update(self):
        self.particles = [p for p in self.particles if p.life > 0]
        self.texts = [t for t in self.texts if t.life > 0]
        for p in self.particles: p.update()
        for t in self.texts: t.update()
        
        if self.shake > 0.5:
            self.shake *= self.shake_decay
        else:
            self.shake = 0

    def draw(self, screen):
        for p in self.particles: p.draw(screen)
        for t in self.texts: t.draw(screen)

    def get_shake_offset(self):
        if self.shake > 0:
            return random.uniform(-self.shake, self.shake), random.uniform(-self.shake, self.shake)
        return 0, 0
