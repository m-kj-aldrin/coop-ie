import logging
from logging import _nameToLevel
import sys
from logging.handlers import RotatingFileHandler
from typing import Literal


Level = Literal["INFO", "DEBUG", "ERROR"]


def setup_logger(
    name: str = "coop_ie", log_file: str = "app/data/app.log", level: Level = "INFO"
) -> logging.Logger:
    """
    Set up and configure a logger instance.

    Args:
        name (str): Name of the logger
        log_file (str): Path to the log file
        level (Level): Level of the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    _level = _nameToLevel[level]
    logger = logging.getLogger(name)
    logger.setLevel(_level)

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Create handlers
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_level)
    console_handler.setFormatter(formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(10)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create default logger instance
logger = setup_logger(level="DEBUG")
