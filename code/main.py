import pygame
import sys
from settings import *
from level import Level


class Game:
    def __init__(self) -> None:
        # general setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        pygame.display.set_caption('Epic GAME!!!')
        pygame.mouse.set_visible(False)

        self.level = Level()

    def run(self) -> None:
        """Game loop."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_q]:
                    pygame.quit()
                    sys.exit()

            self.screen.fill('Black')
            self.level.run()
            pygame.display.update()
            self.clock.tick(FPS)


if __name__ == '__main__':
    game = Game()
    game.run()
