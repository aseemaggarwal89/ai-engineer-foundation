from pydantic import BaseModel, Field


class SummaryRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        description="Text to summarize"
    )


class SummaryResponse(BaseModel):
    bullets: list[str] = Field(
        ...,
        description="List of bullet point summaries"
    )