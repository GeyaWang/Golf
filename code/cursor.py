import pygame
from player import Player
from input import Input


class Cursor:
    def __init__(self, player: Player, input_: Input) -> None:
        self.player = player
        self.input = input_

        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_hover = pygame.image.load('../graphics/cursor/cursor_hover.png').convert_alpha()
        self.cursor_locked = pygame.image.load('../graphics/cursor/cursor_locked.png').convert_alpha()
        self.cursor_width = self.cursor_default.get_width()
        self.cursor_height = self.cursor_default.get_height()
        self.hitbox = self.cursor_default.get_rect()

        self.display_surf = pygame.display.get_surface()

        self.locked = False
        self.line_thickness = 5

    def _input(self) -> None:
        """Get and handle player input."""
        self.hitbox.center = self.input.mouse.pos.x, self.input.mouse.pos.y
        self.is_hover = self.hitbox.collidepoint(self.player.offset)

        if not self.input.mouse.is_focused:
            self.locked = False

        if pygame.mouse.get_pressed(3)[0]:  # if left mouse button pressed
            if self.is_hover and self._is_player_can_jump():
                self.locked = True
        else:  # released
            if self.locked:  # previously locked
                self._shoot()
            self.locked = False

    def _shoot(self):
        """Handle shoot event."""
        if self.player.n_jumps > 0:
            self.player.n_jumps -= 1
            self.player.shoot()

    def _get_image(self):
        """Return sprite to display."""
        if self.locked:
            return self.cursor_locked
        if self.is_hover and self._is_player_can_jump():
            return self.cursor_hover
        return self.cursor_default

    def _is_player_can_jump(self):
        """Return if player can jump."""
        return self.player.n_jumps > 0 and self.player.can_jump

    def _draw(self) -> None:
        """Draw objects."""
        if self.locked:
            # draw line
            pygame.draw.line(
                self.display_surf,
                (255, 255, 255),
                (self.input.mouse.pos.x, self.input.mouse.pos.y),
                self.player.offset,
                self.line_thickness
            )
        self.display_surf.blit(self._get_image(), (self.input.mouse.pos.x - self.cursor_width / 2, self.input.mouse.pos.y - self.cursor_height / 2))

    def update(self) -> None:
        """Manage actions per frame."""
        self._input()
        self._draw()
