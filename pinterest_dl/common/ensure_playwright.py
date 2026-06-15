from pinterest_dl.exceptions import BrowserDependencyError

_INSTALL_HINT = (
    "Playwright is required for browser-based features but is not installed.\n"
    "Install the optional browser dependency:\n"
    "    pip install pinterest-dl[browser]\n"
    "Then download the browser binaries:\n"
    "    playwright install chromium\n"
    "Alternatively, capture cookies from an installed browser without Playwright:\n"
    "    pinterest-dl login --from-browser"
)


def ensure_playwright() -> None:
    """Ensure the optional Playwright dependency is importable.

    Uses importlib to probe for the package without importing it, so the check
    stays cheap for callers that only need to fail fast.

    Raises:
        BrowserDependencyError: If `playwright` is not installed, with
            instructions for installing the extra and the browser binaries.
    """
    import importlib.util

    if importlib.util.find_spec("playwright") is None:
        raise BrowserDependencyError(_INSTALL_HINT)
