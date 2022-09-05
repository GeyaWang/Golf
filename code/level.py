import pygame
from tile import Tile, Platform, TileType
from player import Player
from cursor import Cursor
from settings import WIDTH, HEIGHT, TILE_SIZE
from game_data import LevelData, Map
from math import sqrt, copysign


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

    def _spawn_sprite(self, style, pos):
        match style:
            case Map.collision:
                Tile(pos, [self.obstacle_sprites], TileType.block, style)
            case Map.platform:
                Platform(pos, [self.obstacle_sprites], style)
            case Map.player:
                self.player = Player(pos, self.obstacle_sprites, self.visible_sprites)

    def _create_map(self):
        for style, layout in LevelData[0].map.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILE_SIZE
                        y = row_index * TILE_SIZE
                        self._spawn_sprite(style, (x, y))

    def _remove_overlap_hitbox(self):
        for a in self.obstacle_sprites:
            for b in self.obstacle_sprites:
                if a is not b:
                    list_a = a.line_list.copy()
                    list_b = b.line_list.copy()

                    for line_obj_a in list_a:
                        for line_obj_b in list_b:
                            if set(line_obj_a.coords) == set(line_obj_b.coords):
                                a.line_list.remove(line_obj_a)
                                del line_obj_a
                                b.line_list.remove(line_obj_b)
                                del line_obj_b
                                break

    def run(self):
        # background
        for surf in self.background_surfs:
            self.display_surf.blit(surf, (0, 0))

        # tile sprites
        self.visible_sprites.custom_draw(self.player, self.obstacle_sprites)

        # foreground
        self.cursor.update()
        self.player.update()


class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

        self.display_surf = pygame.display.get_surface()
        self.width = self.display_surf.get_width()
        self.half_width = self.width // 2
        self.height = self.display_surf.get_height()
        self.half_height = self.height // 2
        self.offset = pygame.Vector2()

        self.level_surf = pygame.image.load('../graphics/level_0/images/level_map.png').convert_alpha()
        self.level_rect = self.level_surf.get_rect(topleft=(0, 0))

        self.offset.x = 0
        self.offset.y = self.level_rect.height - self.height

        self.camera_exponential_speed = 0.5

    def custom_draw(self, player, test):
        # floor
        level_offset_pos = self.level_rect.topleft - self.offset
        self.display_surf.blit(self.level_surf, level_offset_pos)

        # set player offset
        player.offset = player.rect.center - self.offset

        # kill player if off-screen
        if player.offset.y > self.height:
            player.kill()

        # move camera to player
        target_x = min(max(player.rect.centerx - self.half_width, 0), self.level_rect.width - self.width)
        target_y = min(max(player.rect.centery - self.half_height, 0), self.level_rect.height - self.height)
        diff_x = target_x - self.offset.x
        diff_y = target_y - self.offset.y
        self.offset.x += int(abs(diff_x) ** self.camera_exponential_speed * copysign(1, diff_x))
        self.offset.y += int(abs(diff_y) ** self.camera_exponential_speed * copysign(1, diff_y))
