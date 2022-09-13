import pygame
from dataclasses import dataclass


@dataclass
class MousePos:
    x: int
    y: int


class Mouse:
    def __init__(self) -> None:
        self.display_surf = pygame.display.get_surface()
        self.width = self.display_surf.get_width()
        self.height = self.display_surf.get_height()
        self.half_width = self.width // 2
        self.half_height = self.height // 2

        self.pos = MousePos(
            x=self.half_width,
            y=self.half_height
        )

        self.is_focused = False
        self.is_paused = False
        self.esc_held = False

    def _set_mouse_pos(self):
        """Find fake mouse pos from mouse movements."""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.pos.x = min(max(self.pos.x + mouse_x - self.half_width, 0), self.width)
        self.pos.y = min(max(self.pos.y + mouse_y - self.half_height, 0), self.height)

    def _pause_event(self):
        """Handle paused event."""
        if self.is_paused:
            pygame.mouse.set_visible(True)
        else:
            pygame.mouse.set_visible(False)
            self._reset_mouse_pos()

    def _reset_mouse_pos(self):
        """Reset actual mouse position."""
        pygame.mouse.set_pos(self.half_width, self.half_height)

    def update(self):
        """Manage actions."""
        self.is_focused = pygame.mouse.get_focused()
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            if not self.esc_held:
                self.esc_held = True
                self.is_paused = not self.is_paused
                self._pause_event()
        else:
            self.esc_held = False

        if not self.is_paused and self.is_focused and pygame.mouse.get_pos() != (self.half_width, self.half_height):
            self._set_mouse_pos()
            self._reset_mouse_pos()
