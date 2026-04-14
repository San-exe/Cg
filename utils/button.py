import pygame
from settings import *

class Button:
    def __init__(self, rect, text, font, base_color=BUTTON, hover_color=BUTTON_HOVER, text_color=BUTTON_TEXT, accent_color=ACCENT, border_radius=14):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.accent_color = accent_color
        self.border_radius = border_radius
        self.label = self.font.render(self.text, True, self.text_color)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, surface):
        color = self.hover_color if self.is_hovered() else self.base_color
        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, self.accent_color, self.rect, width=2, border_radius=self.border_radius)
        label_rect = self.label.get_rect(center=self.rect.center)
        surface.blit(self.label, label_rect)
