"""
Domain-level exceptions.

These exceptions represent business and application errors.
They are NOT HTTP-aware and should be raised from services or repositories.
The HTTP layer translates them via global exception handlers.
"""


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
    pass