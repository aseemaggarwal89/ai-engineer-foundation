from fastapi import Depends, Request
from pydantic import ValidationError as PydanticValidationError

from app.schemas.ai_summary import SummaryRequest
from app.core.config import get_settings, Settings
from app.domain.exceptions.exceptions import (
    BadRequestError,
    RequestValidationError,
)


async def parse_summary_request(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> SummaryRequest:

    # -------- JSON Parsing --------
    try:
        body = await request.json()

    except Exception:
        raise BadRequestError("Invalid JSON body")

    # -------- Schema Validation --------
    try:
        return SummaryRequest.model_validate(
            body,
            context={"ai_settings": settings.ai},
        )

    except PydanticValidationError:
        raise RequestValidationError()
