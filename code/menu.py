import pygame
from PIL import Image, ImageFilter


class Menu:
    def __init__(self) -> None:
        self.paused = self.Paused()

    class Paused:
        def __init__(self):
            self.display_surf = pygame.display.get_surface()
            self.screen_width = self.display_surf.get_width()
            self.screen_height = self.display_surf.get_height()

            self.blur_magnitude = 2

        def blur(self, magnitude: float) -> None:
            data = pygame.image.tostring(self.display_surf, 'RGBA')
            blured = Image.frombytes('RGBA', (self.screen_width, self.screen_height), data).filter(ImageFilter.GaussianBlur(radius=magnitude))
            image = pygame.image.frombuffer(blured.tobytes('raw', 'RGBA'), (self.screen_width, self.screen_height), 'RGBA')
            self.display_surf.blit(image, (0, 0))

        def draw(self) -> None:
            self.blur(self.blur_magnitude)
