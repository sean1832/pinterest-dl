"""Deprecated: This module has been reorganized.

The low_level module has been flattened:
- low_level.api → pinterest_dl.api
- low_level.http → pinterest_dl.download
- low_level.hls → pinterest_dl.download.video
- low_level.webdriver → pinterest_dl.webdriver

This backward compatibility module will be removed in version 1.1.0.
"""

import warnings


def __getattr__(name: str):
    """Provide backward compatibility with deprecation warnings for old module structure."""
    warnings.warn(
        f"Importing from pinterest_dl.low_level.{name} is deprecated and will be removed in version 1.1.0. "
        f"The module has been moved. Check the documentation for the new import path.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Try to provide the actual module if possible
    if name == "api":
        import pinterest_dl.api as api

        return api
    elif name == "http":
        import pinterest_dl.download as download

        return download
    elif name == "hls":
        import pinterest_dl.download.video as video

        return video
    elif name == "webdriver":
        import pinterest_dl.webdriver as webdriver

        return webdriver

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
