"""Error handling and retry logic for Betfair API operations.

This module provides robust error handling and automatic retry mechanisms
for common Betfair API errors, including:
- INVALID_SESSION_TOKEN: Automatic session refresh
- TOO_MANY_REQUESTS: Exponential backoff retry
- TOO_MUCH_DATA: Request splitting guidance
- THROTTLED: Temporary ban handling
"""

import asyncio
import logging
from typing import Any, Callable, TypeVar

from betfairlightweight.exceptions import BetfairError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    RetryError,
)

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')


class BetfairAPIError(Exception):
    """Base exception for Betfair API errors."""
    pass


class SessionExpiredError(BetfairAPIError):
    """Exception raised when the session token is invalid or expired."""
    pass


class RateLimitError(BetfairAPIError):
    """Exception raised when rate limits are exceeded."""
    pass


class DataLimitError(BetfairAPIError):
    """Exception raised when request contains too much data."""
    pass


class ThrottledError(BetfairAPIError):
    """Exception raised when temporarily banned due to excessive requests."""
    pass


def classify_betfair_error(error: BetfairError) -> Exception:
    """Classify a Betfair error into specific exception types.

    Args:
        error: The BetfairError to classify

    Returns:
        A more specific exception type based on the error message
    """
    error_msg = str(error).upper()

    if "INVALID_SESSION_TOKEN" in error_msg or "SESSION" in error_msg:
        return SessionExpiredError(f"Session expired or invalid: {error}")

    if "TOO_MANY_REQUESTS" in error_msg:
        return RateLimitError(f"Rate limit exceeded: {error}")

    if "TOO_MUCH_DATA" in error_msg:
        return DataLimitError(f"Request contains too much data: {error}")

    if "THROTTLED" in error_msg or "TEMPORARY_BAN" in error_msg:
        return ThrottledError(f"Temporarily throttled or banned: {error}")

    # Return original error if not classified
    return error


async def retry_with_session_refresh(
    operation: Callable[..., T],
    session_manager: Any,
    *args: Any,
    **kwargs: Any
) -> T:
    """Execute an operation with automatic session refresh on INVALID_SESSION_TOKEN.

    This wrapper catches session expiry errors and automatically refreshes
    the session before retrying the operation.

    Args:
        operation: The async operation to execute
        session_manager: The BetfairSessionManager instance
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        The result of the operation

    Raises:
        BetfairAPIError: If the operation fails after session refresh
    """
    max_attempts = 2  # Try once, then retry after refresh

    for attempt in range(max_attempts):
        try:
            # Ensure session is active
            await asyncio.to_thread(session_manager.ensure_logged_in)

            # Execute the operation
            return await operation(*args, **kwargs)

        except BetfairError as e:
            classified_error = classify_betfair_error(e)

            if isinstance(classified_error, SessionExpiredError):
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"Session expired on attempt {attempt + 1}, refreshing session..."
                    )
                    # Force logout and re-login
                    await asyncio.to_thread(session_manager.logout)
                    await asyncio.to_thread(session_manager.ensure_logged_in)
                    logger.info("Session refreshed successfully")
                    continue
                else:
                    logger.error("Session refresh failed after maximum attempts")
                    raise classified_error
            else:
                # Not a session error, re-raise
                raise classified_error

    # Should never reach here, but just in case
    raise BetfairAPIError("Operation failed after all retry attempts")


def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
):
    """Create a retry decorator for Betfair API operations.

    This decorator handles transient errors with exponential backoff,
    specifically for rate limiting errors.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        A tenacity retry decorator
    """
    return retry(
        retry=retry_if_exception_type(RateLimitError),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


async def execute_with_retry(
    operation: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    **kwargs: Any
) -> T:
    """Execute an operation with automatic retry for rate limit errors.

    Uses exponential backoff for retries when encountering TOO_MANY_REQUESTS.

    Args:
        operation: The async operation to execute
        *args: Positional arguments for the operation
        max_attempts: Maximum number of retry attempts
        **kwargs: Keyword arguments for the operation

    Returns:
        The result of the operation

    Raises:
        BetfairAPIError: If the operation fails after all retries
    """
    retry_decorator = create_retry_decorator(max_attempts=max_attempts)

    async def wrapped_operation():
        try:
            return await operation(*args, **kwargs)
        except BetfairError as e:
            classified_error = classify_betfair_error(e)
            logger.error(f"Betfair API error: {classified_error}")
            raise classified_error

    try:
        return await retry_decorator(wrapped_operation)()
    except RetryError as e:
        logger.error(f"Operation failed after {max_attempts} attempts: {e}")
        raise BetfairAPIError(f"Operation failed after {max_attempts} retries") from e


def log_api_error(error: Exception, operation: str, context: dict = None) -> None:
    """Log Betfair API errors with context information.

    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        context: Additional context information (optional)
    """
    context_str = f" | Context: {context}" if context else ""
    logger.error(
        f"Betfair API error in {operation}: {type(error).__name__}: {error}{context_str}"
    )


async def handle_data_limit_error(
    market_ids: list[str],
    max_markets_per_request: int = 50
) -> list[list[str]]:
    """Split a large market ID list into smaller chunks to avoid TOO_MUCH_DATA.

    Args:
        market_ids: List of market IDs
        max_markets_per_request: Maximum markets per request chunk

    Returns:
        List of market ID chunks
    """
    chunks = []
    for i in range(0, len(market_ids), max_markets_per_request):
        chunk = market_ids[i:i + max_markets_per_request]
        chunks.append(chunk)

    if len(chunks) > 1:
        logger.warning(
            f"Split {len(market_ids)} markets into {len(chunks)} chunks "
            f"to avoid data limit errors"
        )

    return chunks
