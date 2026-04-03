from typing import Any, Coroutine

from ._utils import WrapperBase, ubus_method


class File(WrapperBase):
    @ubus_method("data")
    def read(self, *, path: str) -> Coroutine[Any, Any, str]: ...

    @ubus_method()
    def write(
        self, *, path: str, data: str, append: bool | None = None
    ) -> Coroutine[Any, Any, dict]: ...
