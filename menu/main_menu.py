import pygame
from settings import *
from utils.button import Button

class MainMenu:
    def __init__(self, game):
        self.game = game
        self.options = [
            ("Aim Trainer", "aim"),
            ("Dodge Cars", "cars"),
            ("Memory Game", "memory"),
            ("Tetris", "tetris"),
            ("Toggle Fullscreen", "toggle_fullscreen"),
        ]
        self.buttons = []

    def run(self, events):
        width, height = self.game.screen.get_size()

        # 🔥 slightly improved scaling (prevents UI from becoming too big)
        scale = min(width / 1200, height / 800)

        title_font = pygame.font.SysFont(None, int(56 * scale), bold=True)
        body_font = pygame.font.SysFont(None, int(28 * scale))

        panel_margin_y = int(80 * scale)
        panel_width = min(int(width * 0.65), width - int(240 * scale))
        panel_margin_x = (width - panel_width) // 2
        panel_height = height - panel_margin_y * 2

        mouse_pressed = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pressed = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.game.state = "aim"
                elif event.key == pygame.K_2:
                    self.game.state = "cars"
                elif event.key == pygame.K_3:
                    self.game.state = "memory"
                elif event.key == pygame.K_4:
                    self.game.state = "tetris"

        self.game.screen.fill(DARK_BG)

        # Background glow
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        for i in range(1, 5):
            radius = int((120 + i * 28) * scale)
            alpha = max(10, 60 - i * 10)
            center_x = panel_margin_x + panel_width - int(120 * scale)
            center_y = panel_margin_y + int((100 + i * 80) * scale)
            pygame.draw.circle(overlay, (*ACCENT, alpha), (center_x, center_y), radius)
        self.game.screen.blit(overlay, (0, 0))

        # Card panel
        card_rect = pygame.Rect(panel_margin_x, panel_margin_y, panel_width, panel_height)
        pygame.draw.rect(self.game.screen, CARD, card_rect, border_radius=int(30 * scale))
        pygame.draw.rect(self.game.screen, ACCENT, card_rect, width=int(3 * scale), border_radius=int(30 * scale))

        # Text surfaces
        title = title_font.render("CG Game Hub", True, WHITE)
        subtitle = body_font.render("Choose your challenge and press a button.", True, SECONDARY)
        hint = body_font.render("Click any card or press 1-4 to start.", True, TEXT)
        fullscreen_hint = body_font.render("Press F11 to toggle fullscreen/windowed.", True, SECONDARY)
        footer = body_font.render("Press ESC in any game to return.", True, TEXT)

        # ----------- DYNAMIC LAYOUT (FIX) -----------

        center_x = width // 2
        y = panel_margin_y + int(30 * scale)

        # Title
        self.game.screen.blit(title, (center_x - title.get_width() // 2, y))
        y += title.get_height() + int(15 * scale)

        # Subtitle
        self.game.screen.blit(subtitle, (center_x - subtitle.get_width() // 2, y))
        y += subtitle.get_height() + int(15 * scale)

        # Hint
        self.game.screen.blit(hint, (center_x - hint.get_width() // 2, y))
        y += hint.get_height() + int(30 * scale)

        # Buttons
        button_width = min(int(panel_width * 0.65), int(450 * scale))
        button_height = int(50 * scale)
        spacing = int(12 * scale)
        button_x = panel_margin_x + (panel_width - button_width) // 2

        self.buttons = []
        for label, state in self.options:
            rect = (button_x, y, button_width, button_height)
            button = Button(rect, label, body_font, border_radius=int(14 * scale))
            button.state = state
            self.buttons.append(button)
            y += button_height + spacing

        # Draw buttons
        for button in self.buttons:
            button.draw(self.game.screen)
            if mouse_pressed and button.is_hovered():
                if button.state == "toggle_fullscreen":
                    self.game.toggle_fullscreen()
                else:
                    self.game.state = button.state

        # Footer (fixed to bottom)
        footer_y = panel_margin_y + panel_height - int(70 * scale)
        fullscreen_y = panel_margin_y + panel_height - int(35 * scale)

        self.game.screen.blit(
            footer,
            (center_x - footer.get_width() // 2, footer_y)
        )

        self.game.screen.blit(
            fullscreen_hint,
            (center_x - fullscreen_hint.get_width() // 2, fullscreen_y)
        )

        # ----------- END FIX -----------

        pygame.display.flip()