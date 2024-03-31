from pathlib import Path

from PIL import Image


def get_root():
    return Path(__file__).parent.absolute()


def prune_by_resolution(input_file, resolution):
    size = (0, 0)
    with Image.open(input_file) as im:
        size = im.size

    res = tuple(map(int, resolution.split("x")))

    if size < res:
        input_file.unlink()
        print(f"Removed {input_file}, resolution: {size} < {res}")
