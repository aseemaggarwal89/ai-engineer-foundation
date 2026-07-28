from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


SummaryText = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=20_000,
    ),
]


class SummaryRequest(BaseModel):
    text: SummaryText = Field(
        ...,
        description="Text to summarize",
    )


class SummaryResponse(BaseModel):
    bullets: list[str] = Field(
        ...,
        description="List of bullet point summaries"
    )
