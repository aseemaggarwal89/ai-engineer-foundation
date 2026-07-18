from app.application.ai.domain.ai_pipeline_port import AIResponsePipeline
from app.application.ai.validator.response.response_scorer import AIResponseScorer
from app.application.ai.validator.response.response_validator import AIResponseValidator
from app.domain.exceptions.exceptions import ModelRefusalError


class ChatPipeline(AIResponsePipeline):
    """
    Converts raw chat model text into a safe application response.

    Chat output is less structured than summarization, so this pipeline focuses
    on deterministic hygiene: normalize text, reject empty/malformed output,
    detect common refusal boilerplate, and assign a quality score.
    """

    REFUSAL_PHRASES = (
        "i can't assist",
        "i cannot assist",
        "i can't help",
        "i cannot help",
        "i am unable to",
        "i'm unable to",
    )

    def __init__(
        self,
        validator: AIResponseValidator,
        scorer: AIResponseScorer,
    ):
        self.validator = validator
        self.scorer = scorer

    def run(self, raw_response: str) -> tuple[str, float]:
        """
        Chat reliability workflow:
        raw text -> normalize -> validate -> refusal guard -> score.
        """
        response = self._normalize(raw_response)

        self.validator.validate(response)
        self._reject_refusal(response)

        score = self.scorer.score(response)

        return response, score

    def _normalize(self, raw_response: str) -> str:
        """
        Keep model content readable without changing its meaning.
        """
        lines = [line.strip() for line in raw_response.splitlines()]
        non_empty_lines = [line for line in lines if line]

        return "\n".join(non_empty_lines).strip()

    def _reject_refusal(self, response: str) -> None:
        lower_response = response.lower()

        if any(phrase in lower_response for phrase in self.REFUSAL_PHRASES):
            raise ModelRefusalError()
