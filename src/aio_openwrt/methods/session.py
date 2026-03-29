from typing import Any, Coroutine

from ._utils import UbusInterface, ubus_method


class Session:
    def __init__(self, client: UbusInterface) -> None:
        self._client = client

    @ubus_method
    def login(self, *, username: str, password: str) -> Coroutine[Any, Any, dict]: ...

    @ubus_method
    def access(self) -> Coroutine[Any, Any, dict]: ...

    @ubus_method
    def destroy(self) -> Coroutine[Any, Any, dict]: ...
