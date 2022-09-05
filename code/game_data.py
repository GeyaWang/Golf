from helper import import_csv_layout
from dataclasses import dataclass
from enum import Enum


class Map(Enum):
    collision = 0
    platform = 1
    player = 2


@dataclass
class Data:
    map: dict
    backgrounds: tuple


Level0 = Data(
    {
        Map.collision: import_csv_layout('../graphics/level_0/tilemap/collision_map.csv'),
        Map.platform: import_csv_layout('../graphics/level_0/tilemap/platform_map.csv'),
        Map.player: import_csv_layout('../graphics/level_0/tilemap/player_spawn_map.csv')
    },
    (
        '../graphics/level_0/images/background_0.png',
        '../graphics/level_0/images/background_1.png',
        '../graphics/level_0/images/background_2.png'
    )
)

LevelData = (Level0,)
