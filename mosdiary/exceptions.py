class MOSDiaryBaseException(Exception):
    """Базовое исключение `mosdiary`."""


class APIException(MOSDiaryBaseException):
    """Базовое исключение при взаимодействии с API МЭШ."""


class APIHTTPException(APIException):
    """API МЭШ вернул ошибочный HTTP-статус."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        method: str | None = None,
        url: str | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.method = method
        self.url = url


class APIConnectionException(APIException, ConnectionError):
    """Не удалось установить или поддержать соединение с API МЭШ."""


class APITimeoutException(APIException, TimeoutError):
    """Истёк тайм-аут запроса к API МЭШ."""


class AuthenticationException(MOSDiaryBaseException):
    """Базовое исключение авторизации в МЭШ."""


class AuthenticationRequiredException(AuthenticationException):
    """Для запроса не передан токен авторизации."""


class TokenExpired(AuthenticationException):
    """Срок действия `aupd_token` истёк."""


class InvalidResponseException(APIException):
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


class VerificationCodeExpiredException(QRLoginException, TimeoutError):
    """Срок действия кода второго фактора истёк."""


class VerificationAttemptsExhaustedException(QRLoginException):
    """Попытки ввода кода второго фактора исчерпаны."""


class LoginTokenMissingException(QRLoginException):
    """Mos ID не вернул токены после успешного входа."""


__all__ = (
    'APIConnectionException',
    'APIException',
    'APIHTTPException',
    'APITimeoutException',
    'AuthenticationException',
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
    'TokenExpired',
    'TwoFactorRequiredException',
    'VerificationAttemptsExhaustedException',
    'VerificationCodeExpiredException',
)
