"""
Logging configuration for Pinterest-DL.

Provides tqdm-compatible logging with structured format [time] [level] [message].
"""

import logging
import sys

from tqdm import tqdm


class TqdmLoggingHandler(logging.Handler):
    """
    Logging handler that uses tqdm.write() to avoid corrupting progress bars.

    tqdm.write() ensures log messages are printed above the progress bar,
    keeping the progress bar at the bottom of the terminal.
    """

    def __init__(self, stream=None):
        super().__init__()
        self.stream = stream or sys.stderr

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            tqdm.write(msg, file=self.stream)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure the root logger with tqdm-compatible console output.

    Args:
        verbose: If True, set level to DEBUG. Otherwise, set to WARNING.

    The log format is: [HH:MM:SS] [LEVEL] message
    """
    # TODO: Add --log-file flag for optional file output

    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Set level based on verbose flag
    level = logging.DEBUG if verbose else logging.WARNING

    # Create formatter with structured format
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create tqdm-compatible handler
    handler = TqdmLoggingHandler()
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
