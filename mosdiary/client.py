from asyncio import sleep, TimeoutError 
from collections.abc import Awaitable, Callable, Mapping
from datetime import date
from html import unescape
from inspect import isawaitable
from io import BytesIO
from re import IGNORECASE, search
from time import time
from types import TracebackType
from typing import Literal

from aiohttp import (
    ClientConnectionError,
    ClientResponse,
    ClientSession,
    ClientSSLError,
    ServerFingerprintMismatch,
)
from yarl import URL

from .exceptions import (
    AuthenticationRequiredException,
    InvalidLoginParameterException,
    InvalidResponseException,
    InvalidVerificationCodeException,
    LoginTokenMissingException,
    QRLoginExpiredException,
    QRLoginInitializationException,
    QRLoginStateException,
    TwoFactorRequiredException,
)
from .types.profile import UserInfo, Family
from .types.homework import Homework
from .types.marks import Mark, SubjectMark


class MOSDiaryClient:
    BASE_URL = 'https://school.mos.ru/api/'
    def __init__(self, aupd_token: str | None = None, timeout: float = 30, headers: Mapping[str, str] | None = None):
        """
        Клиент МЭШ

        Args:
            aupd_token (`str | None`): Токен (кука) авторизации
            timeout (`float`): Тайм-аут запросов в секундах.
            headers (`Mapping[str, str] | None`): Общие заголовки запросов.
        """
        
        self.aupd_token = aupd_token
        """Токен (кука) авторизации"""
        self.timeout = timeout
        self.headers = dict(headers or {})

        self.id: int | None = None
        """ID аккаунта МЭШ"""

        self._session: ClientSession | None = None

    async def __aenter__(self) -> 'MOSDiaryClient':
        self._ensure_session()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None,
    ) -> None:
        await self.close()

    def _ensure_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession(headers=self.headers)

        return self._session

    async def close(self) -> None:
        if self._session is None:
            return

        session = self._session
        self._session = None
        if not session.closed:
            await session.close()

    async def _send_request(
        self,
        method: Literal['GET', 'POST'],
        endpoint: str,
        use_auth: bool = True,
        return_type: Literal['dict', 'response', 'bool'] = 'dict',
        **kwargs,
    ) -> dict | ClientResponse | bool:
        """Отправить запрос и вернуть JSON, сырой ответ или признак успеха."""
        if return_type not in ('dict', 'response', 'bool'):
            raise ValueError(f'Неизвестный тип возврата: {return_type}')

        url = (
            self.BASE_URL + endpoint
            if not endpoint.startswith('http')
            else endpoint
        )
        headers = dict(kwargs.pop('headers', {}) or {})
        cookies = dict(kwargs.pop('cookies', {}) or {})
        if use_auth and self.aupd_token is not None:
            cookies['aupd_token'] = self.aupd_token
            headers.setdefault('Authorization', f'Bearer {self.aupd_token}')
            headers.setdefault('Accept', 'application/json, text/plain, */*')
            headers.setdefault('X-mes-subsystem', 'familyweb')
        elif use_auth and self.aupd_token is None:
            raise AuthenticationRequiredException('Этот метод требует авторизации. Заполните поле aupd_token в MOSDiaryClient.')

        retry_number = 0

        while True:
            try:
                response = await self._ensure_session().request(
                    method,
                    url,
                    headers=headers,
                    cookies=cookies,
                    timeout=self.timeout,
                    **kwargs,
                )

                if return_type == 'response':
                    return response

                async with response:
                    if return_type == 'bool':
                        return 200 <= response.status < 300

                    response.raise_for_status()
                    data = await response.json()
                    if not isinstance(data, dict):
                        raise InvalidResponseException('Ответ API не является JSON-объектом')
                    return data
            except (ClientSSLError, ServerFingerprintMismatch):
                raise
            except (ClientConnectionError, TimeoutError):
                # POST could already have been processed, and a streamed body
                # could already be consumed. Neither can be safely replayed.
                if (
                    method != 'GET'
                    or 'data' in kwargs
                    or retry_number >= 2
                ):
                    raise

                await sleep(0.5 * 2 ** retry_number)
                retry_number += 1

    #TODO: Проверить
    async def logout(self)-> bool:
        """
        Завершает сессию, сбрасывает self.id и self.aupd_token

        Returns:
            bool:
                Выполнен ли запрос успешно
        """
        success = await self._send_request(
            'GET',
            'https://school.mos.ru/v3/auth/logout',
            return_type='bool',
        )
        if success:
            self.id = None
            self.aupd_token = None
            await self.close()
            return True
        return False


    #TODO: Проверить
    #TODO: Описать для чего нужен accessTokenEom
    async def refresh_session(self)-> tuple[str, str] | None:
        """
        Обновление (рефреш) сессии для получения `aupd_token` и `access_token_eom`\n
        с автоматической вставкой `self.aupd_token` в `MOSDiaryClient`
        Returns:
            tuple[str, str] | None:
                `(aupd_token, access_token_eom)` —
                токены AUPD и EOM соответственно.
        """
        resp = await self._send_request('POST', 'https://uchebnik.mos.ru/acl/api/session/v2/refresh')
        self.aupd_token = resp['accessTokenAupd']
        return self.aupd_token, resp['accessTokenEom']


    async def start_qr_login(self, return_type: Literal['link', 'qr', 'link&qr'] = 'link')-> tuple[str, int] | tuple[bytes, int] | tuple[str, bytes, int]:
        """
        Начать вход по QR-коду. После используйте `wait_qr_login(expires)`

        Args:
            return_type (`Literal`): Вернуть ссылку, PNG-изображение QR-кода
                либо ссылку и изображение.

        Returns:
            tuple[str, int] | tuple[bytes, int] | tuple[str, bytes, int]:
                Запрошенные данные и время истечения QR-кода в Unix time.
        """
        if return_type not in ('link', 'qr', 'link&qr'):
            raise InvalidLoginParameterException(f'Неизвестный тип возвращаемого результата: {return_type}')

        response = await self._send_request(
            'GET',
            'https://school.mos.ru/v3/auth/sudir/login',
            use_auth=False,
            return_type='response',
        )
        async with response:
            response.raise_for_status()
            html = await response.text()

        match = search(r'url=([^"\'>]+)', html, IGNORECASE)
        if match is None:
            raise QRLoginInitializationException('МЭШ не вернул ссылку для авторизации')

        response = await self._send_request(
            'GET',
            unescape(match.group(1)),
            use_auth=False,
            return_type='response',
            headers={'Referer': 'https://school.mos.ru/'}
        )
        async with response:
            response.raise_for_status()

        data = await self._poll_qr_login()
        if data.get('command') != 'showQRCode':
            raise QRLoginInitializationException('МЭШ не создал QR-код для входа')

        link = data.get('link')
        expires = data.get('expires')
        if not isinstance(link, str) or not isinstance(expires, int):
            raise QRLoginInitializationException('МЭШ вернул некорректные данные QR-кода')

        if return_type == 'link':
            return link, expires

        from segno import make_qr
        with BytesIO() as image:
            make_qr(link, error='m', boost_error=False).save(image, kind='png', scale=4)
            qr = image.getvalue()

        if return_type == 'link&qr':
            return link, qr, expires
        return qr, expires


    async def _poll_qr_login(self)-> dict:
        response = await self._send_request(
            'GET',
            'https://login.mos.ru/sps/login/methods/headless/qrCode/pull',
            use_auth=False,
            return_type='response',
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
            }
        )
        async with response:
            response.raise_for_status()
            return await response.json()


    async def wait_qr_login(
        self,
        expires: int,
        get_code: Callable[[], str | Awaitable[str]] | None = None,
        verification_method: Literal['flash_call', 'email', 'sms'] = 'flash_call',
        trust_browser: bool = False,
    )-> tuple[str, str]:
        """
        Дождаться подтверждения QR-входа и вернуть токены AUPD.

        Args:
            expires (`int`): Время истечения QR-кода в Unix time.
            get_code (`Callable | None`): Функция, возвращающая четырёхзначный
                или шестизначный код второго фактора. Может быть асинхронной.
            verification_method (`Literal`): Получить код звонком, по почте
                или по SMS.
            trust_browser (`bool`): Не запрашивать второй фактор при следующих
                входах из этой сессии.
        """
        try:
            method_name = {
                'flash_call': 'flashCall',
                'email': 'email',
                'sms': 'sms',
            }[verification_method]
        except KeyError:
            raise InvalidLoginParameterException(f'Неизвестный способ подтверждения: {verification_method}') from None

        while time() < expires:
            data = await self._poll_qr_login()
            command = data.get('command')

            if command == 'needComplete':
                break
            if command == 'needRefresh':
                raise QRLoginStateException(command, data.get('cause', 'unknown'))
            if command not in ('showQRCode', 'askForConfirm'):
                raise QRLoginStateException(command)

            await sleep(1)
        else:
            raise QRLoginExpiredException('Срок действия QR-кода истёк')

        cookie_jar = self._ensure_session().cookie_jar
        headers = {'Origin': 'https://login.mos.ru'}
        origin_cookie = cookie_jar.filter_cookies(
            URL('https://login.mos.ru/sps/login/methods/password')
        ).get('origin')
        if origin_cookie is not None and '|' in origin_cookie.value:
            headers['Referer'] = (
                'https://login.mos.ru/sps/login/methods/password?bo='
                f'{origin_cookie.value.split("|", 1)[1]}'
            )

        response = await self._send_request(
            'POST',
            'https://login.mos.ru/sps/login/methods/qrCode/complete',
            use_auth=False,
            return_type='response',
            data={},
            headers=headers
        )
        async with response:
            response.raise_for_status()

        if response.url.path.startswith('/sps/login/methods2/'):
            if get_code is None:
                raise TwoFactorRequiredException('Mos ID требует второй фактор. Передайте get_code в wait_qr_login() и повторите вход по новому QR-коду')

            back_url = response.url.query.get('bo')
            if back_url is None:
                raise QRLoginStateException('missing_back_url')

            if response.url.name != method_name:
                referer = str(response.url)
                response = await self._send_request(
                    'GET',
                    str(URL(f'https://login.mos.ru/sps/login/methods2/{method_name}').with_query(bo=back_url)),
                    use_auth=False,
                    return_type='response',
                    headers={'Referer': referer},
                )
                async with response:
                    response.raise_for_status()

            if verification_method == 'flash_call':
                referer = str(response.url)
                response = await self._send_request(
                    'POST',
                    str(URL('https://login.mos.ru/sps/login/method/flashCall').with_query(bo=back_url)),
                    use_auth=False,
                    return_type='response',
                    data={},
                    headers={
                        'Origin': 'https://login.mos.ru',
                        'Referer': referer,
                    },
                )
                async with response:
                    response.raise_for_status()

                code_field = 'code'
                code_length = 4
                code_url = URL('https://login.mos.ru/sps/login/method/flashCall/code').with_query(bo=back_url)
                code_paths = (
                    '/sps/login/method/flashCall',
                    '/sps/login/method/flashCall/code',
                )
            else:
                code_field = f'{method_name}-code'
                code_length = 6
                code_url = URL(f'https://login.mos.ru/sps/login/methods/{method_name}').with_query(bo=back_url)
                code_paths = (
                    f'/sps/login/methods2/{method_name}',
                    f'/sps/login/methods/{method_name}'
                )

            while response.url.path in code_paths:
                code = get_code()
                if isawaitable(code):
                    code = await code
                if (
                    not isinstance(code, str)
                    or len(code) != code_length
                    or not code.isdigit()
                ):
                    raise InvalidVerificationCodeException(f'Код подтверждения должен состоять из {code_length} цифр')

                referer = str(response.url)
                response = await self._send_request(
                    'POST',
                    str(code_url),
                    use_auth=False,
                    return_type='response',
                    data={code_field: code},
                    headers={
                        'Origin': 'https://login.mos.ru',
                        'Referer': referer,
                    },
                )
                async with response:
                    response.raise_for_status()

            if response.url.path == '/sps/login/ur/askToTrust':
                response = await self._send_request(
                    'POST',
                    str(response.url),
                    use_auth=False,
                    return_type='response',
                    data={'action': 'trust' if trust_browser else 'do_not_trust'},
                    headers={
                        'Origin': 'https://login.mos.ru',
                        'Referer': str(response.url),
                    },
                )
                async with response:
                    response.raise_for_status()

        token_cookie = None
        refresh_cookie = None
        for redirect_response in (*response.history, response):
            token_cookie = redirect_response.cookies.get('aupd_token') or token_cookie
            refresh_cookie = redirect_response.cookies.get('aupd_refresh_token') or refresh_cookie

        for cookie in cookie_jar:
            if cookie.key == 'aupd_token':
                token_cookie = cookie
            elif cookie.key == 'aupd_refresh_token':
                refresh_cookie = cookie

        if token_cookie is None or refresh_cookie is None:
            cookie_names = sorted(cookie.key for cookie in cookie_jar)
            raise LoginTokenMissingException(f'МЭШ не вернул токены после авторизации. Последний адрес: {response.url.with_query(None)}; cookies: {cookie_names}')

        aupd_token = token_cookie.value
        aupd_refresh_token = refresh_cookie.value
        self.aupd_token = aupd_token
        return aupd_token, aupd_refresh_token

    #TODO: Проверить
    async def get_detail_info(self):
        resp = await self._send_request('GET', 'https://school.mos.ru/v3/userinfo')
        return resp


    async def get(self)-> Family:
        """Получить информацию о себе, как о члене семьи.\n\n*При вызове автоматически вставляет `self.id`*"""
        resp = await self._send_request('GET', 'family/web/v1/profile')
        self.id = resp.get('profile')['id']
        return Family.model_validate(resp)


    async def get_base_info(self)-> UserInfo:
        """Получить базовую информацию о себе"""
        return UserInfo.model_validate(await self._send_request('GET', 'https://school.mos.ru/v1/oauth/userinfo'))

    #TODO: Проверить
    async def get_lessons(self, from_date: date, to_date: date):
        resp = await self._send_request('GET', f'family/web/v1/schedule/short?student_id={self.id}&dates=2026-09-13,2026-09-14,2026-09-15,2026-09-16')

    #TODO: Проверить
    async def get_schedule_events(self):
        return


    async def get_homework(self, from_date: date, to_date: date)-> list[Homework]:
        """
        Получить Д/З

        Args:
            from_date (`date`): От даты
            to_date (`date`): До даты
        """

        return [Homework.model_validate(homework) for homework in (await self._send_request('GET', f'family/web/v1/homeworks?from={from_date}&to={to_date}&student_id={self.id}'))['payload']]


    async def get_marks(self)-> list[SubjectMark]:
        """Получить оценки по всем предметам"""
        return [SubjectMark.model_validate(mark) for mark in (await self._send_request('GET', f'family/web/v1/subject_marks?student_id={self.id}'))['payload']]


    async def get_date_marks(self, from_date: date, to_date: date)-> list[Mark]:
        """
        Получить оценки по дате

        Args:
            from_date (`date`): От даты
            to_date (`date`): До даты
        """

        return [Mark.model_validate(mark) for mark in (await self._send_request('GET', f'family/web/v1/marks?student_id={self.id}&from={from_date}&to={to_date}'))['payload']]