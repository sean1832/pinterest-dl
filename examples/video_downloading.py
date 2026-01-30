"""
Example: Video Downloading
===========================

This example demonstrates how to download video streams from Pinterest
using the HLS video processing capabilities.
"""

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these to your actual Pinterest links/queries
# ============================================================================
VIDEO_PIN_URL = "https://www.pinterest.com/pin/12345678/"  # Replace with pin that has videos
VIDEO_SEARCH_QUERY = "cooking tutorials"  # Change to your search query


def example_1_basic_video_download():
    """Download videos with default settings."""
    print("Example 1: Basic Video Download")
    print("-" * 50)

    # Download both images and videos
    items = PinterestDL.with_api().scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/basic",
        num=20,
        download_streams=True,  # Enable video downloading
    )

    if items:
        print(f"> Downloaded {len(items)} items (images and videos)")
    else:
        print("Warning: No items downloaded")
    print()


def example_2_video_with_captions():
    """Download videos with caption files."""
    print("Example 2: Video with Captions")
    print("-" * 50)

    items = PinterestDL.with_api().scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/with_captions",
        num=15,
        download_streams=True,
        caption="txt",  # Save descriptions to .txt files
    )

    if items:
        print(f"> Downloaded {len(items)} items with captions")
    else:
        print("Warning: No items downloaded")
    print()


def example_3_video_only_search():
    """Search for content and download videos."""
    print("Example 3: Video Search")
    print("-" * 50)

    # Search for video-rich content
    items = PinterestDL.with_api().search_and_download(
        query=VIDEO_SEARCH_QUERY,
        output_dir="downloads/videos/cooking",
        num=30,
        download_streams=True,
    )

    if items:
        print(f"> Downloaded {len(items)} items from search")
    else:
        print("Warning: No items downloaded")
    print()


def example_4_video_with_json_metadata():
    """Download videos and save full metadata to JSON."""
    print("Example 4: Video with JSON Metadata")
    print("-" * 50)

    items = PinterestDL.with_api().scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/with_json",
        num=10,
        download_streams=True,
        caption="json",  # Save full metadata
    )

    if items:
        print(f"> Downloaded {len(items)} items with JSON metadata")
    else:
        print("Warning: No items downloaded")
    print()


def example_5_separate_video_scrape_and_download():
    """Separate scraping and downloading for videos."""
    print("Example 5: Separate Video Scrape and Download")
    print("-" * 50)

    from pinterest_dl.scrapers import operations

    # Step 1: Scrape media (includes video stream info)
    scraped_medias = PinterestDL.with_api().scrape(
        url=VIDEO_PIN_URL,
        num=15,
    )

    print(f"> Scraped {len(scraped_medias)} items")

    # Step 2: Check which items have videos
    video_count = sum(1 for media in scraped_medias if media.video_stream)
    print(f"> Found {video_count} items with video streams")

    # Step 3: Download with video streams enabled
    output_dir = "downloads/videos/separate"
    downloaded_items = operations.download_media(
        media=scraped_medias,
        output_dir=output_dir,
        download_streams=True,  # Download videos
    )

    print(f"> Downloaded {len(downloaded_items)} items")
    print()


def example_6_video_with_cache():
    """Cache video metadata for later use."""
    print("Example 6: Video with Cache")
    print("-" * 50)

    items = PinterestDL.with_api().scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/cached",
        num=20,
        download_streams=True,
        cache_path="cache/video_metadata.json",  # Cache includes video info
    )

    if items:
        print(f"> Downloaded {len(items)} items")
    else:
        print("Warning: No items downloaded")
    print("> Video metadata cached to cache/video_metadata.json")
    print()


def example_7_video_with_resolution_preference():
    """Filter by minimum resolution (applies to images, not video streams)."""
    print("Example 7: Video with Resolution Filter")
    print("-" * 50)

    # Note: min_resolution filters images, not video streams
    items = PinterestDL.with_api().scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/filtered",
        num=25,
        download_streams=True,
        min_resolution=(800, 600),  # Filter images by resolution
    )

    if items:
        print(f"> Downloaded {len(items)} items (high-res images + videos)")
    else:
        print("Warning: No items downloaded")
    print()


def example_8_video_verbose_mode():
    """Download videos with verbose logging."""
    print("Example 8: Video with Verbose Logging")
    print("-" * 50)

    # Verbose mode shows HLS processing details
    items = PinterestDL.with_api(
        verbose=True,  # Show detailed logs
    ).scrape_and_download(
        url=VIDEO_PIN_URL,
        output_dir="downloads/videos/verbose",
        num=10,
        download_streams=True,
    )

    if items:
        print(f"> Downloaded {len(items)} items with verbose logging")
    else:
        print("Warning: No items downloaded")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Video Downloading Examples")
    print("=" * 50)
    print()
    print("Note: Video downloading requires ffmpeg to be installed")
    print("      and available in your system PATH.")
    print()

    # Run examples (comment out the ones you don't need)
    example_1_basic_video_download()
    example_2_video_with_captions()
    example_3_video_only_search()
    example_4_video_with_json_metadata()
    example_5_separate_video_scrape_and_download()
    example_6_video_with_cache()
    example_7_video_with_resolution_preference()
    example_8_video_verbose_mode()

    print("=" * 50)
    print("All video examples completed!")
    print("=" * 50)
