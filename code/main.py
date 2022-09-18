import sys
import pygame
from settings import *
from level import Level
from input import Input
from typing import Callable
from cursor import Cursor
from loading_screen import LoadingScreen
from threading import Thread


class Game:
    """Control game processes."""
    def __init__(self) -> None:
        # general setup
        pygame.init()
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.SCALED
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags=flags, vsync=1)
        self.clock = pygame.time.Clock()
        pygame.display.set_caption('Golf Game')

        # split player calculations into chunks
        frame_chunks = 1
        chunk_deltatime = (1 / FPS) / frame_chunks

        self.input = Input()
        self.cursor = Cursor(self.input)
        pygame.mouse.set_cursor(self.cursor)
        self.level = Level(self.input, frame_chunks, chunk_deltatime)
        self.loading_screen = LoadingScreen(self.level)

        self.is_running = True
        self.commands: dict[int: Callable] = {
            pygame.K_q: self.stop,
            pygame.K_h: self.toggle_hitboxes,
        }

    def stop(self) -> None:
        self.is_running = False

    def toggle_hitboxes(self) -> None:
        self.level.camera.is_draw_hitboxes = not self.level.camera.is_draw_hitboxes

    def _run(self) -> None:
        """Game loop."""
        while self.is_running:
            event_list = pygame.event.get()
            for event in event_list:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in self.commands:
                        self.commands[event.key]()  # call function

            self.screen.fill('Black')

            self.input.update(event_list)  # input
            self.level.run()  # level
            self.cursor.update()  # cursor
            pygame.mouse.set_cursor(self.cursor)

            pygame.display.flip()
            self.clock.tick(FPS)

    def _load(self):
        """Load game objects."""
        # start loading thread
        load_thread = Thread(target=self.level.loading)
        load_thread.start()

        # show loading screen
        self.loading_screen.run()

        # setup once loading is finished
        self.player = self.level.player
        self.cursor.player = self.player
        pygame.event.set_grab(True)

    def start(self) -> None:
        """Start game."""
        self._load()
        self._run()

        # cleanup
        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.start()
