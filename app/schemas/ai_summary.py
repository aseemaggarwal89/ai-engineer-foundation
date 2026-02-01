from pydantic import BaseModel, Field, ValidationInfo, field_validator
from app.core.ai_guardrails import (
    enforce_prompt_guardrails,
    sanitize_text,
)
from app.core.config import AISettings


class SummaryRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Text to summarize"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str, info: ValidationInfo):

        ai_settings = info.context["ai_settings"]

        return enforce_prompt_guardrails(
            value,
            ai_settings,
        )


class SummaryResponse(BaseModel):
    bullets: list[str] = Field(
        ...,
        description="List of bullet point summaries"
    )