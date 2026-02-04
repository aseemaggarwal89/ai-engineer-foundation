from app.application.ai.core.ai_guardrails import AIGuardrails
from app.application.ai.services.summary_service import SummaryService


class SummarizeTextUseCase:

    def __init__(
        self,
        guardrails: AIGuardrails,
        summary_service: SummaryService,
    ):
        self.guardrails = guardrails
        self.summary_service = summary_service

    async def execute(self, text: str) -> list[str]:

        # 🔥 Boundary protection
        self.guardrails.validate_prompt(text)

        return await self.summary_service.summarize(text)
