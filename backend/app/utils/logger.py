"""Centralized logging utility for vector search pipeline experiments."""
import logging
import sys
from pathlib import Path
from datetime import datetime


def get_search_logger(name: str = "vector_search"):
    """
    Get a configured logger that writes to both stdout and a log file.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent.parent.parent / "test"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "search_experiments.log"

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(message)s"  # Clean format for readability
    )
    console_handler.setFormatter(console_formatter)

    # File handler (append to experiments log)
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def log_section(logger: logging.Logger, title: str, width: int = 80):
    """Log a formatted section header."""
    separator = "=" * width
    logger.info(f"\n{separator}")
    logger.info(f"  {title}")
    logger.info(f"{separator}\n")


def log_subsection(logger: logging.Logger, title: str, width: int = 80):
    """Log a formatted subsection header."""
    separator = "-" * width
    logger.info(f"\n{separator}")
    logger.info(f"  {title}")
    logger.info(f"{separator}")