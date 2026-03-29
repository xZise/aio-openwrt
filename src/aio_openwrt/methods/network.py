from typing import Any, Coroutine

from ._utils import UbusInterface, ubus_method, ubus_property


class Network:
    class Device:
        def __init__(self, client: UbusInterface) -> None:
            self._client = client

        @ubus_method
        def status(self, *, name: str | None = None) -> Coroutine[Any, Any, dict]: ...

    class Interface:
        class Entry:
            def __init__(self, client: UbusInterface, key: str) -> None:
                self._client = client
                self._key = key

            @ubus_method
            def status(self) -> Coroutine[Any, Any, dict]: ...

        def __init__(self, client: UbusInterface) -> None:
            self._client = client

        def __getitem__(self, key) -> "Network.Interface.Entry":
            return Network.Interface.Entry(self._client, key)

    def __init__(self, client: UbusInterface) -> None:
        self._client = client

    device = ubus_property(Device)
    interface = ubus_property(Interface)
