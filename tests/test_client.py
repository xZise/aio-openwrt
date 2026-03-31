"""Tests for aio_openwrt._client (Ubus)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aio_openwrt import Ubus
from aio_openwrt.methods import Network, Session, System


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ubus():
    return Ubus("http://router/ubus", "root", "password")


def make_http_response(payload: dict):
    """Return a mock that behaves like an aiohttp response context manager."""
    resp = AsyncMock()
    resp.json = AsyncMock(return_value=payload)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


def patch_post(payload: dict):
    """Patch aiohttp.ClientSession.post to return *payload*."""
    return patch(
        "aiohttp.ClientSession.post",
        return_value=make_http_response(payload),
    )


def ok_result(*result_items) -> dict:
    """Wrap items in a minimal successful JSON-RPC response."""
    return {"jsonrpc": "2.0", "id": 1, "result": list(result_items)}


# ---------------------------------------------------------------------------
# _api_call — error handling
# ---------------------------------------------------------------------------

class TestApiCallErrors:
    # @pytest.mark.asyncio
    async def test_access_denied_raises_permission_error(self, ubus):
        payload = {"error": {"message": "Access denied", "code": -32002}}
        with patch_post(payload):
            with pytest.raises(PermissionError, match="Access denied"):
                await ubus._api_call("call", "system", "board")

    # @pytest.mark.asyncio
    async def test_error_with_message_and_code(self, ubus):
        payload = {"error": {"message": "Not found", "code": 404}}
        with patch_post(payload):
            with pytest.raises(ConnectionError, match=r"Not found.*404"):
                await ubus._api_call("call", "system", "board")

    # @pytest.mark.asyncio
    async def test_error_with_code_only(self, ubus):
        payload = {"error": {"code": 500}}
        with patch_post(payload):
            with pytest.raises(ConnectionError, match="Code: 500"):
                await ubus._api_call("call", "system", "board")

    # @pytest.mark.asyncio
    async def test_error_with_message_only(self, ubus):
        payload = {"error": {"message": "Something went wrong"}}
        with patch_post(payload):
            with pytest.raises(ConnectionError, match="Something went wrong"):
                await ubus._api_call("call", "system", "board")

    # @pytest.mark.asyncio
    async def test_empty_error_dict(self, ubus):
        payload = {"error": {}}
        with patch_post(payload):
            with pytest.raises(ConnectionError, match="Unknown error without code"):
                await ubus._api_call("call", "system", "board")

    # @pytest.mark.asyncio
    async def test_no_error_returns_result(self, ubus):
        payload = {"result": {"board": "ath79"}}
        with patch_post(payload):
            result = await ubus._api_call("list", "system")
        assert result == {"board": "ath79"}


# ---------------------------------------------------------------------------
# call() — status code dispatch
# ---------------------------------------------------------------------------

class TestCallStatusCodes:
    # @pytest.mark.asyncio
    async def test_status_0_returns_data(self, ubus):
        with patch_post(ok_result(0, {"hostname": "OpenWrt"})):
            result = await ubus.call("system", "board")
        assert result == {"hostname": "OpenWrt"}

    # @pytest.mark.asyncio
    async def test_status_2_invalid_arguments(self, ubus):
        with patch_post(ok_result(2)):
            with pytest.raises(ValueError, match="Invalid arguments"):
                await ubus.call("system", "board")

    # @pytest.mark.asyncio
    async def test_status_3_invalid_method(self, ubus):
        with patch_post(ok_result(3)):
            with pytest.raises(ValueError, match="Invalid method"):
                await ubus.call("system", "board")

    # @pytest.mark.asyncio
    async def test_status_6_invalid_credentials(self, ubus):
        with patch_post(ok_result(6)):
            with pytest.raises(ValueError, match="Invalid credentials"):
                await ubus.call("system", "board")

    # @pytest.mark.asyncio
    async def test_unknown_status_code(self, ubus):
        with patch_post(ok_result(99)):
            with pytest.raises(ValueError, match="Unknown status code 99"):
                await ubus.call("system", "board")


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------

class TestLogin:
    # @pytest.mark.asyncio
    async def test_login_sets_session_id(self, ubus):
        session_id = "abc123"
        with patch_post(ok_result(0, {"ubus_rpc_session": session_id, "acls": {}})):
            await ubus.login()
        assert ubus.session_id == session_id

    # @pytest.mark.asyncio
    async def test_login_sets_ubus_access(self, ubus):
        acls = {"network": ["status"], "system": ["board"]}
        with patch_post(ok_result(0, {"ubus_rpc_session": "01234567890123456789012345678901", "acls": {"ubus": acls}})):
            await ubus.login()
        assert ubus.ubus_access == acls

    # @pytest.mark.asyncio
    async def test_login_clears_session_before_call(self, ubus):
        """session_id must be None while the login call is in-flight so that
        EMPTY_SESSION is used instead of a stale session token."""
        ubus.session_id = "stale-token"
        captured: list[str | None] = []

        original_api_call = ubus._api_call

        async def capturing_api_call(*args, **kwargs):
            captured.append(ubus.session_id)
            return await original_api_call(*args, **kwargs)

        with patch_post(ok_result(0, {"ubus_rpc_session": "new", "acls": {}})):
            with patch.object(ubus, "_api_call", side_effect=capturing_api_call):
                await ubus.login()

        assert captured[0] is None

    # @pytest.mark.asyncio
    async def test_login_missing_keys_does_not_crash(self, ubus):
        with patch_post(ok_result(0, {})):
            await ubus.login()
        assert ubus.session_id is None
        assert ubus.ubus_access == {}


# ---------------------------------------------------------------------------
# Session lifecycle / context manager
# ---------------------------------------------------------------------------

class TestSessionLifecycle:
    # @pytest.mark.asyncio
    async def test_aenter_creates_http_session(self, ubus):
        async with ubus:
            assert ubus._http_session is not None

    # @pytest.mark.asyncio
    async def test_aexit_closes_http_session(self, ubus):
        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value = mock_session
            async with ubus:
                session = ubus._http_session
        assert ubus._http_session is None
        session.close.assert_called_once()

    # @pytest.mark.asyncio
    async def test_close_is_idempotent(self, ubus):
        async with ubus:
            pass
        # Second close should not raise
        await ubus.close()
        assert ubus._http_session is None

    # @pytest.mark.asyncio
    async def test_lazy_session_creation(self, ubus):
        """A session should be created automatically on the first call."""
        assert ubus._http_session is None
        with patch_post({"result": {}}):
            await ubus._api_call("list", "system")
        assert ubus._http_session is not None
        await ubus.close()


# ---------------------------------------------------------------------------
# ubus_property
# ---------------------------------------------------------------------------

class TestUbusProperty:
    def test_network_returns_network_instance(self, ubus):
        assert isinstance(ubus.network, Network)

    def test_session_returns_session_instance(self, ubus):
        assert isinstance(ubus.session, Session)

    def test_system_returns_system_instance(self, ubus):
        assert isinstance(ubus.system, System)

    def test_property_not_cached(self, ubus):
        """Each access creates a fresh wrapper instance."""
        assert ubus.network is not ubus.network

    def test_wrapper_shares_client(self, ubus):
        """The wrapper's _client must be the Ubus instance itself."""
        assert ubus.network._client is ubus