"""
Pydantic models for MCP tool inputs and outputs.

This module defines strongly-typed models for tool parameters,
providing validation and better error messages.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ListEventsInput(BaseModel):
    """Input parameters for listing events."""

    event_type_id: Optional[str] = Field(
        default=None,
        description="Sport ID to filter by (e.g., '1' for Soccer)",
    )
    competition_id: Optional[str] = Field(
        default=None,
        description="Competition ID to filter by",
    )
    text_query: Optional[str] = Field(
        default=None,
        description="Text to search in event names",
    )


class ListCompetitionsInput(BaseModel):
    """Input parameters for listing competitions."""

    event_type_id: Optional[str] = Field(
        default=None,
        description="Sport ID to filter by (e.g., '1' for Soccer)",
    )


class ListMarketCatalogueInput(BaseModel):
    """Input parameters for listing market catalogue."""

    event_id: Optional[str] = Field(
        default=None,
        description="Event ID to filter by",
    )
    event_type_id: Optional[str] = Field(
        default=None,
        description="Sport ID to filter by",
    )
    competition_id: Optional[str] = Field(
        default=None,
        description="Competition ID to filter by",
    )
    market_type_codes: Optional[List[str]] = Field(
        default=None,
        description='Market types (e.g., ["MATCH_ODDS", "OVER_UNDER_25"])',
    )
    max_results: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum markets to return (1-1000)",
    )

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int) -> int:
        """Ensure max_results is within Betfair's limits."""
        if v < 1:
            raise ValueError("max_results must be at least 1")
        if v > 1000:
            raise ValueError("max_results cannot exceed 1000 (Betfair API limit)")
        return v


class GetMarketPricesInput(BaseModel):
    """Input parameters for getting market prices."""

    market_ids: List[str] = Field(
        ...,
        min_length=1,
        max_length=250,
        description="List of market IDs to get prices for (1-250)",
    )

    @field_validator("market_ids")
    @classmethod
    def validate_market_ids(cls, v: List[str]) -> List[str]:
        """Ensure market_ids list is within limits."""
        if len(v) < 1:
            raise ValueError("At least one market_id is required")
        if len(v) > 250:
            raise ValueError("Cannot request more than 250 markets (Betfair API limit)")
        # Ensure no empty strings
        if any(not mid.strip() for mid in v):
            raise ValueError("Market IDs cannot be empty strings")
        return v
