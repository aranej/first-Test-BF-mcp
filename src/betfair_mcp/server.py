"""
Betfair MCP Server - Main server implementation.

This module initializes the FastMCP server and registers all available
tools for interacting with the Betfair Exchange API.
"""

import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from .auth import BetfairSessionManager, create_session_manager_from_env
from .formatters import (
    format_account_balance,
    format_account_details,
    format_competitions,
    format_event_types,
    format_events,
    format_market_catalogue,
    format_market_prices,
)
from .models import (
    GetMarketPricesInput,
    ListCompetitionsInput,
    ListEventsInput,
    ListMarketCatalogueInput,
)
from .rate_limiter import get_rate_limiter, cleanup_rate_limiter_task
from .tools import account, events, markets

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="betfair",
    version="0.1.0",
    description="MCP server for Betfair Exchange API - provides read-only access to betting markets, odds, and account information",
)

# Global session manager
session_manager: Optional[BetfairSessionManager] = None


@mcp.on_startup
async def startup():
    """
    Initialize the Betfair session on server startup.

    This lifecycle hook is called when the MCP server starts up.
    It creates the session manager and logs in to Betfair.
    """
    global session_manager
    logger.info("Starting Betfair MCP server...")

    try:
        # Initialize rate limiter
        rate_limiter = get_rate_limiter()
        logger.info("Rate limiter initialized")

        # Create session manager from environment variables
        session_manager = create_session_manager_from_env()
        logger.info("Session manager created")

        # Login to Betfair (in a thread pool since it's sync)
        await asyncio.to_thread(session_manager.ensure_logged_in)
        logger.info("Successfully logged in to Betfair")

        # Start background tasks
        asyncio.create_task(keep_alive_loop())
        logger.info("Keep-alive loop started")

        asyncio.create_task(cleanup_rate_limiter_task())
        logger.info("Rate limiter cleanup task started")

    except Exception as e:
        logger.error(f"Failed to initialize Betfair session: {e}")
        raise


@mcp.on_shutdown
async def shutdown():
    """
    Cleanup the Betfair session on server shutdown.

    This lifecycle hook is called when the MCP server shuts down.
    It logs out from Betfair to cleanup the session.
    """
    global session_manager
    logger.info("Shutting down Betfair MCP server...")

    if session_manager:
        try:
            await asyncio.to_thread(session_manager.logout)
            logger.info("Successfully logged out from Betfair")
        except Exception as e:
            logger.error(f"Error during logout: {e}")


async def keep_alive_loop():
    """
    Background task to send periodic keep-alive requests.

    This prevents the Betfair session from timing out due to inactivity.
    Keep-alive is sent every 30 minutes with rate limiting.
    """
    rate_limiter = get_rate_limiter()

    while True:
        try:
            # Wait 30 minutes
            await asyncio.sleep(30 * 60)

            if session_manager:
                logger.debug("Sending keep-alive request")
                # Rate limit keep-alive (counts as login operation)
                await rate_limiter.acquire_login()
                await asyncio.to_thread(session_manager.keep_alive)
        except Exception as e:
            logger.error(f"Error in keep-alive loop: {e}")


def get_client():
    """
    Get the authenticated Betfair API client.

    Returns:
        The betfairlightweight API client

    Raises:
        RuntimeError: If session manager is not initialized
    """
    if session_manager is None:
        raise RuntimeError("Session manager not initialized")
    return session_manager.get_client()


