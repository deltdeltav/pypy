import pygame, math, random
from settings import *
from engine import to_iso, draw_health_bar

class Projectile:
    def __init__(self, x, y, target, dmg, color, p_type, tower_range, tower_pos):
        self.x, self.y = x, y
        self.start_x, self.start_y = tower_pos 
        self.tower_range = tower_range * TILE_W
        self.dmg = dmg
        self.color = color
        self.p_type = p_type
        self.speed = 14
        self.active = True
        
        if target:
            dx = target.screen_x - x
            dy = target.screen_y - y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
            else:
                self.vx, self.vy = self.speed, 0
        else:
            self.vx, self.vy = self.speed, 0

    def update(self, enemies, fx):
        if not self.active: return
        self.x += self.vx
        self.y += self.vy
        dist_from_tower = math.hypot(self.x - self.start_x, self.y - self.start_y)
        if dist_from_tower > self.tower_range + 60:
            self.active = False
            return

        hit_enemy = None
        for e in enemies:
            if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 18:
                hit_enemy = e
                break

        if hit_enemy:
            if self.p_type == 'aoe' or self.p_type == 'missile':
                if self.p_type == 'missile': fx.spawn_explosion(self.x, self.y, self.color, count=25); fx.add_shake(4)
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 60: e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'nuke':
                fx.spawn_explosion(self.x, self.y, (255, 0, 0), count=50); fx.add_shake(15)
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 150: e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'strike':
                fx.spawn_explosion(self.x, self.y, (255, 255, 255), count=30); fx.add_shake(8)
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 80: e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'pierce':
                hit_enemy.take_damage(self.dmg, fx); fx.spawn_gold_sparks(self.x, self.y)
                self.dmg *= 0.8
                if self.dmg < 10: self.active = False
            
            elif self.p_type == 'drone':
                 hit_enemy.take_damage(self.dmg, fx); self.active = False
            
            else:
                hit_enemy.take_damage(self.dmg, fx); self.active = False

    def draw(self, screen):
        if self.p_type in ['missile', 'drone', 'sniper', 'single', 'railgun', 'nuke']:
             pygame.draw.line(screen, (*self.color, 150), (int(self.x-self.vx*2), int(self.y-self.vy*2)), (int(self.x), int(self.y)), 2)

        if self.p_type == 'railgun':
            pygame.draw.line(screen, (220, 255, 255), (int(self.x-self.vx*5), int(self.y-self.vy*5)), (int(self.x), int(self.y)), 5)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), 4)
        elif self.p_type == 'nuke':
            pygame.draw.circle(screen, (120, 0, 0), (int(self.x), int(self.y)), 9)
            pygame.draw.circle(screen, (255, 60, 0), (int(self.x), int(self.y)), 5)
            pygame.draw.circle(screen, (255, 200, 0), (int(self.x), int(self.y)), 2)
        elif self.p_type == 'drone':
            pts = [(self.x, self.y-5), (self.x-5, self.y+4), (self.x+5, self.y+4)]
            pygame.draw.polygon(screen, self.color, [(int(p[0]), int(p[1])) for p in pts])
        elif self.p_type == 'pierce':
            pts = [(self.x, self.y-7), (self.x+5, self.y), (self.x, self.y+7), (self.x-5, self.y)]
            pygame.draw.polygon(screen, self.color, [(int(p[0]), int(p[1])) for p in pts])
            pygame.draw.circle(screen, (255,255,255), (int(self.x), int(self.y)), 2)
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 5)

