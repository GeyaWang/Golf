from csv import reader
from settings import TILE_SIZE
import pygame.image
from collections import namedtuple


Point = namedtuple('Point', 'x, y')


def import_csv_layout(path) -> list[list[str]]:
    """Open csv file and save as list."""
    terrain_map = []
    with open(path) as map_:
        level = reader(map_, delimiter=',')
        for row in level:
            terrain_map.append(list(row))
    return terrain_map


def import_cut_graphics(path) -> list[pygame.Surface]:
    """Returns a list of cut tiles from an image path."""
    image = pygame.image.load(path).convert_alpha()
    n_tiles_x = image.get_width() // TILE_SIZE
    n_tiles_y = image.get_height() // TILE_SIZE

    tiles = []
    for row in range(n_tiles_y):
        for col in range(n_tiles_x):
            x = col * TILE_SIZE
            y = row * TILE_SIZE

            tile_img = image.subsurface((x, y, TILE_SIZE, TILE_SIZE))
            tiles.append(tile_img)
    return tiles
