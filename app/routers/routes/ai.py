from fastapi import APIRouter, Depends
from app.application.ai.schemas.ai_summary import SummaryRequest, SummaryResponse
from app.application.ai.usecases.summarize_text import SummarizeTextUseCase
from app.dependencies.ai_dependencies import get_summarize_use_case

# ---------------------------------------------------------------------
# Public routes (no authentication)
# ---------------------------------------------------------------------
public_router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)


@public_router.post("/summarize",
                    response_model=SummaryResponse)
async def summarize(
    request: SummaryRequest,
    use_case: SummarizeTextUseCase = Depends(get_summarize_use_case),
):
    # Keep the HTTP layer thin. The use case owns safety checks and delegates
    # provider/cache/pipeline work to the AI application layer.
    bullets = await use_case.execute(request.text)

    return SummaryResponse(bullets=bullets)
