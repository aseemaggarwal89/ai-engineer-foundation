class AppException(Exception):
    """Base application exception"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a resource is not found"""
    pass


class ServiceError(AppException):
    """Raised for internal service failures"""
    pass