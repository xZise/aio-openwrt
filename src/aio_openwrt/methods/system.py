from typing import Any, Coroutine

from ._utils import UbusInterface, ubus_method


class System:
    def __init__(self, client: UbusInterface) -> None:
        self._client = client

    @ubus_method
    def board(self) -> Coroutine[Any, Any, dict]: ...

    @ubus_method
    def info(self) -> Coroutine[Any, Any, dict]: ...
