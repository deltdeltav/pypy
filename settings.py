import pygame

# --- ЭКРАН ---
W, H = 1280, 720
FPS = 60
TILE_W, TILE_H = 50, 30
SCREEN_FLAGS = pygame.SCALED | pygame.RESIZABLE

# --- ЦВЕТА ---
class Colors:
    BG_SUMMER = (15, 25, 15)
    BG_MOUNTAIN = (30, 25, 20)
    BG_WINTER = (180, 190, 200)
    ACCENT = (0, 255, 230)
    UI_BG = (10, 10, 15, 220)
    UI_PANEL = (20, 20, 30)
    UI_TAB = (40, 40, 60)
    WHITE = (255, 255, 255)
    GOLD = (255, 210, 0)
    CRYSTAL = (0, 200, 255)
    GREEN = (0, 200, 100)
    RED = (200, 50, 50)
    
    ZOMBIE_NORMAL = (80, 180, 80)
    ZOMBIE_RUNNER = (220, 80, 80)
    ZOMBIE_TANK   = (100, 20, 20)
    BOSS_MINI = (140, 0, 220)
    BOSS_NORM = (200, 0, 0)
    BOSS_MEGA = (220, 180, 0)

# --- ДАННЫЕ ---
START_MONEY = 800
START_CRYSTALS = 0
global_upgrades = {'dmg': 0, 'rate': 0, 'hp': 0, 'income': 0, 'capacity': 0}

UNITS = {
    'soldier': {'name': 'SOLDIER', 'cost': 100, 'dmg': 25, 'range': 5, 'rate': 30, 'color': (0, 200, 100), 'type': 'single'},
    'flame':   {'name': 'PYRO',    'cost': 350, 'dmg': 30, 'range': 2, 'rate': 25, 'color': (255, 120, 0), 'type': 'aoe'},
    'sniper':  {'name': 'SNIPER',  'cost': 600, 'dmg': 200,'range': 14,'rate': 150,'color': (0, 120, 255), 'type': 'projectile'},
    'mine':    {'name': 'MINE',    'cost': 180, 'dmg': 500,'range': 0, 'rate': 0,  'color': (60, 60, 60), 'type': 'trap'}
}

SHOP_UNITS = {
    'laser':  {'name': 'LASER', 'cost_crystals': 5,  'cost': 900, 'dmg': 80, 'range': 8, 'rate': 40, 'color': (255, 0, 255), 'type': 'beam'},
    'missile':{'name': 'MISSILE','cost_crystals': 12, 'cost': 1500,'dmg': 300,'range': 10,'rate': 200,'color': (255, 100, 0), 'type': 'aoe'}
}

ENEMIES = {
    'normal': {'hp': 120, 'speed': 0.04, 'reward': 25, 'color': Colors.ZOMBIE_NORMAL},
    'runner': {'hp': 70,  'speed': 0.10, 'reward': 35, 'color': Colors.ZOMBIE_RUNNER},
    'tank':   {'hp': 500, 'speed': 0.02, 'reward': 60, 'color': Colors.ZOMBIE_TANK},
}

BOSS_STATS = {
    5:  {'hp': 3000, 'speed': 0.03, 'reward': 800, 'crystals': 2,  'color': Colors.BOSS_MINI, 'scale': 1.5, 'summons': False},
    10: {'hp': 10000,'speed': 0.02, 'reward': 2500,'crystals': 5,  'color': Colors.BOSS_NORM, 'scale': 2.0, 'summons': True},
    50: {'hp': 70000,'speed': 0.01, 'reward': 15000,'crystals': 15, 'color': Colors.BOSS_MEGA, 'scale': 3.0, 'summons': True},
}

UPGRADE_COSTS = {
    'dmg': [100, 250, 500, 1000, 2500],
    'rate': [150, 400, 800, 2000, 5000],
    'hp': [5000, 15000, 40000, 100000, 300000],
    'income': [200, 500, 1200, 3000, 8000],
    'capacity': [300, 800, 2000, 5000, 12000]
}

LOCATIONS = [{'bg': Colors.BG_SUMMER}, {'bg': Colors.BG_MOUNTAIN}, {'bg': Colors.BG_WINTER}]
