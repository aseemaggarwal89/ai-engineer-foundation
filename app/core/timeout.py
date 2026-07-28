import asyncio
from functools import wraps
from app.domain.exceptions.exceptions import ServiceError


def timeout_from_self(func):
    """
    Decorator to enforce timeout on async functions.
    """

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await asyncio.wait_for(
                func(self, *args, **kwargs),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise ServiceError(
                f"{func.__name__} timed out after {self.timeout_seconds}s"
            ) from exc
        
    return wrapper
