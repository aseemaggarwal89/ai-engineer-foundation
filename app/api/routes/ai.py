from fastapi import APIRouter, Depends
from app.schemas.ai_summary import SummaryRequest, SummaryResponse
from app.application.ai.services import SummaryService
from app.dependencies.deps import get_summary_service

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------
public_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@public_router.post("/ai/summarize", response_model=SummaryResponse)
async def summarize(
    req: SummaryRequest,
    svc: SummaryService = Depends(get_summary_service)
):
    bullets = await svc.summarize(req.text)
    return {"bullets": bullets}
