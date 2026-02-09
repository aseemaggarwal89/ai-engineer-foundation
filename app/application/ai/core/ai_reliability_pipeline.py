from app.application.ai.core.bullet_parser import BulletParser
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
        parser: BulletParser,
    ):
        self.hallucination_guard = hallucination_guard
        self.validator = validator
        self.scorer = scorer
        self.parser = parser

    def run(self, response):
        # raw text
        self.validator.validate(response)
        # parsed + structured
        bullets = self.parser.parse(response)
        # bullet validation
        response = self.validator.validate_bullets(bullets)

        # hallucination detection
        self.hallucination_guard.check_bullets(response)

        # score
        score = self.scorer.score_bullets(response)
        return response, score
