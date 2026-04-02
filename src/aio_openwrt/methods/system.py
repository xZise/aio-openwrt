from typing import Any, Coroutine

from ._utils import WrapperBase, ubus_method


class System(WrapperBase):
    @ubus_method()
    def board(self) -> Coroutine[Any, Any, dict]: ...

    @ubus_method()
    def info(self) -> Coroutine[Any, Any, dict]: ...
