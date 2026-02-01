from fastapi import APIRouter, Depends
from app.dependencies.ai_parsers import parse_summary_request
from app.schemas.ai_summary import SummaryRequest, SummaryResponse
from app.application.ai.services.summary_service import SummaryService
from app.dependencies.deps import get_summary_service

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------
public_router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@public_router.post("/summarize", response_model=SummaryResponse)
async def summarize(
    req: SummaryRequest = Depends(parse_summary_request),
    svc: SummaryService = Depends(get_summary_service),
):
    bullets = await svc.summarize(req.text)

    return SummaryResponse(bullets=bullets)