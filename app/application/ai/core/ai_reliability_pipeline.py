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
    
    def run(self, raw_response: str) -> tuple[list[str], float]:
        """
        Reliability pipeline:
        raw text → validate → parse → validate bullets → hallucination guard → score
        """

        # -------- raw validation --------
        self.validator.validate(raw_response)

        # -------- parsing --------
        bullets: list[str] = self.parser.parse(raw_response)

        # -------- structured validation --------
        valid_bullets: list[str] = self.validator.validate_bullets(bullets)

        # -------- hallucination detection --------
        self.hallucination_guard.check_bullets(valid_bullets)

        # -------- scoring --------
        score: float = self.scorer.score_bullets(valid_bullets)

        return valid_bullets, score