from asyncio import sleep, TimeoutError 
from types import TracebackType
from typing import Literal, cast

from aiohttp import (
    ClientConnectionError,
    ClientResponse,
    ClientSession,
    ClientSSLError,
    ServerFingerprintMismatch,
)

from .models.profile import User
from .models.schemas import UserSchema


class MOSDiaryClient:
    BASE_URL = 'https://school.mos.ru/api/'

    def __init__(self, audp_token: str):
        """
        Клиент МЭШ

        Args:
            audp_token (`str`): Токен (кука) авторизации
        """
        
        self.audp_token = audp_token

        self.id: int = None
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
            self._session = ClientSession()

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
        **kwargs,
    ) -> ClientResponse:
        url = (
            self.BASE_URL + endpoint
            if not endpoint.startswith('http')
            else endpoint
        )
        cookies = dict(kwargs.pop('cookies', {}) or {})
        cookies['aupd_token'] = self.audp_token

        retry_number = 0

        while True:
            try:
                return await self._ensure_session().request(
                    method,
                    url,
                    cookies=cookies,
                    **kwargs,
                )
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


    async def get(self)-> User:
        """Получение данных об аккаунте"""

        resp: User = await self._send_request('GET', 'ej/acl/v1/sessions', json={'auth_token': self.audp_token})
        data = cast(UserSchema, await resp.json())
        
        self.id = resp.id

        return User.from_schema(data)
        

    async def get_family(self):

        resp = await self._send_request('GET', 'family/web/v1/profile')


    async def get_info(self):
        """Альтернативный вариант получения информации о себе"""

        resp = await self._send_request('GET', 'https://school.mos.ru/v3/userinfo')