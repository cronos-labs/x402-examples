# lib/errors/app_error.py
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def log(self) -> None:
        logger.error(f"{self.__class__.__name__}: {self.message}", extra=self.context)


class ConfigError(AppError):
    pass


class NetworkError(AppError):
    pass


class LlmError(AppError):
    pass


class ValidationError(AppError):
    pass
