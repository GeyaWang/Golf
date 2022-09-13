from helper import import_csv_layout
from dataclasses import dataclass
from enum import Enum, auto


class Map(Enum):
    terrain = auto()
    collision = auto()
    platform = auto()
    player = auto()


@dataclass
class Data:
    map: dict
    backgrounds: tuple


Level0 = Data(
    map={
        Map.terrain: import_csv_layout('../graphics/level_0/map/map_terrain.csv'),
        Map.collision: import_csv_layout('../graphics/level_0/map/map_collision.csv'),
        Map.platform: import_csv_layout('../graphics/level_0/map/map_platform.csv'),
        Map.player: import_csv_layout('../graphics/level_0/map/map_player_spawn.csv')
    },
    backgrounds=(
        '../graphics/level_0/images/background_0.png',
        '../graphics/level_0/images/background_1.png',
        '../graphics/level_0/images/background_2.png'
    )
)

LevelData = (Level0,)
