import json
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import tqdm

from pinterest_dl.data_model.pinterest_image import PinterestImage
from pinterest_dl.low_level.ops import downloader


class _ScraperBase:
    def __init__(self):
        pass

    @staticmethod
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

    @staticmethod
    def add_captions_to_file(
        images: List[PinterestImage],
        output_dir: Union[str, Path],
        extension: Literal["txt", "json"] = "txt",
        verbose: bool = False,
    ) -> None:
        """Add captions to downloaded images and save them to a file.

        Args:
            images (List[PinterestImage]): List of PinterestImage objects to add captions to.
            output_dir (Union[str, Path]): Directory to save image captions.
            extension (Literal["txt","json"]): File extension for the captions.
                'txt' for alt text in separate files,
                'json' for full image data.
            verbose (bool): Enable verbose logging.
            remove_no_alt (bool): Remove images with no alt text.
        """
        if not isinstance(output_dir, Path):
            output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"Saving captions to {output_dir}...")
        for img in tqdm.tqdm(images, desc="Captioning to file", disable=verbose):
            if not img.local_path:
                continue
            if extension == "json":
                with open(output_dir / f"{img.local_path.stem}.json", "w") as f:
                    f.write(json.dumps(img.to_dict(), indent=4))
            elif extension == "txt":
                if img.alt:
                    with open(output_dir / f"{img.local_path.stem}.txt", "w") as f:
                        f.write(img.alt)
                else:
                    if verbose:
                        print(f"No alt text for {img.local_path}")
            else:
                raise ValueError("Invalid file extension. Use 'txt' or 'json'.")
            if verbose:
                print(f"Caption saved for {img.local_path}: '{img.alt}'")


    @staticmethod
    def add_captions_to_meta(
        images: List[PinterestImage], indices: Optional[List[int]] = None, verbose: bool = False
    ) -> None:
        """Add captions and origin information to downloaded images.

        Args:
            images (List[PinterestImage]): List of PinterestImage objects to add captions to.
            indices (List[int]): Specific indices to add captions for. Default is all images.
            verbose (bool): Enable verbose logging.
        """
        if not indices:
            indices_list = range(len(images))
        else:
            indices_list = indices

        for index in tqdm.tqdm(indices_list, desc="Captioning to metadata", disable=verbose):
            img = None
            try:
                img = images[index]
                if not img.local_path:
                    continue
                if img.local_path.suffix == ".gif":
                    if verbose:
                        print(f"Skipping captioning for {img.local_path} (GIF)")
                    continue
                if img.origin:
                    img.meta_write_comment(img.origin)
                    if verbose:
                        print(f"Origin added to {img.local_path}: '{img.origin}'")
                if img.alt:
                    img.meta_write_subject(img.alt)
                    if verbose:
                        print(f"Caption added to {img.local_path}: '{img.alt}'")

            except Exception as e:
                if img:
                    print(f"Error captioning {img.local_path}: {e}")
                else:
                    print(f"Error captioning image at index {index}: {e}")

    @staticmethod
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
