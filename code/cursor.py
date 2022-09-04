import pygame
from math import atan2, cos, sin, sqrt


class Cursor:
    def __init__(self, player):
        self.player = player

        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_hover = pygame.image.load('../graphics/cursor/cursor_hover.png').convert_alpha()
        self.cursor_locked = pygame.image.load('../graphics/cursor/cursor_locked.png').convert_alpha()
        self.cursor_width, self.cursor_height = self.cursor_default.get_size()
        self.hitbox = self.cursor_default.get_rect()

        self.display_surf = pygame.display.get_surface()

        self.locked = False
        self.line_thickness = 5

    def _input(self):
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()
        self.hitbox.center = self.mouse_x, self.mouse_y
        self.is_hover = self.hitbox.collidepoint(self.player.offset)
        self.screen_focused = pygame.mouse.get_focused()

        if not self.screen_focused:
            self.locked = False

        if pygame.mouse.get_pressed(3)[0]:  # if left mouse button pressed
            if self.is_hover and self._player_can_jump():
                self.locked = True
        else:  # released
            if self.locked:  # previously locked
                self._shoot()
            self.locked = False

    def _shoot(self):
        if self.player.n_jumps > 0:
            self.player.n_jumps -= 1
            self.player.shoot()

    def _get_image(self):
        # find image type
        if self.locked:
            return self.cursor_locked
        if self.is_hover and self._player_can_jump():
            return self.cursor_hover
        return self.cursor_default

    def _player_can_jump(self):
        return self.player.n_jumps > 0 and self.player.can_jump

    def _draw(self):
        if self.locked:
            pygame.draw.line(
                self.display_surf,
                (255, 255, 255),
                (self.mouse_x, self.mouse_y),
                self.player.offset,
                self.line_thickness
            )
        if pygame.mouse.get_focused():
            self.display_surf.blit(self._get_image(), (self.mouse_x - self.cursor_width / 2, self.mouse_y - self.cursor_height / 2))

    def update(self):
        self._input()
        self._draw()
