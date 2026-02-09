from app.application.ai.core.bullet_parser import BulletParser
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.application.ai.validator.prompt_evaluator import PromptEvaluator
from app.core.config import AISettings
from app.application.ai.domain.ai_model_port import AIModelPort


class SummaryService:

    def __init__(
        self,
        model: AIModelPort,
        prompt: SummaryPrompt,
        parser: BulletParser,
        evaluator: PromptEvaluator,
        settings: AISettings
    ):
        self.model = model
        self.prompt = prompt
        self.parser = parser
        self.evaluator = evaluator
        self.settings = settings

    async def summarize(self, text: str) -> list[str]:
        prompt_text = self.prompt.build(text)

        raw_output = await self.model.generate(
            prompt_text,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
        )

        # observability
        self.evaluator.evaluate(
            prompt_version=self.prompt.VERSION,
            output=raw_output,
        )
        
        return self.parser.parse(raw_output)