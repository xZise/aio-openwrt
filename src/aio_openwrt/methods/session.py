from typing import Any, Coroutine

from ._utils import WrapperBase, ubus_method


class Session(WrapperBase):
    @ubus_method()
    def login(self, *, username: str, password: str) -> Coroutine[Any, Any, dict]: ...

    @ubus_method()
    def access(self) -> Coroutine[Any, Any, dict]: ...

    @ubus_method()
    def destroy(self) -> Coroutine[Any, Any, dict]: ...
