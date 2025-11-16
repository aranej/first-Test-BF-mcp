"""
Market data weight calculation for Betfair API compliance.

This module calculates the "weight" of API requests to ensure compliance
with Betfair's 200-point limit per request. Different combinations of
market projections and price data have different weights.

Reference: https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Market+Data+Request+Limits
"""

import logging
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class MarketDataWeightCalculator:
    """
    Calculator for Betfair API market data request weights.

    Betfair enforces a maximum weight of 200 points per request.
    Different data projections have different weights:
    
    MarketProjection weights (per market):
    - COMPETITION: 1 point
    - EVENT: 1 point
    - EVENT_TYPE: 1 point
    - MARKET_DESCRIPTION: 1 point
    - RUNNER_DESCRIPTION: 1 point
    - RUNNER_METADATA: 2 points
    - MARKET_START_TIME: 1 point
    
    PriceProjection weights (per market):
    - EX_BEST_OFFERS: 2 points
    - EX_ALL_OFFERS: 5 points
    - EX_TRADED: 3 points
    - SP_AVAILABLE: 1 point
    - SP_TRADED: 1 point
    
    Base weight per market: 1 point
    """

    # Market projection weights
    MARKET_PROJECTION_WEIGHTS = {
        "COMPETITION": 1,
        "EVENT": 1,
        "EVENT_TYPE": 1,
        "MARKET_DESCRIPTION": 1,
        "RUNNER_DESCRIPTION": 1,
        "RUNNER_METADATA": 2,
        "MARKET_START_TIME": 1,
    }

    # Price projection weights
    PRICE_PROJECTION_WEIGHTS = {
        "EX_BEST_OFFERS": 2,
        "EX_ALL_OFFERS": 5,
        "EX_TRADED": 3,
        "SP_AVAILABLE": 1,
        "SP_TRADED": 1,
    }

    # Base weight per market
    BASE_WEIGHT_PER_MARKET = 1

    # Maximum allowed weight per request
    MAX_WEIGHT = 200

    @classmethod
    def calculate_market_catalogue_weight(
        cls,
        num_markets: int,
        market_projection: Optional[List[str]] = None,
    ) -> int:
        """
        Calculate weight for a listMarketCatalogue request.

        Args:
            num_markets: Number of markets in the request
            market_projection: List of market projections requested

        Returns:
            Total weight of the request
        """
        if market_projection is None:
            market_projection = []

        # Start with base weight
        weight_per_market = cls.BASE_WEIGHT_PER_MARKET

        # Add weights for each projection
        for projection in market_projection:
            projection_upper = projection.upper()
            if projection_upper in cls.MARKET_PROJECTION_WEIGHTS:
                weight_per_market += cls.MARKET_PROJECTION_WEIGHTS[projection_upper]
            else:
                logger.warning(f"Unknown market projection: {projection}")

        total_weight = num_markets * weight_per_market

        logger.debug(
            f"Market catalogue weight: {total_weight} "
            f"({num_markets} markets × {weight_per_market} points/market)"
        )

        return total_weight

    @classmethod
    def calculate_market_book_weight(
        cls,
        num_markets: int,
        price_data: Optional[List[str]] = None,
        order_projection: bool = False,
        match_projection: bool = False,
    ) -> int:
        """
        Calculate weight for a listMarketBook request.

        Args:
            num_markets: Number of markets in the request
            price_data: List of price projections requested
            order_projection: Whether order projection is requested
            match_projection: Whether match projection is requested

        Returns:
            Total weight of the request
        """
        if price_data is None:
            price_data = []

        # Start with base weight
        weight_per_market = cls.BASE_WEIGHT_PER_MARKET

        # Add weights for price projections
        for projection in price_data:
            projection_upper = projection.upper()
            if projection_upper in cls.PRICE_PROJECTION_WEIGHTS:
                weight_per_market += cls.PRICE_PROJECTION_WEIGHTS[projection_upper]
            else:
                logger.warning(f"Unknown price projection: {projection}")

        # Order and match projections add weight
        if order_projection:
            weight_per_market += 2  # Approximate weight for order projection
        if match_projection:
            weight_per_market += 2  # Approximate weight for match projection

        total_weight = num_markets * weight_per_market

        logger.debug(
            f"Market book weight: {total_weight} "
            f"({num_markets} markets × {weight_per_market} points/market)"
        )

        return total_weight

    @classmethod
    def validate_weight(cls, weight: int, operation: str = "request") -> None:
        """
        Validate that a request weight is within limits.

        Args:
            weight: The calculated weight
            operation: Name of the operation (for logging)

        Raises:
            ValueError: If weight exceeds maximum
        """
        if weight > cls.MAX_WEIGHT:
            raise ValueError(
                f"{operation} weight ({weight}) exceeds maximum allowed ({cls.MAX_WEIGHT}). "
                f"Reduce the number of markets or requested data fields."
            )

        logger.debug(f"{operation} weight ({weight}) is within limits")

    @classmethod
    def calculate_max_markets(
        cls,
        market_projection: Optional[List[str]] = None,
        price_data: Optional[List[str]] = None,
    ) -> int:
        """
        Calculate maximum number of markets that can be requested.

        Args:
            market_projection: List of market projections (for catalogue)
            price_data: List of price projections (for book)

        Returns:
            Maximum number of markets that can be requested
        """
        # Determine which type of request
        if price_data:
            # Market book request
            weight_per_market = cls.BASE_WEIGHT_PER_MARKET
            for projection in price_data:
                projection_upper = projection.upper()
                weight_per_market += cls.PRICE_PROJECTION_WEIGHTS.get(
                    projection_upper, 0
                )
        elif market_projection:
            # Market catalogue request
            weight_per_market = cls.BASE_WEIGHT_PER_MARKET
            for projection in market_projection:
                projection_upper = projection.upper()
                weight_per_market += cls.MARKET_PROJECTION_WEIGHTS.get(
                    projection_upper, 0
                )
        else:
            # Minimal request
            weight_per_market = cls.BASE_WEIGHT_PER_MARKET

        if weight_per_market == 0:
            return cls.MAX_WEIGHT  # Should never happen

        max_markets = cls.MAX_WEIGHT // weight_per_market

        logger.debug(
            f"Maximum markets for this request: {max_markets} "
            f"(weight per market: {weight_per_market})"
        )

        return max_markets

    @classmethod
    def split_markets_by_weight(
        cls,
        market_ids: List[str],
        market_projection: Optional[List[str]] = None,
        price_data: Optional[List[str]] = None,
    ) -> List[List[str]]:
        """
        Split market IDs into chunks that respect weight limits.

        Args:
            market_ids: List of market IDs to split
            market_projection: Market projections (for catalogue)
            price_data: Price projections (for book)

        Returns:
            List of market ID chunks, each within weight limits
        """
        max_markets = cls.calculate_max_markets(
            market_projection=market_projection,
            price_data=price_data,
        )

        chunks = []
        for i in range(0, len(market_ids), max_markets):
            chunk = market_ids[i:i + max_markets]
            chunks.append(chunk)

        if len(chunks) > 1:
            logger.info(
                f"Split {len(market_ids)} markets into {len(chunks)} chunks "
                f"to respect weight limits (max {max_markets} markets/chunk)"
            )

        return chunks
