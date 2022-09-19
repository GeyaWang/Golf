import pygame
from input import Input
from enum import Enum, auto


class CursorType(Enum):
    DEFAULT = auto()
    HOVER = auto()
    LOCKED = auto()


class Cursor(pygame.cursors.Cursor):
    def __init__(self, input_: Input) -> None:
        self.input = input_

        self.cursor_default = pygame.image.load('../graphics/cursor/cursor_default.png').convert_alpha()
        self.cursor_hover = pygame.image.load('../graphics/cursor/cursor_hover.png').convert_alpha()
        self.cursor_locked = pygame.image.load('../graphics/cursor/cursor_locked.png').convert_alpha()

        self.display_surf = pygame.display.get_surface()
        self.half_width = self.cursor_default.get_width() // 2
        self.rect = self.cursor_default.get_rect()

        self.locked = False
        self.player = None

        self.hotspot = (self.half_width, self.half_width)
        super().__init__(self.hotspot, self.cursor_default)

    def _get_cursor_image(self) -> None:
        if self.locked:
            style = CursorType.LOCKED
        elif self.is_hover and self._is_player_can_jump():
            style = CursorType.HOVER
        else:
            style = CursorType.DEFAULT
        self.set_image(style)

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

    def set_image(self, style: CursorType):
        match style:
            case CursorType.DEFAULT:
                surf = self.cursor_default
            case CursorType.HOVER:
                surf = self.cursor_hover
            case CursorType.LOCKED:
                surf = self.cursor_locked
            case x:
                raise ValueError(f"Invalid cursor type: {x}")
        self.data = (self.hotspot, surf)

    def update(self) -> None:
        if self.player is not None:
            self._input()
            self._get_cursor_image()
