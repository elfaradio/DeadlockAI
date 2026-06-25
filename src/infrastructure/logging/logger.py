from __future__ import annotations

import logging
from pathlib import Path

from src.presentation.api.middleware.correlation import correlation_id_ctx_var


class CorrelationIdFilter(logging.Filter):
    """Filter to inject correlation_id contextvar into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            corr_id = correlation_id_ctx_var.get()
        except LookupError:
            corr_id = ""
        record.correlation_id = corr_id if corr_id else "-"
        return True


def setup_logger(name: str = "deadlock_app") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Format includes correlation_id
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(filename)s:%(lineno)d] [CorrID: %(correlation_id)s] - %(message)s"
    )

    corr_filter = CorrelationIdFilter()

    # File Handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.addFilter(corr_filter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(corr_filter)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
