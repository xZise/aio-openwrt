from typing import Any, Coroutine

from ._utils import (
    UbusInterface,
    WrapperBase,
    WrapperListBase,
    ubus_method,
    ubus_property,
)


class InterfaceEntry(WrapperBase):
    def __init__(self, client: UbusInterface, key: str) -> None:
        super().__init__(client)
        self._key = key

    @ubus_method()
    def status(self) -> Coroutine[Any, Any, dict]: ...


class Network(WrapperBase):
    class Device(WrapperBase):
        @ubus_method()
        def status(self, *, name: str | None = None) -> Coroutine[Any, Any, dict]: ...

    class Interface(WrapperListBase):
        def __getitem__(self, key: str) -> InterfaceEntry:
            return InterfaceEntry(self._client, key)

    device = ubus_property(Device)
    interface = ubus_property(Interface)
