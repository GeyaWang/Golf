import pygame
from tile import Tile, Platform, Terrain, TileType
from player import Player
from cursor import Cursor
from settings import WIDTH, HEIGHT, TILE_SIZE, FPS
from game_data import Map, GameData
from helper import import_cut_graphics
from math import copysign, ceil
from input import Input


class Level:
    """Creates and controls the level and camera."""
    def __init__(self, input_: Input) -> None:
        self.input = input_

        self.level_data = GameData.level_data_dict
        self.level = 0
        self.show_hitboxes = False

        # split player calculations into chunks
        self.frame_chunks = 2
        self.chunk_deltatime = (1 / FPS) / self.frame_chunks

        # sprite groups
        self.display_surf = pygame.display.get_surface()
        self.obstacle_sprites = pygame.sprite.Group()
        self.loaded_obstacle_sprites = pygame.sprite.Group()
        self.visible_sprites = CameraGroup(self._get_terrain_data(), self.loaded_obstacle_sprites, self.obstacle_sprites, self)

        # create level
        self._import_cut_graphics()
        self._create_map()
        self.cursor: Cursor = Cursor(self.player, self.input)
        self._remove_overlap_hitbox()

        self.background_surfs = self._get_background_surfaces()

    def _import_cut_graphics(self) -> None:
        self.cut_tile_list = import_cut_graphics('../graphics/level_0/images/tileset.png')

    def _get_terrain_data(self) -> list[list[str]]:
        """Return all terrain data for a specific level."""
        return self.level_data[self.level].map[Map.terrain]

    def _get_tile_image(self, raw_id: int) -> pygame.Surface:
        """Return transformed image from integer id"""
        # change into unsigned integer with 34 bytes
        if raw_id < 0:
            raw_id += 2 ** 32
        binary_id = format(raw_id, '#034b')  # convert to binary

        vertical, horizontal, antidiagonal = tuple(bool(int(i)) for i in binary_id[2:5])  # get rotation info from 3 leading digits
        tile_id = int(binary_id[6:], 2)  # rest consists of the base id
        image = self.cut_tile_list[tile_id]  # retrieve image from id

        # transform image
        image = pygame.transform.flip(image, flip_x=horizontal, flip_y=vertical)
        if antidiagonal:
            # antidiagonal transformation consists of vertical flip and 270-degree rotation
            image = pygame.transform.flip(image, flip_x=False, flip_y=True)
            image = pygame.transform.rotate(image, 270)
        return image

    def _spawn_sprite(self, style: Map, pos: tuple, tile_id: int) -> None:
        """Find which sprite to place."""
        match style:
            case Map.collision:
                Tile(pos, [self.obstacle_sprites], TileType.block, style)
            case Map.platform:
                Platform(pos, [self.obstacle_sprites], style)
            case Map.terrain:
                Terrain(pos, [self.visible_sprites], style, self._get_tile_image(tile_id))
            case Map.player:
                self.player = Player((pos[0] + TILE_SIZE / 2, pos[1] + TILE_SIZE), self.loaded_obstacle_sprites, self.input)

    def _create_map(self) -> None:
        """Iterate through maps and place sprites."""
        for style, layout in self.level_data[self.level].map.items():
            for row_index, row in enumerate(layout):
                for col_index, col in enumerate(row):
                    if col != '-1':
                        x = col_index * TILE_SIZE
                        y = row_index * TILE_SIZE
                        self._spawn_sprite(style, (x, y), int(col))

    def _remove_overlap_hitbox(self) -> None:
        """Remove overlapping hitboxes for optimization."""
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

    def toggle_hitboxes(self) -> None:
        """Toggles if hitboxes are shown or not."""
        self.show_hitboxes = not self.show_hitboxes

    def run(self) -> None:
        """Draw and update sprites."""
        # background
        for image in self.background_surfs:
            self.display_surf.blit(image, (0, 0))

        # tile sprites
        self.visible_sprites.custom_draw(self.player)

        # hitboxes
        if self.show_hitboxes:
            self.visible_sprites.draw_hitboxes()

        # cursor
        self.cursor.update()

        # player
        if not self.input.mouse.is_paused:
            for _ in range(self.frame_chunks):
                self.player.update(self.chunk_deltatime)


class CameraGroup(pygame.sprite.Group):
    def __init__(self, terrain_data, loaded_obstacle_sprites, obstacle_sprites, level) -> None:
        super().__init__()
        self.terrain_data = terrain_data
        self.loaded_obstacle_sprites = loaded_obstacle_sprites
        self.obstacle_sprites = obstacle_sprites
        self.level = level

        self.setup_init_hitboxes = False

        # display setup
        self.display_surf = pygame.display.get_surface()
        self.width = self.display_surf.get_width()
        self.half_width = self.width // 2
        self.height = self.display_surf.get_height()
        self.half_height = self.height // 2
        self.quarter_height = self.height // 4

        # camera setup
        self.map_height = len(self.terrain_data) * TILE_SIZE - self.height
        self.offset = pygame.Vector2((ceil(WIDTH / TILE_SIZE) * TILE_SIZE - WIDTH) / 2, self.map_height)
        self.rel_camera_height = 0  # relative to half a screen height

        # camera attributes
        self.camera_exponential_speed = 0.5
        self.follow_threshold_top = self.height * (2 / 3)

    def _call_reload_hitboxes(self) -> None:
        """Call level function to reload hitboxes with y level range."""
        self.level.reload_hitboxes(
            y1=self.map_height - ((self.rel_camera_height - 2) * self.quarter_height),
            y2=self.map_height - ((self.rel_camera_height + 1) * self.quarter_height)
        )

    def draw_hitboxes(self) -> None:
        """Draw hitboxes to display surface with camera offset"""
        for sprite in self.loaded_obstacle_sprites:
            if sprite.type != Map.terrain:
                for line in sprite.line_list:
                    pygame.draw.line(
                        self.display_surf,
                        (255, 0, 0),
                        line.coords[0] - self.offset,
                        line.coords[1] - self.offset
                    )

    def custom_draw(self, player: Player) -> None:
        """Draw sprites with camera offset."""
        # draw sprite
        for sprite in self.sprites():
            sprite_offset = sprite.rect.topleft - self.offset
            self.display_surf.blit(sprite.image, sprite_offset)

        # set player offset
        player.offset = player.rect.center - self.offset
        player.draw()

        # kill player if off-screen
        if player.offset.y > self.height and (player.offset.x < 0 or player.offset.x > self.width):
            player.kill()

        # move camera to player if player is on ground or beneath threshold
        if player.is_on_ground or player.offset.y > self.follow_threshold_top:
            target_y = min(max(player.rect.centery - self.half_height, 0), len(self.terrain_data) * TILE_SIZE - self.height)
            diff_y = target_y - self.offset.y
            self.offset.y += int(abs(diff_y) ** self.camera_exponential_speed * copysign(1, diff_y))

        # init hitboxes after level is initialized
        if not self.setup_init_hitboxes and self.obstacle_sprites.sprites():
            self.setup_init_hitboxes = True
            self._call_reload_hitboxes()

        # if player goes above relative camera height, reload hitboxes
        if player.pos.y < self.map_height - self.rel_camera_height * self.quarter_height:
            self.rel_camera_height += 1
            self._call_reload_hitboxes()
        elif player.pos.y > self.map_height - (self.rel_camera_height - 1) * self.quarter_height:
            self.rel_camera_height -= 1
            self._call_reload_hitboxes()
