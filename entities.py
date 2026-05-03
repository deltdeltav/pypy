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

    def update(self, enemies, projectiles, cam_x, cam_y, fx, screen, energy, dark_matter):
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
            u_type = self.data['type']

            if u_type == 'slow':
                fx.spawn_flame_stream(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y)
                target.take_damage(final_dmg, fx); target.speed *= 0.5 
                
            elif u_type == 'chain': # TESLA
                energy_cost = 20
                if energy >= energy_cost:
                    chain_targets = [target]
                    for e in enemies:
                        if e != target and math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 70:
                            chain_targets.append(e)
                            if len(chain_targets) >= 4: break
                    fx.spawn_lightning(self.screen_x, self.screen_y-15, target.screen_x, target.screen_y)
                    for i in range(1, len(chain_targets)):
                        prev = chain_targets[i-1]; curr = chain_targets[i]
                        fx.spawn_lightning(prev.screen_x, prev.screen_y, curr.screen_x, curr.screen_y)
                        curr.take_damage(final_dmg, fx)
                else: fx.spawn_explosion(self.screen_x, self.screen_y-15, (100, 200, 255), count=3)
                    
            elif u_type == 'nuke':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'nuke', self.data['range'], (self.screen_x, self.screen_y)))
                fx.add_shake(10)
                
            elif u_type == 'swarm':
                for _ in range(3):
                    angle_var = self.angle + random.uniform(-0.2, 0.2)
                    fake_target = type('obj', (object,), {'screen_x': self.screen_x + math.cos(angle_var)*100, 'screen_y': self.screen_y + math.sin(angle_var)*100})()
                    projectiles.append(Projectile(self.screen_x, self.screen_y, fake_target, final_dmg, self.data['color'], 'drone', self.data['range'], (self.screen_x, self.screen_y)))

            elif u_type == 'pierce':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'pierce', self.data['range'], (self.screen_x, self.screen_y)))
                fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

            elif u_type == 'knockback':
                target.take_damage(final_dmg, fx); fx.add_shake(5); fx.spawn_explosion(target.screen_x, target.screen_y, (150,150,150), count=10)

            elif u_type == 'heal':
                fx.spawn_gold_sparks(self.screen_x, self.screen_y-15)

            elif u_type == 'strike': # ORBITAL
                energy_cost = 50
                if energy >= energy_cost:
                    fx.spawn_target_zone(target.screen_x, target.screen_y, self.data['range'] * TILE_W)
                    fx.add_delayed_strike(target.screen_x, target.screen_y, final_dmg, enemies)
                    fx.add_shake(10)
                else: fx.spawn_explosion(self.screen_x, self.screen_y-15, (100, 200, 255), count=3)

            elif u_type == 'pull': # VOID
                dm_cost = 0.5
                if dark_matter >= dm_cost:
                    for e in enemies:
                        if math.hypot(e.screen_x - self.screen_x, e.screen_y - self.screen_y) < self.data['range'] * TILE_W:
                            e.current_speed_mult = 0.1
                    fx.spawn_explosion(self.screen_x, self.screen_y, (80, 0, 150), count=3)
                else: fx.spawn_explosion(self.screen_x, self.screen_y, (50, 50, 50), count=1)

            elif u_type == 'aoe' and self.data['name'] == 'PYRO':
                fx.spawn_flame_stream(self.screen_x, self.screen_y - 15, target.screen_x, target.screen_y)
                for e in enemies:
                    if math.hypot(e.screen_x - target.screen_x, e.screen_y - target.screen_y) < 45: e.take_damage(final_dmg, fx)
            
            elif u_type == 'beam':
                target.take_damage(final_dmg, fx); fx.add_shake(1.5)

            elif u_type == 'missile':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'missile', self.data['range'], (self.screen_x, self.screen_y)))
                fx.add_shake(3)
            
            elif u_type == 'projectile':
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'sniper', self.data['range'], (self.screen_x, self.screen_y)))
            
            else:
                projectiles.append(Projectile(self.screen_x, self.screen_y, target, final_dmg, self.data['color'], 'single', self.data['range'], (self.screen_x, self.screen_y)))

    def draw(self, screen, energy_level=0, dark_matter_level=0):
        x, y = self.screen_x, self.screen_y
        u_type = self.data['type']
        color = self.data['color']

        # --- 1. SOLDIER / RANGER ---
        if u_type == 'projectile' and self.data['name'] == 'Soldier':
            pygame.draw.rect(screen, (50, 150, 50), (x-8, y-20, 16, 16))
            pygame.draw.circle(screen, (0, 255, 0), (x, y-12), 3)

        # --- 2. FLAME / INCINERATOR ---
        elif u_type == 'aoe' and self.data['name'] == 'Pyro':
            pygame.draw.polygon(screen, (150, 70, 0), [(x-10,y), (x+10,y), (x,y-20)])
            pygame.draw.circle(screen, (255, 100, 0), (x, y-20), 5)

        # --- 3. SNIPER / MARKSMAN ---
        elif u_type == 'projectile' and self.data['name'] == 'Sniper':
            pygame.draw.polygon(screen, (50, 50, 150), [(x-8,y), (x+8,y), (x,y-25)])
            pygame.draw.line(screen, (0, 0, 255), (x, y-25), (x + math.cos(self.angle)*15, y-25 + math.sin(self.angle)*15), 2)

        # --- 4. MINE / TRAP ---
        elif u_type == 'trap':
            pygame.draw.circle(screen, (100, 100, 100), (x, y-5), 8)
            pygame.draw.circle(screen, (255, 0, 0), (x, y-5), 3)

        # --- 5. FROST / CRYO ---
        elif u_type == 'slow':
            pygame.draw.polygon(screen, (0, 150, 255), [(x-10,y), (x+10,y), (x+5,y-15), (x-5,y-15)])
            pygame.draw.circle(screen, (200, 255, 255), (x, y-15), 4)

        # --- 6. CANNON / HOWITZER ---
        elif u_type == 'knockback':
            pygame.draw.rect(screen, (100, 50, 50), (x-10, y-15, 20, 15))
            pygame.draw.circle(screen, (50, 50, 50), (x, y-15), 8)
            pygame.draw.line(screen, (0,0,0), (x, y-15), (x + math.cos(self.angle)*12, y-15 + math.sin(self.angle)*12), 4)

        # --- 7. LASER / PRISM ---
        elif u_type == 'beam':
            pygame.draw.polygon(screen, (150, 0, 150), [(x-10,y), (x+10,y), (x,y-20)])
            pygame.draw.circle(screen, (255, 0, 255), (x, y-20), 5)

        # --- 8. MISSILE / ROCKETEER ---
        elif u_type == 'missile':
            pygame.draw.polygon(screen, (150, 150, 0), [(x-10,y), (x+10,y), (x,y-20)])
            pygame.draw.circle(screen, (255, 255, 0), (x, y-20), 5)

        # --- 9. HIVE / SWARM ---
        elif u_type == 'swarm':
            pygame.draw.polygon(screen, (255, 200, 0), [(x-10,y), (x+10,y), (x+5,y-15), (x-5,y-15)])
            pygame.draw.circle(screen, (0,0,0), (x, y-10), 3)

        # --- 10. G-SNIPER / PIERCER ---
        elif u_type == 'pierce':
            pygame.draw.polygon(screen, (255, 215, 0), [(x-10,y), (x+10,y), (x,y-25)])
            pygame.draw.line(screen, (255, 255, 255), (x, y-25), (x + math.cos(self.angle)*15, y-25 + math.sin(self.angle)*15), 3)

        # --- 11. HEALER / MEDIC ---
        elif u_type == 'heal':
            pygame.draw.polygon(screen, (80, 80, 80), [(x-10,y), (x+10,y), (x+8,y-15), (x-8,y-15)])
            pygame.draw.polygon(screen, (255, 215, 0), [(x-8,y-15), (x+8,y-15), (x+5,y-22), (x-5,y-22)])
            f = pygame.font.SysFont('consolas', 10, bold=True)
            screen.blit(f.render("$", True, (0,0,0)), (x-3, y-20))

        # --- 12. TESLA / COIL ---
        elif u_type == 'chain':
            pygame.draw.polygon(screen, (10, 10, 10), [(x-12,y), (x+12,y), (x,y-20)])
            pygame.draw.circle(screen, (200, 200, 200), (x, y-20), 6)
            pygame.draw.ellipse(screen, (255, 100, 0), (x-15, y-24, 30, 10), 2)
            pygame.draw.ellipse(screen, (255, 100, 0), (x-6, y-32, 12, 24), 2)

        # --- 13. VOID / SINGULARITY ---
        elif u_type == 'pull':
            pygame.draw.rect(screen, (0, 0, 200), (x-8, y-24, 16, 16))
            time_val = pygame.time.get_ticks() * 0.005
            for i in range(1, 3):
                r = 15 + i*10 + int(math.sin(time_val)*5)
                col = (0, 0, 255, max(0, 200 - i*80))
                s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(s, col, (r,r), r, 2)
                screen.blit(s, (x-r, y-12-r))

        # --- 14. ORBITAL / STRIKE ---
        elif u_type == 'strike':
            pygame.draw.polygon(screen, (50, 50, 50), [(x-12,y), (x+12,y), (x,y-25)])
            pygame.draw.circle(screen, (255, 0, 0), (x, y-25), 6)

        # --- 15. NUKE / DOOMSDAY ---
        elif u_type == 'nuke':
            pygame.draw.circle(screen, (40, 0, 0), (x, y-15), 12)
            pygame.draw.circle(screen, (255, 0, 0), (x, y-15), 6)

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
        size = int(16 * self.scale)
        pygame.draw.ellipse(screen, (0,0,0,90), (x-size, y+size, size*2, size))
        pygame.draw.rect(screen, self.color, (x-size//2, y-size, size, size*1.5))
        draw_health_bar(screen, x, y-size-8, size*2, self.hp, self.max_hp)
