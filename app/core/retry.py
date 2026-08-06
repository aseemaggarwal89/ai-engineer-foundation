from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, retry_if_exception, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.domain.exceptions.exceptions import AIProviderError


def db_retry():
    return retry(
        retry=retry_if_exception_type(SQLAlchemyError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=2),
        reraise=True,
    )


def infra_retry():
    """
    Retry for external infrastructure calls (AI, cache, APIs).
    """
    return retry(
        retry=retry_if_exception(_is_retryable_infrastructure_error),
        stop=stop_after_attempt(2),  # AI is expensive → fewer retries
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        reraise=True,
    )


def _is_retryable_infrastructure_error(exc: BaseException) -> bool:
    if isinstance(exc, AIProviderError):
        return exc.fallback_eligible

    return isinstance(exc, Exception)
