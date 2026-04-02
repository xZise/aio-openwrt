"""Tests for aio_openwrt.methods._utils — ubus_method() decorator."""

from typing import Any, Coroutine
from unittest.mock import AsyncMock, MagicMock

from aio_openwrt.methods._utils import (
    UbusInterface,
    WrapperBase,
    ubus_method,
    ubus_property,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_client(return_value: dict | None = None) -> AsyncMock:
    """Return a mock UbusInterface whose call() resolves immediately."""
    client = MagicMock(spec=UbusInterface)
    client.call = AsyncMock(return_value=return_value or {})
    return client


# ---------------------------------------------------------------------------
# Path derivation from __qualname__
# ---------------------------------------------------------------------------


class TestUbusMethodPathDerivation:
    async def test_simple_path(self):
        class System(WrapperBase):
            @ubus_method
            def board(self) -> Coroutine[None, Any, Any]: ...

        client = make_client()
        await System(client).board()
        client.call.assert_called_once_with("system", "board", {})

    async def test_nested_path(self):
        class Network(WrapperBase):
            class Device(WrapperBase):
                @ubus_method
                def status(self) -> Coroutine[None, Any, Any]: ...

            device = ubus_property(Device)

        client = make_client()
        await Network(client).device.status()
        client.call.assert_called_once_with("network.device", "status", {})

    async def test_path_is_lowercase(self):
        class MyService(WrapperBase):
            @ubus_method
            def MyMethod(self) -> Coroutine[None, Any, Any]: ...

        client = make_client()
        await MyService(client).MyMethod()
        path_used = client.call.call_args[0][0]
        assert path_used == path_used.lower()

    async def test_key_substituted_into_path(self):
        """When self._key is set, it should be appended to the parent path."""

        class Network(WrapperBase):
            class Entry(WrapperBase):
                @ubus_method
                def status(self) -> Coroutine[None, Any, Any]: ...

            def __getitem__(self, key):
                return Network.Entry(self, key)

        client = make_client()
        await Network(client)["wan"].status()
        client.call.assert_called_once_with("network.wan", "status", {})


# ---------------------------------------------------------------------------
# kwargs filtering
# ---------------------------------------------------------------------------


class TestUbusMethodKwargsFiltering:
    async def test_none_kwargs_filtered(self):
        class Svc(WrapperBase):
            @ubus_method
            def query(
                self, *, name: str | None = None, value: str | None = None
            ) -> Coroutine[None, Any, Any]: ...

        client = make_client()
        await Svc(client).query(name="lan", value=None)
        client.call.assert_called_once_with("svc", "query", {"name": "lan"})

    async def test_all_kwargs_none_sends_empty_dict(self):
        class Svc(WrapperBase):
            @ubus_method
            def query(
                self, *, name: str | None = None
            ) -> Coroutine[None, Any, Any]: ...

        client = make_client()
        await Svc(client).query(name=None)
        client.call.assert_called_once_with("svc", "query", {})

    async def test_all_kwargs_present(self):
        class Svc(WrapperBase):
            @ubus_method
            def query(self, *, a: str, b: str) -> Coroutine[None, Any, Any]: ...

        client = make_client()
        await Svc(client).query(a="x", b="y")
        client.call.assert_called_once_with("svc", "query", {"a": "x", "b": "y"})


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------


class TestUbusMethodReturnValue:
    async def test_returns_client_call_result(self):
        class Svc(WrapperBase):
            @ubus_method
            def info(self) -> Coroutine[None, Any, Any]: ...

        expected = {"key": "value"}
        client = make_client(return_value=expected)
        result = await Svc(client).info()
        assert result == expected
