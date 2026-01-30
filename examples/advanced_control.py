"""
Example: Advanced Control with Lower-Level API
===============================================

This example demonstrates how to use the lower-level API for
more granular control over scraping, downloading, and processing.
"""

import json
from pathlib import Path

from pinterest_dl import PinterestDL
from pinterest_dl.scrapers import operations

# ============================================================================
# Configuration - Change these URLs to your actual Pinterest links
# ============================================================================
PIN_URL = "https://www.pinterest.com/pin/12345678/"
SEARCH_QUERY = "mountain landscapes"


def example_1_separate_scrape_and_download():
    """Scrape first, then download separately."""
    print("Example 1: Separate Scrape and Download")
    print("-" * 50)

    # Step 1: Scrape media metadata
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=20,
        min_resolution=(512, 512),
    )

    print(f"> Scraped {len(scraped_medias)} items")

    # Step 2: Download media
    output_dir = "downloads/advanced/separate"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=True,
    )

    print(f"> Downloaded {len(downloaded_items)} items to {output_dir}")
    print()


def example_2_save_metadata_to_json():
    """Save scraped metadata to JSON for later use."""
    print("Example 2: Save Metadata to JSON")
    print("-" * 50)

    # Scrape media
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=15,
    )

    # Convert to dictionary and save
    media_data = [media.to_dict() for media in scraped_medias]
    cache_path = Path("cache/metadata.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    with open(cache_path, "w") as f:
        json.dump(media_data, f, indent=4)

    print(f"> Saved {len(media_data)} items to {cache_path}")
    print()


def example_3_add_captions_as_metadata():
    """Embed alt text into image metadata."""
    print("Example 3: Add Captions as Metadata")
    print("-" * 50)

    # Scrape and download
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=10,
    )

    output_dir = "downloads/advanced/with_metadata"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    # Add alt text as image metadata
    operations.add_captions_to_meta(images=downloaded_items)

    print(f"> Added alt text metadata to {len(downloaded_items)} images")
    print()


def example_4_add_captions_as_txt_files():
    """Save alt text to separate .txt files."""
    print("Example 4: Add Captions as TXT Files")
    print("-" * 50)

    # Scrape and download
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=10,
    )

    output_dir = "downloads/advanced/with_txt"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    # Add alt text as .txt files
    operations.add_captions_to_file(downloaded_items, output_dir, extension="txt")

    print(f"> Added .txt caption files for {len(downloaded_items)} images")
    print()


def example_5_add_captions_as_json_files():
    """Save full metadata to separate .json files."""
    print("Example 5: Add Captions as JSON Files")
    print("-" * 50)

    # Scrape and download
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=10,
    )

    output_dir = "downloads/advanced/with_json"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    # Add full metadata as .json files
    operations.add_captions_to_file(downloaded_items, output_dir, extension="json")

    print(f"> Added .json metadata files for {len(downloaded_items)} images")
    print()


def example_6_prune_by_resolution():
    """Download first, then remove low-resolution images."""
    print("Example 6: Prune by Resolution")
    print("-" * 50)

    # Scrape and download (no resolution filter)
    scraped_medias = PinterestDL.with_api().scrape(
        url=PIN_URL,
        num=20,
    )

    output_dir = "downloads/advanced/prune"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    print(f"> Downloaded {len(downloaded_items)} items")

    # Remove images that don't meet resolution criteria
    kept_items = operations.prune_images(images=downloaded_items, min_resolution=(800, 800))

    pruned_count = len(downloaded_items) - len(kept_items)
    print(f"> Pruned {pruned_count} low-resolution images")
    print(f"> Kept {len(kept_items)} high-resolution images")
    print()


def example_7_search_separate_steps():
    """Search with separate scrape and download steps."""
    print("Example 7: Search with Separate Steps")
    print("-" * 50)

    # Step 1: Search and scrape
    scraped_medias = PinterestDL.with_api().search(
        query=SEARCH_QUERY,
        num=25,
        min_resolution=(1024, 768),
        delay=0.4,
    )

    print(f"> Found {len(scraped_medias)} search results")

    # Step 2: Save metadata
    cache_path = Path("cache/search_results.json")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    media_data = [media.to_dict() for media in scraped_medias]
    with open(cache_path, "w") as f:
        json.dump(media_data, f, indent=4)

    # Step 3: Download
    output_dir = "downloads/advanced/search"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    # Step 4: Add captions
    operations.add_captions_to_file(downloaded_items, output_dir, extension="txt")

    print(f"> Downloaded {len(downloaded_items)} items with captions")
    print()


def example_8_browser_mode():
    """Use browser automation for scraping."""
    print("Example 8: Browser Mode (Playwright)")
    print("-" * 50)

    # Scrape using Playwright browser
    scraped_medias = PinterestDL.with_browser(
        browser_type="chromium",
        headless=True,
        ensure_alt=True,
    ).scrape(
        url=PIN_URL,
        num=15,
    )

    print(f"> Scraped {len(scraped_medias)} items using browser")

    # Download
    output_dir = "downloads/advanced/browser"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=False,
    )

    # Prune low-res images
    kept_items = operations.prune_images(images=downloaded_items, min_resolution=(512, 512))

    print(f"> Downloaded and kept {len(kept_items)} high-res images")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Advanced Control Examples")
    print("=" * 50)
    print()

    # Run examples (comment out the ones you don't need)
    example_1_separate_scrape_and_download()
    example_2_save_metadata_to_json()
    example_3_add_captions_as_metadata()
    example_4_add_captions_as_txt_files()
    example_5_add_captions_as_json_files()
    example_6_prune_by_resolution()
    example_7_search_separate_steps()
    example_8_browser_mode()

    print("=" * 50)
    print("All advanced examples completed!")
    print("=" * 50)
