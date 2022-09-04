import pygame
from tile import Tile, TileType
from player import Player
from cursor import Cursor
from settings import *
from game_data import LevelData


class Level:
    def __init__(self):
        self.display_surf = pygame.display.get_surface()
        self.visible_sprites = CameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        self.rel_width = WIDTH / TILE_SIZE
        self.rel_height = HEIGHT / TILE_SIZE

        self._create_map()
        self.cursor = Cursor(self.player)
        self._remove_overlap_hitbox()

        self.background_surfs = [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (WIDTH, HEIGHT)) for path in LevelData[0].backgrounds]

    def _create_map(self):
        for style, layout in LevelData[0].map.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILE_SIZE
                        y = row_index * TILE_SIZE
                        if style == 'collision':
                            Tile((x, y), [self.obstacle_sprites], TileType.block)
                        elif style == 'platform':
                            pass
                            # Tile((x, y), [self.obstacle_sprites], TileType.block)
                        elif style == 'spawn':
                            self.player = Player((x, y + TILE_SIZE), [self.visible_sprites], self.obstacle_sprites, self.visible_sprites)

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
        # background
        for surf in self.background_surfs:
            self.display_surf.blit(surf, (0, 0))

        # tile sprites
        self.visible_sprites.custom_draw(self.player)

        # foreground
        self.cursor.update()
        self.player.update()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

        self.display_surf = pygame.display.get_surface()
        self.half_width = self.display_surf.get_width() // 2
        self.half_height = self.display_surf.get_height() // 2
        self.offset = pygame.Vector2()

        self.level_surf = pygame.image.load('../graphics/level_0/images/level_map.png').convert_alpha()
        self.level_rect = self.level_surf.get_rect(topleft=(0, 0))

        self.offset.x = 0
        self.offset.y = self.level_rect.height - self.display_surf.get_height()

    def custom_draw(self, player):
        # floor
        level_offset_pos = self.level_rect.topleft - self.offset
        self.display_surf.blit(self.level_surf, level_offset_pos)

        # sprites
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surf.blit(sprite.image, offset_pos)

        # set player offset
        player.offset = player.rect.center - self.offset

        # move camera to player
