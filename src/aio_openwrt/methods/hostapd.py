from typing import Any, Coroutine

from ._utils import UbusInterface, WrapperBase, ubus_method


class Hostapd(WrapperBase):
    class Entry(WrapperBase):
        def __init__(self, client: UbusInterface, key: str) -> None:
            super().__init__(client)
            self._key = key

        @ubus_method
        def get_clients(self) -> Coroutine[Any, Any, dict]: ...

    def __getitem__(self, key) -> "Hostapd.Entry":
        return Hostapd.Entry(self._client, key)
