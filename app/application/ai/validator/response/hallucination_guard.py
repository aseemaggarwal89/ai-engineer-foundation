from app.domain.exceptions.exceptions import ResponseValidationError


class HallucinationGuard:
    MAX_BULLET_LENGTH = 300

    def check_bullets(self, bullets: list[str]):

        for bullet in bullets:
            if len(bullet) > self.MAX_BULLET_LENGTH:
                raise ResponseValidationError(
                    "Suspicious AI output detected"
                )
