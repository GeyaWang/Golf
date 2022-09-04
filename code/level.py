import pygame
from tile import Tile, TileType
from player import Player
from cursor import Cursor
from settings import *


class Level:
    def __init__(self):
        self.display_surf = pygame.display.get_surface()

        self.tile_sprites = pygame.sprite.Group()
        self.obstacle_sprites = pygame.sprite.Group()

        self.rel_width = WIDTH / TILE_SIZE
        self.rel_height = HEIGHT / TILE_SIZE

        self._create_map()
        self.cursor = Cursor(self.player)

        self._remove_overlap_hitbox()

    def _create_map(self):
        player = None
        for row_index, row in enumerate(MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                if col == 'x':
                    Tile((x, y), [self.tile_sprites, self.obstacle_sprites], TileType.block)
                elif col == 'a':
                    Tile((x, y), [self.tile_sprites, self.obstacle_sprites], TileType.slope0)
                elif col == 'b':
                    Tile((x, y), [self.tile_sprites, self.obstacle_sprites], TileType.slope1)
                elif col == 'c':
                    Tile((x, y), [self.tile_sprites, self.obstacle_sprites], TileType.slope2)
                elif col == 'd':
                    Tile((x, y), [self.tile_sprites, self.obstacle_sprites], TileType.slope3)
                elif col == 'p':
                    self.player = Player((x + TILE_SIZE / 2, y + TILE_SIZE), self.obstacle_sprites)

    def _remove_overlap_hitbox(self):
        for a in self.obstacle_sprites:
            for b in self.obstacle_sprites:
                if a is not b:
                    list_a = a.hitbox_list.copy()
                    list_b = b.hitbox_list.copy()

                    for line_a in list_a:
                        for line_b in list_b:
                            if set(line_a.coords) == set(line_b.coords):
                                a.hitbox_list.remove(line_a)
                                del line_a
                                b.hitbox_list.remove(line_b)
                                del line_b
                                break

    def run(self):
        self.tile_sprites.draw(self.display_surf)

        # for sprite in self.obstacle_sprites:
        #     pygame.draw.polygon(
        #         self.display_surf,
        #         (0, 255, 0),
        #         sprite.real_coord_list
        #     )

        #  Foreground
        self.cursor.update()
        self.player.update()
