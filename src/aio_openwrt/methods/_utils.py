import functools
from typing import Any, Coroutine, Protocol, Type, TypeVar


class UbusInterface(Protocol):
    async def call(
        self, path: str, method: str, message: dict[str, Any] | None = None
    ) -> dict: ...


def ubus_method(func):
    @functools.wraps(func)
    def wrapper(self, **kwargs) -> Coroutine[Any, Any, dict]:
        if not hasattr(func, "_path"):
            # "Network.Device.status" -> "network.device"
            path, _ = func.__qualname__.rsplit(".", 1)
            if hasattr(self, "_key"):
                path, _ = path.rsplit(".", 1)
                path += "." + self._key
            func._path = path.lower()

        params = {key: value for (key, value) in kwargs.items() if value is not None}

        return self._client.call(func._path, func.__name__, params)

    return wrapper


class _ClientConstructible(Protocol):
    def __init__(self, client: UbusInterface) -> None: ...


T = TypeVar("T", bound=_ClientConstructible)


def ubus_property(cls: Type[T]) -> T:
    def getter(self):
        return cls(self._client)

    return property(getter)  # pyright: ignore[reportReturnType]