class Tower:
    def __init__(self, c, r, key):
        self.c, self.r = c, r
        self.data = UNITS.get(key, SHOP_UNITS.get(key, UNITS['soldier']))
        self.cd = 0
        self.angle = 0
        self.screen_x, self.screen_y = 0, 0
        self.dmg_mult = 1.0 + (global_upgrades['dmg'] * 0.15)
        self.rate_mult = 1.0 + (global_upgrades['rate'] * 0.1)

    def update_pos(self, cam_x, cam_y):
        self.screen_x, self.screen_y = to_iso(self.c, self.r, cam_x, cam_y)
        self.screen_y -= 5
        return None

    def update(self, enemies, projectiles, cam_x, cam_y, fx, screen, energy, dark_matter):
        self.screen_x, self.screen_y = to_iso(self.c, self.r, cam_x, cam_y)
        self.screen_y -= 5
        
        # --- ПРОВЕРКА РЕЖИМА ЗАРЯДА ---
        is_charging = self.data.get('charge', False)
        
        if is_charging:
            # РЕЖИМ НАКОПЛЕНИЯ
            if self.cd < self.data['rate']:
                self.cd += 1
                return 
            
            # ЕСЛИ ЗАРЯДИЛСЯ: Ищем цель и стреляем
            target = None
            range_px = self.data['range'] * TILE_W
            for e in enemies:
                dist = math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y)
                if dist < range_px:
                    target = e
                    self.angle = math.atan2(e.screen_y - self.screen_y, e.screen_x - self.screen_x)
                    break
            
            if target:
                self.fire(target, projectiles, fx, energy, dark_matter, enemies)
                self.cd = 0 # Сброс для начала нового цикла заряда
                
        else:
            # ОБЫЧНЫЙ РЕЖИМ
            if self.cd > 0: 
                self.cd -= 1
                return
            
            target = None
            range_px = self.data['range'] * TILE_W
            for e in enemies:
                dist = math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y)
                if dist < range_px:
                    target = e
                    self.angle = math.atan2(e.screen_y - self.screen_y, e.screen_x - self.screen_x)
                    break

            if target:
                self.fire(target, projectiles, fx, energy, dark_matter, enemies)
                # <<< ВАЖНО: Устанавливаем кулдаун для обычных башен >>>
                # Для обычных башен rate - это задержка между выстрелами
                self.cd = int(self.data['rate']) 

    def fire(self, target, projectiles, fx, energy, dark_matter, enemies_list):
        """Логика стрельбы. Кулдаун теперь ставится в update()"""
        final_dmg = int(self.data['dmg'] * self.dmg_mult)
        u_type = self.data['type']

        # --- ЛОГИКА СПЕЦИАЛЬНЫХ АТАК ---
        
        if u_type == 'slow': # FROST
            fx.spawn_flame_stream(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y)
            target.take_damage(final_dmg, fx)
            target.speed *= 0.5 
            
        elif u_type == 'chain': # TESLA
            energy_cost = 20
            if energy >= energy_cost:
                chain_targets = [target]
                for e in enemies_list:
                    if e != target and math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 70:
                        chain_targets.append(e)
                        if len(chain_targets) >= 4: break
                
                fx.spawn_lightning(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y)
                for i in range(1, len(chain_targets)):
                    prev = chain_targets[i-1]; curr = chain_targets[i]
                    fx.spawn_lightning(prev.screen_x, prev.screen_y, curr.screen_x, curr.screen_y)
                    curr.take_damage(final_dmg, fx)
            else: 
                fx.spawn_explosion(self.screen_x, self.screen_y-15, (100, 200, 255), count=3)
                    
        elif u_type == 'nuke':
            projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'nuke', self.data['range'], (self.screen_x, self.screen_y)))
            fx.add_shake(10)
            
        elif u_type == 'swarm':
            for _ in range(3):
                angle_var = self.angle + random.uniform(-0.2, 0.2)
                fake_target = type('obj', (object,), {'screen_x': self.screen_x + math.cos(angle_var)*100, 'screen_y': self.screen_y + math.sin(angle_var)*100})()
                projectiles.append(Projectile(self.screen_x, self.screen_y, fake_target, final_dmg, self.data['color'], 'drone', self.data['range'], (self.screen_x, self.screen_y)))

        elif u_type == 'pierce': # RAILGUN
            projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'pierce', self.data['range'], (self.screen_x, self.screen_y)))
            fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

        elif u_type == 'knockback': # CANNON
            target.take_damage(final_dmg, fx)
            fx.add_shake(5)
            fx.spawn_explosion(target.screen_x, target.screen_y, (150,150,150), count=10)

        elif u_type == 'heal':
            fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

        elif u_type == 'strike': # ORBITAL
            energy_cost = 50
            if energy >= energy_cost:
                fx.spawn_target_zone(target.screen_x, target.screen_y, self.data['range'] * TILE_W)
                fx.add_delayed_strike(target.screen_x, target.screen_y, final_dmg, enemies_list)
                fx.add_shake(10)
            else: 
                fx.spawn_explosion(self.screen_x, self.screen_y-15, (100, 200, 255), count=3)

        elif u_type == 'pull': # VOID
            dm_cost = 0.5
            if dark_matter >= dm_cost:
                fx.spawn_explosion(self.screen_x, self.screen_y, (80, 0, 150), count=3)
            else: 
                fx.spawn_explosion(self.screen_x, self.screen_y, (50, 50, 50), count=1)

        elif u_type == 'aoe' and self.data['name'].upper() == 'PYRO':
            fx.spawn_flame_stream(self.screen_x, self.screen_y - 15, target.screen_x, target.screen_y)
            for e in enemies_list:
                 if math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 45: 
                     e.take_damage(final_dmg, fx)
            
        elif u_type == 'beam': # LASER
            target.take_damage(final_dmg, fx)
            fx.add_shake(1.5)
            fx.spawn_lightning(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y, color=(255, 0, 255), life=6)

        elif u_type == 'missile':
            projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'missile', self.data['range'], (self.screen_x, self.screen_y)))
            fx.add_shake(3)
        
        elif u_type == 'projectile': # SNIPER
            projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'sniper', self.data['range'], (self.screen_x, self.screen_y)))
        
        else: # SOLDIER / SINGLE
            projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'single', self.data['range'], (self.screen_x, self.screen_y)))

    def draw(self, screen, energy_level=0, dark_matter_level=0):
        x, y = self.screen_x, self.screen_y
        u_type = self.data['type']
        name = self.data.get('name', '').upper() 
        
        base_pts = [(x-10, y), (x+10, y), (x+8, y-15), (x-8, y-15)]

        # --- ОТРИСОВКА БАШЕН ---
        if u_type == 'single' and name == 'SOLDIER':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (50, 200, 50), (x, y-15), 6)
            bx, by = x + math.cos(self.angle)*12, y-15 + math.sin(self.angle)*12
            pygame.draw.line(screen, (30, 30, 30), (x, y-15), (bx, by), 3)
            pygame.draw.circle(screen, (50, 255, 50), (int(bx), int(by)), 2)

        elif u_type == 'aoe' and name == 'PYRO':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.polygon(screen, (255, 100, 0), [(x-6,y-15), (x+6,y-15), (x+4,y-22), (x-4,y-22)])
            bx, by = x + math.cos(self.angle)*10, y-18 + math.sin(self.angle)*10
            pygame.draw.line(screen, (50, 50, 50), (x, y-18), (bx, by), 4)
            pygame.draw.circle(screen, (255, 200, 0), (int(bx), int(by)), 3)

        elif u_type == 'projectile' and name == 'SNIPER':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (50, 50, 200), (x, y-15), 5)
            bx, by = x + math.cos(self.angle)*18, y-15 + math.sin(self.angle)*18
            pygame.draw.line(screen, (20, 20, 20), (x, y-15), (bx, by), 2)
            pygame.draw.circle(screen, (100, 150, 255), (int(bx), int(by)), 2)

        elif u_type == 'trap':
            pygame.draw.ellipse(screen, (80, 80, 80), (x-8, y-4, 16, 8))
            pygame.draw.circle(screen, (255, 50, 50), (x, y-4), 4)

        elif u_type == 'slow':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (0, 150, 255), (x, y-15), 5)
            bx, by = x + math.cos(self.angle)*10, y-15 + math.sin(self.angle)*10
            pygame.draw.line(screen, (100, 200, 255), (x, y-15), (bx, by), 3)
            for i in range(3):
                cx = bx + math.cos(self.angle + i)*6
                cy = by + math.sin(self.angle + i)*6
                pygame.draw.circle(screen, (200, 255, 255), (int(cx), int(cy)), 2)

        elif u_type == 'knockback':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (80, 80, 80), (x, y-15), 7)
            bx, by = x + math.cos(self.angle)*9, y-15 + math.sin(self.angle)*9
            pygame.draw.line(screen, (40, 40, 40), (x, y-15), (bx, by), 6)
            pygame.draw.circle(screen, (100, 100, 100), (int(bx), int(by)), 3)

        elif u_type == 'beam':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (100, 200, 255), (x, y-15), 5)
            bx, by = x + math.cos(self.angle)*14, y-15 + math.sin(self.angle)*14
            pts = []
            for i in range(5):
                t = i/4
                px = x + (bx-x)*t + math.sin(t*10)*3
                py = y-15 + (by-(y-15))*t
                pts.append((px, py))
            pygame.draw.lines(screen, (100, 255, 255), False, pts, 2)

        elif u_type == 'missile':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (100, 100, 100), (x, y-15), 6)
            bx, by = x + math.cos(self.angle)*11, y-15 + math.sin(self.angle)*11
            pygame.draw.line(screen, (50, 50, 50), (x, y-15), (bx, by), 4)
            pygame.draw.polygon(screen, (255, 100, 0), [(bx-3, by-2), (bx+3, by-2), (bx, by-6)])

        elif u_type == 'swarm':
            pygame.draw.polygon(screen, (40, 40, 40), base_pts)
            pygame.draw.circle(screen, (20, 20, 20), (x, y-15), 6)
            ang = pygame.time.get_ticks() * 0.015
            for i in range(3):
                a = ang + i * (math.pi * 2 / 3)
                px, py = x + math.cos(a)*8, y-15 + math.sin(a)*8
                pygame.draw.line(screen, (255, 150, 0), (x, y-15), (px, py), 2)
            pygame.draw.circle(screen, (255, 200, 0), (x, y-15), 2)

        elif u_type == 'pierce':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (255, 215, 0), (x, y-15), 5)
            bx, by = x + math.cos(self.angle)*20, y-15 + math.sin(self.angle)*20
            pygame.draw.line(screen, (200, 200, 0), (x, y-15), (bx, by), 3)
            pygame.draw.circle(screen, (255, 255, 150), (int(bx), int(by)), 2)

        elif u_type == 'chain':
            pygame.draw.polygon(screen, (20, 20, 20), [(x-12,y), (x+12,y), (x,y-20)])
            pygame.draw.circle(screen, (180, 180, 180), (x, y-20), 6)
            pygame.draw.ellipse(screen, (255, 100, 0), (x-14, y-23, 28, 8), 2)
            pygame.draw.ellipse(screen, (255, 100, 0), (x-5, y-30, 10, 20), 2)

        elif u_type == 'heal':
            pygame.draw.rect(screen, (70, 70, 70), (x-9, y-18, 18, 18))
            pygame.draw.polygon(screen, (255, 215, 0), [(x-7,y-18), (x+7,y-18), (x+4,y-24), (x-4,y-24)])
            orb_y = y - 28 + math.sin(pygame.time.get_ticks() * 0.005) * 3
            pygame.draw.circle(screen, (255, 255, 150), (x, int(orb_y)), 4)

        elif u_type == 'pull':
            pygame.draw.rect(screen, (30, 30, 150), (x-9, y-22, 18, 18))
            t = pygame.time.get_ticks() * 0.003
            for i in range(2):
                r = 12 + i*8 + math.sin(t)*3
                alpha = max(50, 200 - i*60)
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (50, 50, 255, alpha), (r,r), r, 2)
                screen.blit(s, (x-r, y-13-r))

        elif u_type == 'strike':
            pygame.draw.polygon(screen, (60, 60, 60), [(x-10,y), (x+10,y), (x+5,y-18), (x-5,y-18)])
            pygame.draw.polygon(screen, (80, 80, 80), [(x-5,y-18), (x+5,y-18), (x+2,y-25), (x-2,y-25)])
            pygame.draw.circle(screen, (255, 50, 50), (x, y-22), 5)
            bx, by = x + math.cos(self.angle)*15, y-22 + math.sin(self.angle)*15
            pygame.draw.line(screen, (255, 100, 100), (x, y-22), (bx, by), 2)

        elif u_type == 'nuke':
            pygame.draw.polygon(screen, (60, 60, 60), base_pts)
            pygame.draw.circle(screen, (100, 100, 100), (x, y-15), 8)
            rad_t = pygame.time.get_ticks() * 0.001
            for i in range(3):
                a = i * (math.pi * 2 / 3) + rad_t
                pygame.draw.arc(screen, (255, 50, 50), (x-6, y-21, 12, 12), a, a+1.5, 2)
            pygame.draw.circle(screen, (255, 50, 50), (x, y-15), 2)

        else:
            base_h = 15
            pygame.draw.polygon(screen, (40,40,50), [(x-12,y), (x+12,y), (x+10,y-base_h), (x-10,y-base_h)])
            gx = x + math.cos(self.angle) * 18
            gy = y - base_h + math.sin(self.angle) * 18
            pygame.draw.line(screen, self.data['color'], (x, y-base_h), (gx, gy), 4)

        # --- ПОЛОСКА ЗАРЯДА ---
        if self.data.get('charge', False):
            bar_w = 30
            bar_h = 4
            x_bar = self.screen_x - bar_w // 2
            y_bar = self.screen_y - 35 
            
            pygame.draw.rect(screen, (30, 30, 30), (x_bar, y_bar, bar_w, bar_h))
            charge_percent = self.cd / self.data['rate']
            color_charge = (255, 255, 0) if charge_percent < 0.9 else (0, 255, 0) 
            pygame.draw.rect(screen, color_charge, (x_bar, y_bar, bar_w * charge_percent, bar_h))
            pygame.draw.rect(screen, (100, 100, 100), (x_bar, y_bar, bar_w, bar_h), 1)

        # --- ПОЛОСКИ РЕСУРСОВ ---
        if u_type == 'pull':
            bar_w, bar_h = 30, 4
            col = (100, 0, 255) if dark_matter_level > 0 else (50,50,50)
            pygame.draw.rect(screen, col, (x-bar_w//2, y-40, bar_w, bar_h))
        if u_type == 'heal':
            bar_w, bar_h = 30, 4
            pygame.draw.rect(screen, (255, 215, 0), (x-bar_w//2, y-35, bar_w, bar_h))
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
        self.base_speed = self.speed
        self.current_speed_mult = 1.0

    def move(self, grid_map):
        if self.idx >= len(self.path) - 1: return True
        actual_speed = self.base_speed * self.current_speed_mult
        self.progress += actual_speed
        if self.progress >= 1.0:
            self.progress = 0.0; self.idx += 1
            self.c, self.r = self.path[self.idx]
            if 0 <= self.r < len(grid_map) and 0 <= self.c < len(grid_map[0]):
                if grid_map[self.r][self.c] == 2:
                    self.hp -= 500; grid_map[self.r][self.c] = 1
        return False

    def take_damage(self, amt, fx=None):
        self.hp -= amt
        if fx: fx.spawn_damage(self.screen_x, self.screen_y - 20, amt)
        
    def is_dead(self): return self.hp <= 0

    def update_speed_recovery(self):
        if self.current_speed_mult < 1.0:
            self.current_speed_mult += 0.05
            if self.current_speed_mult > 1.0: self.current_speed_mult = 1.0

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
        size = int(14 * self.scale) 
        
        # Эффект "шатания" при ходьбе
        wobble = math.sin(pygame.time.get_ticks() * 0.01 + self.c) * 3
        
        # --- ТЕЛО ---
        # Используем self.color из настроек врага
        body_color = self.color
        
        # Тело (трапеция)
        pts_body = [
            (x - size//2 + wobble, y - size),      
            (x + size//2 + wobble, y - size),      
            (x + size, y + size//2),               
            (x - size, y + size//2)                
        ]
        pygame.draw.polygon(screen, body_color, pts_body)
        
        # --- ГОЛОВА ---
        head_y = y - size - 5 + wobble
        pygame.draw.circle(screen, body_color, (int(x + wobble), int(head_y)), int(size * 0.6))
        
        # --- ГЛАЗА (Светящиеся) ---
        eye_offset = size * 0.25
        eye_size = max(2, int(size * 0.15))
        
        # Цвет глаз по умолчанию желтый, можно сделать зависимым от цвета тела
        eye_color = (255, 255, 0) 
        if body_color == (200, 50, 50): eye_color = (255, 0, 0) # Если красный - красные глаза
        elif body_color == (80, 80, 80): eye_color = (0, 255, 255) # Если серый - синие глаза
        
        pygame.draw.circle(screen, eye_color, (int(x + wobble - eye_offset), int(head_y)), eye_size)
        pygame.draw.circle(screen, eye_color, (int(x + wobble + eye_offset), int(head_y)), eye_size)
        
        # --- РУКИ ---
        pygame.draw.line(screen, body_color, 
                         (x - size//2 + wobble, y - size//2), 
                         (x - size//2 + wobble - 5, y + size//2 - 5), 4)
        pygame.draw.line(screen, body_color, 
                         (x + size//2 + wobble, y - size//2), 
                         (x + size//2 + wobble + 5, y + size//2 - 5), 4)

        # --- ПОЛОСКА ЗДОРОВЬЯ ---
        bar_w = size * 2
        bar_h = 4
        bar_x = x - bar_w // 2
        bar_y = y - size * 1.5 - 10 + wobble
        
        pygame.draw.rect(screen, (30, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        hp_percent = self.hp / self.max_hp
        color_hp = (255, 0, 0) if hp_percent < 0.3 else (0, 255, 0)
        pygame.draw.rect(screen, color_hp, (bar_x, bar_y, bar_w * hp_percent, bar_h))
