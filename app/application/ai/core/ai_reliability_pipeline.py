from app.application.ai.validator.request.ai_safety import AISafetyFilter
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.domain.exceptions.exceptions import ResponseValidationError


class AIReliabilityPipeline:
    def __init__(
        self,
        hallucination_guard: HallucinationGuard,
        validator: AIResponseValidator,
        scorer: AIResponseScorer,
    ):
        self.hallucination_guard = hallucination_guard
        self.validator = validator
        self.scorer = scorer

    async def run(self, response):

        response = self.validator.validate_bullets(response)
        self.hallucination_guard.check(response)
        score = self.scorer.score_bullets(response)
        if score < 0.6:
            raise ResponseValidationError("Low confidence AI output")

        return response, score
