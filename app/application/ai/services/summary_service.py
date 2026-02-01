from app.application.ai.parsers.bullet_parser import BulletParser
from app.application.ai.prompts.summary_prompt import SummaryPrompt
from app.core.config import AISettings
from app.domain.ai.ai_model_port import AIModelPort


class SummaryService:

    def __init__(
        self,
        model: AIModelPort,
        prompt: SummaryPrompt,
        parser: BulletParser,
        settings: AISettings
    ):
        self.model = model
        self.prompt = prompt
        self.parser = parser
        self.settings = settings

    async def summarize(self, text: str):

        built = self.prompt.build(text)

        raw = await self.model.generate(
            built,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens
        )

        return self.parser.parse(raw)
