import re
from app.domain.exceptions.exceptions import (
    PromptTooLargeError,
    BadRequestError,
    RequestValidationError,
)

from app.core.config import AISettings


class AIGuardrails:

    def __init__(self, settings: AISettings):
        self.settings = settings

    def validate_prompt(self, text: str) -> str:
        if not text or not text.strip():
            raise BadRequestError("Prompt cannot be empty")
        HARD_LIMIT = self.settings.hard_prompt_limit
        SOFT_LIMIT = self.settings.max_prompt_length
        value = text.strip()

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
        value = self.sanitize_text(value)

        # SOFT truncate (cost protection)
        if len(value) > SOFT_LIMIT:
            value = value[:SOFT_LIMIT]

        return value

    def sanitize_text(self, text: str) -> str:
        """
        Removes dangerous control characters
        and normalizes whitespace.
        """
        CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
        # Remove unsafe control chars while preserving normal whitespace
        # separators so words from different lines do not get joined together.
        text = CONTROL_CHAR_PATTERN.sub("", text)

        # Normalize whitespace
        text = " ".join(text.split())

        return text

