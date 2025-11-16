"""
Rate limiting module for Betfair API compliance.

This module provides rate limiting to ensure compliance with Betfair API limits:
- Login: Maximum 100 requests per minute
- listMarketBook: Maximum 5 requests per second per market ID
- General API calls: Managed to prevent TOO_MANY_REQUESTS errors
"""

import asyncio
import logging
from typing import Dict, Optional

from aiolimiter import AsyncLimiter

logger = logging.getLogger(__name__)


class BetfairRateLimiter:
    """
    Rate limiter for Betfair API operations.

    Implements rate limiting according to Betfair's documented limits:
    - Login operations: 100 per minute (hard limit)
    - Market data per market: 5 requests per second
    - General operations: Conservative limits to prevent throttling
    """

    def __init__(self):
        """Initialize rate limiters for different operation types."""
        # Login rate limiter: 100 requests per minute
        # Using 90/minute to leave safety margin
        self.login_limiter = AsyncLimiter(max_rate=90, time_period=60)

        # General API rate limiter: Conservative 20 requests per second
        # Betfair doesn't have a hard limit, but this prevents TOO_MANY_REQUESTS
        self.general_limiter = AsyncLimiter(max_rate=20, time_period=1)

        # Per-market rate limiters: 5 requests per second per market ID
        # Dictionary to store limiters for each market ID
        self._market_limiters: Dict[str, AsyncLimiter] = {}
        self._market_limiters_lock = asyncio.Lock()

    async def acquire_login(self) -> None:
        """
        Acquire permission to perform a login operation.

        This enforces the 100 requests/minute limit for login operations.
        Blocks until permission is granted.
        """
        logger.debug("Acquiring login rate limit token")
        async with self.login_limiter:
            logger.debug("Login rate limit token acquired")

    async def acquire_general(self) -> None:
        """
        Acquire permission to perform a general API operation.

        This enforces a conservative rate limit to prevent TOO_MANY_REQUESTS.
        Blocks until permission is granted.
        """
        logger.debug("Acquiring general API rate limit token")
        async with self.general_limiter:
            logger.debug("General API rate limit token acquired")

    async def acquire_market(self, market_id: str) -> None:
        """
        Acquire permission to access a specific market.

        This enforces the 5 requests/second limit per market ID.
        Blocks until permission is granted.

        Args:
            market_id: The market ID to rate limit
        """
        # Get or create limiter for this market ID
        async with self._market_limiters_lock:
            if market_id not in self._market_limiters:
                # 5 requests per second per market
                self._market_limiters[market_id] = AsyncLimiter(max_rate=5, time_period=1)
                logger.debug(f"Created rate limiter for market {market_id}")

            limiter = self._market_limiters[market_id]

        logger.debug(f"Acquiring market rate limit token for {market_id}")
        async with limiter:
            logger.debug(f"Market rate limit token acquired for {market_id}")

    async def acquire_markets(self, market_ids: list[str]) -> None:
        """
        Acquire permission to access multiple markets.

        This ensures rate limiting is applied to all requested markets.
        For efficiency, we only rate limit on the general limiter when
        requesting multiple markets (as Betfair allows batch requests).

        Args:
            market_ids: List of market IDs to rate limit
        """
        # For batch requests, we use general limiter instead of per-market
        # as the API allows requesting multiple markets in one call
        await self.acquire_general()
        logger.debug(f"Rate limit acquired for {len(market_ids)} markets in batch")

    async def cleanup_old_limiters(self, max_limiters: int = 1000) -> None:
        """
        Cleanup old market limiters to prevent memory leaks.

        Removes market limiters when the total count exceeds max_limiters,
        keeping only the most recently used ones.

        Args:
            max_limiters: Maximum number of market limiters to keep
        """
        async with self._market_limiters_lock:
            if len(self._market_limiters) > max_limiters:
                # Remove oldest limiters (simple FIFO cleanup)
                to_remove = len(self._market_limiters) - max_limiters
                for market_id in list(self._market_limiters.keys())[:to_remove]:
                    del self._market_limiters[market_id]
                    logger.debug(f"Removed old rate limiter for market {market_id}")

                logger.info(f"Cleaned up {to_remove} old market rate limiters")


# Global rate limiter instance
_rate_limiter: Optional[BetfairRateLimiter] = None


def get_rate_limiter() -> BetfairRateLimiter:
    """
    Get the global rate limiter instance.

    Returns:
        BetfairRateLimiter: The global rate limiter

    Raises:
        RuntimeError: If rate limiter is not initialized
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = BetfairRateLimiter()
        logger.info("Rate limiter initialized")
    return _rate_limiter


async def cleanup_rate_limiter_task():
    """
    Background task to periodically cleanup old market limiters.

    Runs every hour to prevent memory leaks from accumulating market limiters.
    """
    rate_limiter = get_rate_limiter()

    while True:
        try:
            # Wait 1 hour
            await asyncio.sleep(3600)

            # Cleanup old limiters
            await rate_limiter.cleanup_old_limiters()
            logger.debug("Rate limiter cleanup completed")

        except Exception as e:
            logger.error(f"Error in rate limiter cleanup task: {e}")
