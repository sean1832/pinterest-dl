from pathlib import Path
from typing import Optional

import pyexiv2
from PIL import Image


def get_root() -> Path:
    return Path(__file__).parent.absolute()


def parse_resolution(resolution: str) -> tuple[int, int]:
    """Parse resolution string to tuple of integers.

    Args:
        resolution (str): Resolution string in the format 'width x height'.

    Returns:
        tuple[int, int]: Tuple of integers representing the resolution.
    """
    try:
        width, height = map(int, resolution.split("x"))
        return width, height
    except ValueError:
        raise ValueError("Invalid resolution format. Use 'width x height'.")


def prune_by_resolution(
    input_file: str | Path, resolution: tuple[int, int], verbose: bool = False
) -> bool:
    size = (0, 0)
    with Image.open(input_file) as im:
        size = im.size

    if size < resolution:
        if isinstance(input_file, str):
            input_file = Path(input_file)
        input_file.unlink()
        if verbose:
            print(f"Removed {input_file}, resolution: {size} < {resolution}")
        return True
    return False


def get_appdata_dir(path_under: Optional[str] = None) -> Path:
    if path_under:
        return Path.home().joinpath("AppData", "Local", "pinterest-dl", path_under)
    return Path.home().joinpath("AppData", "Local", "pinterest-dl")


def write_img_comment(image_path: str | Path, comment: str) -> None:
    with pyexiv2.Image(str(image_path)) as img:
        img.modify_exif({"Exif.Image.XPComment": comment})


def write_img_subject(image_path: str | Path, subject: str) -> None:
    with pyexiv2.Image(str(image_path)) as img:
        img.modify_exif({"Exif.Image.XPSubject": subject})
