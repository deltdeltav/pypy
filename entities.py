import pygame, math, random
from settings import *
from engine import to_iso, draw_health_bar

class Projectile:
    def __init__(self, x, y, target, dmg, color, p_type, tower_range, tower_pos):
        self.x, self.y = x, y
        # Запоминаем начальную позицию башни для расчета лимита дальности
        self.start_x, self.start_y = tower_pos 
        self.tower_range = tower_range * TILE_W
        
        self.dmg = dmg
        self.color = color
        self.p_type = p_type
        self.speed = 14
        self.active = True
        
        # --- ЛОГИКА СНАЙПЕРА ДЛЯ ВСЕХ ---
        # Вычисляем вектор направления СРАЗУ при создании
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

        # Движение по запомненному вектору (как у снайпера)
        self.x += self.vx
        self.y += self.vy
        
        # Проверка: улетел ли снаряд за пределы радиуса башни?
        # Если расстояние от старта больше радиуса + буфер (60px), удаляем
        dist_from_tower = math.hypot(self.x - self.start_x, self.y - self.start_y)
        if dist_from_tower > self.tower_range + 60:
            self.active = False
            return

        # Поиск столкновения с любым врагом на пути
        hit_enemy = None
        for e in enemies:
            # Радиус хитбокса врага ~18 пикселей
            if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 18:
                hit_enemy = e
                break

        if hit_enemy:
            # Обработка попадания в зависимости от типа
            if self.p_type == 'aoe' or self.p_type == 'missile':
                if self.p_type == 'missile':
                    fx.spawn_explosion(self.x, self.y, self.color, count=25)
                    fx.add_shake(4)
                # Урон по площади
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 60:
                        e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'nuke':
                fx.spawn_explosion(self.x, self.y, (255, 0, 0), count=50)
                fx.add_shake(15)
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 150:
                        e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'strike': # Orbital
                fx.spawn_explosion(self.x, self.y, (255, 255, 255), count=30)
                fx.add_shake(8)
                for e in enemies:
                    if math.hypot(e.screen_x - self.x, e.screen_y - self.y) < 80:
                        e.take_damage(self.dmg, fx)
            
            elif self.p_type == 'pierce': # G-Sniper (пробивает)
                hit_enemy.take_damage(self.dmg, fx)
                fx.spawn_gold_sparks(self.x, self.y)
                self.dmg *= 0.8 # Урон падает с каждым пробитием
                if self.dmg < 10: self.active = False
            
            elif self.p_type == 'drone': # Hive (самонаводился до момента, теперь летит прямо, но ищем цель рядом)
                 # Если дрон пролетает мимо цели, он все равно может задеть её боком
                 hit_enemy.take_damage(self.dmg, fx)
                 self.active = False # Дрон взрывается об первого встречного
            
            else:
                # Обычный одиночный выстрел (Soldier, Sniper, Laser beam start point)
                hit_enemy.take_damage(self.dmg, fx)
                self.active = False

    def draw(self, screen):
        # Рисуем шлейф для быстрых снарядов
        if self.p_type in ['missile', 'drone', 'sniper', 'single']:
             pygame.draw.line(screen, self.color, 
                              (int(self.x - self.vx*2), int(self.y - self.vy*2)), 
                              (int(self.x), int(self.y)), 2)
        
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

    def update(self, enemies, projectiles, cam_x, cam_y, fx, screen):
        self.screen_x, self.screen_y = to_iso(self.c, self.r, cam_x, cam_y)
        self.screen_y -= 5
        if self.data['type'] == 'trap': return
        if self.cd > 0: self.cd -= 1; return

        target = None
        range_px = self.data['range'] * TILE_W
        
        # Ищем ближайшую цель
        for e in enemies:
            dist = math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y)
            if dist < range_px:
                target = e
                self.angle = math.atan2(e.screen_y - self.screen_y, e.screen_x - self.screen_x)
                break

        if target:
            self.cd = int(self.data['rate'] / self.rate_mult)
            final_dmg = int(self.data['dmg'] * self.dmg_mult)
            u_type = self.data['type']

            # --- ЛОГИКА СПЕЦ-ЮНИТОВ ---
            
            if u_type == 'slow': # FROST
                fx.spawn_flame_stream(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y)
                target.take_damage(final_dmg, fx)
                target.speed *= 0.5 
                
            elif u_type == 'chain': # TESLA
                chain_targets = [target]
                for e in enemies:
                    if e != target and math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 60:
                        chain_targets.append(e)
                        if len(chain_targets) >= 3: break
                for ct in chain_targets:
                    ct.take_damage(final_dmg, fx)
                    # Рисуем молнию сразу (так как это мгновенный эффект)
                    pygame.draw.line(screen, self.data['color'], (self.screen_x, self.screen_y-15), (ct.screen_x, ct.screen_y), 2)
                    
            elif u_type == 'nuke': # NUKE
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'nuke', self.data['range'], (self.screen_x, self.screen_y)))
                fx.add_shake(10)
                
            elif u_type == 'swarm': # HIVE
                for _ in range(3):
                    # Дроны теперь тоже летят по прямой, но создаются с небольшим разбросом угла
                    angle_var = self.angle + random.uniform(-0.2, 0.2)
                    # Создаем фиктивную цель в направлении угла, чтобы Projectile взял вектор
                    fake_target = type('obj', (object,), {
                        'screen_x': self.screen_x + math.cos(angle_var)*100,
                        'screen_y': self.screen_y + math.sin(angle_var)*100
                    })()
                    projectiles.append(Projectile(self.screen_x, self.screen_y, fake_target, final_dmg, self.data['color'], 'drone', self.data['range'], (self.screen_x, self.screen_y)))

            elif u_type == 'pierce': # G-SNIPER
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'pierce', self.data['range'], (self.screen_x, self.screen_y)))
                fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

            elif u_type == 'knockback': # CANNON
                target.take_damage(final_dmg, fx)
                fx.add_shake(5)
                fx.spawn_explosion(target.screen_x, target.screen_y, (150,150,150), count=10)

            elif u_type == 'heal': # HEALER
                fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

            elif u_type == 'strike': # ORBITAL
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'strike', self.data['range'], (self.screen_x, self.screen_y)))
                fx.add_shake(10)

            elif u_type == 'pull': # VOID
                for e in enemies:
                    if math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y) < self.data['range'] * TILE_W:
                        e.speed *= 0.2
                fx.spawn_explosion(self.screen_x, self.screen_y, (50, 0, 100), count=5)

            elif u_type == 'aoe' and self.data['name'] == 'PYRO':
                fx.spawn_flame_stream(self.screen_x, self.screen_y - 15, target.screen_x, target.screen_y)
                for e in enemies:
                    if math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 45:
                        e.take_damage(final_dmg, fx)
            
            elif u_type == 'beam': # LASER
                target.take_damage(final_dmg, fx)
                fx.add_shake(1.5)
                # Луч рисуется в draw()

            elif u_type == 'missile':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'missile', self.data['range'], (self.screen_x, self.screen_y)))
                fx.add_shake(3)
            
            elif u_type == 'projectile': # SNIPER
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'sniper', self.data['range'], (self.screen_x, self.screen_y)))
            
            else: # SOLDIER / DEFAULT
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'single', self.data['range'], (self.screen_x, self.screen_y)))

    def draw(self, screen):
        x, y = self.screen_x, self.screen_y
        base_h = 15
        
        if self.data['type'] == 'beam':
             pygame.draw.polygon(screen, (40, 0, 40), [(x,y), (x+10,y-10), (x,y-20), (x-10,y-10)])
        elif self.data['type'] == 'nuke':
             pygame.draw.circle(screen, (40, 0, 0), (x, y-10), 12)
        else:
             pygame.draw.polygon(screen, (35,35,45), [(x-12,y), (x+12,y), (x+10,y-base_h), (x-10,y-base_h)])

        gx = x + math.cos(self.angle) * 18
        gy = y - base_h + math.sin(self.angle) * 18
        
        from engine import draw_glow_circle
        draw_glow_circle(screen, int(gx), int(gy), 6, self.data['color'], 150)
        
        pygame.draw.line(screen, self.data['color'], (x, y-base_h), (gx, gy), 4)
        
        # Отрисовка луча лазера (мгновенный)
        if self.data['type'] == 'beam' and self.cd > self.data['rate'] - 5:
            lx = x + math.cos(self.angle) * 40
            ly = y - base_h + math.sin(self.angle) * 40
            pygame.draw.line(screen, self.data['color'], (x, y-base_h), (lx, ly), 4)
            pygame.draw.line(screen, (255,255,255), (x, y-base_h), (lx, ly), 1)

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

    def take_damage(self, amt, fx=None):
        self.hp -= amt
        if fx: fx.spawn_damage(self.screen_x, self.screen_y - 20, amt)
        
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
