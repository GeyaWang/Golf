from helper import import_csv_layout
from dataclasses import dataclass
import pygame


@dataclass
class Data:
    map: dict
    backgrounds: tuple


Level0 = Data(
    {
        'collision': import_csv_layout('../graphics/level_0/tilemap/collision_map.csv'),
        'platform': import_csv_layout('../graphics/level_0/tilemap/platform_map.csv'),
        'spawn': import_csv_layout('../graphics/level_0/tilemap/spawn_map.csv')
    },
    (
        '../graphics/level_0/images/background_0.png',
        '../graphics/level_0/images/background_1.png',
        '../graphics/level_0/images/background_2.png'
    )
)

LevelData = (Level0,)
