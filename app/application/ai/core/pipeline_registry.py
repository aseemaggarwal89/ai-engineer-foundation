from app.application.ai.domain.ai_capability import AICapability
from app.application.ai.domain.ai_pipeline_port import AIResponsePipeline


class PipelineRegistry:

    def __init__(self):
        self._registry: dict[AICapability, AIResponsePipeline] = {}

    def register(
        self,
        capability: AICapability,
        pipeline: AIResponsePipeline,
    ):
        self._registry[capability] = pipeline

    def get(self, capability: AICapability) -> AIResponsePipeline:

        if capability not in self._registry:
            raise ValueError(f"No pipeline registered for {capability}")

        return self._registry[capability]