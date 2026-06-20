import pygame, sys, random, math
from settings import *
from engine import draw_tile_3d, from_iso, to_iso
from entities import Tower, Enemy, Projectile
from map_gen import generate_path
from save_manager import load_game, save_game
from effects import EffectsManager
from ui import UIManager

pygame.init()
screen = pygame.display.set_mode((W, H), SCREEN_FLAGS)
pygame.display.set_caption("DELTA CORE: PRO")
clock = pygame.time.Clock()

font = pygame.font.SysFont('consolas', 18, bold=True)
font_big = pygame.font.SysFont('consolas', 40, bold=True)
font_menu_btn = pygame.font.SysFont('consolas', 28, bold=True)
font_arrow = pygame.font.SysFont('consolas', 24, bold=True)

ui_manager = UIManager(screen, font, font_big, font_menu_btn, font_arrow)

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
money, crystals = START_MONEY, START_CRYSTALS
energy = START_ENERGY
max_energy = MAX_ENERGY
dark_matter = START_DARK_MATTER
max_dark_matter = MAX_DARK_MATTER
wave, lives = 1, 20
LEVEL = 1
cam_x, cam_y = W//2, H//3
path, grid_map = None, None
towers, enemies, projectiles = [], [], []
spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
selected_unit, dragging, last_mouse = 'soldier', False, (0,0)
drag_start_pos = (0,0)
game_state = 'playing'
menu_open, menu_tab = False, 0
pause_menu_open = False
shop_scroll = 0
unit_scroll = 0
upgrade_scroll = 0
global_upgrades = {'dmg': 0, 'rate': 0, 'hp': 0, 'income': 0, 'capacity': 0, 'energy_cap': 0}
fx = EffectsManager()

BIOMES = [
    {'name': 'FOREST',   'bg': (34, 60, 34)},
    {'name': 'DESERT',   'bg': (82, 70, 48)},
    {'name': 'ICE',      'bg': (40, 60, 80)},
    {'name': 'VOLCANO',  'bg': (60, 30, 30)},
    {'name': 'VOID',     'bg': (20, 10, 40)},
]

def start_wave():
    global enemies_to_spawn, boss_wave, wave_active
    wave_active = True
    if wave % 5 == 0 and wave % 50 != 0:
        enemies_to_spawn, boss_wave = 1, 5 if wave == 5 else 10
    elif wave % 50 == 0:
        enemies_to_spawn, boss_wave = 1, 50
    else:
        enemies_to_spawn, boss_wave = 6 + wave * 2, 0

def reset():
    global money, crystals, energy, max_energy, dark_matter, max_dark_matter
    global wave, lives, LEVEL, cam_x, cam_y, path, grid_map
    global towers, enemies, projectiles, spawn_timer, wave_active, enemies_to_spawn, boss_wave
    global game_state, menu_open, menu_tab, shop_scroll, unit_scroll, upgrade_scroll, pause_menu_open
    
    saved = load_game()
    crystals = saved['crystals']
    for key in saved['unlocked_units']:
        if key in SHOP_UNITS and key not in UNITS:
            UNITS[key] = SHOP_UNITS[key]

    LEVEL = 1
    wave = 1
    lives = 20
    money = START_MONEY * LEVEL + 200 * (LEVEL - 1)
    energy, max_energy = START_ENERGY, MAX_ENERGY
    dark_matter, max_dark_matter = START_DARK_MATTER, MAX_DARK_MATTER
    cam_x, cam_y = W//2, H//3
    
    path, grid_map = generate_path(COLS, ROWS)
    towers, enemies, projectiles = [], [], []
    spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
    game_state = 'playing'
    menu_open, menu_tab = False, 0
    pause_menu_open = False
    shop_scroll, unit_scroll, upgrade_scroll = 0, 0, 0
    global_upgrades['energy_cap'] = 0
    start_wave()

reset()

