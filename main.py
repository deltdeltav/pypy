import pygame, sys, random
from settings import *
from engine import draw_tile_3d, from_iso, to_iso
from entities import Tower, Enemy, Projectile

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

def reset():
    global money, crystals, wave, lives, cam_x, cam_y, path, grid_map
    global towers, enemies, projectiles, spawn_timer, wave_active, enemies_to_spawn, boss_wave
    global game_state, mega_boss_killed, menu_open, menu_tab
    money, crystals, wave, lives = START_MONEY, START_CRYSTALS, 1, 20
    cam_x, cam_y = W//2, H//3
    path, grid_map = generate_path(COLS, ROWS)
    towers, enemies, projectiles = [], [], []
    spawn_timer, wave_active, enemies_to_spawn, boss_wave = 0, True, 0, 0
    game_state, mega_boss_killed, menu_open, menu_tab = 'playing', False, False, 0
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

def generate_path(cols, rows):
    path, grid = [], [[0]*cols for _ in range(rows)]
    c, r = cols//2, 0
    path.append((c,r)); grid[r][c] = 1
    while r < rows - 1:
        moves = []
        if c > 0 and grid[r][c-1]==0: moves.append((-1,0))
        if c < cols-1 and grid[r][c+1]==0: moves.append((1,0))
        if r < rows-1 and grid[r+1][c]==0: moves.append((0,1))
        if not moves:
            if r < rows-1: r+=1; path.append((c,r)); grid[r][c]=1
            else: break
        else:
            dc, dr = random.choice(moves); c+=dc; r+=dr
            path.append((c,r)); grid[r][c]=1
    return path, grid

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
            
            # 🔥 ГОРЯЧИЕ КЛАВИШИ 1-6
            if not menu_open:
                if ev.key == pygame.K_1: selected_unit = 'soldier'
                if ev.key == pygame.K_2: selected_unit = 'flame'
                if ev.key == pygame.K_3: selected_unit = 'sniper'
                if ev.key == pygame.K_4: selected_unit = 'mine'
                if ev.key == pygame.K_5 and 'laser' in UNITS: selected_unit = 'laser'
                if ev.key == pygame.K_6 and 'missile' in UNITS: selected_unit = 'missile'

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            mx, my = ev.pos
            if menu_open:
                # Вкладки меню (увеличены для пальца)
                tab_w = 130
                for t in range(3):
                    if 190 + t*tab_w < mx < 190 + (t+1)*tab_w and 70 < my < 110:
                        menu_tab = t
                # Закрыть
                if 20 < mx < 110 and H-80 < my < H-20: menu_open = False
                
                # Логика вкладок
                if menu_tab == 0: # Прокачка
                    upgrades = [('dmg', 160), ('rate', 230), ('income', 300), ('capacity', 370)]
                    for key, y_pos in upgrades:
                        lvl = global_upgrades[key]
                        if lvl < 5 and 100 < mx < 420 and y_pos < my < y_pos+60:
                            cost = UPGRADE_COSTS[key][lvl]
                            if money >= cost: money -= cost; global_upgrades[key] += 1
                            
                elif menu_tab == 1: # Магазин
                    for i, (k, v) in enumerate(SHOP_UNITS.items()):
                        if 100 < mx < 460 and 150 + i*75 < my < 225 + i*75:
                            if crystals >= v['cost_crystals'] and k not in UNITS:
                                UNITS[k] = v; crystals -= v['cost_crystals']
                                
                elif menu_tab == 2: # Донат
                    if 100 < mx < 420 and 170 < my < 230: crystals += 1 # Реклама
                    if 100 < mx < 420 and 250 < my < 310 and money >= 500: money -= 500; crystals += 3
                    if 100 < mx < 420 and 330 < my < 390 and crystals >= 10: crystals -= 10
            else:
                # Геймплей: выбор юнита / постройка
                ui_h = 100
                if my > H-ui_h:
                    bw, sx = 115, (W - 6*125)//2
                    unit_keys = [k for k in ['soldier','flame','sniper','mine']+list(SHOP_UNITS.keys())[:2] if k in UNITS]
                    for i,k in enumerate(unit_keys):
                        if sx+i*125 < mx < sx+i*125+bw and H-ui_h+10 < my < H-ui_h+65:
                            selected_unit = k
                else:
                    c,r = from_iso(mx,my,cam_x,cam_y)
                    if 0<=c<COLS and 0<=r<ROWS:
                        cost = UNITS[selected_unit].get('cost', 9999)
                        if money >= cost:
                            if selected_unit=='mine' and grid_map[r][c]==1:
                                grid_map[r][c]=2; money-=cost
                            elif selected_unit!='mine' and grid_map[r][c]==0 and len(towers) < 10 + global_upgrades['capacity']*2:
                                towers.append(Tower(c,r,selected_unit)); grid_map[r][c]=1; money-=cost
                                
            # Начало драга камеры (только если клик не по UI)
            if not menu_open and my < H-100:
                dragging = True
                last_mouse = (mx, my)
            
        if ev.type == pygame.MOUSEBUTTONUP and ev.button==1:
            dragging = False
            
        if ev.type == pygame.MOUSEMOTION:
            if dragging:
                dx = ev.pos[0]-last_mouse[0]
                dy = ev.pos[1]-last_mouse[1]
                # Фильтр микро-движений для сенсора
                if abs(dx) > 2 or abs(dy) > 2:
                    cam_x += dx; cam_y += dy
                    last_mouse = ev.pos

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
        if e.is_dead(): money += e.reward; crystals += e.crystals; enemies.remove(e)
        if lives<=0: game_state='game_over'
    for t in towers:
        t.update(enemies,projectiles,cam_x,cam_y)
    for p in projectiles[:]:
        p.update(enemies)
        if not p.active:
            projectiles.remove(p)

    # === RENDER ===
    loc_idx = 0 if wave<=10 else (1 if wave<=30 else 2)
    screen.fill(LOCATIONS[loc_idx]['bg'])
    for r in range(ROWS):
        for c in range(COLS):
            if grid_map[r][c]==2:
                draw_tile_3d(screen,c,r,'road',cam_x,cam_y)
                x,y = to_iso(c,r,cam_x,cam_y)
                pygame.draw.circle(screen,(70,70,70),(x,y-10),12)
                pygame.draw.circle(screen,(200,0,0),(x,y-10),5)
            elif (c,r) in path: draw_tile_3d(screen,c,r,'road',cam_x,cam_y)
            else: draw_tile_3d(screen,c,r,'grass',cam_x,cam_y)
    for obj in sorted(enemies+towers, key=lambda o:o.screen_y if hasattr(o,'screen_y') else 0): obj.draw(screen)
    for p in projectiles: p.draw(screen)

    # === UI ===
    ui_h = 100
    pygame.draw.rect(screen,Colors.UI_BG,(0,H-ui_h,W,ui_h))
    pygame.draw.line(screen,Colors.ACCENT,(0,H-ui_h),(W,H-ui_h),2)
    info = f"$ {money} | CR: {crystals} | W: {wave} | HP: {lives}"
    screen.blit(font.render(info, True, Colors.ACCENT), (20, H-75))
    
    # Кнопки юнитов + номера
    sx, bw = (W-750)//2, 115
    unit_keys = [k for k in ['soldier','flame','sniper','mine']+list(SHOP_UNITS.keys())[:2] if k in UNITS]
    for i,k in enumerate(unit_keys):
        x,y = sx+i*125, H-ui_h+10
        rect = pygame.Rect(x,y,bw,55)
        pygame.draw.rect(screen, Colors.ACCENT if selected_unit==k else (60,60,70), rect, 2)
        # Номер клавиши
        screen.blit(font.render(f"[{i+1}]", True, (150,150,150)), (x+5, y+3))
        screen.blit(font.render(UNITS[k]['name'], True, Colors.WHITE), (x+25, y+8))
        screen.blit(font.render(f"${UNITS[k].get('cost',0)}", True, Colors.GOLD), (x+25, y+30))

    # Кнопка меню [P]
    pygame.draw.rect(screen, Colors.CRYSTAL, (20, 20, 90, 40), 2)
    screen.blit(font.render("[P] MENU", True, Colors.WHITE), (30, 30))

    # === ОКНО МЕНЮ ===
    if menu_open:
        pygame.draw.rect(screen, Colors.UI_PANEL, (140, 60, 600, 450), border_radius=12)
        pygame.draw.rect(screen, Colors.ACCENT, (140, 60, 600, 450), 3, border_radius=12)
        
        tabs = ['UPGRADES', 'SHOP', 'DONATE']
        for t in range(3):
            col = Colors.ACCENT if menu_tab==t else Colors.WHITE
            bg = Colors.UI_TAB if menu_tab==t else (40,40,60)
            pygame.draw.rect(screen, bg, (190+t*130, 70, 130, 40), border_radius=8)
            screen.blit(font.render(tabs[t], True, col), (205+t*130, 80))
        
        if menu_tab == 0:
            upgrades = [('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                        ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                        ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                        ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL)]
            for i, (name, key, lvl, costs, col) in enumerate(upgrades):
                y = 150 + i*75
                cost = costs[lvl] if lvl < len(costs) else 'MAX'
                can_buy = money >= cost if isinstance(cost, int) else False
                c = Colors.WHITE if lvl>=5 else (col if can_buy else (100,100,100))
                pygame.draw.rect(screen, (50,50,70), (100, y, 480, 65), border_radius=8)
                screen.blit(font.render(f"{name} [Lvl {lvl}/5]", True, Colors.WHITE), (110, y+10))
                screen.blit(font.render(f"Cost: {cost}$", True, c), (110, y+38))
        elif menu_tab == 1:
            for i, (k, v) in enumerate(SHOP_UNITS.items()):
                y = 150 + i*75
                owned = k in UNITS
                status = "OWNED" if owned else f"{v['cost_crystals']} CR"
                col = Colors.GREEN if owned else Colors.CRYSTAL
                pygame.draw.rect(screen, (50,50,70), (100, y, 480, 65), border_radius=8)
                screen.blit(font.render(f"{v['name']} - {status}", True, col), (110, y+15))
                if not owned: screen.blit(font.render(f"Price: ${v['cost']}", True, Colors.GOLD), (110, y+38))
        elif menu_tab == 2:
            btns = [("Watch Ad: +1 CR", Colors.GREEN, 170), ("Buy 3 CR: 500$", Colors.GOLD, 250), ("Monthly Pack: 10 CR", Colors.CRYSTAL, 330)]
            for txt, col, y in btns:
                pygame.draw.rect(screen, (30,40,50), (100, y, 480, 65), border_radius=8)
                screen.blit(font.render(txt, True, col), (110, y+25))
                
        pygame.draw.rect(screen, Colors.RED, (20, H-80, 90, 60), border_radius=8)
        screen.blit(font.render("CLOSE", True, Colors.WHITE), (30, H-60))

    pygame.display.flip()

pygame.quit(); sys.exit()
