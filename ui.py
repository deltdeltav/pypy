import pygame
import random
from settings import *

class UIManager:
    def __init__(self, screen, font, font_big, font_menu_btn, font_arrow):
        self.screen = screen
        self.font = font
        self.font_big = font_big
        self.font_menu_btn = font_menu_btn
        self.font_arrow = font_arrow

    def draw_main_menu(self, crystals, particles, mx, my):
        self.screen.fill((10, 10, 20))
        for p in particles:
            p['y'] += p['speed']
            if p['y'] > H:
                p['y'] = 0
                p['x'] = random.randint(0, W)
            pygame.draw.circle(self.screen, (50, 50, 100), (int(p['x']), int(p['y'])), p['size'])
        
        title_surf = self.font_menu_btn.render("DELTA CORE", True, Colors.ACCENT)
        sub_surf = self.font.render("PRO EDITION", True, (150, 150, 150))
        self.screen.blit(title_surf, (W//2 - title_surf.get_width()//2, 150))
        self.screen.blit(sub_surf, (W//2 - sub_surf.get_width()//2, 230))
        
        cr_surf = self.font.render(f"CRYSTALS: {crystals}", True, Colors.CRYSTAL)
        self.screen.blit(cr_surf, (W//2 - cr_surf.get_width()//2, 550))
        
        play_rect = self._draw_button("PLAY GAME", 300, mx, my)
        shop_rect = self._draw_button("SHOP / UPGRADES", 380, mx, my)
        exit_rect = self._draw_button("EXIT", 460, mx, my)
        return play_rect, shop_rect, exit_rect

    def _draw_button(self, text, y_pos, mx, my):
        btn_w, btn_h = 300, 60
        x = W // 2 - btn_w // 2
        rect = pygame.Rect(x, y_pos, btn_w, btn_h)
        hovered = rect.collidepoint(mx, my)
        color_bg = (50, 50, 80) if not hovered else (80, 80, 150)
        pygame.draw.rect(self.screen, color_bg, rect, border_radius=10)
        pygame.draw.rect(self.screen, (100, 100, 255) if hovered else (50, 50, 100), rect, 3, border_radius=10)
        txt_surf = self.font_menu_btn.render(text, True, Colors.WHITE)
        self.screen.blit(txt_surf, (rect.x + (btn_w - txt_surf.get_width())//2, rect.y + 15))
        return rect

    def draw_game_hud(self, money, crystals, towers_count, current_limit, energy, max_energy, dark_matter, max_dark_matter, lives, wave, LEVEL, biome_name, menu_type, selected_unit, visible_keys, unit_scroll, UNITS, SHOP_UNITS):
        info = f"LVL {LEVEL} | {biome_name} | W: {wave}/50 | $ {money} | CR: {crystals} | T: {towers_count}/{current_limit} | ⚡ {int(energy)} | 🌑 {int(dark_matter)} | HP: {lives}"
        self.screen.blit(self.font.render(info, True, Colors.ACCENT), (10, 10))
        
        self._draw_bar(10, 40, energy/max_energy, (0, 200, 255))
        self._draw_bar(10, 55, dark_matter/max_dark_matter, Colors.VOID_PURPLE)
        self._draw_bar(10, 70, lives/20, (255, 50, 50))

        menu_rect = pygame.Rect(MENU_BTN_X, MENU_BTN_Y, MENU_BTN_W, MENU_BTN_H)
        pygame.draw.rect(self.screen, Colors.ACCENT if menu_type == 'game' else (60,60,80), menu_rect, border_radius=8)
        self.screen.blit(self.font.render("MENU (P)", True, Colors.WHITE), (MENU_BTN_X + 5, MENU_BTN_Y + 10))

        for i, k in enumerate(visible_keys):
            x = V_MENU_X
            y = V_MENU_Y_START + i * (V_BTN_H + V_GAP)
            rect = pygame.Rect(x, y, V_BTN_W, V_BTN_H)
            bg_col = Colors.ACCENT if selected_unit == k else (60,60,70)
            pygame.draw.rect(self.screen, bg_col, rect, border_radius=6)
            pygame.draw.rect(self.screen, (20,20,30), rect, 2, border_radius=6)
            
            self.screen.blit(self.font.render(f"[{unit_scroll + i + 1}]", True, (150,150,150)), (x+5, y+5))
            unit_data = UNITS.get(k, SHOP_UNITS.get(k, {}))
            name = unit_data.get('name', k.upper())
            self.screen.blit(self.font.render(name, True, Colors.WHITE), (x+30, y+5))
            cost = unit_data.get('cost', 0)
            self.screen.blit(self.font.render(f"${cost}", True, Colors.GOLD), (x+30, y+25))

    def _draw_bar(self, x, y, pct, color):
        pygame.draw.rect(self.screen, (30, 30, 40), (x, y, 100, 8), border_radius=2)
        pygame.draw.rect(self.screen, color, (x, y, 100 * max(0, min(1, pct)), 8), border_radius=2)

    # === МЕНЮ ПАУЗЫ (ESC) ===
    def draw_pause_menu(self):
        sys_w, sys_h = 400, 350
        sys_x = (W - sys_w) // 2
        sys_y = (H - sys_h) // 2
        
        # Затемнение фона
        overlay = pygame.Surface((W, H))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(self.screen, (20, 20, 30), (sys_x, sys_y, sys_w, sys_h), border_radius=12)
        pygame.draw.rect(self.screen, Colors.ACCENT, (sys_x, sys_y, sys_w, sys_h), 3, border_radius=12)
        self.screen.blit(self.font_big.render("PAUSE", True, Colors.WHITE), (sys_x + 130, sys_y + 20))
        
        btn_h = 50
        gap = 10
        start_y = sys_y + 70
        btn_w = sys_w - 100
        btn_x = sys_x + 50
        
        labels = [
            ("RESUME", (30, 60, 30), Colors.GREEN),
            ("SAVE", (30, 30, 60), Colors.BLUE),
            ("LOAD", (60, 60, 30), Colors.GOLD),
            ("MAIN MENU", (60, 30, 30), Colors.RED)
        ]
        rects = {}
        for i, (txt, col_bg, col_txt) in enumerate(labels):
            r = pygame.Rect(btn_x, start_y + i * (btn_h + gap), btn_w, btn_h)
            hovered = r.collidepoint(pygame.mouse.get_pos())
            bg = (col_bg[0]+20, col_bg[1]+20, col_bg[2]+20) if hovered else col_bg
            pygame.draw.rect(self.screen, bg, r, border_radius=8)
            pygame.draw.rect(self.screen, col_txt, r, 2, border_radius=8)
            self.screen.blit(self.font.render(txt, True, col_txt), (r.x + 20, r.y + 15))
            rects[txt] = r
        return rects

    def draw_in_game_menu(self, menu_tab, global_upgrades, LEVEL, money, max_energy, energy, UPGRADE_COSTS, ENERGY_UPGRADE_COSTS, ENERGY_UPGRADE_BONUS, SHOP_UNITS, UNITS, crystals, ad_cooldown_timestamp, current_time, ad_watching, upgrade_scroll, shop_scroll):
        menu_w, menu_h = 600, 450
        menu_x = (W - menu_w) // 2
        menu_y = (H - menu_h) // 2
        
        pygame.draw.rect(self.screen, Colors.UI_PANEL, (menu_x, menu_y, menu_w, menu_h), border_radius=12)
        pygame.draw.rect(self.screen, Colors.ACCENT, (menu_x, menu_y, menu_w, menu_h), 3, border_radius=12)
        
        tabs = ['UPGRADES', 'SHOP', 'DONATE']
        tab_w, tab_h = 130, 40
        tab_start_x = menu_x + (menu_w - 3 * tab_w - 2 * 10) // 2
        tab_y = menu_y + 10
        
        for t in range(3):
            tx = tab_start_x + t * (tab_w + 10)
            col = Colors.ACCENT if menu_tab == t else Colors.WHITE
            bg = Colors.UI_TAB if menu_tab == t else (40, 40, 60)
            rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            self.screen.blit(self.font.render(tabs[t], True, col), (tx + 15, tab_y + 10))

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

        if menu_tab == 0:
            all_upgrades = [
                ('Damage +15%', 'dmg', global_upgrades['dmg'], UPGRADE_COSTS['dmg'], Colors.RED),
                ('Fire Rate +10%', 'rate', global_upgrades['rate'], UPGRADE_COSTS['rate'], Colors.GOLD),
                ('Income +5%', 'income', global_upgrades['income'], UPGRADE_COSTS['income'], Colors.GREEN),
                ('Capacity +2', 'capacity', global_upgrades['capacity'], UPGRADE_COSTS['capacity'], Colors.CRYSTAL),
                ('Energy Cap +100', 'energy_cap', global_upgrades['energy_cap'], ENERGY_UPGRADE_COSTS, Colors.BLUE)
            ]
            visible_ups = all_upgrades[upgrade_scroll : upgrade_scroll + max_visible]
            
            pygame.draw.rect(self.screen, (60,60,80), (left_x, start_y_content, scroll_w, item_h), border_radius=5)
            pygame.draw.rect(self.screen, (60,60,80), (right_x, start_y_content, scroll_w, item_h), border_radius=5)
            self.screen.blit(self.font_arrow.render("<", True, Colors.WHITE), (left_x + 15, start_y_content + 15))
            self.screen.blit(self.font_arrow.render(">", True, Colors.WHITE), (right_x + 15, start_y_content + 15))

            for i, (name, key, lvl, costs, col) in enumerate(visible_ups):
                y_card = start_y_content + i * (item_h + 10)
                cost = costs[lvl] if lvl < len(costs) else 'MAX'
                can_buy = money >= cost if isinstance(cost, int) else False
                c_text = Colors.WHITE if lvl >= len(costs) else (col if can_buy else (100,100,100))
                
                rect = pygame.Rect(card_x_start, y_card, card_width, item_h)
                pygame.draw.rect(self.screen, (50,50,70), rect, border_radius=8)
                self.screen.blit(self.font.render(f"{name} [Lvl {lvl}/{len(costs)}]", True, Colors.WHITE), (card_x_start + 10, y_card + 10))
                self.screen.blit(self.font.render(f"Cost: {cost}$", True, c_text), (card_x_start + 10, y_card + 38))

        elif menu_tab == 1:
            visible_keys_shop = list(SHOP_UNITS.keys())[shop_scroll:shop_scroll+max_visible]
            
            pygame.draw.rect(self.screen, (60,60,80), (left_x, start_y_content, scroll_w, item_h), border_radius=5)
            pygame.draw.rect(self.screen, (60,60,80), (right_x, start_y_content, scroll_w, item_h), border_radius=5)
            self.screen.blit(self.font_arrow.render("<", True, Colors.WHITE), (left_x + 15, start_y_content + 15))
            self.screen.blit(self.font_arrow.render(">", True, Colors.WHITE), (right_x + 15, start_y_content + 15))

            for i, k in enumerate(visible_keys_shop):
                v = SHOP_UNITS[k]
                y_card = start_y_content + i * (item_h + 10)
                owned = k in UNITS
                status = "OWNED" if owned else f"{v['cost_crystals']} CR"
                col = Colors.GREEN if owned else Colors.CRYSTAL
                
                rect = pygame.Rect(card_x_start, y_card, card_width, item_h)
                pygame.draw.rect(self.screen, (50,50,70), rect, border_radius=8)
                self.screen.blit(self.font.render(f"{v['name']} - {status}", True, col), (card_x_start + 10, y_card + 15))
                if not owned:
                    self.screen.blit(self.font.render(f"Price: ${v['cost']}", True, Colors.GOLD), (card_x_start + 10, y_card + 38))

        elif menu_tab == 2:
            cooldown_left = ad_cooldown_timestamp - current_time
            if ad_watching:
                txt_ad = "Watching Ad..."
                col_ad = Colors.GOLD
            elif cooldown_left > 0:
                mins = int(cooldown_left) // 60
                txt_ad = f"Cooldown: {mins}m"
                col_ad = (100, 100, 100)
            else:
                txt_ad = "Watch Ad: +10 CR"
                col_ad = Colors.GREEN
            
            ad_rect_vis = pygame.Rect(content_x, content_y, item_w, item_h)
            pygame.draw.rect(self.screen, (30, 40, 50), ad_rect_vis, border_radius=8)
            self.screen.blit(self.font.render(txt_ad, True, col_ad), (content_x + 10, content_y + 20))
            
            donate_rect_vis = pygame.Rect(content_x, content_y + 80, item_w, item_h)
            pygame.draw.rect(self.screen, (30, 40, 50), donate_rect_vis, border_radius=8)
            self.screen.blit(self.font.render("Donate Link", True, Colors.CRYSTAL), (content_x + 10, content_y + 100))

        close_rect = pygame.Rect(menu_x + 20, menu_y + menu_h - 80, 90, 60)
        pygame.draw.rect(self.screen, Colors.RED, close_rect, border_radius=8)
        self.screen.blit(self.font.render("CLOSE", True, Colors.WHITE), (close_rect.x + 10, close_rect.y + 20))

    def draw_game_over(self):
        self.screen.fill((20, 0, 0))
        txt = self.font_menu_btn.render("GAME OVER", True, Colors.RED)
        self.screen.blit(txt, (W//2-txt.get_width()//2, H//2-50))
        restart_rect = pygame.Rect(W//2 - 100, H//2 + 50, 200, 50)
        pygame.draw.rect(self.screen, (100, 0, 0), restart_rect, border_radius=8)
        self.screen.blit(self.font_menu_btn.render("MENU", True, Colors.WHITE), (restart_rect.x + 50, restart_rect.y + 10))
        return restart_rect
