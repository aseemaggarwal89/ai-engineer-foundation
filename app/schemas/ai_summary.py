from pydantic import BaseModel


class SummaryRequest(BaseModel):
    text: str


class SummaryResponse(BaseModel):
    bullets: list[str]
