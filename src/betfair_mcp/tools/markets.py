"""
Market-related MCP tools for Betfair API.

This module provides tools for querying betting markets, odds,
and market information from the Betfair Exchange.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from betfairlightweight.exceptions import BetfairError
from betfairlightweight.filters import market_filter, price_projection

from ..rate_limiter import get_rate_limiter
from ..weight_calculator import MarketDataWeightCalculator
from ..error_handling import classify_betfair_error, log_api_error

logger = logging.getLogger(__name__)


async def list_market_catalogue(
    client: Any,
    event_id: Optional[str] = None,
    event_type_id: Optional[str] = None,
    competition_id: Optional[str] = None,
    market_type_codes: Optional[List[str]] = None,
    max_results: int = 100,
) -> List[Dict[str, Any]]:
    """
    List available betting markets with optional filtering.

    This tool returns detailed information about betting markets,
    including runners and market descriptions.

    Args:
        client: The betfairlightweight API client
        event_id: Optional event ID to filter by
        event_type_id: Optional sport ID to filter by
        competition_id: Optional competition ID to filter by
        market_type_codes: Optional list of market types (e.g., ["MATCH_ODDS", "OVER_UNDER_25"])
        max_results: Maximum number of markets to return (default: 100, max: 1000)

    Returns:
        List of dicts, each containing:
            - market_id: Unique market identifier
            - market_name: Market name (e.g., "Match Odds")
            - market_type: Market type code (e.g., "MATCH_ODDS")
            - event_name: Name of the event this market belongs to
            - competition_name: Name of the competition
            - event_id: ID of the parent event
            - total_matched: Total amount matched on this market
            - runners: List of runners/selections in this market
                - selection_id: Unique runner identifier
                - runner_name: Runner name (e.g., "Manchester United")
                - sort_priority: Display order priority

    Raises:
        BetfairError: If the API request fails
    """
    rate_limiter = get_rate_limiter()

    try:
        logger.info(
            f"Fetching market catalogue (event_id={event_id}, "
            f"event_type_id={event_type_id}, max_results={max_results})"
        )

        # Market projections requested
        market_projection = ["COMPETITION", "EVENT", "RUNNER_DESCRIPTION", "MARKET_DESCRIPTION"]

        # Validate weight for the request
        weight = MarketDataWeightCalculator.calculate_market_catalogue_weight(
            num_markets=max_results,
            market_projection=market_projection,
        )
        MarketDataWeightCalculator.validate_weight(weight, "list_market_catalogue")

        # Apply rate limiting
        await rate_limiter.acquire_general()

        # Build filter
        filter_params = {}
        if event_id:
            filter_params["event_ids"] = [event_id]
        if event_type_id:
            filter_params["event_type_ids"] = [event_type_id]
        if competition_id:
            filter_params["competition_ids"] = [competition_id]
        if market_type_codes:
            filter_params["market_type_codes"] = market_type_codes

        filter_obj = market_filter(**filter_params)

        # Call the sync API in a thread pool
        markets = await asyncio.to_thread(
            client.betting.list_market_catalogue,
            filter=filter_obj,
            max_results=max_results,
            market_projection=market_projection,
        )

        result = []
        for market in markets:
            market_data = {
                "market_id": market.market_id,
                "market_name": market.market_name,
                "market_type": market.description.market_type if market.description else None,
                "event_name": market.event.name if market.event else None,
                "competition_name": (
                    market.competition.name if market.competition else None
                ),
                "event_id": str(market.event.id) if market.event else None,
                "total_matched": float(market.total_matched) if market.total_matched else 0.0,
                "runners": [],
            }

            # Add runner information
            if market.runners:
                for runner in market.runners:
                    market_data["runners"].append({
                        "selection_id": str(runner.selection_id),
                        "runner_name": runner.runner_name,
                        "sort_priority": runner.sort_priority,
                    })

            result.append(market_data)

        logger.info(f"Retrieved {len(result)} markets")
        return result

    except BetfairError as e:
        classified_error = classify_betfair_error(e)
        log_api_error(classified_error, "list_market_catalogue")
        raise classified_error
    except Exception as e:
        logger.error(f"Unexpected error fetching market catalogue: {e}")
        raise


async def get_market_prices(
    client: Any,
    market_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Get current prices and odds for specified markets.

    This tool returns live betting odds, including back and lay prices,
    for the specified markets.

    Args:
        client: The betfairlightweight API client
        market_ids: List of market IDs to get prices for (max 250)

    Returns:
        List of dicts, each containing:
            - market_id: Market identifier
            - status: Market status (OPEN, SUSPENDED, CLOSED)
            - total_matched: Total amount matched
            - runners: List of runners with prices
                - selection_id: Runner identifier
                - status: Runner status (ACTIVE, REMOVED, WINNER, LOSER)
                - last_price_traded: Last traded price
                - total_matched: Total matched on this runner
                - back_prices: Available back prices (to bet on)
                    - price: Decimal odds
                    - size: Amount available at this price
                - lay_prices: Available lay prices (to bet against)
                    - price: Decimal odds
                    - size: Amount available at this price

    Raises:
        BetfairError: If the API request fails
        ValueError: If more than 250 market IDs provided
    """
    if len(market_ids) > 250:
        raise ValueError("Maximum 250 market IDs allowed per request")

    rate_limiter = get_rate_limiter()

    try:
        logger.info(f"Fetching prices for {len(market_ids)} markets")

        # Price data requested
        price_data = ["EX_BEST_OFFERS", "EX_TRADED"]

        # Validate weight for the request
        weight = MarketDataWeightCalculator.calculate_market_book_weight(
            num_markets=len(market_ids),
            price_data=price_data,
        )
        MarketDataWeightCalculator.validate_weight(weight, "get_market_prices")

        # Apply rate limiting for batch market request
        await rate_limiter.acquire_markets(market_ids)

        # Create price projection for full depth
        price_proj = price_projection(
            price_data=price_data,
            virtualise=True,
        )

        # Call the sync API in a thread pool
        market_books = await asyncio.to_thread(
            client.betting.list_market_book,
            market_ids=market_ids,
            price_projection=price_proj,
        )

        result = []
        for book in market_books:
            market_data = {
                "market_id": book.market_id,
                "status": book.status,
                "total_matched": float(book.total_matched) if book.total_matched else 0.0,
                "runners": [],
            }

            # Add runner price information
            if book.runners:
                for runner in book.runners:
                    runner_data = {
                        "selection_id": str(runner.selection_id),
                        "status": runner.status,
                        "last_price_traded": (
                            float(runner.last_price_traded) if runner.last_price_traded else None
                        ),
                        "total_matched": (
                            float(runner.total_matched) if runner.total_matched else 0.0
                        ),
                        "back_prices": [],
                        "lay_prices": [],
                    }

                    # Add back prices
                    if runner.ex and runner.ex.available_to_back:
                        for price_size in runner.ex.available_to_back[:3]:  # Top 3 prices
                            runner_data["back_prices"].append({
                                "price": float(price_size.price),
                                "size": float(price_size.size),
                            })

                    # Add lay prices
                    if runner.ex and runner.ex.available_to_lay:
                        for price_size in runner.ex.available_to_lay[:3]:  # Top 3 prices
                            runner_data["lay_prices"].append({
                                "price": float(price_size.price),
                                "size": float(price_size.size),
                            })

                    market_data["runners"].append(runner_data)

            result.append(market_data)

        logger.info(f"Retrieved prices for {len(result)} markets")
        return result

    except BetfairError as e:
        classified_error = classify_betfair_error(e)
        log_api_error(classified_error, "get_market_prices")
        raise classified_error
    except Exception as e:
        logger.error(f"Unexpected error fetching market prices: {e}")
        raise
