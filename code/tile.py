import pygame
from math import pi, sin, cos, sqrt, acos, atan, degrees
from settings import TILE_SIZE
from collections import namedtuple
from dataclasses import dataclass
from game_data import Map
from shapely.geometry import LineString, Polygon


Point = namedtuple('Point', 'x, y')
TileData = namedtuple('TileData', 'rel_vertices, center')


@dataclass
class LineHitbox:
    rel_coords: tuple
    angle: float
    tile_pos: tuple

    def __post_init__(self):
        self.coords = self._get_real_coords()
        self.normal_vect = self._get_normal_vect()
        self.hitbox = LineString(self.coords)

    def _get_real_coords(self) -> tuple:
        """Returns real coordinates from relative coordinates."""
        return tuple((i[0] * TILE_SIZE + self.tile_pos[0], i[1] * TILE_SIZE + self.tile_pos[1]) for i in self.rel_coords)

    def _get_normal_vect(self) -> pygame.Vector2:
        """Returns normalized normal vector from line angle."""
        angle_rad = self.angle * (pi / 180)
        x = sin(angle_rad)
        y = -cos(angle_rad)
        return pygame.Vector2(x, y).normalize()


@dataclass
class TileType:
    """Defines tile by vertexes and centre."""
    # No convex angles
    block = TileData(
        rel_vertices=(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)),
        center=Point(0.5, 0.5)
    )
    platform = TileData(
        rel_vertices=(Point(0, 0), Point(1, 0)),
        center=Point(0.5, 0)
    )
    slope0 = TileData(
        rel_vertices=(Point(0, 0), Point(1, 1), Point(0, 1)),
        center=Point(0.5, 0.5)
    )
    slope1 = TileData(
        rel_vertices=(Point(0, 0), Point(1, 0), Point(0, 1)),
        center=Point(0.5, 0.5)
    )
    slope2 = TileData(
        rel_vertices=(Point(0, 0), Point(1, 0), Point(1, 1)),
        center=Point(0.5, 0.5)
    )
    slope3 = TileData(
        rel_vertices=(Point(1, 0), Point(1, 1), Point(0, 1)),
        center=Point(0.5, 0.5)
    )
    terrain = TileData(
        rel_vertices=(),
        center=()
    )


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos: tuple, group: list[pygame.sprite.Group], tile_data: TileData, tile_type: Map) -> None:
        super().__init__(group)
        self.rect = pygame.Rect(pos[0], pos[1], TILE_SIZE, TILE_SIZE)
        self.pos = pos

        self.type = tile_type
        self.rel_vertices = tile_data.rel_vertices
        self.center = tile_data.center
        self.real_coord_list = [(i.x * TILE_SIZE + pos[0], i.y * TILE_SIZE + pos[1]) for i in self.rel_vertices]

        self.line_list = self._get_line_data_list()
        self.hitbox: Polygon = self._get_hitbox()

        self.friction = 0.1
        self.bounciness = 0.5

    def _get_line_data_list(self) -> list[LineHitbox]:
        """Returns list with LineHitbox objects."""
        # get all outside connecting lines
        line_list = []
        for i in self.rel_vertices:
            angle_dict = {}  # find 2 lines with the largest angle from the centre
            for j in self.rel_vertices:
                if i is j:
                    continue
                # C = acos((a^2 + b^2 - c^2) / 2ab)
                a = sqrt((i.x - self.center.x) ** 2 + (i.y - self.center.y) ** 2)
                b = sqrt((i.x - j.x) ** 2 + (i.y - j.y) ** 2)
                c = sqrt((j.x - self.center.x) ** 2 + (j.y - self.center.y) ** 2)
                angle = acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                angle_dict[i, j] = angle

            # sort by angle
            if angle_dict:
                coord_list_sort = sorted(angle_dict.keys(), key=lambda k: angle_dict[k], reverse=True)
                for x in range(2):
                    coords = coord_list_sort[x]
                    if coords in line_list or coords[::-1] in line_list:
                        continue
                    line_list.append(coord_list_sort[x])

        # get angle of normal vector facing outwards
        line_data_list = []
        for i, lines in enumerate(line_list):
            dy = lines[0].y - lines[1].y
            dx = lines[0].x - lines[1].x
            if dx == 0:
                # avoid division by 0
                gradient = 999999999
            else:
                gradient = dy / dx

            angle = degrees(atan(gradient))

            # if line faces another point, rotate angle by 180
            x, y = line_list[(i + 1) % len(line_list)][0]
            if y - lines[0].y < gradient * (x - lines[0].x):
                angle = (angle + 180) % 360

            # remove negative by rolling up
            angle = (angle + 360) % 360

            # add to LineHitbox object to line_data_list
            line_data_list.append(LineHitbox(lines, angle, self.pos))
        return line_data_list

    def _get_hitbox(self) -> Polygon:
        """Return polygon hitbox."""
        if len(self.real_coord_list) > 2:
            return Polygon(self.real_coord_list)


class Terrain(Tile):
    def __init__(self, pos: tuple, group: list[pygame.sprite.Group], tile_type: Map, image: pygame.Surface):
        super().__init__(pos, group, TileType.platform, tile_type)
        self.image = image
        self.rect = image.get_rect(topleft=pos)

    def _get_line_data_list(self) -> None:
        return


class Platform(Tile):
    def __init__(self, pos: tuple, group: list[pygame.sprite.Group], tile_type: Map) -> None:
        super().__init__(pos, group, TileType.platform, tile_type)
        self.y = pos[1]

    def _get_line_data_list(self) -> list[LineHitbox]:
        """Returns list with LineHitbox objects."""
        line_list = [LineHitbox((self.rel_vertices[0], self.rel_vertices[1]), 0, self.pos)]
        return line_list
