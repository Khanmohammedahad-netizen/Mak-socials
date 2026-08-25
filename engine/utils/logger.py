import logging
import colorlog
import os
from datetime import datetime

from src.core.logging import install_redaction_filter

def setup_logger(name: str = "engine"):
    """Sets up a structured logger with both console and file output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = os.path.join("output", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Date-based log filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"engine_{date_str}.log")

    # Console Handler (Colored)
    console_handler = colorlog.StreamHandler()
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler (Rotating log)
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    install_redaction_filter(logger)
    install_redaction_filter()  # also cover root, for basicConfig/third-party use

    return logger

# Default logger instance
logger = setup_logger()
