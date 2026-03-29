from typing import Any, Coroutine

from ._utils import UbusInterface, WrapperBase, WrapperListBase, ubus_method


class Entry(WrapperBase):
    def __init__(self, parent: UbusInterface | WrapperBase, key: str) -> None:
        super().__init__(parent, key)

    @ubus_method
    def get_clients(self) -> Coroutine[Any, Any, dict]: ...


class Hostapd(WrapperListBase[Entry]):
    def __getitem__(self, key) -> Entry:
        return Entry(self, key)
