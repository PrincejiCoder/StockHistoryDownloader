import logging
import os
import pathlib
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Determine a writable directory for logs (Local AppData)
    app_dir = pathlib.Path(os.getenv("LOCALAPPDATA")) / "StockHistoryDownloader"
    app_dir.mkdir(parents=True, exist_ok=True)

    log_file = app_dir / "app.log"

    logger = logging.getLogger("StockDownloader")
    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
