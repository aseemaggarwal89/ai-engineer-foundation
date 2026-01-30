from tenacity import retry, stop_after_attempt, wait_exponential


def db_retry():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.2, min=0.2, max=2),
        reraise=True,
    )
