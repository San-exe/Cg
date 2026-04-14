import os
import pygame
import math
from random import shuffle
from settings import *

class MemoryGame:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(None, 48, bold=True)
        self.text_font = pygame.font.SysFont(None, 26)
        
        # Pre-calculate starfield
        from random import uniform
        self.stars = [{"x": uniform(0, 1), "y": uniform(0, 1), "r": uniform(1, 2.5), "alpha_offset": uniform(0, math.pi*2)} for _ in range(80)]
        
        self.card_images = self.load_card_images()
        self.reset()

    def load_card_images(self):
        image_folder = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "assets", "memory_images"))
        if not os.path.isdir(image_folder):
            return []

        images = []
        for filename in sorted(os.listdir(image_folder)):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                try:
                    path = os.path.join(image_folder, filename)
                    image = pygame.image.load(path).convert_alpha()
                    images.append(image)
                except Exception:
                    continue
        return images

    def reset(self):
        self.cards = [i for i in range(8)] * 2
        shuffle(self.cards)
        self.revealed = [False] * 16
        self.matched = [False] * 16
        self.flip_progress = [0.0] * 16
        self.selected = []
        self.wait_until = 0
        self.score = 0
        self.guesses = 0
        self.completed = False
        self.message = "Decrypt the Holographic Data Pairs!"

    def run(self, events):
        if self.game.state != "memory":
            return

        dt = self.game.clock.get_time() / 1000.0
        now = pygame.time.get_ticks()
        time_sec = now / 1000.0
        
        for event in events:
            if event.type == pygame.QUIT:
                self.game.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "menu"
                    self.reset()
                elif event.key == pygame.K_SPACE and self.completed:
                    self.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.wait_until > now:
                    continue
                self.handle_click(event.pos, time_sec)

        if self.wait_until > 0 and now > self.wait_until:
            self.hide_unmatched()

        # Update smooth 3D flip animations
        for i in range(16):
            target = 1.0 if self.revealed[i] else 0.0
            if self.flip_progress[i] < target:
                self.flip_progress[i] = min(target, self.flip_progress[i] + dt * 4.0)
            elif self.flip_progress[i] > target:
                self.flip_progress[i] = max(target, self.flip_progress[i] - dt * 4.0)

        self.draw_screen(time_sec)

    def card_rect(self, index, time_sec):
        cols = 4
        width, height = self.game.screen.get_size()
        gap = max(20, min(width, height) // 40)
        
        max_w = (width - 160 - gap * (cols - 1)) // cols
        max_h = (height - 300 - gap * (cols - 1)) // 4
        size = max(40, min(130, min(max_w, max_h)))
        
        total_w = cols * size + (cols - 1) * gap
        total_h = 4 * size + 3 * gap
        
        start_x = (width - total_w) // 2
        start_y = 230 + max(0, height - 270 - total_h) // 2
        
        col = index % cols
        row = index // cols
        x = start_x + col * (size + gap)
        y = start_y + row * (size + gap)
        
        # Determine exact fixed position
        rect = pygame.Rect(x, y, size, size)
        return rect

    def handle_click(self, pos, time_sec):
        for index in range(16):
            rect = self.card_rect(index, time_sec)
            # Only allow click if fully hidden to prevent clicking while animating/flipped
            if rect.collidepoint(pos) and not self.revealed[index] and not self.matched[index]:
                self.revealed[index] = True
                self.selected.append(index)
                if len(self.selected) == 2:
                    self.guesses += 1
                    first, second = self.selected
                    if self.cards[first] == self.cards[second]:
                        self.matched[first] = True
                        self.matched[second] = True
                        self.score += 1
                        self.message = "Match found!"
                        self.selected = []
                        if all(self.matched):
                            self.completed = True
                            self.message = "All data decrypted! Press SPACE to restart or ESC to return."
                    else:
                        self.message = "Mismatch detected. Realigning links..."
                        self.wait_until = pygame.time.get_ticks() + 1000
                return

    def hide_unmatched(self):
        for index in self.selected:
            if not self.matched[index]:
                self.revealed[index] = False
        self.selected = []
        self.wait_until = 0

    def draw_screen(self, time_sec):
        width, height = self.game.screen.get_size()
        
        # Cosmic deep field rendering
        self.game.screen.fill((4, 6, 12)) 
        
        for star in self.stars:
            sx = int(star["x"] * width)
            sy = int(star["y"] * height)
            alpha_wave = int(128 + 127 * math.sin(time_sec * 3.0 + star["alpha_offset"]))
            r = int(star["r"])
            pygame.draw.circle(self.game.screen, (200, 230, 255, alpha_wave), (sx, sy), r)
        
        # HUD Panel layers holograms
        panel_rect = pygame.Rect(40, 60, width - 80, height - 100)
        hud_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (*CARD, 110), panel_rect, border_radius=30)
        self.game.screen.blit(hud_surf, (0, 0))
        
        # Panel dynamic borders
        pygame.draw.rect(self.game.screen, (*ACCENT, 90), panel_rect, width=2, border_radius=30)
        
        # Centered decorative line
        line_w = int(panel_rect.width * 0.8)
        line_x = panel_rect.left + (panel_rect.width - line_w) // 2
        pygame.draw.rect(self.game.screen, ACCENT, (line_x, 80, line_w, 4), border_radius=2)

        # Typography
        title = self.title_font.render("Memory Match", True, ACCENT2)
        status = self.text_font.render(self.message, True, WHITE)
        score_text = self.text_font.render(f"Pairs found: {self.score}/8", True, WHITE)
        guess_text = self.text_font.render(f"Guesses: {self.guesses}", True, WHITE)

        center_x = width // 2
        self.game.screen.blit(title, (center_x - title.get_width() // 2, 100))
        self.game.screen.blit(score_text, (center_x - score_text.get_width() // 2, 160))
        self.game.screen.blit(guess_text, (center_x - guess_text.get_width() // 2, 190))
        self.game.screen.blit(status, (center_x - status.get_width() // 2, 220))

        # Render floating holographic cards
        for index in range(16):
            rect = self.card_rect(index, time_sec)
            size = rect.height # true max size
            
            # Smooth 3D Flip Mechanics
            progress = self.flip_progress[index]
            scale_x = math.cos(progress * math.pi)
            current_w = size * abs(scale_x)
            
            if current_w >= 1:
                draw_rect = pygame.Rect(0, 0, current_w, size)
                draw_rect.center = rect.center
                
                # Determine front vs back
                if scale_x > 0:
                    # BACK of the hologram tile
                    pygame.draw.rect(self.game.screen, (*CARD, 180), draw_rect, border_radius=16)
                    pygame.draw.rect(self.game.screen, ACCENT, draw_rect, width=2, border_radius=16)
                    
                    # Inner glowing circuit outline
                    inner = draw_rect.inflate(-current_w * 0.4, -size * 0.4)
                    if inner.width > 2 and inner.height > 2:
                        pygame.draw.rect(self.game.screen, ACCENT2, inner, width=2, border_radius=6)
                else:
                    # FRONT of the hologram tile (data revealed)
                    card_id = self.cards[index]
                    if self.card_images and card_id < len(self.card_images):
                        img = self.card_images[card_id]
                        img = pygame.transform.smoothscale(img, (draw_rect.width, draw_rect.height))
                        self.game.screen.blit(img, draw_rect)
                    else:
                        c_palette = [ACCENT, ACCENT2, (255, 116, 196), (115, 247, 172), (255, 201, 84), (180, 104, 255), (116, 211, 255), (170, 255, 192)]
                        c = c_palette[card_id % len(c_palette)]
                        pygame.draw.rect(self.game.screen, c, draw_rect, border_radius=16)
                        pygame.draw.rect(self.game.screen, (255, 255, 255), draw_rect, width=2, border_radius=16)
                        core = draw_rect.inflate(-current_w * 0.6, -size * 0.6)
                        if core.width > 2 and core.height > 2:
                            pygame.draw.rect(self.game.screen, (255, 255, 255), core, border_radius=4)

                    if self.matched[index] and progress > 0.99:
                        glow = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
                        pygame.draw.rect(glow, (255, 255, 255, 50), glow.get_rect(), border_radius=20)
                        self.game.screen.blit(glow, (draw_rect.left - 10, draw_rect.top - 10))

        pygame.display.flip()