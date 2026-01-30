import logging

logger = logging.getLogger(__name__)


async def safe_task(fn, *args, **kwargs):
    try:
        await fn(*args, **kwargs)
    except Exception:
        logger.exception(
            "Background task failed",
            extra={"task": fn.__name__},
        )
