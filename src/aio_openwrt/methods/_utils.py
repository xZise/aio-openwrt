from __future__ import annotations

import functools
from abc import abstractmethod
from typing import Any, Coroutine, Generic, Iterable, Protocol, Type, TypeVar


class UbusInterface(Protocol):
    async def call(
        self, path: str, method: str, message: dict[str, Any] | None = None
    ) -> dict: ...

    async def list(self, path: str) -> dict: ...


class WrapperBase:
    def __init__(
        self, parent: UbusInterface | WrapperBase, name: str | None = None
    ) -> None:
        if not name:
            name = self.__class__.__name__
        name = name.lower()
        if isinstance(parent, WrapperBase):
            self._client = parent._client
            self._path = f"{parent._path}.{name}"
        else:
            self._client = parent
            self._path = name

    # def list_children(self, filter: str = "*") -> Coroutine[dict, Any, Any]:
    #     path = f"{self.__class__.__qualname__}.{filter}"
    #     return self._client.list(path)

    # def list(self) -> Coroutine[dict, Any, Any]:
    #     return self._client.list(self.__class__.__qualname__)


TElement = TypeVar("TElement", bound=WrapperBase)


class WrapperListBase(WrapperBase, Generic[TElement]):
    @abstractmethod
    def __getitem__(self, key: str) -> TElement: ...

    async def list_children(self, filter: str = "*") -> Iterable[TElement]:
        path = f"{self._path}.{filter}".lower()
        list_result: dict[str, Any] = await self._client.list(path)
        # The key is the complete path, so we need to strip the beginning
        return (self[key[len(self._path) + 1 :]] for key in list_result.keys())


def ubus_method(func):
    @functools.wraps(func)
    def wrapper(self: WrapperBase, **kwargs) -> Coroutine[Any, Any, dict]:
        params = {key: value for (key, value) in kwargs.items() if value is not None}
        return self._client.call(self._path, func.__name__, params)

    return wrapper


class _ClientConstructible(Protocol):
    def __init__(
        self, parent: UbusInterface | WrapperBase, name: str | None = None
    ) -> None: ...


T = TypeVar("T", bound=_ClientConstructible)


def ubus_property(cls: Type[T]) -> T:
    def getter(self):
        return cls(self)

    return property(getter)  # pyright: ignore[reportReturnType]
