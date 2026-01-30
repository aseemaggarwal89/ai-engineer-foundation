import asyncio
from functools import wraps
from app.domain.exceptions.exceptions import ServiceError


def timeout(seconds: float):
    """
    Decorator to enforce timeout on async functions.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds,
                )
            except asyncio.TimeoutError:
                raise ServiceError(
                    f"{func.__name__} timed out after {seconds}s"
                )

        return wrapper

    return decorator
