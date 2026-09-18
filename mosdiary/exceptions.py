class MOSDiaryBaseException(Exception):
    """Базовое исключение `mosdiary`."""


class AuthenticationRequiredException(MOSDiaryBaseException):
    """Для запроса не передан токен авторизации."""


class InvalidResponseException(MOSDiaryBaseException):
    """МЭШ вернул ответ неожиданного формата."""


class LoginException(MOSDiaryBaseException):
    """Базовое исключение при входе в аккаунт."""


class InvalidLoginParameterException(LoginException, ValueError):
    """Передан некорректный параметр входа."""


class QRLoginException(LoginException):
    """Базовое исключение QR-входа."""


class QRLoginInitializationException(QRLoginException):
    """Не удалось получить корректный QR-код."""


class QRLoginStateException(QRLoginException):
    """Mos ID вернул ошибочное или неизвестное состояние QR-входа."""

    def __init__(self, state: object, cause: object | None = None):
        self.state = state
        self.cause = cause
        message = f'Некорректное состояние QR-входа: {state}'
        if cause is not None:
            message += f'; причина: {cause}'
        super().__init__(message)


class QRLoginExpiredException(QRLoginException, TimeoutError):
    """Истёк срок действия QR-кода."""


class TwoFactorRequiredException(QRLoginException):
    """Mos ID запросил второй фактор, но callback для кода не передан."""


class InvalidVerificationCodeException(QRLoginException, ValueError):
    """Код второго фактора имеет неверный формат."""


class LoginTokenMissingException(QRLoginException):
    """Mos ID не вернул токены после успешного входа."""


__all__ = (
    'AuthenticationRequiredException',
    'InvalidLoginParameterException',
    'InvalidResponseException',
    'InvalidVerificationCodeException',
    'LoginException',
    'LoginTokenMissingException',
    'MOSDiaryBaseException',
    'QRLoginException',
    'QRLoginExpiredException',
    'QRLoginInitializationException',
    'QRLoginStateException',
    'TwoFactorRequiredException',
)