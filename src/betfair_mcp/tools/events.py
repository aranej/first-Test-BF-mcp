"""
Event-related MCP tools for Betfair API.

This module provides tools for querying sporting events, event types,
and competitions available on the Betfair Exchange.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from betfairlightweight.exceptions import BetfairError
from betfairlightweight.filters import market_filter

logger = logging.getLogger(__name__)


async def list_event_types(client: Any) -> List[Dict[str, Any]]:
    """
    List all available event types (sports).

    This tool returns all available sports/event types on Betfair,
    such as Football, Horse Racing, Tennis, etc.

    Args:
        client: The betfairlightweight API client

    Returns:
        List of dicts, each containing:
            - event_type_id: Unique identifier for the sport
            - event_type_name: Human-readable name (e.g., "Soccer", "Tennis")
            - market_count: Number of markets available for this sport

    Raises:
        BetfairError: If the API request fails
    """
    try:
        logger.info("Fetching event types")

        # Create a filter for all markets
        filter_obj = market_filter()

        # Call the sync API in a thread pool
        event_types = await asyncio.to_thread(
            client.betting.list_event_types, filter=filter_obj
        )

        result = [
            {
                "event_type_id": str(et.event_type.id),
                "event_type_name": et.event_type.name,
                "market_count": et.market_count,
            }
            for et in event_types
        ]

        logger.info(f"Retrieved {len(result)} event types")
        return result

    except BetfairError as e:
        logger.error(f"Failed to fetch event types: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching event types: {e}")
        raise


async def list_events(
    client: Any,
    event_type_id: Optional[str] = None,
    competition_id: Optional[str] = None,
    text_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List sporting events with optional filtering.

    This tool returns a list of events that match the specified criteria.
    Events can be filtered by sport (event type), competition, or text search.

    Args:
        client: The betfairlightweight API client
        event_type_id: Optional sport ID to filter by (e.g., "1" for Soccer)
        competition_id: Optional competition ID to filter by
        text_query: Optional text to search in event names

    Returns:
        List of dicts, each containing:
            - event_id: Unique event identifier
            - event_name: Event name (e.g., "Man Utd vs Liverpool")
            - event_timezone: Event timezone
            - open_date: When the event starts (ISO format)
            - country_code: Country code for the event
            - market_count: Number of markets for this event

    Raises:
        BetfairError: If the API request fails
    """
    try:
        logger.info(
            f"Fetching events (event_type_id={event_type_id}, "
            f"competition_id={competition_id}, text_query={text_query})"
        )

        # Build filter
        filter_params = {}
        if event_type_id:
            filter_params["event_type_ids"] = [event_type_id]
        if competition_id:
            filter_params["competition_ids"] = [competition_id]
        if text_query:
            filter_params["text_query"] = text_query

        filter_obj = market_filter(**filter_params)

        # Call the sync API in a thread pool
        events = await asyncio.to_thread(client.betting.list_events, filter=filter_obj)

        result = [
            {
                "event_id": str(event.event.id),
                "event_name": event.event.name,
                "event_timezone": event.event.timezone,
                "open_date": event.event.open_date.isoformat() if event.event.open_date else None,
                "country_code": event.event.country_code,
                "market_count": event.market_count,
            }
            for event in events
        ]

        logger.info(f"Retrieved {len(result)} events")
        return result

    except BetfairError as e:
        logger.error(f"Failed to fetch events: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching events: {e}")
        raise


async def list_competitions(
    client: Any,
    event_type_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List competitions (leagues/tournaments) with optional filtering.

    This tool returns available competitions/leagues for a given sport.

    Args:
        client: The betfairlightweight API client
        event_type_id: Optional sport ID to filter by (e.g., "1" for Soccer)

    Returns:
        List of dicts, each containing:
            - competition_id: Unique competition identifier
            - competition_name: Competition name (e.g., "Premier League")
            - market_count: Number of markets in this competition

    Raises:
        BetfairError: If the API request fails
    """
    try:
        logger.info(f"Fetching competitions (event_type_id={event_type_id})")

        # Build filter
        filter_params = {}
        if event_type_id:
            filter_params["event_type_ids"] = [event_type_id]

        filter_obj = market_filter(**filter_params)

        # Call the sync API in a thread pool
        competitions = await asyncio.to_thread(
            client.betting.list_competitions, filter=filter_obj
        )

        result = [
            {
                "competition_id": str(comp.competition.id),
                "competition_name": comp.competition.name,
                "market_count": comp.market_count,
            }
            for comp in competitions
        ]

        logger.info(f"Retrieved {len(result)} competitions")
        return result

    except BetfairError as e:
        logger.error(f"Failed to fetch competitions: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching competitions: {e}")
        raise
