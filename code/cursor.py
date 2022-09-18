import pygame
from player import Player
from input import Input


class Cursor(pygame.cursors.Cursor):
    def __init__(self, player: Player, input_: Input, surf=None) -> None:
        self.player = player
        self.input = input_

        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_hover = pygame.image.load('../graphics/cursor/cursor_hover.png').convert_alpha()
        self.cursor_locked = pygame.image.load('../graphics/cursor/cursor_locked.png').convert_alpha()

        self.display_surf = pygame.display.get_surface()
        self.half_width = self.cursor_default.get_width() // 2
        self.rect = self.cursor_default.get_rect()

        self.locked = False
        self.line_thickness = 5

        self.hotspot = (self.half_width, self.half_width)
        if surf is None:
            surf = self.cursor_default
        super().__init__(self.hotspot, surf)

    def _get_cursor_image(self) -> None:
        if self.locked:
            surf = self.cursor_locked
        elif self.is_hover and self._is_player_can_jump():
            surf = self.cursor_hover
        else:
            surf = self.cursor_default
        self.data = (self.hotspot, surf)

    def _is_player_can_jump(self) -> bool:
        """Return logic if player can jump."""
        return self.player.n_jumps > 0 and self.player.can_jump

    def _shoot(self) -> None:
        """Handle shoot event."""
        if self.player.n_jumps > 0:
            self.player.shoot()

    def _input(self) -> None:
        """Get and handle player input."""
        self.rect.center = self.input.mouse.pos.x, self.input.mouse.pos.y
        self.is_hover = self.rect.collidepoint(self.player.offset)

        if not self.input.mouse.is_focused:
            self.locked = False

        if pygame.mouse.get_pressed(3)[0]:  # if left mouse button pressed
            if self.is_hover and self._is_player_can_jump():
                self.locked = True
        else:  # released
            if self.locked:  # previously locked
                self._shoot()
            self.locked = False

    def _draw_line(self) -> None:
        if self.locked:
            # draw line
            pygame.draw.line(
                self.display_surf,
                (255, 255, 255),
                (self.input.mouse.pos.x, self.input.mouse.pos.y),
                self.player.offset,
                self.line_thickness
            )

    def update(self) -> None:
        self._input()
        self._draw_line()
        self._get_cursor_image()
