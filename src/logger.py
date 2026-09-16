"""Logging configuration and utilities."""

import logging
import logging.handlers
from pathlib import Path
from config import config


def setup_logger(name: str = "m365-automation") -> logging.Logger:
    """
    Setup application logger with file and console handlers.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    config.ensure_directories()

    logger = logging.getLogger(name)
    logger.setLevel(config.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(config.LOG_LEVEL)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Global logger instance
logger = setup_logger()
