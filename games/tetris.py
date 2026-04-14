import pygame
import math
from random import choice, uniform
from settings import *

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 0, 1], [1, 1, 1]],
]
COLORS = [ACCENT, ACCENT2, (255, 116, 196), (115, 247, 172), (255, 201, 84), (180, 104, 255), (116, 211, 255)]

class Tetris:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(None, 48, bold=True)
        self.text_font = pygame.font.SysFont(None, 26)
        
        # Cosmic deep space background
        self.stars = [{"x": uniform(0, 1), "y": uniform(0, 1), "r": uniform(1, 2.5), "speed": uniform(0.01, 0.05), "w": uniform(0, math.pi*2)} for _ in range(100)]
        self.reset()

    def reset(self):
        self.cols = 10
        self.rows = 20
        self.cell = 32
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        # Physics arrays for inertia settling
        self.board_y_offsets = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.game_over = False
        self.score = 0
        self.level = 1
        
        self.spawn_piece()
        self.visual_x = self.piece_x * self.cell
        self.visual_y = (self.piece_y - 2) * self.cell
        
        self.drop_delay = 800
        self.last_drop = pygame.time.get_ticks()
        self.particles = []

    def spawn_piece(self):
        self.shape = choice(SHAPES)
        self.color = choice(COLORS)
        self.piece_x = self.cols // 2 - len(self.shape[0]) // 2
        self.piece_y = 0
        
        # Calculate start for smooth float-in
        self.visual_x = self.piece_x * self.cell
        self.visual_y = -3 * self.cell
        
        if self.check_collision(self.piece_x, self.piece_y, self.shape):
            self.game_over = True

    def rotate_shape(self, shape):
        return [list(row) for row in zip(*shape[::-1])]

    def check_collision(self, x, y, shape):
        for row_index, row in enumerate(shape):
            for col_index, cell in enumerate(row):
                if cell:
                    board_x = x + col_index
                    board_y = y + row_index
                    if board_x < 0 or board_x >= self.cols or board_y >= self.rows:
                        return True
                    if board_y >= 0 and self.board[board_y][board_x]:
                        return True
        return False

    def lock_piece(self):
        for row_index, row in enumerate(self.shape):
            for col_index, cell in enumerate(row):
                if cell:
                    bx = self.piece_x + col_index
                    by = self.piece_y + row_index
                    if by >= 0:
                        self.board[by][bx] = self.color
                        # Apply inertia bounce effect when locked
                        self.board_y_offsets[by][bx] = -15.0 
                        
                        # Particles for lock effect
                        for _ in range(5):
                            self.particles.append({
                                "gx": bx * self.cell + uniform(0, self.cell),
                                "gy": by * self.cell + uniform(0, self.cell),
                                "vx": uniform(-30, 30),
                                "vy": uniform(-30, 30),
                                "life": 0.4,
                                "color": self.color
                            })
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        lines_cleared = []
        for y in range(self.rows):
            if all(self.board[y][x] != 0 for x in range(self.cols)):
                lines_cleared.append(y)
                
        if not lines_cleared: return
        
        lines = len(lines_cleared)
        self.score += lines * 100 * self.level
        self.level = min(15, 1 + self.score // 500)
        
        # Remove lines and insert at top
        for y in lines_cleared:
            del self.board[y]
            del self.board_y_offsets[y]
            self.board.insert(0, [0 for _ in range(self.cols)])
            self.board_y_offsets.insert(0, [0.0 for _ in range(self.cols)])
            
        # Apply drop inertia bounce to everything above cleared lines
        for r in range(max(lines_cleared) + 1):
            for c in range(self.cols):
                if self.board[r][c] != 0:
                    self.board_y_offsets[r][c] -= 20.0 * lines

    def run(self, events):
        if self.game.state != "tetris":
            return

        dt = self.game.clock.get_time() / 1000.0
        if dt > 0.1: dt = 0.1
        now = pygame.time.get_ticks()

        for event in events:
            if event.type == pygame.QUIT:
                self.game.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.state = "menu"
                    self.reset()
                elif self.game_over and event.key == pygame.K_SPACE:
                    self.reset()
                if not self.game_over:
                    if event.key == pygame.K_LEFT:
                        if not self.check_collision(self.piece_x - 1, self.piece_y, self.shape):
                            self.piece_x -= 1
                    if event.key == pygame.K_RIGHT:
                        if not self.check_collision(self.piece_x + 1, self.piece_y, self.shape):
                            self.piece_x += 1
                    if event.key == pygame.K_DOWN:
                        if not self.check_collision(self.piece_x, self.piece_y + 1, self.shape):
                            self.piece_y += 1
                    if event.key == pygame.K_UP:
                        rotated = self.rotate_shape(self.shape)
                        if not self.check_collision(self.piece_x, self.piece_y, rotated):
                            self.shape = rotated
                    if event.key == pygame.K_SPACE:
                        while not self.check_collision(self.piece_x, self.piece_y + 1, self.shape):
                            self.piece_y += 1
                        self.lock_piece()
                        self.last_drop = now

        # Gravity Drop Timer
        current_delay = max(100, self.drop_delay - self.level * 40)
        if not self.game_over and now - self.last_drop > current_delay:
            self.last_drop = now
            if not self.check_collision(self.piece_x, self.piece_y + 1, self.shape):
                self.piece_y += 1
            else:
                self.lock_piece()

        # Update smooth visual physics parameters
        target_x = self.piece_x * self.cell
        target_y = self.piece_y * self.cell
        
        self.visual_x += (target_x - self.visual_x) * 18.0 * dt
        self.visual_y += (target_y - self.visual_y) * 18.0 * dt
        
        for y in range(self.rows):
            for x in range(self.cols):
                if self.board_y_offsets[y][x] != 0:
                    # Spring dampener settling simulation
                    self.board_y_offsets[y][x] -= self.board_y_offsets[y][x] * 12.0 * dt
                    if abs(self.board_y_offsets[y][x]) < 0.5:
                        self.board_y_offsets[y][x] = 0.0

        for p in reversed(self.particles):
            p["life"] -= dt
            p["gx"] += p["vx"] * dt
            p["gy"] += p["vy"] * dt
            if p["life"] <= 0:
                self.particles.remove(p)

        self.draw_screen(now / 1000.0)

    def draw_screen(self, time_sec):
        width, height = self.game.screen.get_size()
        
        # Cosmic Background
        self.game.screen.fill((4, 5, 10))
        for star in self.stars:
            sx = int(star["x"] * width)
            # star falls slowly
            star["y"] = (star["y"] + star["speed"] * 0.01) % 1.0
            sy = int(star["y"] * height)
            alpha = int(128 + 127 * math.sin(time_sec * 3 + star["w"]))
            pygame.draw.circle(self.game.screen, (180, 220, 255, alpha), (sx, sy), int(star["r"]))

        # Dynamic Game Board calculations
        board_w = self.cols * self.cell
        board_h = self.rows * self.cell
        board_x = width // 2 - board_w // 2 - 120 # offset to left
        
        # Zero gravity board hover
        hover_y = math.sin(time_sec * 2.0) * 8.0
        board_y = height // 2 - board_h // 2 + hover_y

        # Glass board panel
        board_rect = pygame.Rect(board_x - 12, board_y - 12, board_w + 24, board_h + 24)
        panel_surf = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (*CARD, 130), board_rect, border_radius=16)
        self.game.screen.blit(panel_surf, (0, 0))
        
        pygame.draw.rect(self.game.screen, (*ACCENT, 100), board_rect, width=2, border_radius=16)

        # Holographic Grid Overlays
        for x in range(1, self.cols):
            lx = board_x + x * self.cell
            pygame.draw.line(self.game.screen, (255, 255, 255, 10), (lx, board_y), (lx, board_y + board_h))
        for y in range(1, self.rows):
            ly = board_y + y * self.cell
            pygame.draw.line(self.game.screen, (255, 255, 255, 10), (board_x, ly), (board_x + board_w, ly))

        def draw_block(surf, x, y, size, color):
            # Inner glass fill with neon borders
            rect = pygame.Rect(x, y, size, size)
            # Drop shadow/glow
            glow = pygame.Surface((size+8, size+8), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 40), glow.get_rect(), border_radius=6)
            surf.blit(glow, (x-4, y-4))
            
            # Base Block
            pygame.draw.rect(surf, (*color, 200), rect.inflate(-4, -4), border_radius=6)
            # Glowing edges
            pygame.draw.rect(surf, (255, 255, 255), rect.inflate(-4, -4), width=1, border_radius=6)
            # Center bright core
            pygame.draw.rect(surf, (255, 255, 255, 120), rect.inflate(-16, -16), border_radius=3)

        # Draw Locked Blocks
        for y in range(self.rows):
            for x in range(self.cols):
                cell_color = self.board[y][x]
                if cell_color:
                    bx = board_x + x * self.cell
                    by = board_y + y * self.cell + self.board_y_offsets[y][x]
                    draw_block(self.game.screen, bx, by, self.cell, cell_color)

        # Draw Smooth Falling Piece with Inertia
        if not self.game_over:
            for row_index, row in enumerate(self.shape):
                for col_index, cell in enumerate(row):
                    if cell:
                        bx = board_x + self.visual_x + col_index * self.cell
                        by = board_y + self.visual_y + row_index * self.cell
                        if by > board_y - self.cell: # only draw if mainly within board bounds vertically
                            draw_block(self.game.screen, bx, by, self.cell, self.color)

        # Draw Particles
        for p in self.particles:
            ratio = p["life"] / 0.4
            alpha = int(255 * ratio)
            r = int(4 * ratio)
            if r > 0:
                p_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*p["color"], alpha), (r, r), r)
                self.game.screen.blit(p_surf, (board_x + p["gx"], board_y + p["gy"]))

        # Typography UI Side Panel
        info_x = board_x + board_w + 50
        info_y = board_y + 40
        
        ui_rect = pygame.Rect(info_x - 20, info_y - 20, 300, 200)
        pygame.draw.rect(self.game.screen, (*CARD, 180), ui_rect, border_radius=16)
        pygame.draw.rect(self.game.screen, ACCENT, ui_rect, width=2, border_radius=16)
        
        title = self.title_font.render("Block Drop", True, ACCENT2)
        score_text = self.text_font.render(f"SCORE: {self.score}", True, WHITE)
        level_text = self.text_font.render(f"LEVEL: {self.level}", True, WHITE)
        hint1 = self.text_font.render("ARROWS: Move & Rotate", True, SECONDARY)
        hint2 = self.text_font.render("SPACE: Hard Drop", True, SECONDARY)
        
        self.game.screen.blit(title, (info_x, info_y))
        self.game.screen.blit(score_text, (info_x, info_y + 60))
        self.game.screen.blit(level_text, (info_x, info_y + 90))
        self.game.screen.blit(hint1, (info_x, info_y + 130))
        self.game.screen.blit(hint2, (info_x, info_y + 160))

        if self.game_over:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.game.screen.blit(overlay, (0, 0))
            
            game_over_text = self.title_font.render("System Failure", True, (255, 100, 100))
            prompt = self.text_font.render("Press SPACE to restart, ESC to reboot subsystem.", True, TEXT)
            self.game.screen.blit(game_over_text, (width // 2 - game_over_text.get_width() // 2, height // 2 - 50))
            self.game.screen.blit(prompt, (width // 2 - prompt.get_width() // 2, height // 2 + 20))

        pygame.display.flip()