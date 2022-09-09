from csv import reader


def import_csv_layout(path) -> list[list[str]]:
    """Open csv file and save as list."""
    terrain_map = []
    with open(path) as map_:
        level = reader(map_, delimiter=',')
        for row in level:
            terrain_map.append(list(row))
    return terrain_map
