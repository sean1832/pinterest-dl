import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_appdata_dir(path_under: Optional[str] = None) -> Path:
    if path_under:
        return Path.home().joinpath("AppData", "Local", "pinterest-dl", path_under)
    return Path.home().joinpath("AppData", "Local", "pinterest-dl")


def append_json(data: Dict[str, Any], file_path: str | Path, indent: int | None = None) -> None:
    with open(file_path, "r+") as f:
        file_data = json.load(f)
        file_data.update(data)
        f.seek(0)
        json.dump(file_data, f, indent=indent)


def write_json(
    data: Dict[str, Any] | List[Dict[str, Any]], file_path: str | Path, indent: int | None = None
) -> None:
    with open(file_path, "w") as f:
        json.dump(data, f, indent=indent)


def read_json(filename: str | Path) -> Dict[str, Any] | List[Dict[str, Any]]:
    with open(filename, "r") as f:
        return json.load(f)


def write_text(data: str | List[str], filename: str) -> None:
    if isinstance(data, list):
        data = "\n".join(data)
    with open(filename, "w") as f:
        f.write(data)


def unzip(
    zip_path: Path, extract_to: Path, target_file: Optional[str] = None, verbose: bool = False
) -> None:
    """
    Extract a specific file from a zip file if target_file is specified.
    Extracts everything otherwise.

    Args:
        zip_path (str): Path to the zip file.
        extract_to (str): Directory where the files should be extracted to.
        target_file (str, optional): Specific file to extract. If None, everything is extracted.
    """
    if not zip_path or not str(zip_path).endswith(".zip"):
        raise ValueError(f"Invalid zip file. [{zip_path}]")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        if target_file:
            # Target file specified, extract only this file
            for file in zip_ref.namelist():
                if file.endswith(target_file):
                    zip_ref.extract(file, extract_to)
                    # Move the file if it's within a directory
                    extracted_path = os.path.join(extract_to, file)
                    final_path = os.path.join(extract_to, os.path.basename(target_file))
                    if os.path.exists(final_path):
                        os.remove(final_path)
                    os.rename(extracted_path, final_path)
                    # Attempt to remove the directory structure if any
                    dir_path = os.path.dirname(extracted_path)
                    if dir_path != extract_to:  # Check to avoid deleting the extract_to dir
                        os.removedirs(dir_path)
                    if verbose:
                        print(f"{target_file} has been extracted to {final_path}")
                    break
            else:
                print(f"{target_file} was not found in the zip file.")
        else:
            # No specific file to extract, extract everything
            zip_ref.extractall(extract_to)
            print(f"All files have been extracted to {extract_to}")
