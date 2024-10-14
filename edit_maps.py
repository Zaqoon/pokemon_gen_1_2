import nbtlib


def get_nbt_file(map_id: int):
    map_string = f'map_{map_id}'
    directory = f'C:/Users/Andreas/AppData/Roaming/.minecraft/saves/Naraka/data/{map_string}.dat'
    nbt_file = nbtlib.load(directory)

    map_data = nbt_file['data']
    colors = map_data['colors']

    # Convert colors into a mutable list
    colors_list = list(colors)

    outline_rectangles(colors_list)

    map_data['colors'] = nbtlib.tag.ByteArray(colors_list)

    return nbt_file


def outline_rectangles(colors):
    fill_rectangle(3, 128, colors, reverse=False)
    fill_rectangle(128, 3, colors, reverse=False)
    fill_rectangle(3, 128, colors, reverse=True)
    fill_rectangle(128, 3, colors, reverse=True)


def set_pixel(x, y, colors):
    index = 128 * x + y
    colors[index] = 74

    return colors


def fill_rectangle(x, y, colors, reverse):
    s_x = 0
    s_y = 0
    if reverse:
        if x < 128:
            s_x = 125
            x = 128
        if y < 128:
            s_y = 125
            y = 128

    for a in range(s_x, x):
        for b in range(s_y, y):
            colors = set_pixel(a, b, colors)


if __name__ == '__main__':
    ranges = [
        [30001, 30007], [32001, 33674], [64001, 64054]
    ]
    for r in ranges:
        for map_id in range(r[0], r[1]):
            nbt_file = get_nbt_file(map_id)
            nbt_file.save()

            print(f'Successfully saved: map_{map_id}.dat')
