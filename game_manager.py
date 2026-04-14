from menu.main_menu import MainMenu
from games.aim_trainer import AimTrainer
from games.dodge_cars import DodgeCars
from games.memory_game import MemoryGame
from games.tetris import Tetris
from settings import *
import pygame
import os

_FULLSCREEN_CYCLE = (None, "exclusive", "windowed")
_RESIZE_EVENTS = (pygame.VIDEORESIZE,)


class GameManager:
    def __init__(self):
        self.running = True
        self.state = "menu"
        self.previous_state = None
        self.fullscreen_mode = FULLSCREEN_MODE
        if self.fullscreen_mode not in _FULLSCREEN_CYCLE:
            self.fullscreen_mode = None

        # Cache desktop resolution before any set_mode call
        info = pygame.display.Info()
        self._desktop_w, self._desktop_h = info.current_w, info.current_h

        pygame.display.set_caption("CG Game Hub")
        self.screen = self._create_display()
        self.clock = pygame.time.Clock()

        self.display_width, self.display_height = self.screen.get_size()

        self.menu = MainMenu(self)
        self.aim = AimTrainer(self)
        self.cars = DodgeCars(self)
        self.memory = MemoryGame(self)
        self.tetris = Tetris(self)

    def _clamp_window_size(self, width, height):
        """Fit the window inside the current display (taskbar / scaling safe)."""
        margin_w, margin_h = 80, 120
        max_w = max(640, self._desktop_w - margin_w)
        max_h = max(480, self._desktop_h - margin_h)
        return min(width, max_w), min(height, max_h)

    def _create_display(self):
        """Create display with current fullscreen mode."""
        width, height = WIDTH, HEIGHT
        flags = pygame.DOUBLEBUF

        if self.fullscreen_mode == "exclusive":
            flags |= pygame.FULLSCREEN

        elif self.fullscreen_mode == "windowed":
            info = pygame.display.Info()
            width, height = info.current_w, info.current_h
            flags |= pygame.NOFRAME
            os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"

        else:
            flags |= pygame.RESIZABLE
            width, height = self._clamp_window_size(width, height)

        return pygame.display.set_mode((width, height), flags, vsync=1)

    def toggle_fullscreen(self):
        """Cycle: resizable window -> exclusive fullscreen -> borderless desktop -> resizable window."""
        try:
            i = _FULLSCREEN_CYCLE.index(self.fullscreen_mode)
        except ValueError:
            i = -1
        self.fullscreen_mode = _FULLSCREEN_CYCLE[(i + 1) % len(_FULLSCREEN_CYCLE)]
        self.screen = self._create_display()
        self.display_width, self.display_height = self.screen.get_size()

    def run(self):
        state_changed = self.state != self.previous_state
        old_state = self.previous_state
        if state_changed:
            self.previous_state = self.state
            current = getattr(self, self.state, None)
            if current is not None and hasattr(current, "reset"):
                current.reset()

            if old_state == "aim" and self.state != "aim":
                pygame.mouse.set_visible(True)
                self.aim._hidden_cursor = False

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                self.toggle_fullscreen()
            elif self.fullscreen_mode is None and event.type in _RESIZE_EVENTS:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE | pygame.DOUBLEBUF, vsync=1
                )
                self.display_width, self.display_height = self.screen.get_size()

        current = getattr(self, self.state, None)
        if current is not None:
            current.run(events)

        self.clock.tick(FPS)