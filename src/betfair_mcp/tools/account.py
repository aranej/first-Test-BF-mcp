"""
Account-related MCP tools for Betfair API.

This module provides tools for querying account information such as
balance, funds, and account details.
"""

import asyncio
import logging
from typing import Any, Dict

from betfairlightweight.exceptions import BetfairError

from ..rate_limiter import get_rate_limiter
from ..error_handling import classify_betfair_error, log_api_error

logger = logging.getLogger(__name__)


async def get_account_balance(client: Any) -> Dict[str, Any]:
    """
    Get the current account balance and available funds.

    This tool retrieves the user's account balance, including available
    to bet balance, exposure, and other fund-related information.

    Args:
        client: The betfairlightweight API client (from session manager)

    Returns:
        Dict containing:
            - available_to_bet: Amount available to place bets
            - exposure: Current exposure from open bets
            - retained_commission: Commission retained
            - exposure_limit: Maximum allowed exposure
            - discount_rate: Current discount rate
            - wallet: Wallet name (UK/AUS)

    Raises:
        BetfairError: If the API request fails
    """
    rate_limiter = get_rate_limiter()

    try:
        logger.info("Fetching account balance")

        # Apply rate limiting
        await rate_limiter.acquire_general()

        # Call the sync API in a thread pool
        funds = await asyncio.to_thread(client.account.get_account_funds)

        result = {
            "available_to_bet": float(funds.available_to_bet_balance),
            "exposure": float(funds.exposure),
            "retained_commission": float(funds.retained_commission),
            "exposure_limit": float(funds.exposure_limit),
            "discount_rate": float(funds.discount_rate),
            "wallet": funds.wallet,
        }

        logger.info(f"Account balance retrieved: £{result['available_to_bet']:.2f} available")
        return result

    except BetfairError as e:
        classified_error = classify_betfair_error(e)
        log_api_error(classified_error, "get_account_balance")
        raise classified_error
    except Exception as e:
        logger.error(f"Unexpected error fetching account balance: {e}")
        raise


async def get_account_details(client: Any) -> Dict[str, Any]:
    """
    Get account details including personal information and settings.

    Args:
        client: The betfairlightweight API client

    Returns:
        Dict containing account details:
            - first_name: User's first name
            - last_name: User's last name
            - currency_code: Account currency (e.g., GBP, EUR)
            - locale_code: User's locale
            - timezone: Account timezone
            - discount_rate: Betfair Points discount rate
            - points_balance: Current Betfair Points balance

    Raises:
        BetfairError: If the API request fails
    """
    rate_limiter = get_rate_limiter()

    try:
        logger.info("Fetching account details")

        # Apply rate limiting
        await rate_limiter.acquire_general()

        # Call the sync API in a thread pool
        details = await asyncio.to_thread(client.account.get_account_details)

        result = {
            "first_name": details.first_name,
            "last_name": details.last_name,
            "currency_code": details.currency_code,
            "locale_code": details.locale_code,
            "timezone": details.timezone,
            "discount_rate": float(details.discount_rate),
            "points_balance": int(details.points_balance),
        }

        logger.info(f"Account details retrieved for {result['first_name']} {result['last_name']}")
        return result

    except BetfairError as e:
        classified_error = classify_betfair_error(e)
        log_api_error(classified_error, "get_account_details")
        raise classified_error
    except Exception as e:
        logger.error(f"Unexpected error fetching account details: {e}")
        raise
