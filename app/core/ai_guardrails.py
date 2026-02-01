import re

from app.domain.exceptions.exceptions import (
    RequestValidationError,
    PromptTooLargeError,
)

# MAX_PROMPT_LENGTH = 8_000        # characters (~2k tokens approx)
# MAX_REQUEST_BYTES = 32_000      # protects API gateway / FastAPI
# HARD_PROMPT_LIMIT = 20000


def enforce_prompt_guardrails(value: str, ai_settings) -> str:
    HARD_LIMIT = ai_settings.hard_prompt_limit
    SOFT_LIMIT = ai_settings.max_prompt_length

    value = value.strip()

    if not value:
        raise RequestValidationError("Input cannot be empty")

    # HARD reject (infra protection)
    if len(value) > HARD_LIMIT:
        raise PromptTooLargeError()

    # Binary detection
    non_printable_ratio = sum(
        ord(c) < 32 and c not in "\n\r\t"
        for c in value
    ) / len(value)

    if non_printable_ratio > 0.05:
        raise RequestValidationError("Binary input detected")

    # sanitize
    value = sanitize_text(value)

    # SOFT truncate (cost protection)
    if len(value) > SOFT_LIMIT:
        value = value[:SOFT_LIMIT]

    return value


CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1F\x7F]")


def sanitize_text(text: str) -> str:
    """
    Removes dangerous control characters
    and normalizes whitespace.
    """

    # Remove control chars
    text = CONTROL_CHAR_PATTERN.sub("", text)

    # Normalize whitespace
    text = " ".join(text.split())

    return text
