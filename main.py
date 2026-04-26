import pygame, sys, random
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

money, crystals = START_MONEY, START_CRYSTALS
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
unit_scroll = 0 # Индекс начала страницы (0, 5, 10...)

fx = EffectsManager()

def reset():
    global money, crystals, wave, lives, cam_x, cam_y, path, grid_map
    global towers, enemies, projectiles, spawn_timer, wave_active, enemies_to_spawn, boss_wave
    global game_state, mega_boss_killed, menu_open, menu_tab, shop_scroll, unit_scroll
    
    saved = load_game()
    crystals = saved['crystals']
    for key in saved['unlocked_units']:
        if key in SHOP_UNITS and key not in UNITS:
            UNITS[key] = SHOP_UNITS[key]
    
    money, wave, lives = START_MONEY, 1, 20
    cam_x, cam_y = W//2, H//3
    path, grid_map = generate_path(COLS, ROWS)
    towers, enemies, projectiles = [], [], []
    spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
    game_state, mega_boss_killed, menu_open, menu_tab, shop_scroll, unit_scroll = 'playing', False, False, 0, 0, 0
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
            
            # Горячие клавиши 1-5 для ТЕКУЩЕЙ ВИДИМОЙ ПЯТЕРКИ
            if not menu_open:
                all_keys_temp = ['soldier', 'flame', 'sniper', 'mine']
                for k in SHOP_UNITS.keys():
                    if k in UNITS: all_keys_temp.append(k)
                
                start_idx = unit_scroll
                end_idx = min(start_idx + 5, len(all_keys_temp))
                visible_temp = all_keys_temp[start_idx:end_idx]
                
                if ev.key == pygame.K_1 and len(visible_temp) > 0: selected_unit = visible_temp[0]
                if ev.key == pygame.K_2 and len(visible_temp) > 1: selected_unit = visible_temp[1]
                if ev.key == pygame.K_3 and len(visible_temp) > 2: selected_unit = visible_temp[2]
                if ev.key == pygame.K_4 and len(visible_temp) > 3: selected_unit = visible_temp[3]
                if ev.key == pygame.K_5 and len(visible_temp) > 4: selected_unit = visible_temp[4]

        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            
            # --- ЛКМ (1) ---
            if ev.button == 1:
                if menu_open:
                    menu_w_tmp, menu_h_tmp = 600, 450
                    menu_x_tmp = (W - menu_w_tmp) // 2
                    menu_y_tmp = (H - menu_h_tmp) // 2
                    
                    tab_w = 130
                    tab_start_x_tmp = menu_x_tmp + (menu_w_tmp - 3 * tab_w - 2 * 10) // 2
                    tab_y_tmp = menu_y_tmp + 10
                    
                    clicked = False
                    for t in range(3):
                        tx = tab_start_x_tmp + t * (tab_w + 10)
                        rect = pygame.Rect(tx, tab_y_tmp, tab_w, 40)
                        if rect.collidepoint(mx, my):
                            menu_tab = t
                            clicked = True
                    
                    close_rect_tmp = pygame.Rect(menu_x_tmp + 20, menu_y_tmp + menu_h_tmp - 80, 90, 60)
                    if close_rect_tmp.collidepoint(mx, my): 
                        menu_open = False
                        clicked = True
                    
                    if not clicked:
                        content_x_tmp = menu_x_tmp + 30
                        content_y_tmp = menu_y_tmp + 70
                        item_w_tmp = menu_w_tmp - 60
                        item_h_tmp = 65

                        if menu_tab == 0: # Upgrades
                            upgrades = [('dmg', 160), ('rate', 230), ('income', 300), ('capacity', 370)]
                            for key_idx, y_pos_offset in enumerate([0, 75, 150, 225]):
                                 y_abs = content_y_tmp + y_pos_offset
                                 key_name = ['dmg','rate','income','capacity'][key_idx]
                                 lvl = global_upgrades[key_name]
                                 rect_up = pygame.Rect(content_x_tmp, y_abs, item_w_tmp, item_h_tmp)
                                 if rect_up.collidepoint(mx, my):
                                     cost = UPGRADE_COSTS[key_name][lvl]
                                     if lvl < 5 and money >= cost: 
                                         money -= cost; global_upgrades[key_name] += 1
                        
                        elif menu_tab == 1: # SHOP
                            visible_keys = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll+3]
                            scroll_w = 50
                            shop_item_h = 75
                            start_y_shop = menu_y_tmp + 80 
                            
                            left_x = menu_x_tmp + 40
                            right_x = menu_x_tmp + menu_w_tmp - 40 - scroll_w
                            card_x_start = menu_x_tmp + 100 
                            card_width = menu_w_tmp - 200   

                            if pygame.Rect(left_x, start_y_shop, scroll_w, shop_item_h).collidepoint(mx, my):
                                if shop_scroll > 0: shop_scroll -= 1
                                pygame.time.wait(150)
                            elif pygame.Rect(right_x, start_y_shop, scroll_w, shop_item_h).collidepoint(mx, my):
                                if shop_scroll < len(SHOP_UNITS) - 3: shop_scroll += 1
                                pygame.time.wait(150)
                            else:
                                for i, k in enumerate(visible_keys):
                                    v = SHOP_UNITS[k]
                                    y_card = start_y_shop + i * (shop_item_h + 10)
                                    rect_card = pygame.Rect(card_x_start, y_card, card_width, shop_item_h)
                                    if rect_card.collidepoint(mx, my):
                                        if crystals >= v['cost_crystals'] and k not in UNITS:
                                            UNITS[k] = v
                                            crystals -= v['cost_crystals']
                                            save_game(crystals, list(UNITS.keys()))
                                            pygame.time.wait(200)

                        elif menu_tab == 2: # Donate
                             donate_items = [("Watch Ad: +1 CR", Colors.GREEN), ("Buy 3 CR: 500$", Colors.GOLD), ("Monthly Pack: 10 CR", Colors.CRYSTAL)]
                             for i, (txt, col) in enumerate(donate_items):
                                 y_don = content_y_tmp + i * (item_h_tmp + 10)
                                 rect_don = pygame.Rect(content_x_tmp, y_don, item_w_tmp, item_h_tmp)
                                 if rect_don.collidepoint(mx, my):
                                     if "Ad" in txt: crystals += 1
                                     if "Buy" in txt and money >= 500: money -= 500; crystals += 3
                                     if "Pack" in txt and crystals >= 10: crystals -= 10
                
                else: # Геймплей
                    ui_h = 100
                    
                    # --- ЛОГИКА НИЖНЕЙ ПАНЕЛИ (СДВИГ ВПРАВО НА 150PX) ---
                    offset_right = 150 # Сдвиг всего блока вправо, чтобы не перекрывать HP
                    
                    all_unit_keys = ['soldier', 'flame', 'sniper', 'mine']
                    for k in SHOP_UNITS.keys():
                        if k in UNITS: all_unit_keys.append(k)
                    
                    max_visible = 5
                    btn_w, gap = 110, 10
                    arrow_w = 40
                    
                    start_idx = unit_scroll
                    end_idx = min(start_idx + max_visible, len(all_unit_keys))
                    visible_keys_game = all_unit_keys[start_idx : end_idx]
                    
                    current_count = len(visible_keys_game)
                    buttons_width = current_count * btn_w + (current_count - 1) * gap
                    
                    if len(all_unit_keys) > max_visible:
                        total_block_width = arrow_w + gap + buttons_width + gap + arrow_w
                        # Центрируем, но добавляем смещение вправо
                        start_x_total = ((W - total_block_width) // 2) + offset_right
                        
                        left_arrow_x = start_x_total
                        buttons_start_x = start_x_total + arrow_w + gap
                        right_arrow_x = start_x_total + arrow_w + gap + buttons_width + gap
                        
                        left_arrow_rect = pygame.Rect(left_arrow_x, H-ui_h+10, arrow_w, 55)
                        right_arrow_rect = pygame.Rect(right_arrow_x, H-ui_h+10, arrow_w, 55)
                        
                        if left_arrow_rect.collidepoint(mx, my):
                            if unit_scroll >= max_visible: unit_scroll -= max_visible
                            else: unit_scroll = 0
                            pygame.time.wait(200)
                        elif right_arrow_rect.collidepoint(mx, my):
                            if unit_scroll + max_visible < len(all_unit_keys): unit_scroll += max_visible
                            else: unit_scroll = 0
                            pygame.time.wait(200)
                        else:
                            for i, k in enumerate(visible_keys_game):
                                x = buttons_start_x + i * (btn_w + gap)
                                if x < mx < x + btn_w and H-ui_h+10 < my < H-ui_h+65:
                                    selected_unit = k
                    else:
                        # Если юнитов мало, тоже сдвигаем вправо
                        start_x_game = ((W - buttons_width) // 2) + offset_right
                        for i, k in enumerate(visible_keys_game):
                            x = start_x_game + i * (btn_w + gap)
                            if x < mx < x + btn_w and H-ui_h+10 < my < H-ui_h+65:
                                selected_unit = k

                    if my < H-ui_h:
                         c,r = from_iso(mx,my,cam_x,cam_y)
                         if 0<=c<COLS and 0<=r<ROWS:
                             cost = UNITS[selected_unit].get('cost', 9999)
                             if money >= cost:
                                 if selected_unit=='mine' and grid_map[r][c]==1:
                                     grid_map[r][c]=2; money-=cost
                                 elif selected_unit!='mine' and grid_map[r][c]==0 and len(towers) < 10 + global_upgrades['capacity']*2:
                                     towers.append(Tower(c,r,selected_unit)); grid_map[r][c]=1; money-=cost
                         dragging = True; last_mouse = (mx, my)

            # --- ПКМ (3) ПРОДАЖА ---
            elif ev.button == 3:
                if not menu_open and my < H - 100:
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
            
        if ev.type == pygame.MOUSEMOTION:
            if dragging:
                dx = ev.pos[0]-last_mouse[0]; dy = ev.pos[1]-last_mouse[1]
                if abs(dx) > 2 or abs(dy) > 2:
                    cam_x += dx; cam_y += dy; last_mouse = ev.pos

    # === LOGIC ===
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
        t.update(enemies,projectiles,cam_x,cam_y, fx, screen)
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
        if hasattr(obj, 'update_pos'): obj.update_pos(r_cam_x, r_cam_y)
        
    all_drawable = sorted(enemies + towers, key=lambda o:o.screen_y if hasattr(o,'screen_y') else 0)
    for obj in all_drawable: obj.draw(screen)
    for p in projectiles: p.draw(screen)
    fx.draw(screen)

    # === UI НИЖНЯЯ ПАНЕЛЬ (СДВИГ ВПРАВО НА 150PX) ===
    ui_h = 100
    pygame.draw.rect(screen, Colors.UI_BG, (0, H-ui_h, W, ui_h))
    pygame.draw.line(screen, Colors.ACCENT, (0, H-ui_h), (W, H-ui_h), 2)
    
    info = f"$ {money} | CR: {crystals} | W: {wave} | HP: {lives}"
    screen.blit(font.render(info, True, Colors.ACCENT), (20, H-75))

    all_unit_keys = ['soldier', 'flame', 'sniper', 'mine']
    for k in SHOP_UNITS.keys():
        if k in UNITS: all_unit_keys.append(k)

    max_visible = 5
    btn_w, gap = 110, 10
    arrow_w = 40
    offset_right = 150 # Тот же сдвиг
    
    start_idx = unit_scroll
    end_idx = min(start_idx + max_visible, len(all_unit_keys))
    visible_keys_render = all_unit_keys[start_idx : end_idx]
    
    current_count = len(visible_keys_render)
    buttons_width = current_count * btn_w + (current_count - 1) * gap
    
    if len(all_unit_keys) > max_visible:
        total_block_width = arrow_w + gap + buttons_width + gap + arrow_w
        start_x_total = ((W - total_block_width) // 2) + offset_right
        
        left_arrow_x = start_x_total
        buttons_start_x = start_x_total + arrow_w + gap
        right_arrow_x = start_x_total + arrow_w + gap + buttons_width + gap
        
        pygame.draw.rect(screen, (60,60,80), (left_arrow_x, H-ui_h+10, arrow_w, 55), border_radius=6)
        pygame.draw.rect(screen, (60,60,80), (right_arrow_x, H-ui_h+10, arrow_w, 55), border_radius=6)
        
        font_arrow = pygame.font.SysFont('consolas', 24, bold=True)
        screen.blit(font_arrow.render("<", True, Colors.WHITE), (left_arrow_x + 12, H-ui_h+25))
        screen.blit(font_arrow.render(">", True, Colors.WHITE), (right_arrow_x + 12, H-ui_h+25))
        
    else:
        buttons_start_x = ((W - buttons_width) // 2) + offset_right

    for i, k in enumerate(visible_keys_render):
        x = buttons_start_x + i * (btn_w + gap)
        y = H - ui_h + 10
        
        rect = pygame.Rect(x, y, btn_w, 55)
        
        bg_col = Colors.ACCENT if selected_unit == k else (60,60,70)
        pygame.draw.rect(screen, bg_col, rect, border_radius=6)
        pygame.draw.rect(screen, (20,20,30), rect, 2, border_radius=6)
        
        screen.blit(font.render(f"[{i+1}]", True, (100,100,100)), (x+6, y+4))
        screen.blit(font.render(UNITS[k]['name'], True, Colors.WHITE), (x+20, y+10))
        screen.blit(font.render(f"${UNITS[k].get('cost',0)}", True, Colors.GOLD), (x+20, y+32))

    pygame.draw.rect(screen, Colors.CRYSTAL, (20, 20, 90, 40), 2)
    screen.blit(font.render("[P] MENU", True, Colors.WHITE), (30, 30))

    # === ОКНО МЕНЮ (ОТРИСОВКА) ===
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
        
        if menu_tab == 0:
            upgrades = [('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                        ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                        ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                        ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL)]
            for i, (name, key, lvl, costs, col) in enumerate(upgrades):
                y = content_y + i * (item_h + 10)
                cost = costs[lvl] if lvl < len(costs) else 'MAX'
                can_buy = money >= cost if isinstance(cost, int) else False
                c = Colors.WHITE if lvl>=5 else (col if can_buy else (100,100,100))
                rect = pygame.Rect(content_x, y, item_w, item_h)
                pygame.draw.rect(screen, (50,50,70), rect, border_radius=8)
                screen.blit(font.render(f"{name} [Lvl {lvl}/5]", True, Colors.WHITE), (content_x + 10, y + 10))
                screen.blit(font.render(f"Cost: {cost}$", True, c), (content_x + 10, y + 38))

        elif menu_tab == 1: # SHOP VISUAL
            visible_keys_shop = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll+3]
            scroll_w = 50
            shop_item_h = 75
            start_y_shop = menu_y + 80 
            
            left_x = menu_x + 40
            right_x = menu_x + menu_w - 40 - scroll_w
            card_x_start = menu_x + 100 
            card_width = menu_w - 200   

            pygame.draw.rect(screen, (60,60,80), (left_x, start_y_shop, scroll_w, shop_item_h), border_radius=5)
            pygame.draw.rect(screen, (60,60,80), (right_x, start_y_shop, scroll_w, shop_item_h), border_radius=5)
            
            font_arrow = pygame.font.SysFont('consolas', 30, bold=True)
            screen.blit(font_arrow.render("<", True, Colors.WHITE), (left_x + 15, start_y_shop + 15))
            screen.blit(font_arrow.render(">", True, Colors.WHITE), (right_x + 15, start_y_shop + 15))

            for i, k in enumerate(visible_keys_shop):
                v = SHOP_UNITS[k]
                y_card = start_y_shop + i * (shop_item_h + 10)
                
                owned = k in UNITS
                status = "OWNED" if owned else f"{v['cost_crystals']} CR"
                col = Colors.GREEN if owned else Colors.CRYSTAL
                
                rect = pygame.Rect(card_x_start, y_card, card_width, shop_item_h)
                pygame.draw.rect(screen, (50,50,70), rect, border_radius=8)
                
                screen.blit(font.render(f"{v['name']} - {status}", True, col), (card_x_start + 10, y_card + 15))
                if not owned: 
                    screen.blit(font.render(f"Price: ${v['cost']}", True, Colors.GOLD), (card_x_start + 10, y_card + 40))

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
