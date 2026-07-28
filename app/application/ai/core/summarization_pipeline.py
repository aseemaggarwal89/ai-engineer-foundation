from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.domain.ai_pipeline_port import AIResponsePipeline
from app.application.ai.validator.response.hallucination_guard import HallucinationGuard
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator


class SummarizationPipeline(AIResponsePipeline):
    """
    Converts raw model text into validated summary bullets.

    Keep this pipeline deterministic and fast. Expensive judging/evaluation can
    be added later as another pipeline step or background observation path.
    """
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
        raw text -> validate -> parse -> validate bullets -> guard -> score
        """

        # Reject obviously broken or unsafe raw text before parsing.
        self.validator.validate(raw_response)

        # Normalize provider-specific bullet formatting into application data.
        bullets: list[str] = self.parser.parse(raw_response)

        # Apply zero-trust validation to parsed bullets, not only raw text.
        valid_bullets: list[str] = self.validator.validate_bullets(bullets)

        # Current guard is simple, but this is the extension point for stronger
        # factuality checks or source-grounding checks.
        self.hallucination_guard.check_bullets(valid_bullets)

        # Score is used by SummaryService to decide whether to return or reject.
        score: float = self.scorer.score_bullets(valid_bullets)

        return valid_bullets, score
