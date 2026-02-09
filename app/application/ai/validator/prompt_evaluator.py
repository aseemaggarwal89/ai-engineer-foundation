import logging

logger = logging.getLogger(__name__)


class PromptEvaluator:

    def evaluate(
        self,
        *,
        prompt_version: str,
        output: str,
    ) -> None:

        logger.info(
            "prompt_evaluated",
            extra={
                "prompt_version": prompt_version,
                "output_chars": len(output),
            },
        )
