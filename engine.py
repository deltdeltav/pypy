import pygame
import math
from settings import *

def to_iso(c, r, cam_x, cam_y):
    return (c - r) * TILE_W + cam_x, (c + r) * TILE_H + cam_y

def from_iso(mx, my, cam_x, cam_y):
    x, y = mx - cam_x, my - cam_y
    c = (x / TILE_W + y / TILE_H) / 2
    r = (y / TILE_H - x / TILE_W) / 2
    return int(c), int(r)

def draw_glow_circle(screen, x, y, radius, color, alpha=100):
    surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        a = int(alpha * (r/radius))
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    screen.blit(surf, (x-radius, y-radius))

def draw_tile_3d(screen, c, r, type, cam_x, cam_y, color_override=None):
    x, y = to_iso(c, r, cam_x, cam_y)
    if x < -150 or x > W + 150 or y < -150 or y > H + 150:
        return
    
    h = 20
    if type == 'road': 
        top, side = (35, 35, 40), (20, 20, 25)
    elif type == 'base': 
        top, side = (15, 15, 25), (5, 5, 10)
    else: 
        top, side = (30, 100, 30), (15, 70, 15)
        
    if color_override:
        top = color_override

    pts_top = [(x, y-TILE_H+5), (x+TILE_W-5, y), (x, y+TILE_H-5), (x-TILE_W+5, y)]
    pts_left = [(x-TILE_W+5, y), (x, y+TILE_H-5), (x, y+TILE_H+h), (x-TILE_W+5, y+h)]
    pts_right = [(x+TILE_W-5, y), (x, y+TILE_H-5), (x, y+TILE_H+h), (x+TILE_W-5, y+h)]

    pygame.draw.polygon(screen, side, pts_left)
    pygame.draw.polygon(screen, side, pts_right)
    pygame.draw.polygon(screen, top, pts_top)
    
    # БЕЗ ОБВОДКИ

def draw_health_bar(screen, x, y, w, hp, max_hp, color=(0,255,0)):
    ratio = max(0, min(1, hp / max_hp))
    pygame.draw.rect(screen, (0,0,0), (x-w//2-1, y-1, w+2, 7))
    pygame.draw.rect(screen, (40,0,0), (x-w//2, y, w, 5))
    pygame.draw.rect(screen, color, (x-w//2, y, w*ratio, 5))
