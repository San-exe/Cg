import pygame
import math
from random import randint, uniform, choice
from settings import *

class DodgeCars:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(None, 48, bold=True)
        self.text_font = pygame.font.SysFont(None, 26)
        
        # Parallax starfield for deep space
        self.stars = []
        for _ in range(120):
            self.stars.append({
                "x": uniform(0, 1),
                "y": uniform(0, 1),
                "radius": uniform(0.5, 3.0),
                "parallax": uniform(0.2, 1.2),
                "glow": uniform(0.5, 1.0)
            })
            
        self.reset()

    def reset(self):
        width, height = self.game.screen.get_size()
        self.player_x = width / 2
        self.player_y = height - 150
        self.player_vx = 0.0
        
        self.speed = 400.0 # Vertical track speed
        self.score = 0
        self.spawn_delay = 1.0 # seconds
        self.timer = 0.0
        
        self.cars = []      # Enemy vehicles
        self.particles = [] # Engine trails & explosions
        self.lane_offset = 0.0
        
        self.move_left = False
        self.move_right = False
        self.game_over = False
        
        self.create_car()

    def create_car(self):
        width, height = self.game.screen.get_size()
        lanes = 2
        margins = width // 2 - 240
        lane_w = max(80, (width - margins * 2) // lanes)
        lane = randint(0, lanes - 1)
        
        # Randomize spawn X within the lane to make it unpredictable
        lane_center = margins + lane * lane_w + lane_w / 2
        offset = uniform(-lane_w * 0.35, lane_w * 0.35)
        x = lane_center + offset
        
        # Start above the screen natively
        self.cars.append({
            "x": x,
            "y": -80.0,
            "speed": uniform(1.1, 2.0), # multiplier of track speed
            "width": 42,
            "height": 115, # sleeker, longer cars
            "sway": uniform(0, math.pi * 2), # independent horizontal sway offset
            "color": choice([(255, 80, 100), (255, 156, 85), (200, 100, 255)])
        })

    def run(self, events):
        if self.game.state != "cars":
            return

        dt = self.game.clock.get_time() / 1000.0
        if dt > 0.1: dt = 0.1
        current_time = pygame.time.get_ticks() / 1000.0

        if self.game_over:
            for event in events:
                if event.type == pygame.QUIT:
                    self.game.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game.state = "menu"
                        self.reset()
                    elif event.key == pygame.K_SPACE:
                        self.reset()
            self.draw_screen(game_over=True, time=current_time)
            return

        for event in events:
            if event.type == pygame.QUIT:
                self.game.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "menu"
                    self.reset()
                if event.key == pygame.K_LEFT:
                    self.move_left = True
                if event.key == pygame.K_RIGHT:
                    self.move_right = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.move_left = False
                if event.key == pygame.K_RIGHT:
                    self.move_right = False

        width, height = self.game.screen.get_size()
        margins = width // 2 - 240
        # Physics - Inertia and friction for anti-gravity feel
        accel = 2400.0
        friction = 6.0
        if self.move_left:
            self.player_vx -= accel * dt
        if self.move_right:
            self.player_vx += accel * dt
            
        self.player_vx -= self.player_vx * friction * dt
        self.player_x += self.player_vx * dt
        
        # Soft bounce on borders
        limit_left = margins + 30
        limit_right = width - margins - 30
        if self.player_x < limit_left:
            self.player_x = limit_left
            self.player_vx *= -0.5
        elif self.player_x > limit_right:
            self.player_x = limit_right
            self.player_vx *= -0.5

        # Track and Lane movement
        progress = self.speed * dt
        self.lane_offset = (self.lane_offset + progress) % 80
        
        # Parallax stars
        for star in self.stars:
            star["y"] += star["parallax"] * progress / height
            if star["y"] > 1.0:
                star["y"] = 0.0
                star["x"] = uniform(0, 1)

        # Spawning mechanism
        self.timer += dt
        # Dynamically scale difficulty with more randomness
        base_delay = uniform(0.6, 1.5)
        current_delay = max(0.35, base_delay - (self.score * 0.015))
        
        if self.timer > current_delay:
            self.create_car()
            self.timer = 0
            self.score += 1
            # Slowly increase track speed
            self.speed = min(1100.0, self.speed + 8.0)

        # Update enemy vehicles & detect collision
        # Also give player an elongated hitbox
        player_rect = pygame.Rect(self.player_x - 18, self.player_y - 50, 36, 100)
        
        for car in reversed(self.cars):
            # Anti-gravity slide
            car["sway"] += dt * 3.0
            car_x = car["x"] + math.sin(car["sway"]) * 10.0
            car["y"] += self.speed * car["speed"] * dt
            
            car_rect = pygame.Rect(car_x - car["width"]/2, car["y"] - car["height"]/2, car["width"], car["height"])
            
            # Reduce hitbox slightly for fair dodges
            if car_rect.inflate(-15, -15).colliderect(player_rect.inflate(-10, -10)):
                self.game_over = True
                self.explode(self.player_x, self.player_y, ACCENT)
                self.explode(car_x, car["y"], car["color"])
                
            if car["y"] > height + 100:
                self.cars.remove(car)
            else:
                # Add engine trail
                self.particles.append({
                    "x": car_x + uniform(-10, 10),
                    "y": car["y"] - car["height"]/2,  # exhaust out the back/top
                    "vy": -self.speed * 0.2, # drifts up
                    "life": 0.3, "max_life": 0.3, "color": car["color"]
                })

        # Add player engine trails
        if not self.game_over:
            self.particles.append({
                "x": self.player_x - 10 + uniform(-3, 3),
                "y": self.player_y + 36,
                "vy": self.speed * 0.5,
                "life": 0.25, "max_life": 0.25, "color": (102, 219, 255)
            })
            self.particles.append({
                "x": self.player_x + 10 + uniform(-3, 3),
                "y": self.player_y + 36,
                "vy": self.speed * 0.5,
                "life": 0.25, "max_life": 0.25, "color": (102, 219, 255)
            })

        # Particles update
        for p in reversed(self.particles):
            p["life"] -= dt
            if p["life"] <= 0:
                self.particles.remove(p)
            else:
                p["x"] += getattr(p, "vx", 0.0) * dt
                p["y"] += getattr(p, "vy", p.get("vy", 0)) * dt

        self.draw_screen(game_over=False, time=current_time)

    def explode(self, x, y, color):
        for _ in range(40):
            ang = uniform(0, math.pi * 2)
            spd = uniform(100, 600)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "life": 1.5, "max_life": 1.5,
                "color": choice([color, (255, 255, 255), (255, 200, 100)])
            })

    def draw_screen(self, game_over, time):
        width, height = self.game.screen.get_size()
        margins = width // 2 - 240
        
        # Deep space background
        self.game.screen.fill((5, 8, 16))
        
        # Render Starfield layer
        for star in self.stars:
            sx = int(star["x"] * width)
            sy = int(star["y"] * height)
            alpha = int((math.sin(time * 4 + star["x"] * 10) * 0.5 + 0.5) * 200) + 50
            r = int(star["radius"])
            if r > 0:
                pygame.draw.circle(self.game.screen, (200, 240, 255, alpha), (sx, sy), r)
        
        # Glass HUD Panel
        hud_rect = pygame.Rect(40, 50, width - 80, height - 100)
        hud_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (*CARD, 120), hud_rect, border_radius=30)
        self.game.screen.blit(hud_surf, (0, 0))
        pygame.draw.rect(self.game.screen, (*ACCENT, 80), hud_rect, width=2, border_radius=30)
        
        title = self.title_font.render("Road Dodger", True, ACCENT2)
        score_text = self.text_font.render(f"SCORE: {self.score}", True, WHITE)
        speed_text = self.text_font.render(f"SPEED: {int(self.speed)} KM/H", True, WHITE)
        instructions = self.text_font.render("Use Left and Right to dodge cars! ESC returns.", True, TEXT)

        self.game.screen.blit(title, (70, 70))
        self.game.screen.blit(score_text, (70, 120))
        self.game.screen.blit(speed_text, (70, 150))
        self.game.screen.blit(instructions, (70, 190))

        # Holographic Track
        track_rect = pygame.Rect(margins, 230, width - margins * 2, height - 320)
        pygame.draw.rect(self.game.screen, (*PANEL, 150), track_rect, border_radius=20)
        # Glowing edges of track
        pygame.draw.rect(self.game.screen, ACCENT, track_rect, width=2, border_radius=20)

        # Animated Lane Dividers and Boundaries
        lanes = 2
        lane_w = (width - margins * 2) // lanes
        lx = margins + lane_w # Center line
        
        for y_off in range(230 - 80 + int(self.lane_offset), height - 80, 80):
            if y_off > 230:
                # Center dashed line
                pygame.draw.rect(self.game.screen, (*ACCENT, 180), (lx - 2, y_off, 4, 40), border_radius=2)
                
                # Thick glowing boundary blocks on the sides
                pygame.draw.rect(self.game.screen, ACCENT2, (margins + 4, y_off, 6, 60), border_radius=2)
                pygame.draw.rect(self.game.screen, ACCENT2, (width - margins - 10, y_off, 6, 60), border_radius=2)

        # Draw engine trail particles inside track area
        for p in self.particles:
            ratio = p["life"] / p["max_life"]
            r = max(1, int(6 * ratio))
            # Just rough boundary checks so trails don't draw over UI too badly
            if p["y"] > 230 and p["y"] < height - 90:
                p_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*p["color"], int(255 * ratio)), (r, r), r)
                self.game.screen.blit(p_surf, (int(p["x"]-r), int(p["y"]-r)))

        hover = math.sin(time * 8) * 8 # Simulate vertical hover bouncing visually
        
        # Vehicles Drawing Helper
        def draw_antigrav_car(screen, cx, cy, w, h, color):
            # Cast a shadow down
            pygame.draw.ellipse(screen, (0, 0, 0, 100), (cx - w/2 - 10, cy + h/2 - 10, w + 20, 30))
            
            # Cyberpunk chassis 
            sh = h * 0.8
            chassis = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.polygon(chassis, color, [(w/2, 0), (w, sh*0.2), (w*0.8, sh), (w*0.2, sh), (0, sh*0.2)])
            
            # Cockpit top
            pygame.draw.polygon(chassis, (20, 25, 35), [(w/2, sh*0.1), (w*0.8, sh*0.4), (w*0.5, sh*0.7), (w*0.2, sh*0.4)])
            
            # Thruster glow back
            pygame.draw.ellipse(chassis, ACCENT, (w*0.2, sh - 5, w*0.6, 10))
            pygame.draw.ellipse(chassis, (255, 255, 255), (w*0.35, sh - 2, w*0.3, 4))
            
            screen.blit(chassis, (int(cx - w/2), int(cy - h/2 + hover)))

        # Draw enemies
        for car in self.cars:
            if car["y"] > 230 and car["y"] < height - 50:
                draw_antigrav_car(self.game.screen, car["x"] + math.sin(car["sway"])*10, car["y"], car["width"], car["height"], car["color"])

        # Draw Player (sleeker player chassis size)
        if not game_over:
            draw_antigrav_car(self.game.screen, self.player_x, self.player_y, 40, 115, ACCENT)

        if game_over:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((5, 8, 16, 200))
            self.game.screen.blit(overlay, (0, 0))
            
            end_text = self.title_font.render("VEHICLE DESTROYED", True, (255, 100, 100))
            self.game.screen.blit(end_text, (width // 2 - end_text.get_width() // 2, height // 2 - 40))
            
            return_text = self.text_font.render("Simulation Failed. Press SPACE to restart or ESC to return.", True, TEXT)
            self.game.screen.blit(return_text, (width // 2 - return_text.get_width() // 2, height // 2 + 20))

        pygame.display.flip()