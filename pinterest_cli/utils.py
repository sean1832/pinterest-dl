from pathlib import Path


def get_root():
    return Path(__file__).parent.absolute()
