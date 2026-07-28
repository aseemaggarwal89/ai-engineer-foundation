from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


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
        stop=stop_after_attempt(2),  # AI is expensive → fewer retries
        wait=wait_exponential(multiplier=0.5, min=0.5, max=3),
        reraise=True,
    )
