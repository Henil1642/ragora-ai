"""
Logging configuration
"""

import logging
import sys
from config.settings import settings


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with configuration"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)