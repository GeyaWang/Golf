import pygame
from tile import Tile, Platform, TileType
from player import Player
from cursor import Cursor
from settings import WIDTH, HEIGHT, TILE_SIZE
from game_data import LevelData, Map


class Level:
    def __init__(self):
        self.display_surf = pygame.display.get_surface()
        self.visible_sprites = CameraGroup()
        self.obstacle_sprites = pygame.sprite.Group()

        self.rel_width = WIDTH / TILE_SIZE
        self.rel_height = HEIGHT / TILE_SIZE

        self._create_map()
        self.cursor = Cursor(self.player)

        self.background_surfs = [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (WIDTH, HEIGHT)) for path in LevelData[0].backgrounds]

    def _spawn_sprite(self, style, pos):
        match style:
            case Map.collision:
                Tile(pos, [self.obstacle_sprites], TileType.block, style)
            case Map.platform:
                Platform(pos, [self.obstacle_sprites], style)
            case Map.player:
                self.player = Player(pos, [self.visible_sprites], self.obstacle_sprites, self.visible_sprites)

    def _create_map(self):
        for style, layout in LevelData[0].map.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILE_SIZE
                        y = row_index * TILE_SIZE
                        self._spawn_sprite(style, (x, y))

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
