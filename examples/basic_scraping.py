"""
Example: Basic Scraping and Downloading
========================================

This example demonstrates the simplest way to scrape and download
images from Pinterest using the high-level API.
"""

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these URLs to your actual Pinterest links
# ============================================================================
PIN_URL = "https://au.pinterest.com/pin/900438519273272242/"
BOARD_URL = "https://au.pinterest.com/pin/900438519273272242/"  # Replace with actual board URL


def example_1_simple_pin_scrape():
    """Scrape a single pin and download its images."""
    print("Example 1: Simple Pin Scrape")
    print("-" * 50)

    # Scrape and download in one step
    images = PinterestDL.with_api().scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/pin",
        num=10,
    )

    if images:
        print(f"> Downloaded {len(images)} images to downloads/pin/")
    else:
        print("Warning: No images downloaded")
    print()


def example_2_board_scrape():
    """Scrape an entire board."""
    print("Example 2: Board Scrape")
    print("-" * 50)

    images = PinterestDL.with_api(
        verbose=False,  # Disable detailed logging
        timeout=5,  # Set request timeout to 5 seconds
    ).scrape_and_download(
        url=BOARD_URL,
        output_dir="downloads/board",
        num=50,  # Download up to 50 images
        delay=0.5,  # Add delay between requests
    )

    if images:
        print(f"> Downloaded {len(images)} images from board")
    else:
        print("Warning: No images downloaded")
    print()


def example_3_with_resolution_filter():
    """Download only high-resolution images."""
    print("Example 3: With Resolution Filter")
    print("-" * 50)

    images = PinterestDL.with_api().scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/high_res",
        num=20,
        min_resolution=(1024, 1024),  # Only download images >= 1024x1024
    )

    if images:
        print(f"> Downloaded {len(images)} high-resolution images")
    else:
        print("Warning: No high-resolution images found")
    print()


def example_4_with_captions():
    """Download images with caption files."""
    print("Example 4: With Captions")
    print("-" * 50)

    # Download with txt captions (alt text in separate .txt files)
    images = PinterestDL.with_api().scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/with_captions",
        num=10,
        caption="txt",  # Options: 'txt', 'json', 'metadata', 'none'
    )

    if images:
        print(f"> Downloaded {len(images)} images with .txt caption files")
    else:
        print("Warning: No images downloaded")
    print()


def example_5_with_cache():
    """Cache scraped data to JSON for reuse."""
    print("Example 5: With Cache")
    print("-" * 50)

    images = PinterestDL.with_api().scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/cached",
        num=15,
        cache_path="cache/scraped_data.json",  # Save scraped metadata
    )

    if images:
        print(f"> Downloaded {len(images)} images")
    else:
        print("Warning: No images downloaded")
    print("> Scraped metadata cached to cache/scraped_data.json")
    print()


def example_6_with_video_streams():
    """Download video streams if available."""
    print("Example 6: With Video Streams")
    print("-" * 50)

    images = PinterestDL.with_api().scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/videos",
        num=10,
        download_streams=True,  # Download video streams as .mp4
    )

    if images:
        print(f"> Downloaded {len(images)} items (images and videos)")
    else:
        print("Warning: No items downloaded")
    print()


def example_7_verbose_mode():
    """Enable verbose logging for debugging."""
    print("Example 7: Verbose Mode")
    print("-" * 50)

    images = PinterestDL.with_api(
        verbose=True,  # Show detailed logs
    ).scrape_and_download(
        url=PIN_URL,
        output_dir="downloads/verbose",
        num=5,
    )

    if images:
        print(f"> Downloaded {len(images)} images with verbose logging")
    else:
        print("Warning: No images downloaded")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Basic Scraping Examples")
    print("=" * 50)
    print()

    # Run examples (comment out the ones you don't need)
    example_1_simple_pin_scrape()
    example_2_board_scrape()
    example_3_with_resolution_filter()
    example_4_with_captions()
    example_5_with_cache()
    example_6_with_video_streams()
    example_7_verbose_mode()

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)
