"""
Example: Search Functionality
==============================

This example demonstrates how to search Pinterest for images
using search queries and download the results.
"""

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these search queries to your interests
# ============================================================================
SEARCH_QUERY_1 = "landscape photography"
SEARCH_QUERY_2 = "abstract art"
SEARCH_QUERIES = ["cats", "dogs", "birds"]
SEARCH_QUERY_3 = "minimalist design"
SEARCH_QUERY_4 = "cooking recipes"
SEARCH_QUERY_5 = "travel destinations"


def example_1_basic_search():
    """Simple search and download."""
    print("Example 1: Basic Search")
    print("-" * 50)

    # Search for images and download them
    images = PinterestDL.with_api().search_and_download(
        query=SEARCH_QUERY_1,
        output_dir="downloads/search/landscapes",
        num=20,
    )

    if images:
        print(f"> Downloaded {len(images)} landscape images")
    else:
        print("Warning: No images found")
    print()


def example_2_search_with_filters():
    """Search with resolution and caption filters."""
    print("Example 2: Search with Filters")
    print("-" * 50)

    images = PinterestDL.with_api().search_and_download(
        query=SEARCH_QUERY_2,
        output_dir="downloads/search/art",
        num=30,
        min_resolution=(800, 800),  # Only high-res images
        caption="json",  # Save full metadata as JSON
        delay=0.4,  # Slower requests to avoid rate limiting
    )

    if images:
        print(f"> Downloaded {len(images)} high-res abstract art images")
    else:
        print("Warning: No high-res images found")
    print()


def example_3_multiple_searches():
    """Run multiple searches programmatically."""
    print("Example 3: Multiple Searches")
    print("-" * 50)

    scraper = PinterestDL.with_api(verbose=False)

    for query in SEARCH_QUERIES:
        print(f"Searching for: {query}")
        images = scraper.search_and_download(
            query=query,
            output_dir=f"downloads/search/{query}",
            num=15,
            delay=0.3,
        )
        if images:
            print(f"  > Downloaded {len(images)} images\n")
        else:
            print("  Warning: No images found\n")

    print()


def example_4_search_with_cache():
    """Cache search results for later use."""
    print("Example 4: Search with Cache")
    print("-" * 50)

    images = PinterestDL.with_api().search_and_download(
        query=SEARCH_QUERY_3,
        output_dir="downloads/search/minimalist",
        num=25,
        cache_path="cache/search_minimalist.json",  # Save results
    )

    if images:
        print(f"> Downloaded {len(images)} images")
    else:
        print("Warning: No images downloaded")
    print("> Search results cached to cache/search_minimalist.json")
    print()


def example_5_search_with_videos():
    """Search and download videos if available."""
    print("Example 5: Search with Videos")
    print("-" * 50)

    images = PinterestDL.with_api().search_and_download(
        query=SEARCH_QUERY_4,
        output_dir="downloads/search/cooking",
        num=20,
        download_streams=True,  # Include videos
    )

    if images:
        print(f"> Downloaded {len(images)} items (images and videos)")
    else:
        print("Warning: No items downloaded")
    print()


def example_6_ensure_alt_text():
    """Search with guaranteed alt text for accessibility."""
    print("Example 6: Ensure Alt Text")
    print("-" * 50)

    images = PinterestDL.with_api(
        ensure_alt=True,  # Skip images without alt text
    ).search_and_download(
        query=SEARCH_QUERY_5,
        output_dir="downloads/search/travel",
        num=20,
        caption="txt",  # Save alt text to .txt files
    )

    if images:
        print(f"> Downloaded {len(images)} images (all with alt text)")
    else:
        print("Warning: No images with alt text found")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Search Examples")
    print("=" * 50)
    print()

    # Run examples (comment out the ones you don't need)
    example_1_basic_search()
    example_2_search_with_filters()
    example_3_multiple_searches()
    example_4_search_with_cache()
    example_5_search_with_videos()
    example_6_ensure_alt_text()

    print("=" * 50)
    print("All search examples completed!")
    print("=" * 50)
