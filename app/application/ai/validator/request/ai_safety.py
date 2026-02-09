from app.domain.exceptions.exceptions import RequestValidationError


class AISafetyFilter:

    BLOCKED_TERMS = {
        "credit card",
        "cvv",
        "password",
        "ssn",
    }

    def check(self, text: str):

        lower = text.lower()

        for term in self.BLOCKED_TERMS:
            if term in lower:
                raise RequestValidationError(
                    "Sensitive data detected"
                )
