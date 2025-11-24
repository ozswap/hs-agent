"""Retry policy for LLM invocations with exponential backoff and prompt variation.

This module provides a reusable retry policy that handles:
- Exponential backoff for transient failures
- Prompt variation on retries (adds line breaks)
- Comprehensive logging of retry attempts
- Graceful degradation after max retries
"""

import asyncio
from typing import Any, List, Optional

from hs_agent.utils.logger import get_logger

logger = get_logger("hs_agent.policies.retry")


class RetryPolicy:
    """Policy for retrying LLM invocations with exponential backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        prompt_variation: bool = True
    ):
        """Initialize retry policy.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            initial_delay: Initial delay between retries in seconds (default: 1.0)
            prompt_variation: Whether to add line breaks to prompts on retry (default: True)
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.prompt_variation = prompt_variation

    async def invoke_with_retry(
        self,
        model: Any,
        messages: List,
    ) -> Optional[Any]:
        """Invoke LLM with retry logic for None results.

        Args:
            model: The LLM model to invoke
            messages: Messages to send to the model

        Returns:
            LLM response, or None if all retries exhausted

        Note:
            Returns None if all retries are exhausted. Caller should handle this
            by returning a "000000" (insufficient information) response.

            On retries, adds line breaks to the prompt for variation if enabled.
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Add prompt variation on retries by appending line breaks
                # This gives the LLM a slightly different context which may help
                messages_to_send = messages
                if attempt > 0 and self.prompt_variation:
                    # Create a modified copy with line breaks added to the last message
                    messages_to_send = messages[:-1] + [
                        type(messages[-1])(content=messages[-1].content + "\n" * attempt)
                    ]
                    logger.debug(f"🔄 Added {attempt} line break(s) to prompt for variation")

                result = await model.ainvoke(messages_to_send)

                if result is not None:
                    return result

                # Log None result and retry
                logger.warning(f"⚠️  LLM returned None (attempt {attempt + 1}/{self.max_retries})")

                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s, etc.
                    delay = self.initial_delay * (2 ** attempt)
                    logger.info(f"🔄 Retrying in {delay}s...")
                    await asyncio.sleep(delay)

            except Exception as e:
                last_exception = e
                logger.warning(f"⚠️  LLM invocation error (attempt {attempt + 1}/{self.max_retries}): {e}")

                if attempt < self.max_retries - 1:
                    delay = self.initial_delay * (2 ** attempt)
                    logger.info(f"🔄 Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        # All retries exhausted - return None to signal caller to use "000000" code
        error_context = f" (last error: {last_exception})" if last_exception else ""
        logger.error(f"❌ LLM failed after {self.max_retries} attempts{error_context} - will return 000000 (insufficient information)")
        return None