# ============================================================================
# ACCOUNT TOOLS
# ============================================================================

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_get_account_balance() -> dict:
    """
    Get current account balance and available funds.

    Returns account balance information including available to bet balance,
    exposure, and other fund-related details.

    Returns:
        dict: Account balance information with keys:
            - summary: Markdown-formatted summary (str)
            - data: Raw account balance data (dict)
                - available_to_bet: Amount available to place bets (float)
                - exposure: Current exposure from open bets (float)
                - retained_commission: Commission retained (float)
                - exposure_limit: Maximum allowed exposure (float)
                - discount_rate: Current discount rate (float)
                - wallet: Wallet name, e.g., UK or AUS (str)
    """
    client = get_client()
    data = await account.get_account_balance(client)
    return {
        "summary": format_account_balance(data),
        "data": data,
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_get_account_details() -> dict:
    """
    Get account details including personal information and settings.

    Returns account information such as name, currency, timezone,
    and Betfair Points balance.

    Returns:
        dict: Account details with keys:
            - summary: Markdown-formatted summary (str)
            - data: Raw account details (dict)
                - first_name: User's first name (str)
                - last_name: User's last name (str)
                - currency_code: Account currency, e.g., GBP, EUR (str)
                - locale_code: User's locale (str)
                - timezone: Account timezone (str)
                - discount_rate: Betfair Points discount rate (float)
                - points_balance: Current Betfair Points balance (int)
    """
    client = get_client()
    data = await account.get_account_details(client)
    return {
        "summary": format_account_details(data),
        "data": data,
    }


# ============================================================================
# EVENT TOOLS
# ============================================================================

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_list_event_types() -> dict:
    """
    List all available event types (sports).

    Returns all available sports on Betfair, such as Football (Soccer),
    Horse Racing, Tennis, Cricket, etc.

    Returns:
        dict: Response with keys:
            - summary: Markdown-formatted table (str)
            - data: List of event types (list[dict])
                - event_type_id: Unique identifier for the sport (str)
                - event_type_name: Human-readable name, e.g., "Soccer" (str)
                - market_count: Number of markets available (int)
            - count: Total number of event types (int)
    """
    client = get_client()
    data = await events.list_event_types(client)
    return {
        "summary": format_event_types(data),
        "data": data,
        "count": len(data),
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_list_events(params: ListEventsInput) -> dict:
    """
    List sporting events with optional filtering.

    Returns events that match the specified criteria. Can be filtered
    by sport, competition, or text search.

    Args:
        params: Filter parameters with fields:
            - event_type_id: Sport ID to filter by, e.g., "1" for Soccer (optional)
            - competition_id: Competition ID to filter by (optional)
            - text_query: Text to search in event names (optional)

    Returns:
        dict: Response with keys:
            - summary: Markdown-formatted summary (str)
            - data: List of events (list[dict])
                - event_id: Unique event identifier (str)
                - event_name: Event name, e.g., "Man Utd vs Liverpool" (str)
                - event_timezone: Event timezone (str)
                - open_date: When the event starts in ISO format (str)
                - country_code: Country code for the event (str)
                - market_count: Number of markets for this event (int)
            - count: Total number of events (int)
    """
    client = get_client()
    data = await events.list_events(
        client,
        event_type_id=params.event_type_id,
        competition_id=params.competition_id,
        text_query=params.text_query,
    )
    return {
        "summary": format_events(data),
        "data": data,
        "count": len(data),
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_list_competitions(params: ListCompetitionsInput) -> dict:
    """
    List competitions (leagues/tournaments).

    Returns available competitions/leagues for a given sport,
    such as Premier League, Champions League, etc.

    Args:
        params: Filter parameters with fields:
            - event_type_id: Sport ID to filter by, e.g., "1" for Soccer (optional)

    Returns:
        dict: Response with keys:
            - summary: Markdown-formatted table (str)
            - data: List of competitions (list[dict])
                - competition_id: Unique competition identifier (str)
                - competition_name: Competition name, e.g., "Premier League" (str)
                - market_count: Number of markets in this competition (int)
            - count: Total number of competitions (int)
    """
    client = get_client()
    data = await events.list_competitions(
        client,
        event_type_id=params.event_type_id,
    )
    return {
        "summary": format_competitions(data),
        "data": data,
        "count": len(data),
    }


# ============================================================================
# MARKET TOOLS
# ============================================================================

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def betfair_list_market_catalogue(params: ListMarketCatalogueInput) -> dict:
    """
    List available betting markets with optional filtering.

    Returns detailed information about betting markets, including
    market names, types, and available runners/selections.

    Args:
        params: Filter parameters with fields:
            - event_id: Event ID to filter by (optional)
            - event_type_id: Sport ID to filter by (optional)
            - competition_id: Competition ID to filter by (optional)
            - market_type_codes: Market types, e.g., ["MATCH_ODDS", "OVER_UNDER_25"] (optional)
            - max_results: Maximum markets to return, default 100, max 1000 (optional)

    Returns:
        dict: Response with keys:
            - summary: Markdown-formatted summary (str)
            - data: List of markets (list[dict])
                - market_id: Unique market identifier (str)
                - market_name: Market name, e.g., "Match Odds" (str)
                - market_type: Market type code, e.g., "MATCH_ODDS" (str)
                - event_name: Name of the parent event (str)
                - competition_name: Name of the competition (str)
                - event_id: ID of the parent event (str)
                - total_matched: Total amount matched on this market (float)
                - runners: List of runners/selections (list[dict])
                    - selection_id: Unique runner identifier (str)
                    - runner_name: Runner name, e.g., "Manchester United" (str)
                    - sort_priority: Display order priority (int)
            - count: Total number of markets (int)
    """
    client = get_client()
    data = await markets.list_market_catalogue(
        client,
        event_id=params.event_id,
        event_type_id=params.event_type_id,
        competition_id=params.competition_id,
        market_type_codes=params.market_type_codes,
        max_results=params.max_results,
    )
    return {
        "summary": format_market_catalogue(data),
        "data": data,
        "count": len(data),
    }


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def betfair_get_market_prices(params: GetMarketPricesInput) -> dict:
    """
    Get current prices and odds for specified markets.

    Returns live betting odds including back (bet on) and lay (bet against)
    prices for all runners in the specified markets.

    Args:
        params: Request parameters with fields:
            - market_ids: List of market IDs to get prices for (1-250, required)

    Returns:
        dict: Response with keys:
            - summary: Markdown-formatted odds table (str)
            - data: List of market prices (list[dict])
                - market_id: Market identifier (str)
                - status: Market status: OPEN, SUSPENDED, or CLOSED (str)
                - total_matched: Total amount matched (float)
                - runners: List of runners with prices (list[dict])
                    - selection_id: Runner identifier (str)
                    - status: Runner status: ACTIVE, REMOVED, WINNER, LOSER (str)
                    - last_price_traded: Last traded price (float)
                    - total_matched: Total matched on this runner (float)
                    - back_prices: Available back prices to bet on (list[dict])
                        - price: Decimal odds (float)
                        - size: Amount available at this price (float)
                    - lay_prices: Available lay prices to bet against (list[dict])
                        - price: Decimal odds (float)
                        - size: Amount available at this price (float)
            - count: Total number of markets (int)
    """
    client = get_client()
    data = await markets.get_market_prices(client, params.market_ids)
    return {
        "summary": format_market_prices(data),
        "data": data,
        "count": len(data),
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
