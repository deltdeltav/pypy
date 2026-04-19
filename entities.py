import pygame, math
from settings import *
from engine import to_iso, draw_health_bar

class Projectile:
    def __init__(self, x, y, target, dmg, color, p_type, tower_range, tower_pos):
        self.x, self.y = x, y
        self.target = target
        self.dmg = dmg
        self.color = color
        self.p_type = p_type
        self.speed = 12
        self.active = True
        self.tower_range = tower_range * TILE_W
        self.tower_pos = tower_pos  # (x, y) башни для расчёта радиуса

    def update(self, enemies):
        if not self.active: return
        
        # Если цель мертва — ищем новую в зоне полёта
        if not self.target or self.target.hp <= 0:
            new_target = None
            for e in enemies:
                if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 40:
                    new_target = e
                    break
            if new_target:
                self.target = new_target
            # Если новой цели нет — проверяем, не улетел ли снаряд за радиус башни
            elif math.hypot(self.x - self.tower_pos[0], self.y - self.tower_pos[1]) > self.tower_range + 50:
                self.active = False
                return

        if not self.target:
            self.active = False
            return
            
        dx, dy = self.target.screen_x - self.x, self.target.screen_y - self.y
        dist = math.hypot(dx, dy)
        
        # Попадание
        if dist < self.speed + 5:
            if self.p_type == 'aoe':
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 50:
                        e.take_damage(self.dmg)
            else:
                self.target.take_damage(self.dmg)
            self.active = False
        else:
            self.x += (dx/dist) * self.speed
            self.y += (dy/dist) * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 5)
        if self.p_type == 'sniper':
            pygame.draw.line(screen, self.color, (int(self.tower_pos[0]), int(self.tower_pos[1])), (int(self.x), int(self.y)), 1)

class Tower:
    def __init__(self, c, r, key):
        self.c, self.r = c, r
        self.data = UNITS.get(key, SHOP_UNITS.get(key, UNITS['soldier']))
        self.cd = 0
        self.angle = 0
        self.screen_x, self.screen_y = 0, 0
        self.dmg_mult = 1.0 + (global_upgrades['dmg'] * 0.15)
        self.rate_mult = 1.0 + (global_upgrades['rate'] * 0.1)

    def update(self, enemies, projectiles, cam_x, cam_y):
        self.screen_x, self.screen_y = to_iso(self.c, self.r, cam_x, cam_y)
        self.screen_y -= 5
        if self.data['type'] == 'trap': return
        if self.cd > 0: self.cd -= 1; return

        target = None
        range_px = self.data['range'] * TILE_W
        for e in enemies:
            dist = math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y)
            if dist < range_px:
                target = e
                self.angle = math.atan2(e.screen_y - self.screen_y, e.screen_x - self.screen_x)
                break

        if target:
            self.cd = int(self.data['rate'] / self.rate_mult)
            final_dmg = int(self.data['dmg'] * self.dmg_mult)
            
            if self.data['type'] == 'aoe':
                for e in enemies:
                    if math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 40:
                        e.take_damage(final_dmg)
            elif self.data['type'] == 'projectile':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'sniper', self.data['range'], (self.screen_x, self.screen_y)))
            elif self.data['type'] == 'beam':
                target.take_damage(final_dmg)
            else:
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'single', self.data['range'], (self.screen_x, self.screen_y)))

    def draw(self, screen):
        x, y = self.screen_x, self.screen_y
        base_h = 15
        pygame.draw.polygon(screen, (35,35,45), [(x-12,y), (x+12,y), (x+10,y-base_h), (x-10,y-base_h)])
        pygame.draw.polygon(screen, (50,50,60), [(x-10,y-base_h), (x+10,y-base_h), (x+8,y-base_h-4), (x-8,y-base_h-4)])
        gx = x + math.cos(self.angle) * 18
        gy = y - base_h + math.sin(self.angle) * 18
        pygame.draw.line(screen, self.data['color'], (x, y-base_h), (gx, gy), 5)

class Enemy:
    def __init__(self, path, type_key, wave_mult=1.0, is_boss=False, boss_lvl=0):
        self.path = path; self.idx = 0; self.progress = 0; self.summon_timer = 0
        if is_boss:
            s = BOSS_STATS[boss_lvl]
            self.hp, self.max_hp = s['hp'], s['hp']
            self.speed, self.reward = s['speed'], s['reward']
            self.crystals, self.color = s['crystals'], s['color']
            self.scale, self.summons = s['scale'], s['summons']
        else:
            s = ENEMIES[type_key]
            self.hp = s['hp'] * wave_mult; self.max_hp = self.hp
            self.speed, self.reward = s['speed'], s['reward']
            self.crystals, self.color = 0, s['color']
            self.scale, self.summons = 1.0, False
        self.c, self.r = path[0]
        self.screen_x, self.screen_y = 0, 0

    def move(self, grid_map):
        if self.idx >= len(self.path) - 1: return True
        self.progress += self.speed
        if self.progress >= 1.0:
            self.progress = 0.0; self.idx += 1
            self.c, self.r = self.path[self.idx]
            if 0 <= self.r < len(grid_map) and 0 <= self.c < len(grid_map[0]):
                if grid_map[self.r][self.c] == 2:
                    self.hp -= 500; grid_map[self.r][self.c] = 1
        return False

    def take_damage(self, amt): self.hp -= amt
    def is_dead(self): return self.hp <= 0

    def update_pos(self, cam_x, cam_y):
        nc, nr = self.path[min(self.idx+1, len(self.path)-1)]
        curr_c = self.c + (nc-self.c)*self.progress
        curr_r = self.r + (nr-self.r)*self.progress
        self.screen_x, self.screen_y = to_iso(curr_c, curr_r, cam_x, cam_y)
        self.screen_y -= 15 * self.scale
        if self.summons and self.hp > 0:
            self.summon_timer += 1
            if self.summon_timer > 180:
                self.summon_timer = 0
                return 'spawn'
        return None

    def draw(self, screen):
        x, y = self.screen_x, self.screen_y
        size = int(16 * self.scale)
        pygame.draw.ellipse(screen, (0,0,0,90), (x-size, y+size, size*2, size))
        pygame.draw.rect(screen, self.color, (x-size//2, y-size, size, size*1.5))
        draw_health_bar(screen, x, y-size-8, size*2, self.hp, self.max_hp)