running = True
while running:
    dt = clock.tick(FPS)
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == 'playing':
                    pause_menu_open = not pause_menu_open
                    menu_open = False
                elif pause_menu_open:
                    pause_menu_open = False
                    
            if event.key == pygame.K_p and game_state == 'playing' and not pause_menu_open:
                menu_open = not menu_open
                
            if event.key == pygame.K_r and game_state == 'game_over':
                reset()
                
            if game_state == 'playing' and not menu_open and not pause_menu_open:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                    idx = event.key - pygame.K_1
                    all_keys = ['soldier', 'flame', 'sniper', 'mine'] + [k for k in SHOP_UNITS.keys() if k in UNITS]
                    visible = all_keys[unit_scroll:unit_scroll + V_MAX_VISIBLE]
                    if idx < len(visible):
                        selected_unit = visible[idx]

    # === GAME OVER ===
    if game_state == 'game_over':
        screen.fill((0,0,0))
        txt = font_big.render("GAME OVER", True, Colors.RED)
        screen.blit(txt, (W//2-txt.get_width()//2, H//2-40))
        txt2 = font.render(f"CR: {crystals} | Press [R]", True, Colors.WHITE)
        screen.blit(txt2, (W//2-txt2.get_width()//2, H//2+20))
        pygame.display.flip()
        continue

    # === LOGIC ===
    if not menu_open and not pause_menu_open and game_state == 'playing':
        if energy < max_energy:
            energy += ENERGY_REGEN
        if dark_matter < max_dark_matter:
            dark_matter += DARK_MATTER_REGEN

        level_mult = 1 + (LEVEL - 1) * 2
        mult = level_mult * (1 + wave * 0.02) + (global_upgrades['income'] * 0.05)

        if wave_active and enemies_to_spawn > 0:
            spawn_timer += 1
            if spawn_timer > 45:
                tk = 'runner' if wave > 5 and random.random() > 0.6 else 'normal'
                if wave > 12 and random.random() > 0.7:
                    tk = 'tank'
                enemies.append(Enemy(path, tk, mult, boss_wave != 0, boss_wave))
                enemies_to_spawn -= 1
                spawn_timer = 0

        if enemies_to_spawn == 0 and not enemies and wave_active:
            wave_active = False
            money += 150 + wave * 5
            if wave >= 50:
                LEVEL += 1
                wave = 1
                money += 500 * LEVEL
                lives = 20
                path, grid_map = generate_path(COLS, ROWS)
                towers.clear()
                grid_map = [[0] * COLS for _ in range(ROWS)]
                fx.spawn_explosion(W//2, H//2, (255, 215, 0), 50)
                fx.add_shake(15)
            else:
                wave += 1
            start_wave()

        for e in enemies[:]:
            if e.move(grid_map):
                lives -= 1
                enemies.remove(e)
            elif e.is_dead():
                money += e.reward
                crystals += e.crystals
                fx.spawn_explosion(e.screen_x, e.screen_y, e.color, 20)
                fx.add_shake(5)
                if e.crystals > 0:
                    save_game(crystals, list(UNITS.keys()))
                enemies.remove(e)
            else:
                e.update_speed_recovery()
                e.update_pos(cam_x, cam_y)

        for t in towers:
            t.update(enemies, projectiles, cam_x, cam_y, fx, None, energy, dark_matter)

        for p in projectiles[:]:
            p.update(enemies, fx)
            if not p.active:
                projectiles.remove(p)

        fx.update()
        
        if lives <= 0:
            game_state = 'game_over'

    # === INPUT ===
    mouse_buttons = pygame.mouse.get_pressed()
    
    if mouse_buttons[0] and game_state == 'playing' and not menu_open and not pause_menu_open:
        if not dragging:
            dragging = True
            drag_start_pos = (mx, my)
        else:
            dx = mx - drag_start_pos[0]
            dy = my - drag_start_pos[1]
            cam_x += dx * 0.3
            cam_y += dy * 0.3
            drag_start_pos = (mx, my)
    
    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        if dragging and game_state == 'playing':
            dragging = False
            if math.hypot(mx - drag_start_pos[0], my - drag_start_pos[1]) < 5 and not menu_open and not pause_menu_open:
                c, r = from_iso(mx, my, cam_x, cam_y)
                if 0 <= r < ROWS and 0 <= c < COLS:
                    # === ПРОВЕРКА: ЕСТЬ ЛИ УЖЕ БАШНЯ НА ЭТОЙ КЛЕТКЕ ===
                    tower_exists = any(t.c == c and t.r == r for t in towers)
                    
                    if grid_map[r][c] == 0 and not tower_exists:  # ТОЛЬКО ТРАВА И НЕТ БАШНИ!
                        current_limit = BASE_TOWER_LIMIT + (global_upgrades['capacity'] * 2)
                        unit_data = UNITS.get(selected_unit)
                        if unit_data and money >= unit_data['cost']:
                            if len(towers) < current_limit:
                                money -= unit_data['cost']
                                towers.append(Tower(c, r, selected_unit, global_upgrades))
                                fx.spawn_explosion(mx, my, (0, 255, 0), 5)
                            else:
                                fx.spawn_damage(mx, my, "FULL!")
                        else:
                            fx.spawn_damage(mx, my, "NO $")
                    elif grid_map[r][c] == 1 and selected_unit == 'mine' and not tower_exists:  # МИНА НА ДОРОГЕ
                        unit_data = UNITS.get('mine')
                        if unit_data and money >= unit_data['cost']:
                            money -= unit_data['cost']
                            grid_map[r][c] = 2
                            fx.spawn_explosion(mx, my, (0, 255, 0), 5)
                    elif tower_exists:
                        fx.spawn_damage(mx, my, "OCCUPIED!")

    # УДАЛЕНИЕ БАШНИ (ПКМ)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        if game_state == 'playing' and not menu_open and not pause_menu_open:
            c, r = from_iso(mx, my, cam_x, cam_y)
            if 0 <= c < COLS and 0 <= r < ROWS:
                for t in towers[:]:
                    if t.c == c and t.r == r:
                        money += int(t.data['cost'] * 0.3)
                        towers.remove(t)
                        # grid_map НЕ МЕНЯЕМ - трава остается!
                        fx.spawn_explosion(t.screen_x, t.screen_y, (0, 255, 0), 10)
                        break

    # МЕНЮ ПАУЗЫ (ESC)
    if pause_menu_open:
        rects = ui_manager.draw_pause_menu()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if rects.get("RESUME") and rects["RESUME"].collidepoint(mx, my):
                pause_menu_open = False
            elif rects.get("SAVE") and rects["SAVE"].collidepoint(mx, my):
                save_game(crystals, list(UNITS.keys()))
                fx.spawn_explosion(W//2, H//2, (0, 255, 0), 30)
            elif rects.get("LOAD") and rects["LOAD"].collidepoint(mx, my):
                saved = load_game()
                crystals = saved['crystals']
                for key in saved['unlocked_units']:
                    if key in SHOP_UNITS and key not in UNITS:
                        UNITS[key] = SHOP_UNITS[key]
                fx.spawn_explosion(W//2, H//2, (255, 215, 0), 30)
            elif rects.get("MAIN MENU") and rects["MAIN MENU"].collidepoint(mx, my):
                game_state = 'main_menu'
                pause_menu_open = False

    # МЕНЮ ПРОКАЧКИ (P)
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if game_state == 'playing' and menu_open:
            menu_w, menu_h = 600, 450
            menu_x = (W - menu_w) // 2
            menu_y = (H - menu_h) // 2
            
            close_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 80, 90, 60)
            if close_rect.collidepoint(mx, my):
                menu_open = False
            
            tabs = ['UPGRADES', 'SHOP', 'DONATE']
            tab_w, tab_h = 130, 40
            tab_start_x = menu_x + (menu_w - 3 * tab_w - 2 * 10) // 2
            tab_y = menu_y + 10
            for t in range(3):
                tx = tab_start_x + t * (tab_w + 10)
                rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
                if rect.collidepoint(mx, my):
                    menu_tab = t
            
            content_x = menu_x + 30
            content_y = menu_y + 70
            item_w = menu_w - 60
            item_h = 65
            scroll_w = 50
            left_x = menu_x + 40
            right_x = menu_x + menu_w - 40 - scroll_w
            start_y_content = menu_y + 80
            
            if menu_tab == 0:
                max_allowed = (LEVEL * (LEVEL + 1) // 2) * 5
                all_upgrades = [
                    ('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                    ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                    ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                    ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL),
                    ('Energy Cap +100', 'energy_cap', global_upgrades['energy_cap'], ENERGY_UPGRADE_COSTS, Colors.BLUE)
                ]
                if pygame.Rect(left_x, start_y_content, scroll_w, item_h).collidepoint(mx, my):
                    if upgrade_scroll > 0:
                        upgrade_scroll -= 1
                elif pygame.Rect(right_x, start_y_content, scroll_w, item_h).collidepoint(mx, my):
                    if upgrade_scroll < len(all_upgrades) - 5:
                        upgrade_scroll += 1
                else:
                    visible_ups = all_upgrades[upgrade_scroll:upgrade_scroll + 5]
                    card_x_start = menu_x + 100
                    card_width = menu_w - 200
                    for i, (name, key, lvl, costs, col) in enumerate(visible_ups):
                        y_card = start_y_content + i * (item_h + 10)
                        rect_card = pygame.Rect(card_x_start, y_card, card_width, item_h)
                        if rect_card.collidepoint(mx, my):
                            cost = costs[lvl] if lvl < len(costs) else 'MAX'
                            if lvl < max_allowed and lvl < len(costs) and money >= cost:
                                money -= cost
                                global_upgrades[key] += 1
                                if key == 'energy_cap':
                                    max_energy += ENERGY_UPGRADE_BONUS[lvl]
                                    energy = min(energy + ENERGY_UPGRADE_BONUS[lvl], max_energy)
            
            elif menu_tab == 1:
                visible_keys_shop = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll + 5]
                if pygame.Rect(left_x, start_y_content, scroll_w, item_h).collidepoint(mx, my):
                    if shop_scroll > 0:
                        shop_scroll -= 1
                elif pygame.Rect(right_x, start_y_content, scroll_w, item_h).collidepoint(mx, my):
                    if shop_scroll < len(SHOP_UNITS) - 5:
                        shop_scroll += 1
                else:
                    card_x_start = menu_x + 100
                    card_width = menu_w - 200
                    for i, k in enumerate(visible_keys_shop):
                        v = SHOP_UNITS[k]
                        y_card = start_y_content + i * (item_h + 10)
                        rect_card = pygame.Rect(card_x_start, y_card, card_width, item_h)
                        if rect_card.collidepoint(mx, my):
                            if crystals >= v['cost_crystals'] and k not in UNITS:
                                UNITS[k] = v
                                crystals -= v['cost_crystals']
                                save_game(crystals, list(UNITS.keys()))
            
            elif menu_tab == 2:
                donate_items = [("Watch Ad: +1 CR", Colors.GREEN), ("Buy 3 CR: 500$", Colors.GOLD), ("Monthly Pack: 10 CR", Colors.CRYSTAL)]
                for i, (txt, col) in enumerate(donate_items):
                    y_don = content_y + i * (item_h + 10)
                    rect_don = pygame.Rect(content_x, y_don, item_w, item_h)
                    if rect_don.collidepoint(mx, my):
                        if "Ad" in txt:
                            crystals += 1
                        if "Buy" in txt and money >= 500:
                            money -= 500
                            crystals += 3
                        if "Pack" in txt and crystals >= 10:
                            crystals -= 10

    # === RENDER ===
    sx, sy = fx.get_shake_offset()
    r_cam_x, r_cam_y = cam_x + sx, cam_y + sy
    
    biome_idx = ((LEVEL - 1) // 10) % len(BIOMES)
    current_biome = BIOMES[biome_idx]
    screen.fill(current_biome['bg'])
    
    # ОТРИСОВКА КАРТЫ
    for r in range(ROWS):
        for c in range(COLS):
            if grid_map and r < len(grid_map) and c < len(grid_map[r]):
                if grid_map[r][c] == 2:  # МИНА
                    draw_tile_3d(screen, c, r, 'road', r_cam_x, r_cam_y)
                    x, y = to_iso(c, r, r_cam_x, r_cam_y)
                    pygame.draw.circle(screen, (70,70,70), (x,y-10), 12)
                    pygame.draw.circle(screen, (200,0,0), (x,y-10), 5)
                elif grid_map[r][c] == 1:  # ДОРОГА
                    draw_tile_3d(screen, c, r, 'road', r_cam_x, r_cam_y)
                else:  # ТРАВА
                    draw_tile_3d(screen, c, r, 'grass', r_cam_x, r_cam_y)

    # ОТРИСОВКА БАШЕН, ВРАГОВ, СНАРЯДОВ
    for t in towers:
        t.draw(screen, energy, dark_matter)
    for e in enemies:
        e.draw(screen)
    for p in projectiles:
        p.draw(screen)
    
    fx.draw(screen)

    # === HUD ===
    current_limit = BASE_TOWER_LIMIT + (global_upgrades['capacity'] * 2)
    info = f"LVL {LEVEL} | {current_biome['name']} | W: {wave}/50 | $ {money} | CR: {crystals} | T: {len(towers)}/{current_limit} | ⚡ {int(energy)} | 🌑 {int(dark_matter)} | HP: {lives}"
    screen.blit(font.render(info, True, Colors.ACCENT), (10, 10))
    
    pygame.draw.rect(screen, (30, 30, 40), (10, 40, 100, 8), border_radius=2)
    pygame.draw.rect(screen, (0, 200, 255), (10, 40, 100 * (energy / max_energy), 8), border_radius=2)
    
    pygame.draw.rect(screen, (30, 30, 40), (10, 55, 100, 8), border_radius=2)
    pygame.draw.rect(screen, Colors.VOID_PURPLE, (10, 55, 100 * (dark_matter / max_dark_matter), 8), border_radius=2)
    
    pygame.draw.rect(screen, (30, 30, 40), (10, 70, 100, 8), border_radius=2)
    pygame.draw.rect(screen, (255, 50, 50), (10, 70, 100 * (lives / 20), 8), border_radius=2)

    menu_rect = pygame.Rect(MENU_BTN_X, MENU_BTN_Y, MENU_BTN_W, MENU_BTN_H)
    pygame.draw.rect(screen, Colors.ACCENT if menu_open else (60,60,80), menu_rect, border_radius=8)
    pygame.draw.rect(screen, Colors.WHITE, menu_rect, 2, border_radius=8)
    screen.blit(font.render("MENU (P)", True, Colors.WHITE), (MENU_BTN_X + 5, MENU_BTN_Y + 10))

    all_keys = ['soldier', 'flame', 'sniper', 'mine'] + [k for k in SHOP_UNITS.keys() if k in UNITS]
    start_idx = unit_scroll
    end_idx = min(start_idx + V_MAX_VISIBLE, len(all_keys))
    visible_keys = all_keys[start_idx:end_idx]
    
    for i, k in enumerate(visible_keys):
        x = V_MENU_X
        y = V_MENU_Y_START + i * (V_BTN_H + V_GAP)
        rect = pygame.Rect(x, y, V_BTN_W, V_BTN_H)
        bg_col = Colors.ACCENT if selected_unit == k else (60,60,70)
        pygame.draw.rect(screen, bg_col, rect, border_radius=6)
        pygame.draw.rect(screen, (20,20,30), rect, 2, border_radius=6)
        screen.blit(font.render(f"[{start_idx + i + 1}]", True, (150,150,150)), (x+5, y+5))
        screen.blit(font.render(UNITS[k]['name'], True, Colors.WHITE), (x+30, y+5))
        screen.blit(font.render(f"${UNITS[k].get('cost',0)}", True, Colors.GOLD), (x+30, y+25))
    
    if len(all_keys) > V_MAX_VISIBLE:
        arrow_y = V_MENU_Y_START + len(visible_keys) * (V_BTN_H + V_GAP) + 10
        pygame.draw.rect(screen, (60,60,80), (V_MENU_X, arrow_y, 70, 30), border_radius=4)
        screen.blit(font_arrow.render("<", True, Colors.WHITE), (V_MENU_X + 25, arrow_y + 5))
        pygame.draw.rect(screen, (60,60,80), (V_MENU_X + 80, arrow_y, 70, 30), border_radius=4)
        screen.blit(font_arrow.render(">", True, Colors.WHITE), (V_MENU_X + 105, arrow_y + 5))

    # === МЕНЮ ПРОКАЧКИ (P) ===
    if menu_open and not pause_menu_open:
        ui_manager.draw_in_game_menu(
            menu_tab, global_upgrades, LEVEL, money,
            max_energy, energy, UPGRADE_COSTS,
            ENERGY_UPGRADE_COSTS, ENERGY_UPGRADE_BONUS,
            SHOP_UNITS, UNITS, crystals,
            0, 0, False, upgrade_scroll, shop_scroll
        )

    pygame.display.flip()

pygame.quit()
sys.exit()
