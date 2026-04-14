import pygame
from random import randint, uniform, choice
import math
from settings import *

class AimTrainer:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(None, 48, bold=True)
        self.text_font = pygame.font.SysFont(None, 26)
        
        # Pre-generate starfield
        self.stars = []
        for _ in range(120):
            self.stars.append({
                "x": uniform(0, 1),
                "y": uniform(0, 1),
                "radius": uniform(0.5, 2.5),
                "speed": uniform(0.002, 0.008),
                "phase": uniform(0, math.pi * 2)
            })
            
        self.reset()

    def reset(self):
        self.score = 0
        self.game_time = 30_000 # 30 seconds
        self.start_time = pygame.time.get_ticks()
        self.target_radius = 28
        self.particles = []
        self.spawn_target()
        self.message = "Cyberpunk Antigravity - Neutralize Targets!"
        
        # Pre-render sci-fi gun cursor mapping
        gun_surf = pygame.Surface((60, 40), pygame.SRCALPHA)
        pygame.draw.rect(gun_surf, (200, 200, 210), (0, 7, 40, 6))      # Inner barrel
        pygame.draw.rect(gun_surf, (80, 85, 95), (10, 5, 30, 10))       # Casing
        pygame.draw.rect(gun_surf, (50, 55, 65), (25, 2, 25, 14))       # Back mechanism
        pygame.draw.polygon(gun_surf, (40, 42, 50), [(30, 16), (45, 16), (55, 38), (40, 38)]) # Handle
        
        # Grip details
        pygame.draw.line(gun_surf, (20, 22, 30), (33, 20), (43, 20), 2)
        pygame.draw.line(gun_surf, (20, 22, 30), (36, 26), (46, 26), 2)
        pygame.draw.line(gun_surf, (20, 22, 30), (39, 32), (49, 32), 2)
        
        # Neon glowing energy cell & emitter tip
        pygame.draw.rect(gun_surf, ACCENT, (15, 7, 10, 6), border_radius=2)
        pygame.draw.rect(gun_surf, (255, 255, 255), (17, 9, 6, 2))
        pygame.draw.rect(gun_surf, (255, 50, 100), (0, 6, 4, 8))
        
        # Apply 45 deg tilt
        self.gun_cursor = pygame.transform.rotate(gun_surf, -45)

    def spawn_target(self):
        width, height = self.game.screen.get_size()
        margin = 120
        self.target_pos = [
            float(randint(margin, width - margin)),
            float(randint(margin + 80, height - margin)),
        ]
        # Random velocity vector for drift
        angle = uniform(0, math.pi * 2)
        speed = uniform(60.0, 150.0) # pixels per second
        self.target_base_speed = speed
        self.target_v = [math.cos(angle) * speed, math.sin(angle) * speed]
        
        self.target_rect = pygame.Rect(0, 0, self.target_radius * 2, self.target_radius * 2)
        self.target_rect.center = (int(self.target_pos[0]), int(self.target_pos[1]))

    def spawn_explosion(self, x, y):
        for _ in range(20):
            angle = uniform(0, math.pi * 2)
            speed = uniform(100.0, 400.0)
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": 0.8,
                "max_life": 0.8,
                "color": choice([ACCENT, ACCENT2, (255, 100, 150), (255, 255, 255)])
            })

    def run(self, events):
        if self.game.state != "aim":
            if getattr(self, "_hidden_cursor", False):
                pygame.mouse.set_visible(True)
                self._hidden_cursor = False
            return
            
        if not getattr(self, "_hidden_cursor", False):
            pygame.mouse.set_visible(False)
            self._hidden_cursor = True

        width, height = self.game.screen.get_size()
        current_time = pygame.time.get_ticks()
        
        # Frame independent delta time approx
        dt = self.game.clock.get_time() / 1000.0
        # If dt is suspiciously large (e.g. lag spike), cap it
        if dt > 0.1: dt = 0.1
        
        elapsed = current_time - self.start_time
        remaining = max(0, self.game_time - elapsed)
        game_over = remaining == 0
        self.game_over = game_over

        if game_over:
            self.message = "Simulation Complete! Press SPACE to restart, ESC to return."

        for event in events:
            if event.type == pygame.QUIT:
                self.game.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "menu"
                elif event.key == pygame.K_SPACE and game_over:
                    self.reset()
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Better true circular hit detection 
                mx, my = event.pos
                tx, ty = self.target_pos
                dist = math.hypot(mx - tx, my - ty)
                
                if remaining > 0 and dist <= self.target_radius:
                    self.score += 1
                    self.message = choice(["Target Eliminated!", "Bullseye!", "Clean hit!", "Critical Strike!"])
                    self.spawn_explosion(tx, ty)
                    self.spawn_target()
                elif remaining > 0:
                    self.score = max(0, self.score - 1)
                    self.message = "Missed! Re-adjusting aim."

        # Physics update
        if remaining > 0:
            # Gradually increase target speed over time (much stronger acceleration)
            normalized = min(1.0, elapsed / self.game_time)
            speed_factor = 1.0 + normalized * 3.5
            current_speed = math.hypot(self.target_v[0], self.target_v[1])
            if current_speed > 0:
                dir_x = self.target_v[0] / current_speed
                dir_y = self.target_v[1] / current_speed
                scaled_speed = self.target_base_speed * speed_factor
                self.target_v[0] = dir_x * scaled_speed
                self.target_v[1] = dir_y * scaled_speed

            # Move target
            self.target_pos[0] += self.target_v[0] * dt
            self.target_pos[1] += self.target_v[1] * dt
            
            # Bounce roughly off the glass pane boundaries
            tx, ty = self.target_pos
            tr = self.target_radius
            min_x, max_x = 50 + tr, width - 50 - tr
            min_y, max_y = 230 + tr, height - 70 - tr # Keep below the text
            
            if tx < min_x:
                self.target_pos[0] = min_x
                self.target_v[0] *= -1
            elif tx > max_x:
                self.target_pos[0] = max_x
                self.target_v[0] *= -1
                
            if ty < min_y:
                self.target_pos[1] = min_y
                self.target_v[1] *= -1
            elif ty > max_y:
                self.target_pos[1] = max_y
                self.target_v[1] *= -1
                
            self.target_rect.center = (int(self.target_pos[0]), int(self.target_pos[1]))
            
            # Add subtle drift trails
            if randint(0, 100) < 60:
                self.particles.append({
                    "x": tx + uniform(-tr*0.5, tr*0.5),
                    "y": ty + uniform(-tr*0.5, tr*0.5),
                    "vx": self.target_v[0] * 0.05,
                    "vy": self.target_v[1] * 0.05,
                    "life": 0.4,
                    "max_life": 0.4,
                    "color": ACCENT
                })

        # Update all particles
        for p in reversed(self.particles):
            p['life'] -= dt
            if p['life'] <= 0:
                self.particles.remove(p)
            else:
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt

        # Rendering Engine: Background
        self.game.screen.fill((8, 12, 24)) 
        
        # Dynamic Starfield Generation
        for star in self.stars:
            sx = int(star["x"] * width)
            sy = int(star["y"] * height)
            phase = star["phase"] + current_time * star["speed"]
            alpha = int(abs(math.sin(phase)) * 255)
            # Softly blitting stars via alpha
            r = int(star["radius"])
            if r < 1: r = 1
            star_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, (200, 240, 255, alpha), (r, r), r)
            self.game.screen.blit(star_surf, (sx, sy))

        # UI Panels -> glassmorphism/holographic look
        glass_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(glass_surf, (*CARD, 130), (50, 60, width - 100, height - 130), border_radius=30)
        self.game.screen.blit(glass_surf, (0, 0))
        
        # Border
        pygame.draw.rect(self.game.screen, (*ACCENT, 80), (50, 60, width - 100, height - 130), width=2, border_radius=30)
        # Top glowing accent line
        pygame.draw.rect(self.game.screen, ACCENT, (64, 74, width - 128, 2), border_radius=1)

        # Main typography
        title = self.title_font.render("Target Practice", True, ACCENT2)
        score_text = self.text_font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        timer_text = self.text_font.render(f"TIME: {remaining // 1000}.{remaining % 1000 // 100:01d}", True, (255, 255, 255))
        instructions = self.text_font.render(self.message, True, TEXT)

        # Centering typography horizontally inside card
        cx = width // 2
        self.game.screen.blit(title, (cx - title.get_width() // 2, 90))
        self.game.screen.blit(score_text, (cx - score_text.get_width() // 2, 140))
        self.game.screen.blit(timer_text, (cx - timer_text.get_width() // 2, 170))
        self.game.screen.blit(instructions, (cx - instructions.get_width() // 2, 204))

        # Dynamic neon particles layering
        for p in self.particles:
            ratio = p['life'] / p['max_life']
            alpha = int(255 * ratio)
            r = int(5 * ratio)
            if r > 0:
                p_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*p['color'], alpha), (r, r), r)
                self.game.screen.blit(p_surf, (int(p['x']-r), int(p['y']-r)))

        # Blit Drifting Target properly illuminated
        if remaining > 0:
            tx, ty = int(self.target_pos[0]), int(self.target_pos[1])
            tr = self.target_radius
            
            # Stacked alpha gradients simulating physical blur/glow
            glow_surf = pygame.Surface((tr*4, tr*4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*ACCENT, 30), (tr*2, tr*2), tr * 1.6)
            pygame.draw.circle(glow_surf, (*ACCENT, 60), (tr*2, tr*2), tr * 1.1)
            pygame.draw.circle(glow_surf, (*ACCENT2, 160), (tr*2, tr*2), tr * 0.7)
            pygame.draw.circle(glow_surf, (255, 255, 255, 255), (tr*2, tr*2), tr * 0.3)
            
            self.game.screen.blit(glow_surf, (tx - tr*2, ty - tr*2))
            
            # Outer digital rotating HUD reticle 
            time_sec = current_time / 1000.0
            spin = time_sec * 3.0
            p1 = (tx + math.cos(spin)*tr, ty + math.sin(spin)*tr)
            p2 = (tx + math.cos(spin + math.pi)*tr, ty + math.sin(spin + math.pi)*tr)
            pygame.draw.line(self.game.screen, (255, 255, 255), p1, p2, 1)

            p3 = (tx + math.cos(spin + math.pi/2)*tr, ty + math.sin(spin + math.pi/2)*tr)
            p4 = (tx + math.cos(spin - math.pi/2)*tr, ty + math.sin(spin - math.pi/2)*tr)
            pygame.draw.line(self.game.screen, (255, 255, 255), p3, p4, 1)

        # Draw custom Sci-Fi Gun Cursor
        mx, my = pygame.mouse.get_pos()
        
        # Crosshair / Laser Sight
        c_color = (255, 50, 100)
        pygame.draw.line(self.game.screen, c_color, (mx - 15, my), (mx - 5, my), 2)
        pygame.draw.line(self.game.screen, c_color, (mx + 5, my), (mx + 15, my), 2)
        pygame.draw.line(self.game.screen, c_color, (mx, my - 15), (mx, my - 5), 2)
        pygame.draw.line(self.game.screen, c_color, (mx, my + 5), (mx, my + 15), 2)
        pygame.draw.circle(self.game.screen, c_color, (mx, my), 3)

        # Laser beam coming out of the pre-rendered sci-fi gun
        gun_offset = 35
        gun_center = (mx + gun_offset, my + gun_offset)
        
        # Barrel tip is mathematically ~20 pixels top-left from the gun's image center
        tip_x, tip_y = gun_center[0] - 18, gun_center[1] - 18
        
        # Draw solid laser beam behind the gun rendering but tracing to crosshair
        pygame.draw.line(self.game.screen, (255, 50, 100), (tip_x, tip_y), (mx, my), 4)
        pygame.draw.line(self.game.screen, (255, 200, 200), (tip_x, tip_y), (mx, my), 2)

        # Blit the beautifully constructed sci-fi gun cursor
        gun_rect = self.gun_cursor.get_rect(center=gun_center)
        self.game.screen.blit(self.gun_cursor, gun_rect.topleft)

        pygame.display.flip()

