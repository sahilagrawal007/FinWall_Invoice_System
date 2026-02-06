class AppException(Exception):
    """Base exception for application"""

    pass


class NotFoundException(AppException):
    """Raised when resource is not found"""

    pass


class UnauthorizedException(AppException):
    """Raised when user is not authorized"""

    pass


class ValidationException(AppException):
    """Raised when validation fails"""

    pass


class DuplicateException(AppException):
    """Raised when duplicate entry is attempted"""

    pass
