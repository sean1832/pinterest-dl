from pathlib import Path
from typing import List, Optional, Tuple, Union

from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.ops import downloader


def download_images(
    images: List[PinterestImage],
    output_dir: Union[str, Path],
    verbose: bool = False,
) -> List[PinterestImage]:
    """Download images from Pinterest using given URLs and fallbacks.

    Args:
        images (List[PinterestImage]): List of PinterestImage objects to download.
        output_dir (Union[str, Path]): Directory to store downloaded images.
        verbose (bool): Enable verbose logging.

    Returns:
        List[PinterestImage]: List of PinterestImage objects with local paths set.
    """
    urls = [img.src for img in images]
    fallback_urls = [img.fallback_urls for img in images]
    local_paths = downloader.download_concurrent_with_fallback(
        urls, Path(output_dir), verbose=verbose, fallback_urls=fallback_urls
    )

    for img, path in zip(images, local_paths):
        img.set_local(path)

    return images


def add_captions(
    images: List[PinterestImage], indices: Optional[List[int]] = None, verbose: bool = False
) -> None:
    """Add captions and origin information to downloaded images.

    Args:
        images (List[PinterestImage]): List of PinterestImage objects to add captions to.
        indices (List[int]): Specific indices to add captions for.
        verbose (bool): Enable verbose logging.
    """
    if not indices:
        indices_list = range(len(images))
    else:
        indices_list = indices

    for index in indices_list:
        try:
            img = images[index]
            if img.origin:
                img.write_comment(img.origin)
                if verbose:
                    print(f"Origin added to {img.local_path}: '{img.origin}'")
            if img.alt:
                img.write_subject(img.alt)
                if verbose:
                    print(f"Caption added to {img.local_path}: '{img.alt}'")

        except Exception as e:
            print(f"Error captioning {img.local_path}: {e}")


def prune_images(
    images: List[PinterestImage], min_resolution: Tuple[int, int], verbose: bool = False
) -> List[int]:
    """Prune images that do not meet minimum resolution requirements.

    Args:
        images (List[Path]): List of image paths to prune.
        min_resolution (Tuple[int, int]): Minimum resolution requirement (width, height).
        verbose (bool): Enable verbose logging.

    Returns:
        List[int]: List of indices of images that meet the resolution requirements.
    """
    valid_indices = []
    for index, img in enumerate(images):
        if img.prune_local(min_resolution, verbose):
            continue
        valid_indices.append(index)

    pruned_count = len(images) - len(valid_indices)
    print(f"Pruned ({pruned_count}) images")

    if verbose:
        print("Pruned images index:", valid_indices)

    return valid_indices
