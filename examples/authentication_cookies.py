"""
Example: Authentication with Cookies
=====================================

This example demonstrates how to use cookies for authentication
to access private boards and pins on Pinterest.
"""

import json
import os
from pathlib import Path

from pinterest_dl import PinterestDL

# ============================================================================
# Configuration - Change these URLs to your actual Pinterest links
# ============================================================================
PRIVATE_BOARD_URL = (
    "https://au.pinterest.com/pin/900438519273272242/"  # Replace with your private board
)
PRIVATE_PIN_URL = (
    "https://au.pinterest.com/pin/900438519273272242/"  # Replace with your private pin
)
SEARCH_QUERY = "my private collection"  # Change to your search query


def example_1_login_and_save_cookies():
    """Login to Pinterest and save cookies for future use."""
    print("Example 1: Login and Save Cookies")
    print("-" * 50)

    # Get credentials (NEVER hardcode passwords in production!)
    email = input("Enter Pinterest email: ")
    password = os.getenv("PINTEREST_PASSWORD")  # Use environment variable

    if not password:
        print("Warning: Set PINTEREST_PASSWORD environment variable")
        return

    # Login using Playwright (default browser automation)
    print("Logging in to Pinterest...")
    cookies = (
        PinterestDL.with_browser(
            browser_type="chromium",  # or 'firefox'
            headless=True,  # Set to False to see browser window
        )
        .login(email, password)
        .get_cookies(
            after_sec=7,  # Wait 7 seconds after login to ensure cookies are set
        )
    )

    # Save cookies to file
    cookies_path = Path("cookies.json")
    with open(cookies_path, "w") as f:
        json.dump(cookies, f, indent=4)

    print(f"> Cookies saved to {cookies_path}")
    print()


def example_2_load_cookies_from_file():
    """Load cookies from a file and use them for scraping."""
    print("Example 2: Load Cookies from File")
    print("-" * 50)

    cookies_path = Path("cookies.json")

    if not cookies_path.exists():
        print("Warning: No cookies file found. Run example_1 first.")
        return

    # Load cookies
    with open(cookies_path, "r") as f:
        cookies = json.load(f)

    # Use cookies for scraping
    images = (
        PinterestDL.with_api()
        .with_cookies(cookies)  # Add cookies to scraper
        .scrape_and_download(
            url=PRIVATE_BOARD_URL,
            output_dir="downloads/private",
            num=20,
        )
    )

    if images:
        print(f"> Downloaded {len(images)} images from private board")
    else:
        print("Warning: No images downloaded")
    print()


def example_3_use_cookies_path_directly():
    """Use cookies path directly without loading manually."""
    print("Example 3: Use Cookies Path Directly")
    print("-" * 50)

    cookies_path = "cookies.json"

    if not Path(cookies_path).exists():
        print("Warning: No cookies file found. Run example_1 first.")
        return

    # Shorthand: provide path directly
    images = (
        PinterestDL.with_api()
        .with_cookies_path(cookies_path)  # Load cookies from path
        .scrape_and_download(
            url=PRIVATE_PIN_URL,
            output_dir="downloads/private_pin",
            num=10,
        )
    )

    if images:
        print(f"> Downloaded {len(images)} images using cookies")
    else:
        print("Warning: No images downloaded")
    print()


def example_4_cookies_with_search():
    """Use cookies for authenticated search."""
    print("Example 4: Cookies with Search")
    print("-" * 50)

    cookies_path = "cookies.json"

    if not Path(cookies_path).exists():
        print("Warning: No cookies file found. Run example_1 first.")
        return

    # Authenticated search may return different/more results
    images = (
        PinterestDL.with_api()
        .with_cookies_path(cookies_path)
        .search_and_download(
            query=SEARCH_QUERY,
            output_dir="downloads/private_search",
            num=15,
        )
    )

    if images:
        print(f"> Downloaded {len(images)} images from authenticated search")
    else:
        print("Warning: No images downloaded")
    print()


def example_5_selenium_login():
    """Alternative: Login using Selenium (legacy)."""
    print("Example 5: Selenium Login (Legacy)")
    print("-" * 50)

    import warnings

    email = input("Enter Pinterest email: ")
    password = os.getenv("PINTEREST_PASSWORD")

    if not password:
        print("Warning: Set PINTEREST_PASSWORD environment variable")
        return

    # Suppress deprecation warning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        # Login using Selenium
        cookies = (
            PinterestDL.with_selenium(
                browser_type="chrome",  # or 'firefox'
                headless=True,
            )
            .login(email, password)
            .get_cookies(after_sec=7)
        )

    # Save cookies
    with open("cookies_selenium.json", "w") as f:
        json.dump(cookies, f, indent=4)

    print("> Cookies saved using Selenium (legacy method)")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Pinterest-DL Authentication Examples")
    print("=" * 50)
    print()

    print("Choose an example to run:")
    print("1. Login and save cookies")
    print("2. Load cookies from file")
    print("3. Use cookies path directly")
    print("4. Cookies with search")
    print("5. Selenium login (legacy)")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        example_1_login_and_save_cookies()
    elif choice == "2":
        example_2_load_cookies_from_file()
    elif choice == "3":
        example_3_use_cookies_path_directly()
    elif choice == "4":
        example_4_cookies_with_search()
    elif choice == "5":
        example_5_selenium_login()
    else:
        print("Invalid choice. Run the script again.")

    print("=" * 50)
    print("Example completed!")
    print("=" * 50)
