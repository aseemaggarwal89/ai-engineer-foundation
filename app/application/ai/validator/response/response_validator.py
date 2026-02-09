from app.domain.exceptions.exceptions import ResponseValidationError


class AIResponseValidator:
    """
    Reject clearly bad model outputs.
    Fast checks only.
    """
    def validate(self, summary: str) -> None:
        if not summary:
            raise ResponseValidationError("Empty AI response")

        if len(summary) < 10:
            raise ResponseValidationError("Suspiciously short AI response")

        if "I am an AI language model" in summary:
            raise ResponseValidationError("Prompt leakage detected")

        if summary.count("```") > 5:
            raise ResponseValidationError("Malformed output")
    
    """
    Validates model output before returning to clients.
    Zero-trust policy.
    """
    def validate_bullets(self, bullets: list[str]) -> list[str]:

        if not bullets:
            raise ResponseValidationError("Empty AI response")

        # if len(bullets) < 3:
        #     raise ResponseValidationError("Too few bullets from model")

        for b in bullets:
            # if len(b.strip()) < 5:
            #     raise ResponseValidationError("Bullet too short")
            if "As an AI" in b or "As an AI language model" in b:
                raise ResponseValidationError("Prompt leakage detected")

        return bullets[:5]  # clamp