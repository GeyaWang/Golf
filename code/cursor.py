import pygame
from math import atan2, cos, sin, sqrt


class Cursor:
    def __init__(self, player):
        self.player = player

        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_hover = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_width, self.cursor_height = self.cursor_default.get_size()

        self.display_surf = pygame.display.get_surface()

        self.mouse_x = None
        self.mouse_y = None

        self.arrow_length = 50
        self.outer_radius = self.player.rect.width / 2 + 10
        self.inner_radius = self.player.rect.width / 2 + 4

    def _input(self):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed(3)[0]:  # If left mouse button pressed
            self.player.shoot()

    def _draw(self):
        if pygame.mouse.get_focused():
            self.display_surf.blit(self.cursor_default, (self.mouse_x - self.cursor_width / 2, self.mouse_y - self.cursor_height / 2))

    def update(self):
        self._input()
        self._draw()
