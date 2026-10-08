import logging

from .paths import LOG_DIR


def configure_logging() -> logging.Logger:
    logger = logging.getLogger("discord_proxy_manager")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(
        LOG_DIR / "discord-proxy-manager.log", encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger
