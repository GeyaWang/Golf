import pygame
from tile import Tile, Platform, Terrain, TileType
from player import Player
from settings import WIDTH, HEIGHT, TILE_SIZE
from game_data import Map, GameData
from helper import import_cut_graphics
from math import copysign, ceil
from input import Input
from itertools import combinations


class Level:
    """Creates and controls the level and camera."""
    def __init__(self, input_: Input, frame_chunks: int, chunk_deltatime: float) -> None:
        self.input = input_
        self.frame_chunks = frame_chunks
        self.chunk_deltatime = chunk_deltatime

        self.level_data = GameData.level_data_dict
        self.level = 0

        # loading screen
        self.loading_status = ""
        self.loading_progress = 0
        self.loading_total_work = (
            10  # import cut graphics
            + len(self.level_data[self.level].map[Map.terrain0]) * len((self.level_data[self.level].map[Map.terrain0])[0]) * 7  # build map
            + (self._get_n_hitboxes() - 1) * self._get_n_hitboxes() / 2  # remove overlap hitboxes
            + 1  # set player attribute
        )
        self.is_loading = True

        # sprite groups
        self.display_surf = pygame.display.get_surface()
        self.obstacle_sprites = pygame.sprite.Group()
        self.loaded_obstacle_sprites = pygame.sprite.Group()
        map_height = len(self.level_data[self.level].map[Map.terrain0]) * TILE_SIZE
        self.visible_sprites = SpriteCameraGroup()
        self.camera = Camera(map_height, self.visible_sprites, self.loaded_obstacle_sprites, self.obstacle_sprites, self)

        # get background images
        self.background_surfs = self._get_background_surfaces()

    def loading(self):
        """Time-heavy processes to be done on loading screen."""
        # create level
        self.loading_status = "Importing graphics..."
        self._import_cut_graphics()
        self.loading_progress += 10

        self.loading_status = "Building map..."
        self._create_map()

        self.loading_status = "Optimising hitboxes..."
        self._remove_overlap_hitbox()

        self.loading_status = "Creating player..."
        self.camera.player = self.player  # set player attribute in camera object
        self.loading_progress += 1

        self.loading_status = "Done."
        self.is_loading = False

    def _get_n_hitboxes(self) -> int:
        n = 0
        for style, layout in self.level_data[self.level].map.items():
            match style:
                case Map.block_collision | Map.slope_collision | Map.platform_collision:
                    for row_index, row in enumerate(layout):
                        for col_index, col in enumerate(row):
                            if col != '-1':
                                n += 1
        return n

    def _import_cut_graphics(self) -> None:
        self.cut_tile_list = import_cut_graphics('../graphics/levels/level0/images/tileset.png')

    def _get_tile_image(self, raw_id: int) -> pygame.Surface:
        """Return transformed image from id"""
        # change into unsigned integer with 34 bytes
        if raw_id < 0:
            raw_id += 2 ** 32
        binary_id = format(raw_id, '#034b')  # convert to binary

        horizontal, vertical, antidiagonal = tuple(bool(int(i)) for i in binary_id[2:5])  # get rotation info from 3 leading digits
        tile_id = int(binary_id[6:], 2)  # rest consists of the base id
        image = self.cut_tile_list[tile_id]  # retrieve image from id

        # transform image
        image = pygame.transform.flip(image, flip_x=horizontal, flip_y=vertical)
        if antidiagonal:
            # antidiagonal transformation consists of vertical flip and 270-degree rotation
            image = pygame.transform.flip(image, flip_x=False, flip_y=True)
            image = pygame.transform.rotate(image, 90)
        return image

    def _spawn_sprite(self, style: Map, pos: tuple, tile_id: int) -> None:
        """Find which sprite to place."""
        match style:
            case Map.block_collision:
                Tile(pos, [self.obstacle_sprites], TileType.block, style)
            case Map.slope_collision:
                Tile(pos, [self.obstacle_sprites], TileType.slope_dict[tile_id], style)
            case Map.platform_collision:
                Platform(pos, [self.obstacle_sprites], style)
            case Map.terrain0 | Map.terrain1 | Map.wall:
                Terrain(pos, [self.visible_sprites], style, self._get_tile_image(tile_id))
            case Map.player:
                self.player = Player((pos[0] + TILE_SIZE / 2, pos[1] + TILE_SIZE), self.loaded_obstacle_sprites, self.input)

    def _create_map(self) -> None:
        """Iterate through maps and place sprites."""
        for style, layout in self.level_data[self.level].map.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    self.loading_progress += 1
                    if col != '-1':
                        x = col_index * TILE_SIZE
                        y = row_index * TILE_SIZE
                        self._spawn_sprite(style, (x, y), int(col))

    def _remove_overlap_hitbox(self) -> None:
        """Remove overlapping hitboxes for optimization."""
        for a, b in combinations(self.obstacle_sprites, 2):
            self.loading_progress += 1
            list_a = a.line_list.copy()
            list_b = b.line_list.copy()

            for line_a in list_a:
                for line_b in list_b:
                    if set(line_a.coords) == set(line_b.coords):
                        a.line_list.remove(line_a)
                        del line_a
                        b.line_list.remove(line_b)
                        del line_b
                        break
            # kill sprite if no line hitboxes
            if not b.line_list:
                b.kill()
            if not a.line_list:
                a.kill()

    def _get_background_surfaces(self) -> list[pygame.Surface]:
        """Return a list of instantiates images."""
        return [pygame.transform.scale(pygame.image.load(path).convert_alpha(), (WIDTH, HEIGHT)) for path in self.level_data[self.level].backgrounds]

    def unload_hitboxes(self):
        """Delete all hitboxes"""
        for sprite in self.loaded_obstacle_sprites:
            sprite.remove(self.loaded_obstacle_sprites)

    def reload_hitboxes(self, y1, y2) -> None:
        """Reload hitboxes with arguments of screen height relative to tile size."""
        self.unload_hitboxes()
        # Add all obstacle sprites in a y range to loaded obstacle sprites
        for sprite in self.obstacle_sprites:
            if y2 < sprite.pos[1] < y1:
                sprite.add(self.loaded_obstacle_sprites)

    def draw(self) -> None:
        for image in self.background_surfs:
            self.display_surf.blit(image, (0, 0))
        self.camera.draw_sprites()
        self.player.draw()

    def update(self) -> None:
        """Draw and update sprites."""
        self.camera.update()
        self.player.update(self.frame_chunks, self.chunk_deltatime)


