import logging
import sys

import structlog

from src.core.settings.base import settings


def setup_logging() -> None:
    """Настраивает structlog: JSON-логи в stdout, уровень из LOG_LEVEL."""
    logging.basicConfig(format='%(message)s', stream=sys.stdout, level=settings.LOG_LEVEL)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt='iso', utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping()[settings.LOG_LEVEL]),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
