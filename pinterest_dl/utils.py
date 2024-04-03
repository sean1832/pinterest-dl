from pathlib import Path

import pyexiv2
from PIL import Image


def get_root():
    return Path(__file__).parent.absolute()


def parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse resolution string to tuple of integers.

    Args:
        resolution (str): Resolution string in the format 'width x height'.

    Raises:
        ValueError: If the resolution string is invalid.

    Returns:
        tuple[int, int]: Tuple of integers representing the resolution.
    """
    try:
        return tuple(map(int, resolution.split("x")))
    except ValueError:
        raise ValueError("Invalid resolution format. Use 'width x height'.")


def prune_by_resolution(input_file: str | Path, resolution: tuple[int, int]):
    size = (0, 0)
    with Image.open(input_file) as im:
        size = im.size

    if size < resolution:
        input_file.unlink()
        print(f"Removed {input_file}, resolution: {size} < {resolution}")


def get_appdata_dir(path_under=None):
    if path_under:
        return Path.home().joinpath("AppData", "Local", "pinterest-dl", path_under)
    return Path.home().joinpath("AppData", "Local", "pinterest-dl")


def write_img_caption(image_path, comment):
    with pyexiv2.Image(str(image_path)) as img:
        img.modify_exif({"Exif.Image.XPComment": comment})
