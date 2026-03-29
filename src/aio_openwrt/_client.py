from typing import Any

import aiohttp

from . import methods
from .methods._utils import UbusInterface, ubus_property

EMPTY_SESSION = "00000000000000000000000000000000"


class Ubus(UbusInterface):
    def __init__(self, url: str, user: str, password: str, timeout: float = 15) -> None:
        self.url = url
        self.user = user
        self.password = password
        self.id = 1
        self.session_id: str | None = None
        self.ubus_access: dict[str, list[str]] = {}
        self._timeout = aiohttp.ClientTimeout(timeout)
        self._http_session: aiohttp.ClientSession | None = None

    @property
    def _client(self) -> "Ubus":
        return self

    async def close(self):
        if self._http_session:
            await self._http_session.close()
            self._http_session = None

    async def __aenter__(self) -> "Ubus":
        self._http_session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def call(
        self, path: str, method: str, message: dict[str, Any] | None = None
    ) -> dict:
        if not self._http_session:
            self._http_session = aiohttp.ClientSession(timeout=self._timeout)

        json = {
            "jsonrpc": "2.0",
            "id": self.id,
            "method": "call",
            "params": [self.session_id or EMPTY_SESSION, path, method, message or {}],
        }
        self.id += 1
        async with self._http_session.post(self.url, json=json) as resp:
            response_json: dict = await resp.json()

        error = response_json.get("error")
        if error:
            raw_error_message = error.get("message", "")
            if "code" in error:
                error_code = f"Code: {error['code']}"
                if raw_error_message:
                    error_message = f"{raw_error_message} ({error_code})"
                else:
                    error_message = error_code
            elif raw_error_message:
                error_message = raw_error_message
            else:
                error_message = "Unknown error without code"

            if raw_error_message == "Access denied":
                raise PermissionError(error_message)
            raise ConnectionError(error_message)

        result = response_json["result"]
        status_code = result[0]
        match status_code:
            case 0:
                return result[1]
            case 2:
                raise ValueError("Invalid arguments")
            case 3:
                raise ValueError("Invalid method")
            case 6:
                raise ValueError("Invalid credentials")
            case _:
                raise ValueError(f"Unknown status code {status_code}")

    async def login(self):
        self.session_id: str | None = None
        result = await self.session.login(username=self.user, password=self.password)
        self.session_id = result.get("ubus_rpc_session")
        self.ubus_access = result.get("acls", {}).get("ubus", {})

    network = ubus_property(methods.Network)
    session = ubus_property(methods.Session)
    system = ubus_property(methods.System)
