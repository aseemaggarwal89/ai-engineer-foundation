
from app.application.ai.domain.ai_pipeline_port import AIResponsePipeline


class ChatPipeline(AIResponsePipeline):

    def __init__(self, validator, scorer):
        self.validator = validator
        self.scorer = scorer

    def run(self, raw_response: str) -> tuple[str, float]:

        self.validator.validate(raw_response)

        score = self.scorer.score_text(raw_response)

        return raw_response, score