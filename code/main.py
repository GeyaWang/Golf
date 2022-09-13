import pygame
from settings import *
from level import Level
from input import Mouse
from threading import Thread


class Game:
    def __init__(self) -> None:
        # general setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.SCALED, vsync=1)
        self.clock = pygame.time.Clock()

        pygame.display.set_caption('Epic GAME!!!')
        pygame.mouse.set_visible(False)

        self.mouse = Mouse()
        self.level = Level(self.mouse)

        self.is_running = True

    def _mouse_thread(self):
        while self.is_running:
            self.mouse.update()
            self.clock.tick(150)

    def run(self) -> None:
        """Game loop."""

        # initiate mouse thread
        mouse_thread = Thread(target=self._mouse_thread)
        mouse_thread.start()

        try:
            while self.is_running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT or pygame.key.get_pressed()[pygame.K_q]:
                        self.is_running = False

                self.screen.fill('Black')
                self.level.run()
                pygame.display.flip()
                self.clock.tick(FPS)
        except KeyboardInterrupt:
            self.is_running = False

        # cleanup
        mouse_thread.join()  # wait for thread to close
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
