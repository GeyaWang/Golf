from helper import import_csv_layout
from dataclasses import dataclass
from enum import Enum, auto


class Map(Enum):
    wall = auto()
    terrain0 = auto()
    terrain1 = auto()
    block_collision = auto()
    slope_collision = auto()
    platform_collision = auto()
    player = auto()


@dataclass(frozen=True, slots=True)
class Data:
    map: dict
    backgrounds: tuple


@dataclass(frozen=True, slots=True)
class GameData:
    level0 = Data(
        map={
            # order of drawing (top=first, bottom=last)
            Map.wall: import_csv_layout('../graphics/levels/level0/map/map_wall.csv'),
            Map.terrain0: import_csv_layout('../graphics/levels/level0/map/map_terrain0.csv'),
            Map.terrain1: import_csv_layout('../graphics/levels/level0/map/map_terrain1.csv'),

            Map.block_collision: import_csv_layout('../graphics/levels/level0/map/map_block_collision.csv'),
            Map.slope_collision: import_csv_layout('../graphics/levels/level0/map/map_slope_collision.csv'),
            Map.platform_collision: import_csv_layout('../graphics/levels/level0/map/map_platform_collision.csv'),
            Map.player: import_csv_layout('../graphics/levels/level0/map/map_player_spawn.csv')
        },
        backgrounds=(
            '../graphics/levels/level0/images/background_0.png',
            '../graphics/levels/level0/images/background_1.png',
            '../graphics/levels/level0/images/background_2.png'
        )
    )
    level_data_dict = {
        0: level0
    }
