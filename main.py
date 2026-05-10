import pygame, sys, random, math
from settings import *
from engine import draw_tile_3d, from_iso, to_iso
from entities import Tower, Enemy, Projectile
from map_gen import generate_path
from save_manager import load_game, save_game
from effects import EffectsManager

pygame.init()
screen = pygame.display.set_mode((W, H), SCREEN_FLAGS)
pygame.display.set_caption("DELTA CORE: PRO")
clock = pygame.time.Clock()
font = pygame.font.SysFont('consolas', 18, bold=True)
font_big = pygame.font.SysFont('consolas', 40, bold=True)

# --- НАСТРОЙКИ UI И ЛИМИТОВ ---
BASE_TOWER_LIMIT = 6

# Вертикальное меню юнитов (Слева, сдвинуто вниз)
V_MENU_X = 10
V_MENU_Y_START = 110 # Сдвинули ниже, чтобы не лезть на полоски
V_BTN_W = 140
V_BTN_H = 45
V_GAP = 5
V_MAX_VISIBLE = 5    # Сколько кнопок видно за раз

# Кнопка Меню (Правый верхний угол)
MENU_BTN_W = 90
MENU_BTN_H = 40
MENU_BTN_X = W - MENU_BTN_W - 10
MENU_BTN_Y = 10

# Глобальные переменные
money, crystals = START_MONEY, START_CRYSTALS
energy = START_ENERGY
max_energy = MAX_ENERGY
dark_matter = START_DARK_MATTER
max_dark_matter = MAX_DARK_MATTER
wave, lives = 1, 20
cam_x, cam_y = W//2, H//3
COLS, ROWS = 22, 16
path, grid_map = None, None
towers, enemies, projectiles = [], [], []
spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
selected_unit, dragging, last_mouse = 'soldier', False, (0,0)
game_state, mega_boss_killed = 'playing', False
menu_open, menu_tab = False, 0
shop_scroll = 0
unit_scroll = 0
upgrade_scroll = 0

global_upgrades = {'dmg': 0, 'rate': 0, 'hp': 0, 'income': 0, 'capacity': 0, 'energy_cap': 0}

fx = EffectsManager()

def reset():
    global money, crystals, energy, max_energy, dark_matter, max_dark_matter
    global wave, lives, cam_x, cam_y, path, grid_map
    global towers, enemies, projectiles, spawn_timer, wave_active, enemies_to_spawn, boss_wave
    global game_state, mega_boss_killed, menu_open, menu_tab, shop_scroll, unit_scroll, upgrade_scroll
    
    saved = load_game()
    crystals = saved['crystals']
    for key in saved['unlocked_units']:
        if key in SHOP_UNITS and key not in UNITS:
            UNITS[key] = SHOP_UNITS[key]
    
    money, crystals, energy = START_MONEY, START_CRYSTALS, START_ENERGY
    max_energy = MAX_ENERGY
    dark_matter = START_DARK_MATTER
    max_dark_matter = MAX_DARK_MATTER
    
    wave, lives = 1, 20
    cam_x, cam_y = W//2, H//3
    path, grid_map = generate_path(COLS, ROWS)
    towers, enemies, projectiles = [], [], []
    spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
    game_state, mega_boss_killed, menu_open, menu_tab, shop_scroll, unit_scroll, upgrade_scroll = 'playing', False, False, 0, 0, 0, 0
    global_upgrades['energy_cap'] = 0 
    start_wave()

def start_wave():
    global enemies_to_spawn, boss_wave, wave_active
    wave_active = True
    if wave % 5 == 0 and wave % 50 != 0:
        enemies_to_spawn, boss_wave = 1, 5 if wave==5 else 10
    elif wave % 50 == 0:
        enemies_to_spawn, boss_wave = 1, 50
    else:
        enemies_to_spawn, boss_wave = 6 + wave*2, 0

reset()

