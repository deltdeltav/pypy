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

def draw_tile_3d(screen, c, r, type, cam_x, cam_y, color_override=None):
    x, y = to_iso(c, r, cam_x, cam_y)
    if x < -150 or x > W + 150 or y < -150 or y > H + 150: return
    h = 20
    if type == 'road': top, side = (55, 55, 65), (35, 35, 45)
    elif type == 'base': top, side = (20, 20, 30), (10, 10, 15)
    else: top, side = (45, 140, 45), (25, 90, 25)
    if color_override: top = color_override
    pts_top = [(x, y-TILE_H), (x+TILE_W, y), (x, y+TILE_H), (x-TILE_W, y)]
    pts_left = [(x-TILE_W, y), (x, y+TILE_H), (x, y+TILE_H+h), (x-TILE_W, y+h)]
    pts_right = [(x+TILE_W, y), (x, y+TILE_H), (x, y+TILE_H+h), (x+TILE_W, y+h)]
    pygame.draw.polygon(screen, side, pts_left)
    pygame.draw.polygon(screen, side, pts_right)
    pygame.draw.polygon(screen, top, pts_top)
    pygame.draw.polygon(screen, (0,0,0,40), pts_top, 1)

def draw_health_bar(screen, x, y, w, hp, max_hp, color=(0,255,0)):
    ratio = max(0, min(1, hp / max_hp))
    pygame.draw.rect(screen, (20,0,0), (x-w//2, y, w, 5))
    pygame.draw.rect(screen, color, (x-w//2, y, w*ratio, 5))
