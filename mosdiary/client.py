from asyncio import sleep, TimeoutError 
from collections.abc import Awaitable, Callable, Sequence
from datetime import date
from html import unescape
from inspect import isawaitable
from io import BytesIO
from re import DOTALL, IGNORECASE, search
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
from pydantic import ValidationError
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
    TokenExpired,
    TwoFactorRequiredException,
    VerificationAttemptsExhaustedException,
    VerificationCodeExpiredException,
)
from .enums import ScheduleEventType
from .types.profile import UserInfo, Family, ProfileDeatail
from .types.homework import Homework
from .types.marks import Mark, SubjectMark
from .types.lessons import LessonDay
from .types.schedule_events import ScheduleEvent, parse_schedule_event


ScheduleEventInclude = Literal[
    'marks',
    'homework',
    'absence_reason_id',
    'health_status',
    'nonattendance_reason_id',
]
ALL_SCHEDULE_EVENT_INCLUDES: tuple[ScheduleEventInclude, ...] = (
    'marks',
    'homework',
    'absence_reason_id',
    'health_status',
    'nonattendance_reason_id',
)


class MOSDiaryClient:
    def __init__(self, aupd_token: str | None = None, timeout: float = 30, user_agent: str | None = None):
        """
        Клиент МЭШ

        Args:
            aupd_token (`str | None`): Токен (кука) авторизации
            timeout (`float`): Тайм-аут запросов в секундах.
            user_agent (`str | None`): User-Agent для запросов.

        Returns:
            None: Создаёт клиент без выполнения сетевых запросов.
        """
        
        self.aupd_token = aupd_token
        """Токен (кука) авторизации"""
        self.timeout = timeout
        self.user_agent = user_agent

        self.id: int | None = None
        """ID аккаунта МЭШ"""

        self.uid: str | None = None
        """UID персоны МЭШ"""

        self._session: ClientSession | None = None

    async def __aenter__(self) -> 'MOSDiaryClient':
        """Открыть HTTP-сессию клиента.

        Returns:
            MOSDiaryClient: Текущий экземпляр клиента.
        """
        self._ensure_session()
        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None,
    ) -> None:
        """Закрыть HTTP-сессию при выходе из контекстного менеджера.

        Returns:
            None
        """
        await self.close()

    def _ensure_session(self) -> ClientSession:
        """Вернуть действующую HTTP-сессию, создав её при необходимости.

        Returns:
            ClientSession: Открытая сессия `aiohttp`.
        """
        if self._session is None or self._session.closed:
            headers = {'User-Agent': self.user_agent} if self.user_agent is not None else None
            self._session = ClientSession(headers=headers)

        return self._session

    async def close(self) -> None:
        """Закрыть HTTP-сессию клиента.

        Returns:
            None
        """
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
        return_type: Literal['dict', 'response', 'bool', 'text'] = 'dict',
        use_auth: bool = True,
        **kwargs,
    ) -> dict | ClientResponse | bool | str:
        """Отправить HTTP-запрос к API МЭШ.

        Returns:
            dict | ClientResponse | bool | str: JSON-объект, необработанный
                ответ, признак успешного статуса или текст ответа - в
                зависимости от `return_type`.
        """
        if return_type not in ('dict', 'response', 'bool', 'text'):
            raise ValueError(f'Неизвестный тип возврата: {return_type}')

        url = (
            'https://school.mos.ru/api/' + endpoint
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

                if use_auth and response.status == 401:
                    response.release()
                    raise TokenExpired('Срок действия aupd_token истёк')

                if return_type == 'response':
                    return response

                async with response:
                    if return_type == 'bool':
                        return 200 <= response.status < 300

                    response.raise_for_status()
                    if return_type == 'text':
                        return await response.text()

                    data = await response.json()
                    if not isinstance(data, dict):
                        raise InvalidResponseException('Ответ API не является JSON-объектом')
                    return data
            except (ClientSSLError, ServerFingerprintMismatch, TokenExpired):
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


    async def logout(self)-> bool:
        """
        Завершает сессию, сбрасывает `self.aupd_token`, `self.id` и `self.uid`

        Returns:
            bool:
                Выполнен ли запрос успешно
        """
        success = await self._send_request('GET', 'https://school.mos.ru/v3/auth/logout', return_type='bool')
        if success:
            self.id = None
            self.uid = None
            self.aupd_token = None
            await self.close()
            return True
        return False


    async def refresh_session(self, role_id: int = 1)-> str:
        """
        Обновить `aupd_token` в текущей авторизованной HTTP-сессии.

        Требует cookies, созданные QR-входом в этом же экземпляре клиента;
        одного сохранённого `aupd_token` недостаточно.

        Args:
            role_id (`int = 1`): Ваш ID роли. 1 - ученик
        Returns:
            str:
                Токен авторизации
        """
        aupd_token = await self._send_request(
            'GET',
            'https://school.mos.ru/v2/token/refresh',
            return_type='text',
            params={'roleId': role_id, 'subsystem': 2},
            headers={
                'Accept': 'application/json, text/plain, */*',
                'CrossDomain': 'true',
                'Referer': 'https://school.mos.ru/auth/callback'
            },
        )
        self.aupd_token = aupd_token
        return aupd_token


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
            return_type='response',
            use_auth=False,
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
            return_type='response',
            use_auth=False,
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
        """Получить текущее состояние QR-входа.

        Returns:
            dict: Ответ протокола QR-авторизации МЭШ.
        """
        return await self._send_request(
            'GET',
            'https://login.mos.ru/sps/login/methods/headless/qrCode/pull',
            use_auth=False,
            headers={
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
            }
        )


    async def wait_qr_login(
        self,
        expires: int,
        get_code: Callable[[], str | Awaitable[str]] | None = None,
        verification_method: Literal['sms', 'email', 'flash_call'] = 'flash_call',
        trust_browser: bool = False,
    )-> tuple[str, str]:
        """
        Дождаться подтверждения QR-входа и вернуть токены AUPD.

        Args:
            expires (`int`): Время истечения QR-кода в Unix time.
            get_code (`Callable | None`): Функция, возвращающая код второго фактора. Может быть асинхронной.
            verification_method (`Literal`): Получить код по SMS, почте или звонком.
            trust_browser (`bool`): Не запрашивать второй фактор при следующих входах из этой сессии.

        Returns:
            tuple[str, str]: Пара `(aupd_token, aupd_refresh_token)`
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
            return_type='response',
            use_auth=False,
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
                    return_type='response',
                    use_auth=False,
                    headers={'Referer': referer},
                )
                async with response:
                    response.raise_for_status()

            if verification_method == 'flash_call':
                referer = str(response.url)
                response = await self._send_request(
                    'POST',
                    str(URL('https://login.mos.ru/sps/login/method/flashCall').with_query(bo=back_url)),
                    return_type='response',
                    use_auth=False,
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
                    return_type='response',
                    use_auth=False,
                    data={code_field: code},
                    headers={
                        'Origin': 'https://login.mos.ru',
                        'Referer': referer,
                    },
                )
                async with response:
                    response.raise_for_status()
                    if response.url.path in code_paths:
                        config = search(
                            r'var vrfCodeConf\s*=\s*(\{.*?\});',
                            await response.text(),
                            DOTALL,
                        )
                        if config is not None:
                            error = search(r'"error"\s*:\s*"([^"]+)"', config[1])
                            ttl = search(r'"ttl"\s*:\s*(\d+)', config[1])
                            attempts = search(r'"attemptsLeft"\s*:\s*(\d+)', config[1])
                            if (
                                (error is not None and search(r'ист[её]к|просроч', error[1], IGNORECASE))
                                or (ttl is not None and int(ttl[1]) == 0)
                            ):
                                raise VerificationCodeExpiredException('Срок действия кода подтверждения истёк')
                            if attempts is not None and int(attempts[1]) == 0:
                                raise VerificationAttemptsExhaustedException('Попытки ввода кода подтверждения исчерпаны')

            if response.url.path == '/sps/login/ur/askToTrust':
                response = await self._send_request(
                    'POST',
                    str(response.url),
                    return_type='response',
                    use_auth=False,
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


    async def get_detail_info(self)-> ProfileDeatail:
        """Получить подробную информацию о текущем пользователе.

        Returns:
            ProfileDeatail: Подробные данные профиля.
        """
        return ProfileDeatail.model_validate(await self._send_request('GET', 'https://school.mos.ru/v3/userinfo'))


    async def get_family_info(self)-> Family:
        """Получить информацию о себе, как о члене семьи.

        При вызове автоматически заполняет `self.id`.

        Returns:
            Family: Данные профиля, детей и представителей семьи.
        """
        resp = await self._send_request('GET', 'family/web/v1/profile')
        self.id = resp.get('profile')['id']
        return Family.model_validate(resp)


    async def get_base_info(self)-> UserInfo:
        """Получить базовую информацию о текущем пользователе.

        При вызове автоматически заполняет `self.uid`.

        Returns:
            UserInfo: Основные данные учётной записи МЭШ.
        """
        info = UserInfo.model_validate(await self._send_request('GET', 'https://school.mos.ru/v1/oauth/userinfo'))
        self.uid = info.person_uid
        return info


    async def get_lessons(self, dates: list[date])-> list[LessonDay]:
        """Получить расписание уроков на указанные даты.

        Returns:
            list[LessonDay]: Расписание, сгруппированное по дням.
        """
        if self.id is None:
            await self.get_family_info()
        response = await self._send_request(
            'GET', 'family/web/v1/schedule/short',
            params={
                'student_id': self.id,
                'dates': ','.join(lesson_date.isoformat() for lesson_date in dates)
            }
        )
        return [LessonDay.model_validate(day) for day in response['payload']]


    async def get_schedule_events(
        self,
        from_date: date,
        to_date: date,
        include: Sequence[ScheduleEventInclude] | None = None,
        source_types: Sequence[ScheduleEventType] | None = None,
    )-> list[ScheduleEvent]:
        """Получить события расписания за указанный период.

        По умолчанию в `include` и `source_types` передаются все
        поддерживаемые значения.

        Returns:
            list[ScheduleEvent]: Уроки и другие поддерживаемые события периода.
        """
        if self.id is None:
            await self.get_family_info()
        if self.uid is None:
            await self.get_base_info()

        selected_includes = ALL_SCHEDULE_EVENT_INCLUDES if include is None else include
        selected_source_types = tuple(ScheduleEventType) if source_types is None else source_types

        response = await self._send_request(
            'GET', 'eventcalendar/v1/api/events',
            params={
                'person_ids': self.uid,
                'begin_date': from_date.isoformat(),
                'end_date': to_date.isoformat(),
                'expand': ','.join(selected_includes),
                'source_types': ','.join(selected_source_types),
            },
            headers={
                'Profile-Id': str(self.id),
                'X-Mes-Role': 'student',
                'X-mes-subsystem': 'familyweb'
            }
        )
        try:
            schedule_events = response['response']
            if not isinstance(schedule_events, list):
                raise TypeError('Поле response не является списком')
            return [parse_schedule_event(schedule_event) for schedule_event in schedule_events]
        except (KeyError, TypeError, ValidationError, ValueError) as error:
            raise InvalidResponseException(
                'МЭШ вернул некорректный список событий расписания'
            ) from error


    async def get_homework(self, from_date: date, to_date: date)-> list[Homework]:
        """
        Получить Д/З

        Args:
            from_date (`date`): От даты
            to_date (`date`): До даты

        Returns:
            list[Homework]: Домашние задания за указанный период.
        """
        if self.id is None:
            await self.get_family_info()

        return [Homework.model_validate(homework) for homework in (await self._send_request('GET', f'family/web/v1/homeworks?from={from_date}&to={to_date}&student_id={self.id}'))['payload']]


    async def get_marks(self)-> list[SubjectMark]:
        """Получить оценки по всем предметам.

        Returns:
            list[SubjectMark]: Сводные оценки и учебные периоды по предметам.
        """
        if self.id is None:
            await self.get_family_info()
        return [SubjectMark.model_validate(mark) for mark in (await self._send_request('GET', f'family/web/v1/subject_marks?student_id={self.id}'))['payload']]


    async def get_date_marks(self, from_date: date, to_date: date)-> list[Mark]:
        """
        Получить оценки по дате

        Args:
            from_date (`date`): От даты
            to_date (`date`): До даты

        Returns:
            list[Mark]: Оценки, выставленные за указанный период.
        """
        if self.id is None:
            await self.get_family_info()
        return [Mark.model_validate(mark) for mark in (await self._send_request('GET', f'family/web/v1/marks?student_id={self.id}&from={from_date}&to={to_date}'))['payload']]
