"""Tests for RetryPolicy class.

Tests cover:
- Successful invocation without retry
- Retry behavior on None results
- Retry behavior on exceptions
- Exponential backoff timing
- Prompt variation on retries
- Max retries exhaustion
- Custom configuration
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hs_agent.utils.retry import RetryPolicy


class TestRetryPolicyInit:
    """Tests for RetryPolicy initialization."""

    def test_default_values(self):
        """Test default initialization values."""
        policy = RetryPolicy()

        assert policy.max_retries == 3
        assert policy.initial_delay == 1.0
        assert policy.prompt_variation is True

    def test_custom_max_retries(self):
        """Test custom max_retries parameter."""
        policy = RetryPolicy(max_retries=5)

        assert policy.max_retries == 5

    def test_custom_initial_delay(self):
        """Test custom initial_delay parameter."""
        policy = RetryPolicy(initial_delay=2.5)

        assert policy.initial_delay == 2.5

    def test_prompt_variation_disabled(self):
        """Test prompt_variation can be disabled."""
        policy = RetryPolicy(prompt_variation=False)

        assert policy.prompt_variation is False


class TestRetryPolicyInvokeWithRetry:
    """Tests for invoke_with_retry method."""

    @pytest.mark.asyncio
    async def test_successful_invocation_no_retry(self):
        """Test successful invocation returns immediately without retry."""
        policy = RetryPolicy()
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value={"result": "success"})
        messages = [MagicMock(content="test message")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"result": "success"}
        mock_model.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_on_none_result(self):
        """Test retry when model returns None."""
        policy = RetryPolicy(max_retries=3, initial_delay=0.01)
        mock_model = MagicMock()
        # First two calls return None, third returns result
        mock_model.ainvoke = AsyncMock(side_effect=[None, None, {"result": "success"}])
        messages = [MagicMock(content="test message")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"result": "success"}
        assert mock_model.ainvoke.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_on_exception(self):
        """Test retry when model raises exception."""
        policy = RetryPolicy(max_retries=3, initial_delay=0.01)
        mock_model = MagicMock()
        # First two calls raise exception, third succeeds
        mock_model.ainvoke = AsyncMock(
            side_effect=[
                Exception("API error"),
                Exception("API error"),
                {"result": "success"},
            ]
        )
        messages = [MagicMock(content="test message")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"result": "success"}
        assert mock_model.ainvoke.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exhausted_returns_none(self):
        """Test that None is returned after max retries exhausted."""
        policy = RetryPolicy(max_retries=3, initial_delay=0.01)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=None)
        messages = [MagicMock(content="test message")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result is None
        assert mock_model.ainvoke.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exhausted_on_exceptions(self):
        """Test that None is returned after max retries exhausted due to exceptions."""
        policy = RetryPolicy(max_retries=2, initial_delay=0.01)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=Exception("Persistent error"))
        messages = [MagicMock(content="test message")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result is None
        assert mock_model.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test that backoff delays are exponential (1s, 2s, 4s by default)."""
        policy = RetryPolicy(max_retries=3, initial_delay=1.0)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=None)
        messages = [MagicMock(content="test message")]

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch.object(asyncio, "sleep", mock_sleep):
            await policy.invoke_with_retry(mock_model, messages)

        # After 3 attempts, we should have 2 sleep calls (no sleep after last attempt)
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == 1.0  # initial_delay * 2^0
        assert sleep_calls[1] == 2.0  # initial_delay * 2^1

    @pytest.mark.asyncio
    async def test_exponential_backoff_custom_initial_delay(self):
        """Test exponential backoff with custom initial delay."""
        policy = RetryPolicy(max_retries=4, initial_delay=0.5)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=None)
        messages = [MagicMock(content="test message")]

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch.object(asyncio, "sleep", mock_sleep):
            await policy.invoke_with_retry(mock_model, messages)

        # 4 attempts = 3 sleep calls
        assert len(sleep_calls) == 3
        assert sleep_calls[0] == 0.5  # 0.5 * 2^0
        assert sleep_calls[1] == 1.0  # 0.5 * 2^1
        assert sleep_calls[2] == 2.0  # 0.5 * 2^2

    @pytest.mark.asyncio
    async def test_prompt_variation_adds_newlines(self):
        """Test that prompt variation adds line breaks on retry."""
        policy = RetryPolicy(max_retries=3, initial_delay=0.01, prompt_variation=True)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=[None, None, {"result": "success"}])

        # Create a proper message mock with content attribute
        original_message = MagicMock()
        original_message.content = "test message"
        messages = [original_message]

        await policy.invoke_with_retry(mock_model, messages)

        # Check the calls to ainvoke
        calls = mock_model.ainvoke.call_args_list

        # First call should have original message
        first_call_messages = calls[0][0][0]
        assert first_call_messages[0].content == "test message"

        # Second call should have 1 newline added
        second_call_messages = calls[1][0][0]
        assert second_call_messages[0].content == "test message\n"

        # Third call should have 2 newlines added
        third_call_messages = calls[2][0][0]
        assert third_call_messages[0].content == "test message\n\n"

    @pytest.mark.asyncio
    async def test_prompt_variation_disabled(self):
        """Test that prompt variation is skipped when disabled."""
        policy = RetryPolicy(max_retries=3, initial_delay=0.01, prompt_variation=False)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=[None, None, {"result": "success"}])

        original_message = MagicMock()
        original_message.content = "test message"
        messages = [original_message]

        await policy.invoke_with_retry(mock_model, messages)

        # All calls should have the same original messages (no variation)
        calls = mock_model.ainvoke.call_args_list
        for call in calls:
            call_messages = call[0][0]
            # With variation disabled, the original messages list is passed unchanged
            assert call_messages is messages

    @pytest.mark.asyncio
    async def test_preserves_multiple_messages(self):
        """Test that multiple messages are preserved with only last modified."""
        policy = RetryPolicy(max_retries=2, initial_delay=0.01, prompt_variation=True)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=[None, {"result": "success"}])

        system_msg = MagicMock()
        system_msg.content = "system prompt"
        user_msg = MagicMock()
        user_msg.content = "user prompt"
        messages = [system_msg, user_msg]

        await policy.invoke_with_retry(mock_model, messages)

        # First call: original messages
        first_call = mock_model.ainvoke.call_args_list[0][0][0]
        assert first_call[0].content == "system prompt"
        assert first_call[1].content == "user prompt"

        # Second call: system message unchanged, user message has newline
        second_call = mock_model.ainvoke.call_args_list[1][0][0]
        assert second_call[0].content == "system prompt"  # Unchanged
        assert second_call[1].content == "user prompt\n"  # Modified

    @pytest.mark.asyncio
    async def test_single_retry_success(self):
        """Test that a single retry succeeds."""
        policy = RetryPolicy(max_retries=2, initial_delay=0.01)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=[None, {"selected_code": "847130"}])
        messages = [MagicMock(content="test")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"selected_code": "847130"}
        assert mock_model.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_mixed_exceptions_and_none(self):
        """Test handling of mixed exceptions and None results."""
        policy = RetryPolicy(max_retries=4, initial_delay=0.01)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(
            side_effect=[
                Exception("Network error"),
                None,
                Exception("Timeout"),
                {"result": "finally"},
            ]
        )
        messages = [MagicMock(content="test")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"result": "finally"}
        assert mock_model.ainvoke.call_count == 4


class TestRetryPolicyEdgeCases:
    """Edge case tests for RetryPolicy."""

    @pytest.mark.asyncio
    async def test_max_retries_one(self):
        """Test with max_retries=1 (no retries)."""
        policy = RetryPolicy(max_retries=1)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=None)
        messages = [MagicMock(content="test")]

        result = await policy.invoke_with_retry(mock_model, messages)

        assert result is None
        assert mock_model.ainvoke.call_count == 1

    @pytest.mark.asyncio
    async def test_empty_messages_list(self):
        """Test with empty messages list."""
        policy = RetryPolicy(max_retries=1)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value={"result": "ok"})

        result = await policy.invoke_with_retry(mock_model, [])

        assert result == {"result": "ok"}
        mock_model.ainvoke.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_zero_initial_delay(self):
        """Test with zero initial delay."""
        policy = RetryPolicy(max_retries=2, initial_delay=0.0)
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(side_effect=[None, {"result": "ok"}])
        messages = [MagicMock(content="test")]

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch.object(asyncio, "sleep", mock_sleep):
            result = await policy.invoke_with_retry(mock_model, messages)

        assert result == {"result": "ok"}
        # With 0 initial delay, sleep should still be called with 0
        assert sleep_calls == [0.0]
