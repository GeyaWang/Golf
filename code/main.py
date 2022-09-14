import pygame
from settings import *
from level import Level
from input import Input
from threading import Thread
from typing import Callable


class Game:
    """Control game processes."""
    def __init__(self) -> None:
        # general setup
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.SCALED, vsync=1)
        self.clock = pygame.time.Clock()

        self.input = Input()
        self.level = Level(self.input)

        pygame.display.set_caption('Golf Game')
        pygame.mouse.set_visible(False)

        self.is_running = True
        self.commands: dict[int: Callable] = {
            pygame.K_q: self.stop,
            pygame.K_h: self.level.toggle_hitboxes,
        }

    def stop(self) -> None:
        self.is_running = False

    def _run(self) -> None:
        """Game loop."""
        while self.is_running:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    self.is_running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in self.commands:
                        self.commands[event.key]()  # call function

            self.input.update(event_list)

            self.screen.fill('Black')
            self.level.run()
            self.input.mouse.update()
            pygame.display.flip()
            self.clock.tick(FPS)

    def start(self) -> None:
        """Start game."""
        try:
            self._run()
        except KeyboardInterrupt:
            self.is_running = False

        # cleanup
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.start()
