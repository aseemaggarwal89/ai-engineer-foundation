import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Holds model metadata + routing configuration.
    """

    def __init__(self, settings):
        self.settings = settings
        self.models = {}

    async def load(self):

        logger.info("Loading model registry...")

        ai = self.settings.ai

        # You can later load this from:
        # - database
        # - feature flags
        # - config service
        # - S3
        # - LaunchDarkly

        self.models = {
            "summary": {
                "provider": ai.provider,
                "model_name": ai.model_name,
                "fallback": "tinyllama",  # example
            }
        }

        logger.info("Model registry loaded")

    async def close(self):
        logger.info("Model registry closed")

    # ⭐ Example resolver
    def get_summary_config(self):
        return self.models["summary"]
