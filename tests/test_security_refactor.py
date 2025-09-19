"""Tests for security refactoring."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from amazon_ads_mcp.auth.oauth_state_store import OAuthStateStore
from amazon_ads_mcp.auth.secure_token_store import SecureTokenStore
from amazon_ads_mcp.exceptions import (
    OAuthStateError,
    TimeoutError,
    APIError,
    ToolExecutionError,
)
from amazon_ads_mcp.utils.async_compat import (
    CompatibleEventLoopPolicy,
    ensure_event_loop,
    run_async_in_sync,
    AsyncContextManager,
)
from amazon_ads_mcp.utils.response_wrapper import ResponseWrapper
from amazon_ads_mcp.utils.sampling_wrapper import SamplingHandlerWrapper


class TestOAuthStateStore:
    """Test OAuth state store functionality."""

    def test_generate_state(self):
        """Test state generation with HMAC signature."""
        store = OAuthStateStore(secret_key="test_secret")
        state = store.generate_state(
            auth_url="https://example.com/auth",
            user_agent="TestAgent/1.0",
            ip_address="192.168.1.1"
        )

        assert state is not None
        assert "." in state  # Should have signature separator
        assert len(state) > 40  # Should be reasonably long

    def test_validate_state_success(self):
        """Test successful state validation."""
        store = OAuthStateStore(secret_key="test_secret")
        state = store.generate_state(
            auth_url="https://example.com/auth",
            user_agent="TestAgent/1.0"
        )

        is_valid, error = store.validate_state(state, user_agent="TestAgent/1.0")
        assert is_valid is True
        assert error is None

    def test_validate_state_invalid(self):
        """Test invalid state validation."""
        store = OAuthStateStore(secret_key="test_secret")

        # Test with completely invalid state
        is_valid, error = store.validate_state("invalid_state")
        assert is_valid is False
        assert error == "Invalid or expired state"

    def test_validate_state_tampered(self):
        """Test tampered state detection."""
        store = OAuthStateStore(secret_key="test_secret")
        state = store.generate_state(auth_url="https://example.com/auth")

        # Tamper with the signature
        base, sig = state.rsplit(".", 1)
        tampered_state = f"{base}.tampered_signature"

        is_valid, error = store.validate_state(tampered_state)
        assert is_valid is False
        # Tampering the signature changes the state token; store lookup fails first
        assert error in ("Invalid or expired state", "Invalid state signature")

    def test_validate_state_reuse_prevention(self):
        """Test that states cannot be reused."""
        store = OAuthStateStore(secret_key="test_secret")
        state = store.generate_state(auth_url="https://example.com/auth")

        # First validation should succeed
        is_valid, error = store.validate_state(state)
        assert is_valid is True

        # Second validation should fail
        is_valid, error = store.validate_state(state)
        assert is_valid is False
        assert "already used" in error

    def test_state_expiration(self):
        """Test state expiration."""
        store = OAuthStateStore(secret_key="test_secret")
        state = store.generate_state(
            auth_url="https://example.com/auth",
            ttl_minutes=0  # Expire immediately
        )

        # Force expiration
        entry = store._memory_store[state]
        entry.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

        is_valid, error = store.validate_state(state)
        assert is_valid is False
        assert "expired" in error.lower()

    def test_persistence(self, tmp_path):
        """Test state persistence to file."""
        store_path = tmp_path / "oauth_states.json"
        store1 = OAuthStateStore(secret_key="test_secret", store_path=store_path)

        state = store1.generate_state(auth_url="https://example.com/auth")

        # Create new store instance
        store2 = OAuthStateStore(secret_key="test_secret", store_path=store_path)

        # Should be able to validate state from first store
        is_valid, error = store2.validate_state(state)
        assert is_valid is True


class TestSecureTokenStore:
    """Test secure token storage."""

    def test_store_and_retrieve(self, tmp_path):
        """Test storing and retrieving tokens."""
        store = SecureTokenStore(
            storage_path=tmp_path / "tokens.enc",
            encryption_key="test_password"
        )

        store.store_token(
            token_id="test_token",
            token_value="secret_value_123",
            token_type="refresh",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )

        token = store.get_token("test_token")
        assert token is not None
        assert token["value"] == "secret_value_123"
        assert token["type"] == "refresh"

    def test_encryption(self, tmp_path):
        """Test that tokens are encrypted on disk."""
        storage_path = tmp_path / "tokens.enc"
        store = SecureTokenStore(
            storage_path=storage_path,
            encryption_key="test_password"
        )

        store.store_token(
            token_id="sensitive_token",
            token_value="super_secret_value",
            token_type="access"
        )

        # Read raw file content
        with open(storage_path, "rb") as f:
            raw_content = f.read()

        # Should not contain the plaintext token
        assert b"super_secret_value" not in raw_content
        assert b"sensitive_token" not in raw_content  # ID should also be encrypted

    def test_expiration(self, tmp_path):
        """Test token expiration."""
        store = SecureTokenStore(
            storage_path=tmp_path / "tokens.enc",
            encryption_key="test_password"
        )

        # Store expired token
        store.store_token(
            token_id="expired_token",
            token_value="old_value",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )

        # Should not retrieve expired token
        token = store.get_token("expired_token")
        assert token is None

    def test_persistence_across_instances(self, tmp_path):
        """Test token persistence across store instances."""
        storage_path = tmp_path / "tokens.enc"

        # Store token with first instance
        store1 = SecureTokenStore(
            storage_path=storage_path,
            encryption_key="test_password"
        )
        store1.store_token(
            token_id="persistent_token",
            token_value="persistent_value"
        )

        # Retrieve with second instance
        store2 = SecureTokenStore(
            storage_path=storage_path,
            encryption_key="test_password"
        )
        token = store2.get_token("persistent_token")
        assert token is not None
        assert token["value"] == "persistent_value"

    def test_wrong_key_fails(self, tmp_path):
        """Test that wrong encryption key fails gracefully."""
        storage_path = tmp_path / "tokens.enc"

        # Store with one key
        store1 = SecureTokenStore(
            storage_path=storage_path,
            encryption_key="correct_password"
        )
        store1.store_token(token_id="test", token_value="value")

        # Try to load with wrong key
        store2 = SecureTokenStore(
            storage_path=storage_path,
            encryption_key="wrong_password"
        )

        # Should start fresh, not crash
        token = store2.get_token("test")
        assert token is None


class TestAsyncCompatibility:
    """Test async compatibility utilities."""

    def test_compatible_event_loop_policy(self):
        """Test compatible event loop policy."""
        policy = CompatibleEventLoopPolicy()
        asyncio.set_event_loop_policy(policy)

        # Should create loop when needed
        loop = asyncio.get_event_loop()
        assert loop is not None
        assert not loop.is_closed()

        # Clean up
        loop.close()
        asyncio.set_event_loop(None)
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    def test_ensure_event_loop(self):
        """Test ensure_event_loop function."""
        # Clear any existing loop
        try:
            loop = asyncio.get_event_loop()
            loop.close()
        except RuntimeError:
            pass
        asyncio.set_event_loop(None)

        # Should create new loop
        loop = ensure_event_loop()
        assert loop is not None
        assert not loop.is_closed()

        # Clean up
        loop.close()
        asyncio.set_event_loop(None)

    def test_run_async_in_sync(self):
        """Test running async function from sync context."""
        async def async_func(value):
            await asyncio.sleep(0.01)
            return value * 2

        result = run_async_in_sync(async_func, 21)
        assert result == 42

    def test_async_context_manager(self):
        """Test AsyncContextManager."""
        async def async_task():
            await asyncio.sleep(0.01)
            return "completed"

        with AsyncContextManager() as ctx:
            result = ctx.run(async_task())
            assert result == "completed"


class TestResponseWrapper:
    """Test response wrapper functionality."""

    def test_response_wrapper_basic(self):
        """Test basic response wrapper functionality."""
        import httpx

        # Create mock response
        response = httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"key": "value"}'
        )

        wrapper = ResponseWrapper(response)
        assert wrapper.status_code == 200
        assert wrapper.json() == {"key": "value"}

    def test_response_wrapper_modification(self):
        """Test response content modification."""
        import httpx

        response = httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"old": "value"}'
        )

        wrapper = ResponseWrapper(response)
        wrapper.set_json({"new": "value"})

        assert wrapper.json() == {"new": "value"}
        assert wrapper.content == b'{"new": "value"}'

    def test_response_wrapper_modify_json(self):
        """Test JSON modification with function."""
        import httpx

        response = httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"count": 10}'
        )

        wrapper = ResponseWrapper(response)
        wrapper.modify_json(lambda data: {**data, "count": data["count"] * 2})

        assert wrapper.json() == {"count": 20}


class TestStructuredExceptions:
    """Test structured exception classes."""

    def test_oauth_state_error(self):
        """Test OAuthStateError."""
        error = OAuthStateError("Invalid state")
        assert error.code == "OAUTH_STATE_ERROR"
        assert error.message == "Invalid state"

        error_dict = error.to_dict()
        assert error_dict["error"] == "OAUTH_STATE_ERROR"
        assert error_dict["message"] == "Invalid state"

    def test_timeout_error(self):
        """Test TimeoutError."""
        error = TimeoutError("Request timed out", operation="list_campaigns")
        assert error.code == "TIMEOUT_ERROR"
        assert error.details["operation"] == "list_campaigns"

    def test_api_error(self):
        """Test APIError."""
        error = APIError(
            "API request failed",
            status_code=404,
            response_body="Not found"
        )
        assert error.code == "API_ERROR"
        assert error.status_code == 404
        assert error.details["status_code"] == 404
        assert error.details["response_body"] == "Not found"

    def test_tool_execution_error(self):
        """Test ToolExecutionError."""
        original = ValueError("Original error")
        error = ToolExecutionError(
            "Tool failed",
            tool_name="test_tool",
            original_error=original
        )
        assert error.code == "TOOL_EXECUTION_ERROR"
        assert error.tool_name == "test_tool"
        assert error.details["tool"] == "test_tool"
        assert "ValueError" in error.details["error_type"]


class TestSamplingWrapper:
    """Test sampling wrapper functionality."""

    @pytest.mark.asyncio
    async def test_sampling_wrapper_with_handler(self):
        """Test sampling wrapper with configured handler."""
        # Create mock handler
        async def mock_handler(messages, params, context):
            return MagicMock(content="sampled response")

        wrapper = SamplingHandlerWrapper()
        wrapper.set_handler(mock_handler)

        assert wrapper.has_handler() is True

        # Mock context that doesn't support sampling
        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("does not support sampling"))
        mock_ctx.request_context = {}

        result = await wrapper.sample(
            messages="test message",
            ctx=mock_ctx
        )

        assert result == "sampled response"

    @pytest.mark.asyncio
    async def test_sampling_wrapper_no_handler(self):
        """Test sampling wrapper without handler."""
        wrapper = SamplingHandlerWrapper()
        assert wrapper.has_handler() is False

        mock_ctx = MagicMock()
        mock_ctx.sample = AsyncMock(side_effect=Exception("does not support sampling"))

        with pytest.raises(Exception) as exc_info:
            await wrapper.sample(
                messages="test message",
                ctx=mock_ctx
            )

        assert "no server-side fallback is configured" in str(exc_info.value)