class SpriteCameraGroup(pygame.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.display_surf = pygame.display.get_surface()

    def custom_draw(self, camera_offset: float) -> None:
        """Draws each sprite with an offset."""
        for sprite in self.sprites():
            surf = sprite.image
            sprite_offset = sprite.rect.topleft - camera_offset
            self.display_surf.blit(surf, sprite_offset)


class Camera:
    def __init__(self, map_height: int, visible_sprites: pygame.sprite.Group, loaded_obstacle_sprites: pygame.sprite.Group, obstacle_sprites: pygame.sprite.Group, level: Level) -> None:
        self.visible_sprites = visible_sprites
        self.loaded_obstacle_sprites = loaded_obstacle_sprites
        self.obstacle_sprites = obstacle_sprites
        self.level = level

        self.setup_init_hitboxes = False
        self.is_draw_hitboxes = False
        self.player = None  # set to player class when level is created

        # display setup
        self.display_surf = pygame.display.get_surface()
        self.screen_width = self.display_surf.get_width()
        self.screen_half_width = self.screen_width // 2
        self.screen_height = self.display_surf.get_height()
        self.screen_half_height = self.screen_height // 2

        # camera setup
        self.map_height = map_height
        self.offset = pygame.Vector2((ceil(self.screen_width / TILE_SIZE) * TILE_SIZE - self.screen_width) / 2, self.map_height - self.screen_height)

        # camera attributes
        self.camera_exponential_speed = 0.5
        self.follow_threshold_top = self.screen_height * (2 / 3)
        self.hitbox_range = self.screen_height * 2
        self.hitbox_detect_range = self.screen_height // 4

    def _set_hitbox_range(self) -> None:
        """Set hitbox ranges using player position."""
        self.hitbox_y1 = self.player.pos.y + self.hitbox_range / 2
        self.hitbox_y2 = self.player.pos.y - self.hitbox_range / 2
        self.hitbox_detect_y1 = self.player.pos.y + self.hitbox_detect_range / 2
        self.hitbox_detect_y2 = self.player.pos.y - self.hitbox_detect_range / 2

    def _call_reload_hitboxes(self) -> None:
        """Call level function to reload hitboxes with y level range."""
        self.level.reload_hitboxes(
            y1=self.hitbox_y1,
            y2=self.hitbox_y2
        )

    def draw_hitboxes(self) -> None:
        """Draw hitboxes to display surface with camera offset."""
        for sprite in self.loaded_obstacle_sprites:
            for line in sprite.line_list:
                pygame.draw.line(
                    self.display_surf,
                    (255, 0, 0),
                    line.coords[0] - self.offset,
                    line.coords[1] - self.offset
                )

    def _move_camera(self) -> None:
        """Move camera to player if player is on ground or beneath threshold."""
        self.offset.y = min(max(self.player.rect.centery - self.screen_half_height, 0), self.map_height - self.screen_height)
        # if self.player.is_on_ground or self.player.offset.y > self.follow_threshold_top:
        #     target_y = min(max(self.player.rect.centery - self.half_height, 0), self.map_height - self.height)
        #     diff_y = target_y - self.offset.y
        #     self.offset.y += int(abs(diff_y) ** copysign(self.camera_exponential_speed, diff_y))

    def draw_sprites(self) -> None:
        """Draw sprite elements."""
        self.visible_sprites.custom_draw(self.offset)
        if self.is_draw_hitboxes:
            self.draw_hitboxes()

    def update(self) -> None:
        """Update camera position and hitbox positions."""
        if self.player is not None:
            self._move_camera()
            self.player.offset = self.player.pos - self.offset

            # init hitboxes after level is initialized
            if not self.setup_init_hitboxes and self.obstacle_sprites.sprites():
                self.setup_init_hitboxes = True
                self._set_hitbox_range()
                self._call_reload_hitboxes()

            # if player goes above relative camera height, reload hitboxes
            if self.player.pos.y > self.hitbox_detect_y1:
                self._set_hitbox_range()
                self._call_reload_hitboxes()
            elif self.player.pos.y < self.hitbox_detect_y2:
                self._set_hitbox_range()
                self._call_reload_hitboxes()
