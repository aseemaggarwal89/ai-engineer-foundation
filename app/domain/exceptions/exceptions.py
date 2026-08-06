"""
Domain-level exceptions.

These exceptions represent business and application errors.
They are NOT HTTP-aware and should be raised from services or repositories.
The HTTP layer translates them via global exception handlers.
"""

from enum import Enum


class AppException(Exception):
    """
    Base application exception.

    All domain-specific exceptions must inherit from this class.
    It provides:
    - HTTP status code mapping
    - Stable error codes for API clients
    - Default human-readable messages
    """

    status_code: int = 500
    error_code: str = "APP_ERROR"
    message: str = "Application error"

    def __init__(self, message: str | None = None):
        # Allow callers to override the message, otherwise use default
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppException):
    """
    Raised when a requested resource does not exist.
    """
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ServiceError(AppException):
    """
    Raised for internal service or infrastructure failures.
    """
    status_code = 500
    error_code = "SERVICE_ERROR"
    message = "Internal service error"


class UserAlreadyExistsError(AppException):
    """
    Raised when attempting to create a user that already exists.
    """
    status_code = 409
    error_code = "USER_ALREADY_EXISTS"
    message = "User already exists"


class AuthenticationError(AppException):
    """
    Raised when authentication fails.

    Used for:
    - Invalid credentials
    - Missing or invalid token
    - Expired token
    - Inactive account
    """

    status_code = 401
    error_code = "AUTH_401"
    message = "Invalid email or password"


class AuthorizationError(AppException):
    """
    Raised when a user lacks sufficient permissions.
    """
    status_code = 403
    error_code = "FORBIDDEN"
    message = "Insufficient permissions"


# -----------------------------
# Request / Validation Errors
# -----------------------------

class BadRequestError(AppException):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Malformed request body"


class RequestValidationError(AppException):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Invalid request payload"


class PromptTooLargeError(AppException):
    status_code = 413
    error_code = "PROMPT_TOO_LARGE"
    message = "Prompt exceeds allowed size"


class AIError(AppException):
    """
    Base exception for AI inference failures.
    """

    status_code = 502   # ⭐ Important
    error_code = "AI_ERROR"
    message = "AI inference failed"


class ProviderErrorCategory(str, Enum):
    TIMEOUT = "timeout"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    UNAVAILABLE = "unavailable"
    AUTHENTICATION = "authentication"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    CONFIGURATION = "configuration"
    CIRCUIT_OPEN = "circuit_open"
    UNKNOWN = "unknown"


class AIProviderError(AIError):
    """
    Raised when an external AI provider fails.

    Fallback is allowed only for transient or availability-oriented categories.
    """
    error_code = "AI_PROVIDER_ERROR"
    message = "AI provider failure"

    FALLBACK_ELIGIBLE_CATEGORIES = {
        ProviderErrorCategory.TIMEOUT,
        ProviderErrorCategory.NETWORK,
        ProviderErrorCategory.RATE_LIMIT,
        ProviderErrorCategory.UNAVAILABLE,
        ProviderErrorCategory.INVALID_RESPONSE,
        ProviderErrorCategory.CIRCUIT_OPEN,
        ProviderErrorCategory.UNKNOWN,
    }

    def __init__(
        self,
        message: str | None = None,
        *,
        category: ProviderErrorCategory = ProviderErrorCategory.UNKNOWN,
        provider: str | None = None,
        model: str | None = None,
        fallback_eligible: bool | None = None,
    ):
        super().__init__(message)
        self.category = category
        self.provider = provider
        self.model = model
        self.fallback_eligible = (
            category in self.FALLBACK_ELIGIBLE_CATEGORIES
            if fallback_eligible is None
            else fallback_eligible
        )


class ResponseValidationError(AIError):
    """
    Raised when the AI response fails validation checks.
    """

    status_code = 502
    error_code = "INVALID_AI_RESPONSE"
    message = "AI returned an invalid response"


class ModelRefusalError(AIError):
    status_code = 502
    error_code = "MODEL_REFUSAL"
    message = "Model refused to answer"


class LowConfidenceError(AIError):
    status_code = 502
    error_code = "LOW_CONFIDENCE_RESPONSE"
    message = "AI response confidence too low"