running = True
while running:
    clock.tick(FPS)
    screen.fill((0,0,0))
    
    # === GAME OVER ===
    if game_state == 'game_over':
        screen.fill((0,0,0))
        txt = font_big.render("GAME OVER", True, Colors.RED)
        screen.blit(txt, (W//2-txt.get_width()//2, H//2-40))
        txt2 = font.render(f"CR: {crystals} | Press [R]", True, Colors.WHITE)
        screen.blit(txt2, (W//2-txt2.get_width()//2, H//2+20))
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: running=False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r: reset()
        pygame.display.flip(); continue

    # === INPUT ===
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT: running=False
        
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_p: menu_open = not menu_open
            if ev.key == pygame.K_ESCAPE: menu_open = False
            if ev.key == pygame.K_r and game_state=='game_over': reset()
            
            # --- ПРОКРУТКА СПИСКА ЮНИТОВ СТРЕЛКАМИ ---
            if not menu_open:
                all_keys_temp = ['soldier', 'flame', 'sniper', 'mine']
                for k in SHOP_UNITS.keys():
                    if k in UNITS: all_keys_temp.append(k)
                
                if ev.key == pygame.K_LEFT: # Стрелка ВЛЕВО
                    if unit_scroll > 0:
                        unit_scroll -= 1
                        pygame.time.wait(100)
                
                if ev.key == pygame.K_RIGHT: # Стрелка ВПРАВО
                    if unit_scroll + V_MAX_VISIBLE < len(all_keys_temp):
                        unit_scroll += 1
                        pygame.time.wait(100)

                # Клавиши 1-5 выбирают юнита из ВИДИМОГО списка
                start_idx = unit_scroll
                end_idx = min(start_idx + V_MAX_VISIBLE, len(all_keys_temp))
                visible_temp = all_keys_temp[start_idx:end_idx]

                if ev.key == pygame.K_1 and len(visible_temp) > 0: selected_unit = visible_temp[0]
                if ev.key == pygame.K_2 and len(visible_temp) > 1: selected_unit = visible_temp[1]
                if ev.key == pygame.K_3 and len(visible_temp) > 2: selected_unit = visible_temp[2]
                if ev.key == pygame.K_4 and len(visible_temp) > 3: selected_unit = visible_temp[3]
                if ev.key == pygame.K_5 and len(visible_temp) > 4: selected_unit = visible_temp[4]

        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            
            if ev.button == 1:
                # 1. Кнопка Меню (Правый верхний угол)
                menu_rect = pygame.Rect(MENU_BTN_X, MENU_BTN_Y, MENU_BTN_W, MENU_BTN_H)
                if menu_rect.collidepoint(mx, my):
                    menu_open = not menu_open
                    continue

                if menu_open:
                    # --- ЛОГИКА ВНУТРЕННЕГО МЕНЮ ---
                    menu_w_tmp, menu_h_tmp = 600, 450
                    menu_x_tmp = (W - menu_w_tmp) // 2
                    menu_y_tmp = (H - menu_h_tmp) // 2
                    
                    tab_w = 130
                    tab_start_x_tmp = menu_x_tmp + (menu_w_tmp - 3 * tab_w - 2 * 10) // 2
                    tab_y_tmp = menu_y_tmp + 10
                    
                    clicked_menu = False
                    for t in range(3):
                        tx = tab_start_x_tmp + t * (tab_w + 10)
                        rect = pygame.Rect(tx, tab_y_tmp, tab_w, 40)
                        if rect.collidepoint(mx, my):
                            menu_tab = t
                            clicked_menu = True
                    
                    close_rect_tmp = pygame.Rect(menu_x_tmp + 20, menu_y_tmp + menu_h_tmp - 80, 90, 60)
                    if close_rect_tmp.collidepoint(mx, my): 
                        menu_open = False
                        clicked_menu = True
                    
                    if not clicked_menu:
                        content_x_tmp = menu_x_tmp + 30
                        content_y_tmp = menu_y_tmp + 70
                        item_w_tmp = menu_w_tmp - 60
                        item_h_tmp = 65
                        
                        scroll_w = 50
                        left_x = menu_x_tmp + 40
                        right_x = menu_x_tmp + menu_w_tmp - 40 - scroll_w
                        start_y_content = menu_y_tmp + 80 

                        if menu_tab == 0: # UPGRADES
                            all_upgrades = [
                                ('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                                ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                                ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                                ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL),
                                ('Energy Cap +100', 'energy_cap', global_upgrades['energy_cap'], ENERGY_UPGRADE_COSTS, Colors.BLUE)
                            ]
                            
                            if pygame.Rect(left_x, start_y_content, scroll_w, item_h_tmp).collidepoint(mx, my):
                                if upgrade_scroll > 0: upgrade_scroll -= 1
                                pygame.time.wait(150)
                            elif pygame.Rect(right_x, start_y_content, scroll_w, item_h_tmp).collidepoint(mx, my):
                                if upgrade_scroll < len(all_upgrades) - 5: upgrade_scroll += 1
                                pygame.time.wait(150)
                            else:
                                visible_ups = all_upgrades[upgrade_scroll : upgrade_scroll + 5]
                                card_x_start = menu_x_tmp + 100
                                card_width = menu_w_tmp - 200
                                
                                for i, (name, key, lvl, costs, col) in enumerate(visible_ups):
                                    y_card = start_y_content + i * (item_h_tmp + 10)
                                    rect_card = pygame.Rect(card_x_start, y_card, card_width, item_h_tmp)
                                    
                                    if rect_card.collidepoint(mx, my):
                                        cost = costs[lvl] if lvl < len(costs) else 'MAX'
                                        can_buy = money >= cost if isinstance(cost, int) else False
                                        
                                        if lvl < len(costs) and can_buy:
                                            money -= cost
                                            global_upgrades[key] += 1
                                            if key == 'energy_cap':
                                                max_energy += ENERGY_UPGRADE_BONUS[lvl]
                                                energy = min(energy + ENERGY_UPGRADE_BONUS[lvl], max_energy)

                        elif menu_tab == 1: # SHOP
                            visible_keys = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll+5]
                            
                            if pygame.Rect(left_x, start_y_content, scroll_w, item_h_tmp).collidepoint(mx, my):
                                if shop_scroll > 0: shop_scroll -= 1
                                pygame.time.wait(150)
                            elif pygame.Rect(right_x, start_y_content, scroll_w, item_h_tmp).collidepoint(mx, my):
                                if shop_scroll < len(SHOP_UNITS) - 5: shop_scroll += 1
                                pygame.time.wait(150)
                            else:
                                card_x_start = menu_x_tmp + 100
                                card_width = menu_w_tmp - 200
                                
                                for i, k in enumerate(visible_keys):
                                    v = SHOP_UNITS[k]
                                    y_card = start_y_content + i * (item_h_tmp + 10)
                                    rect_card = pygame.Rect(card_x_start, y_card, card_width, item_h_tmp)
                                    
                                    if rect_card.collidepoint(mx, my):
                                        if crystals >= v['cost_crystals'] and k not in UNITS:
                                            UNITS[k] = v
                                            crystals -= v['cost_crystals']
                                            save_game(crystals, list(UNITS.keys()))
                                            pygame.time.wait(200)

                        elif menu_tab == 2: # DONATE
                             donate_items = [("Watch Ad: +1 CR", Colors.GREEN), ("Buy 3 CR: 500$", Colors.GOLD), ("Monthly Pack: 10 CR", Colors.CRYSTAL)]
                             for i, (txt, col) in enumerate(donate_items):
                                 y_don = content_y_tmp + i * (item_h_tmp + 10)
                                 rect_don = pygame.Rect(content_x_tmp, y_don, item_w_tmp, item_h_tmp)
                                 if rect_don.collidepoint(mx, my):
                                     if "Ad" in txt: crystals += 1
                                     if "Buy" in txt and money >= 500: money -= 500; crystals += 3
                                     if "Pack" in txt and crystals >= 10: crystals -= 10
                
                else: # ГЕЙМПЛЕЙ
                    # 2. Проверка клика по вертикальному меню юнитов (Слева)
                    all_unit_keys = ['soldier', 'flame', 'sniper', 'mine']
                    for k in SHOP_UNITS.keys():
                        if k in UNITS: all_unit_keys.append(k)
                    
                    start_idx = unit_scroll
                    end_idx = min(start_idx + V_MAX_VISIBLE, len(all_unit_keys))
                    visible_keys_game = all_unit_keys[start_idx : end_idx]
                    
                    current_count = len(visible_keys_game)
                    buttons_block_height = current_count * V_BTN_H + (current_count - 1) * V_GAP
                    
                    arrow_y_pos = V_MENU_Y_START + buttons_block_height + 10
                    arrow_h = 30
                    arrow_w = 70
                    
                    left_arrow_rect = pygame.Rect(V_MENU_X, arrow_y_pos, arrow_w, arrow_h)
                    right_arrow_rect = pygame.Rect(V_MENU_X + arrow_w + 10, arrow_y_pos, arrow_w, arrow_h)

                    clicked_ui = False
                    
                    # Клик по стрелке ВЛЕВО
                    if len(all_unit_keys) > V_MAX_VISIBLE and left_arrow_rect.collidepoint(mx, my):
                        if unit_scroll > 0: unit_scroll -= 1
                        clicked_ui = True
                        pygame.time.wait(100)
                    
                    # Клик по стрелке ВПРАВО
                    elif len(all_unit_keys) > V_MAX_VISIBLE and right_arrow_rect.collidepoint(mx, my):
                        if unit_scroll + V_MAX_VISIBLE < len(all_unit_keys): unit_scroll += 1
                        clicked_ui = True
                        pygame.time.wait(100)
                    
                    # Клик по кнопкам юнитов
                    else:
                        for i, k in enumerate(visible_keys_game):
                            x = V_MENU_X
                            y = V_MENU_Y_START + i * (V_BTN_H + V_GAP)
                            rect = pygame.Rect(x, y, V_BTN_W, V_BTN_H)
                            if rect.collidepoint(mx, my):
                                selected_unit = k
                                clicked_ui = True
                                break
                    
                    # Если не кликнули по UI -> Драг карты
                    if not clicked_ui:
                        dragging = True
                        last_mouse = (mx, my)

            elif ev.button == 3: # Продажа
                if not menu_open:
                    c, r = from_iso(mx, my, cam_x, cam_y)
                    if 0 <= c < COLS and 0 <= r < ROWS:
                        tower_to_sell = None
                        for t in towers:
                            if t.c == c and t.r == r:
                                tower_to_sell = t
                                break
                        if tower_to_sell:
                            refund = int(tower_to_sell.data['cost'] * 0.2)
                            money += refund
                            grid_map[r][c] = 0
                            towers.remove(tower_to_sell)
                            fx.spawn_explosion(tower_to_sell.screen_x, tower_to_sell.screen_y, (0, 255, 0), count=10)
            
        if ev.type == pygame.MOUSEBUTTONUP and ev.button==1: 
            dragging = False
            # Строительство при отпускании
            if not menu_open:
                 mx, my = pygame.mouse.get_pos()
                 c, r = from_iso(mx, my, cam_x, cam_y)
                 
                 if 0 <= c < COLS and 0 <= r < ROWS:
                     current_limit = BASE_TOWER_LIMIT + (global_upgrades['capacity'] * 2)
                     cost = UNITS[selected_unit].get('cost', 9999)
                     
                     if grid_map[r][c] == 0 and money >= cost:
                         if len(towers) < current_limit:
                             towers.append(Tower(c, r, selected_unit))
                             grid_map[r][c] = 1
                             money -= cost
                         else:
                             fx.spawn_damage(mx, my, "FULL!")
                     elif grid_map[r][c] == 1 and selected_unit == 'mine' and money >= cost:
                         grid_map[r][c] = 2
                         money -= cost
                     elif money < cost:
                         fx.spawn_damage(mx, my, "NO $")

        if ev.type == pygame.MOUSEMOTION:
            if dragging:
                dx = ev.pos[0]-last_mouse[0]; dy = ev.pos[1]-last_mouse[1]
                if abs(dx) > 2 or abs(dy) > 2:
                    cam_x += dx; cam_y += dy; last_mouse = ev.pos

    # === LOGIC ===
    if energy < max_energy:
        energy += ENERGY_REGEN
        if energy > max_energy: energy = max_energy

    if dark_matter < max_dark_matter:
        dark_matter += DARK_MATTER_REGEN
        if dark_matter > max_dark_matter: dark_matter = max_dark_matter

    mult = 1 + (wave * 0.18) + (global_upgrades['income'] * 0.05)
    if wave_active and enemies_to_spawn > 0:
        spawn_timer += 1
        if spawn_timer > 45:
            tk = 'normal'
            if wave>5 and random.random()>0.6: tk='runner'
            if wave>12 and random.random()>0.7: tk='tank'
            enemies.append(Enemy(path, tk, mult, boss_wave!=0, boss_wave))
            enemies_to_spawn -= 1; spawn_timer=0
            
    if enemies_to_spawn==0 and not enemies and wave_active:
        wave_active=False; wave+=1; money+=150+wave*20; start_wave()
        if wave > 50 and not mega_boss_killed: mega_boss_killed=True

    for e in enemies[:]:
        if e.move(grid_map): lives-=1; enemies.remove(e)
        e.update_speed_recovery()
        res = e.update_pos(cam_x,cam_y)
        if res == 'spawn': enemies.append(Enemy(path, 'normal', mult, False, 0))
        if e.is_dead(): 
            money += e.reward; crystals += e.crystals
            fx.spawn_explosion(e.screen_x, e.screen_y, e.color, count=20)
            fx.add_shake(5)
            if e.crystals > 0: save_game(crystals, list(UNITS.keys()))
            enemies.remove(e)
        if lives<=0: game_state='game_over'
        
    for t in towers:
        old_cd = t.cd
        t.update(enemies, projectiles, cam_x, cam_y, fx, screen, energy, dark_matter) 
        
        if t.data['type'] == 'strike':
            if old_cd > 0 and t.cd == 0:
                if energy >= 50: energy -= 50
        elif t.data['type'] == 'chain':
            if old_cd > 0 and t.cd == 0:
                if energy >= 20: energy -= 20
        elif t.data['type'] == 'pull':
            has_target = any(math.hypot(e.screen_x - t.screen_x, e.screen_y - t.screen_y) < t.data['range'] * TILE_W for e in enemies)
            if has_target and dark_matter >= 0.5:
                dark_matter -= 0.5
        
        t.draw(screen, energy, dark_matter)
        
    for p in projectiles[:]:
        p.update(enemies, fx); 
        if not p.active:
            projectiles.remove(p)
    
    fx.update()

    # === RENDER ===
    sx, sy = fx.get_shake_offset()
    r_cam_x, r_cam_y = cam_x + sx, cam_y + sy
    
    loc_idx = 0 if wave<=10 else (1 if wave<=30 else 2)
    screen.fill(LOCATIONS[loc_idx]['bg'])
    
    for r in range(ROWS):
        for c in range(COLS):
            if grid_map[r][c]==2:
                draw_tile_3d(screen,c,r,'road',r_cam_x,r_cam_y)
                x,y = to_iso(c,r,r_cam_x,r_cam_y)
                pygame.draw.circle(screen,(70,70,70),(x,y-10),12)
                pygame.draw.circle(screen,(200,0,0),(x,y-10),5)
            elif (c,r) in path: draw_tile_3d(screen,c,r,'road',r_cam_x,r_cam_y)
            else: draw_tile_3d(screen,c,r,'grass',r_cam_x,r_cam_y)
            
    for obj in enemies + towers: 
        if hasattr(obj, 'update_pos'): 
            obj.update_pos(r_cam_x, r_cam_y)

    all_drawable = sorted(enemies + towers, key=lambda o:o.screen_y if hasattr(o,'screen_y') else 0)
    for obj in all_drawable: 
        obj.draw(screen)
    for p in projectiles: p.draw(screen)
    fx.draw(screen)

    # === UI ===
    
    # 1. Статистика и Полоски Ресурсов
    current_limit = BASE_TOWER_LIMIT + (global_upgrades['capacity'] * 2)
    
    # Текст статистики
    info = f"$ {money}  | CR: {crystals} | T: {len(towers)}/{current_limit} | ⚡ {int(energy)} | 🌑 {int(dark_matter)} | HP: {lives}"
    screen.blit(font.render(info, True, Colors.ACCENT), (10, 10))
    
    # --- ПОЛОСКИ РЕСУРСОВ ---
    
    # 1. Энергия (Синяя)
    pygame.draw.rect(screen, (30, 30, 40), (10, 40, 100, 8), border_radius=2)
    pygame.draw.rect(screen, (0, 200, 255), (10, 40, 100 * (energy / max_energy), 8), border_radius=2)
    
    # 2. Темная Материя (Фиолетовая)
    pygame.draw.rect(screen, (30, 30, 40), (10, 55, 100, 8), border_radius=2)
    pygame.draw.rect(screen, Colors.VOID_PURPLE, (10, 55, 100 * (dark_matter / max_dark_matter), 8), border_radius=2)

    # 3. Жизни / HP (Красная)
    max_lives_display = 20 
    hp_percent = lives / max_lives_display if max_lives_display > 0 else 0
    pygame.draw.rect(screen, (30, 30, 40), (10, 70, 100, 8), border_radius=2)
    pygame.draw.rect(screen, (255, 50, 50), (10, 70, 100 * hp_percent, 8), border_radius=2)

    # 2. Кнопка Меню (ПРАВЫЙ ВЕРХНИЙ УГОЛ)
    menu_rect = pygame.Rect(MENU_BTN_X, MENU_BTN_Y, MENU_BTN_W, MENU_BTN_H)
    col_menu = Colors.ACCENT if menu_open else (60,60,80)
    pygame.draw.rect(screen, col_menu, menu_rect, border_radius=8)
    pygame.draw.rect(screen, Colors.WHITE, menu_rect, 2, border_radius=8)
    screen.blit(font.render("MENU", True, Colors.WHITE), (MENU_BTN_X + 15, MENU_BTN_Y + 10))

    # 3. Вертикальное меню юнитов (Слева столбиком)
    all_unit_keys = ['soldier', 'flame', 'sniper', 'mine']
    for k in SHOP_UNITS.keys():
        if k in UNITS: all_unit_keys.append(k)

    start_idx = unit_scroll
    end_idx = min(start_idx + V_MAX_VISIBLE, len(all_unit_keys))
    visible_keys_render = all_unit_keys[start_idx : end_idx]
    
    current_count = len(visible_keys_render)
    buttons_block_height = current_count * V_BTN_H + (current_count - 1) * V_GAP
    
    arrow_y_pos = V_MENU_Y_START + buttons_block_height + 10
    arrow_h = 30
    arrow_w = 70
    
    left_arrow_rect = pygame.Rect(V_MENU_X, arrow_y_pos, arrow_w, arrow_h)
    right_arrow_rect = pygame.Rect(V_MENU_X + arrow_w + 10, arrow_y_pos, arrow_w, arrow_h)

    # Рисуем кнопки юнитов
    for i, k in enumerate(visible_keys_render):
        x = V_MENU_X
        y = V_MENU_Y_START + i * (V_BTN_H + V_GAP)
        
        rect = pygame.Rect(x, y, V_BTN_W, V_BTN_H)
        bg_col = Colors.ACCENT if selected_unit == k else (60,60,70)
        
        pygame.draw.rect(screen, bg_col, rect, border_radius=6)
        pygame.draw.rect(screen, (20,20,30), rect, 2, border_radius=6)
        
        screen.blit(font.render(f"[{start_idx + i + 1}]", True, (150,150,150)), (x+5, y+5))
        screen.blit(font.render(UNITS[k]['name'], True, Colors.WHITE), (x+30, y+5))
        screen.blit(font.render(f"${UNITS[k].get('cost',0)}", True, Colors.GOLD), (x+30, y+25))

    # Рисуем стрелки ПРОКРУТКИ ПОД кнопками
    if len(all_unit_keys) > V_MAX_VISIBLE:
        # Стрелка ВЛЕВО (<)
        pygame.draw.rect(screen, (60,60,80), left_arrow_rect, border_radius=4)
        font_arrow = pygame.font.SysFont('consolas', 24, bold=True)
        screen.blit(font_arrow.render("< PREV", True, Colors.WHITE), (V_MENU_X + 5, arrow_y_pos + 5))
        
        # Стрелка ВПРАВО (>)
        pygame.draw.rect(screen, (60,60,80), right_arrow_rect, border_radius=4)
        screen.blit(font_arrow.render("NEXT >", True, Colors.WHITE), (V_MENU_X + arrow_w + 15, arrow_y_pos + 5))

    # === ОКНО МЕНЮ (Отрисовка) ===
    if menu_open:
        menu_w, menu_h = 600, 450
        menu_x = (W - menu_w) // 2
        menu_y = (H - menu_h) // 2
        
        pygame.draw.rect(screen, Colors.UI_PANEL, (menu_x, menu_y, menu_w, menu_h), border_radius=12)
        pygame.draw.rect(screen, Colors.ACCENT, (menu_x, menu_y, menu_w, menu_h), 3, border_radius=12)
        
        tabs = ['UPGRADES', 'SHOP', 'DONATE']
        tab_w, tab_h = 130, 40
        tab_start_x = menu_x + (menu_w - 3 * tab_w - 2 * 10) // 2
        tab_y = menu_y + 10
        
        for t in range(3):
            tx = tab_start_x + t * (tab_w + 10)
            col = Colors.ACCENT if menu_tab == t else Colors.WHITE
            bg = Colors.UI_TAB if menu_tab == t else (40, 40, 60)
            rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            pygame.draw.rect(screen, bg, rect, border_radius=8)
            screen.blit(font.render(tabs[t], True, col), (tx + 15, tab_y + 10))

        content_x = menu_x + 30
        content_y = menu_y + 70
        item_w = menu_w - 60
        item_h = 65
        max_visible = 5
        
        scroll_w = 50
        left_x = menu_x + 40
        right_x = menu_x + menu_w - 40 - scroll_w
        start_y_content = menu_y + 80
        card_x_start = menu_x + 100
        card_width = menu_w - 200

        if menu_tab == 0: # UPGRADES VISUAL
            all_upgrades = [
                ('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL),
                ('Energy Cap +100', 'energy_cap', global_upgrades['energy_cap'], ENERGY_UPGRADE_COSTS, Colors.BLUE)
            ]
            
            visible_ups = all_upgrades[upgrade_scroll : upgrade_scroll + max_visible]
            
            pygame.draw.rect(screen, (60,60,80), (left_x, start_y_content, scroll_w, item_h), border_radius=5)
            pygame.draw.rect(screen, (60,60,80), (right_x, start_y_content, scroll_w, item_h), border_radius=5)
            font_arrow = pygame.font.SysFont('consolas', 30, bold=True)
            screen.blit(font_arrow.render("<", True, Colors.WHITE), (left_x + 15, start_y_content + 15))
            screen.blit(font_arrow.render(">", True, Colors.WHITE), (right_x + 15, start_y_content + 15))

            for i, (name, key, lvl, costs, col) in enumerate(visible_ups):
                y_card = start_y_content + i * (item_h + 10)
                cost = costs[lvl] if lvl < len(costs) else 'MAX'
                can_buy = money >= cost if isinstance(cost, int) else False
                c_text = Colors.WHITE if lvl >= len(costs) else (col if can_buy else (100,100,100))
                
                rect = pygame.Rect(card_x_start, y_card, card_width, item_h)
                pygame.draw.rect(screen, (50,50,70), rect, border_radius=8)
                screen.blit(font.render(f"{name} [Lvl {lvl}/{len(costs)}]", True, Colors.WHITE), (card_x_start + 10, y_card + 10))
                screen.blit(font.render(f"Cost: {cost}$", True, c_text), (card_x_start + 10, y_card + 38))

        elif menu_tab == 1: # SHOP VISUAL
            visible_keys_shop = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll+max_visible]
            
            pygame.draw.rect(screen, (60,60,80), (left_x, start_y_content, scroll_w, item_h), border_radius=5)
            pygame.draw.rect(screen, (60,60,80), (right_x, start_y_content, scroll_w, item_h), border_radius=5)
            font_arrow = pygame.font.SysFont('consolas', 30, bold=True)
            screen.blit(font_arrow.render("<", True, Colors.WHITE), (left_x + 15, start_y_content + 15))
            screen.blit(font_arrow.render(">", True, Colors.WHITE), (right_x + 15, start_y_content + 15))

            for i, k in enumerate(visible_keys_shop):
                v = SHOP_UNITS[k]
                y_card = start_y_content + i * (item_h + 10)
                
                owned = k in UNITS
                status = "OWNED" if owned else f"{v['cost_crystals']} CR"
                col = Colors.GREEN if owned else Colors.CRYSTAL
                
                rect = pygame.Rect(card_x_start, y_card, card_width, item_h)
                pygame.draw.rect(screen, (50,50,70), rect, border_radius=8)
                
                screen.blit(font.render(f"{v['name']} - {status}", True, col), (card_x_start + 10, y_card + 15))
                if not owned: 
                    screen.blit(font.render(f"Price: ${v['cost']}", True, Colors.GOLD), (card_x_start + 10, y_card + 38))

        elif menu_tab == 2: # DONATE VISUAL
            donate_items = [("Watch Ad: +1 CR", Colors.GREEN), ("Buy 3 CR: 500$", Colors.GOLD), ("Monthly Pack: 10 CR", Colors.CRYSTAL)]
            for i, (txt, col) in enumerate(donate_items):
                y_don = content_y + i * (item_h + 10)
                rect = pygame.Rect(content_x, y_don, item_w, item_h)
                pygame.draw.rect(screen, (30,40,50), rect, border_radius=8)
                screen.blit(font.render(txt, True, col), (content_x + 10, y_don + 25))

        close_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 80, 90, 60)
        pygame.draw.rect(screen, Colors.RED, close_rect, border_radius=8)
        screen.blit(font.render("CLOSE", True, Colors.WHITE), (close_rect.x + 10, close_rect.y + 20))

    pygame.display.flip()

pygame.quit(); sys.exit()
