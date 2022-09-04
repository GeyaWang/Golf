import pygame
from math import pi, sin, cos, sqrt, acos, atan, atan2, degrees
import shapely.geometry
from settings import TILE_SIZE
from collections import namedtuple
from dataclasses import dataclass


class LineHitbox:
    def __init__(self, coords, angle, tile_pos):
        self.rel_coords = coords
        self.angle = angle
        self.tile_pos = tile_pos

        self._get_real_coords()
        self._get_normal_vect()

        self.hitbox = shapely.geometry.LineString(self.coords)

    def _get_real_coords(self):
        self.coords = tuple((i[0] * TILE_SIZE + self.tile_pos[0], i[1] * TILE_SIZE + self.tile_pos[1]) for i in self.rel_coords)

    def _get_normal_vect(self):
        angle_rad = self.angle * (pi / 180)
        x = sin(angle_rad)
        y = -cos(angle_rad)
        vector = pygame.Vector2(x, y)
        self.normal_vect = vector

    def __repr__(self):
        return 'LineHitbox(coords=%r, angle=%r)' % (self.rel_coords, self.angle)

    def __str__(self):
        return 'Coords: %s, Rel_Coords: %s, Angle: %s' % (self.coords, self.rel_coords, self.angle)


Point = namedtuple('Point', 'x, y')
TileData = namedtuple('TileData', 'sprite, rel_vertices, center')


@dataclass
class TileType:
    # No convex angles
    block = TileData(
        '../graphics/test/block.png',
        (Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1)),
        Point(0.5, 0.5)
    )
    slope0 = TileData(
        '../graphics/test/slope0.png',
        (Point(0, 0), Point(1, 1), Point(0, 1)),
        Point(0.5, 0.5)
    )
    slope1 = TileData(
        '../graphics/test/slope1.png',
        (Point(0, 0), Point(1, 0), Point(0, 1)),
        Point(0.5, 0.5)
    )
    slope2 = TileData(
        '../graphics/test/slope2.png',
        (Point(0, 0), Point(1, 0), Point(1, 1)),
        Point(0.5, 0.5)
    )
    slope3 = TileData(
        '../graphics/test/slope3.png',
        (Point(1, 0), Point(1, 1), Point(0, 1)),
        Point(0.5, 0.5)
    )


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, group, tile_data):
        super().__init__(group)

        self.image = pygame.image.load(tile_data.sprite).convert_alpha()
        self.rect = self.image.get_rect(topleft=pos)

        self.real_coord_list = [(i.x * TILE_SIZE + pos[0], i.y * TILE_SIZE + pos[1]) for i in tile_data.rel_vertices]
        self.hitbox = shapely.geometry.Polygon(self.real_coord_list)

        self.rel_vertices = tile_data.rel_vertices
        self.center = tile_data.center

        self.friction = 0.1
        self.bounciness = 0.3

        self._get_line_data_list()
        self.hitbox_list = [LineHitbox(i[0], i[1], pos) for i in self.line_data_list]

    def _get_line_data_list(self):
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

        self.line_data_list = []
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

            # add to self.line_data_list
            self.line_data_list.append([lines, angle])
