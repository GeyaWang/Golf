import pygame


class Input:
    """Enables easier access to key presses outside game loop."""
    def __init__(self) -> None:
        self.mouse = self.Mouse()

        self.is_paused = False
        self.esc_held = False

        self.event_list = []

    def _pause_event(self):
        """Manage actions on pause."""
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            if not self.esc_held:
                self.is_paused = not self.is_paused
                self.esc_held = True
                if self.is_paused:
                    pygame.event.set_grab(False)
                else:
                    pygame.event.set_grab(True)
        else:
            self.esc_held = False

    def update(self, event_list: list) -> None:
        """Get events."""
        self.event_list = event_list
        self.mouse.update()
        self._pause_event()

    class Mouse:
        def __init__(self) -> None:
            self.display_surf = pygame.display.get_surface()

            self.pos = pygame.Vector2()
            self.is_focused = False

        def update(self) -> None:
            """Manage actions."""
            self.is_focused = pygame.mouse.get_focused()  # get whether the game is focused
            self.pos.update(pygame.mouse.get_pos())  # get mouse position
