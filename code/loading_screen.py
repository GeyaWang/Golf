import pygame
import sys
from level import Level


class LoadingScreen:
    def __init__(self, level: Level) -> None:
        self.level = level
        self.is_loading = True

        self.display_surf = pygame.display.get_surface()
        self.font = pygame.font.SysFont("Roboto", 30)
        self.current_text = ""

        # colours
        self.background_colour = (40, 40, 40)
        self.loading_bar_colour = (226, 65, 103)
        self.text_colour = (255, 255, 255)

        # sprites
        self.loading_bar = pygame.image.load('../graphics/gui/loading_bar.png')
        self.loading_bar_rect = self.loading_bar.get_rect(center=(self.display_surf.get_width() / 2, self.display_surf.get_height() / 2))
        self.loading_bar_padding = 20

        # offsets
        self.text_offset = (0, 110)

    def _draw(self) -> None:
        # loading bar
        self.display_surf.blit(self.loading_bar, self.loading_bar_rect)
        pygame.draw.rect(
            self.display_surf,
            self.loading_bar_colour,
            pygame.Rect(
                self.loading_bar_rect.topleft[0] + self.loading_bar_padding,
                self.loading_bar_rect.topleft[1] + self.loading_bar_padding,
                (self.loading_bar_rect.width - self.loading_bar_padding * 2) * (self.level.loading_progress / self.level.loading_total_work),
                (self.loading_bar_rect.height - self.loading_bar_padding * 2)
            )
        )
        # progress text
        if self.current_text != self.level.loading_status:
            self.current_text = self.level.loading_status
            self.text = self.font.render(self.current_text, True, self.text_colour)
            self.text_rect = self.text.get_rect(center=(self.display_surf.get_width() / 2 + self.text_offset[0], self.display_surf.get_height() / 2 + self.text_offset[1]))
        self.display_surf.blit(self.text, self.text_rect)

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            if not self.level.is_loading:
                break

            self.display_surf.fill(self.background_colour)
            self._draw()
            pygame.display.flip()
