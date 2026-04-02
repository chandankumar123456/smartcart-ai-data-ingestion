import os
import sys
from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: str = "logs/smartcart.log") -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    os.makedirs("logs", exist_ok=True)
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )


log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logger(log_level=log_level)

__all__ = ["logger", "setup_logger"]
