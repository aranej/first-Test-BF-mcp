# Betfair MCP Server - FastMCP Integration Research

**Document:** RESEARCH_05_FASTMCP_INTEGRATION.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [FastMCP Overview](#fastmcp-overview)
3. [Integration Architecture](#integration-architecture)
4. [Tools Implementation](#tools-implementation)
5. [Resources Implementation](#resources-implementation)
6. [Prompts Implementation](#prompts-implementation)
7. [Context & Logging](#context--logging)
8. [Async/Sync Bridge](#asyncsync-bridge)
9. [Streaming Integration](#streaming-integration)
10. [Error Handling](#error-handling)
11. [Complete Server Example](#complete-server-example)
12. [References](#references)

---

## Executive Summary

**FastMCP** is our framework for building the MCP server - it bridges betfairlightweight (sync) with MCP protocol (async).

**Key Integration Points:**
- ✅ **Tools** - AI-executable functions (market queries, balance checks)
- ✅ **Resources** - Structured data URIs (`betfair://markets/{id}`)
- ✅ **Prompts** - Templated queries (analyze market, find value bets)
- ✅ **Context** - Logging, progress reporting, LLM sampling
- ✅ **Async bridge** - `asyncio.to_thread()` for sync SDK calls

**Critical Findings:**
- FastMCP 2.0 is production-ready (enterprise auth, deployment tools)
- Automatic schema generation from type hints and docstrings
- Supports stdio (local) and HTTP (remote) transports
- Built-in error handling and validation
- Context provides `ctx.info()`, `ctx.error()`, `ctx.report_progress()`

**Our Strategy:**
1. Use **stdio transport** for MVP (Claude Desktop integration)
2. Implement **10-15 core tools** for read-only market intelligence
3. Add **5-10 resources** for data access patterns
4. Create **3-5 prompts** for common analysis tasks
5. Future: Add HTTP transport for multi-user deployment

---

## FastMCP Overview

### What is FastMCP?

**FastMCP** = Fast, Pythonic way to build MCP servers and clients

**GitHub:** https://github.com/jlowin/fastmcp
**PyPI:** https://pypi.org/project/fastmcp/
**Docs:** https://gofastmcp.com

**Version:** 2.0+ (major update with enterprise features)

### Core Features

**Developer Experience:**
- ✅ Minimal boilerplate - decorators do the work
- ✅ Automatic schema generation from type hints
- ✅ Built-in validation (Pydantic)
- ✅ Hot reload during development
- ✅ Testing utilities

**Production Features (2.0):**
- ✅ Enterprise authentication (Google, GitHub, Azure, Auth0)
- ✅ Multiple transports (stdio, HTTP, SSE)
- ✅ Deployment tools (Docker, cloud platforms)
- ✅ Monitoring & observability
- ✅ Rate limiting & quotas

**MCP Primitives:**
- ✅ **Tools** - Functions AI can call
- ✅ **Resources** - Data AI can read
- ✅ **Prompts** - Templates for common tasks

### Installation

```bash
pip install fastmcp
```

**pyproject.toml:**
```toml
[project]
dependencies = [
    "fastmcp>=2.0.0",
    "betfairlightweight>=2.21.0",
]
```

---

## Integration Architecture

### High-Level Design

```
┌──────────────────────────────────────────────────┐
│              Claude Desktop / AI Client           │
└────────────────┬─────────────────────────────────┘
                 │ MCP Protocol (stdio)
                 ▼
┌──────────────────────────────────────────────────┐
│           FastMCP Server (betfair-mcp)           │
│  ┌────────────────────────────────────────────┐  │
│  │  FastMCP Layer (Async)                     │  │
│  │  - Tools (@mcp.tool)                       │  │
│  │  - Resources (@mcp.resource)               │  │
│  │  - Prompts (@mcp.prompt)                   │  │
│  └──────────────┬─────────────────────────────┘  │
│                 │ asyncio.to_thread()             │
│                 ▼                                 │
│  ┌────────────────────────────────────────────┐  │
│  │  betfairlightweight (Sync)                 │  │
│  │  - APIClient                               │  │
│  │  - Betting/Account endpoints               │  │
│  │  - Streaming                               │  │
│  └──────────────┬─────────────────────────────┘  │
│                 │ HTTPS/WSS                       │
└─────────────────┼─────────────────────────────────┘
                  ▼
       ┌────────────────────┐
       │  Betfair Exchange  │
       │       API          │
       └────────────────────┘
```

### Project Structure

```
betfair-mcp/
├── src/
│   └── betfair_mcp/
│       ├── __init__.py
│       ├── server.py              # FastMCP server instance
│       ├── client.py              # Betfair client wrapper
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── market_data.py     # Market query tools
│       │   ├── account.py         # Account tools
│       │   └── analysis.py        # Analysis tools
│       ├── resources/
│       │   ├── __init__.py
│       │   └── markets.py         # Market resources
│       ├── prompts/
│       │   ├── __init__.py
│       │   └── analysis.py        # Analysis prompts
│       └── utils/
│           ├── __init__.py
│           ├── rate_limiter.py
│           └── cache.py
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

---

## Tools Implementation

### Basic Tool Pattern

```python
from fastmcp import FastMCP
import asyncio

mcp = FastMCP("betfair")

@mcp.tool()
async def get_account_balance() -> dict:
    """
    Get current Betfair account balance.

    Returns:
        dict: Account balance information including available funds and exposure
    """
    # Bridge to sync betfairlightweight
    funds = await asyncio.to_thread(
        betfair_client.account.get_account_funds
    )

    return {
        "available": float(funds.available_to_bet_balance),
        "exposure": float(funds.exposure),
        "balance": float(funds.balance),
        "currency": "GBP"
    }
```

**What FastMCP generates automatically:**
- JSON schema from type hints
- Parameter validation
- Error handling wrapper
- Documentation from docstring

### Tool with Parameters

```python
@mcp.tool()
async def search_football_events(
    country_code: str = "GB",
    hours_ahead: int = 24
) -> list[dict]:
    """
    Search for upcoming football events.

    Args:
        country_code: ISO country code (e.g., "GB", "IE", "US")
        hours_ahead: Look ahead this many hours (default: 24)

    Returns:
        list[dict]: List of football events with match details
    """
    from datetime import datetime, timedelta

    # Calculate time filter
    time_to = datetime.utcnow() + timedelta(hours=hours_ahead)

    events = await asyncio.to_thread(
        betfair_client.betting.list_events,
        filter={
            'eventTypeIds': ['1'],  # Football
            'marketCountries': [country_code],
            'marketStartTime': {
                'to': time_to.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        }
    )

    return [
        {
            'event_id': e.event.id,
            'name': e.event.name,
            'country': e.event.country_code,
            'start_time': str(e.event.open_date),
            'market_count': e.market_count
        }
        for e in events
    ]
```

### Advanced Tool with Validation

```python
from pydantic import BaseModel, Field

class MarketPriceRequest(BaseModel):
    market_id: str = Field(..., pattern=r'^\d+\.\d+$')
    include_runners: bool = True

@mcp.tool()
async def get_market_prices(request: MarketPriceRequest) -> dict:
    """
    Get current prices for a specific market.

    Args:
        request: Market price request with market_id and options

    Returns:
        dict: Market prices including runners, odds, and liquidity
    """
    market_books = await asyncio.to_thread(
        betfair_client.betting.list_market_book,
        market_ids=[request.market_id],
        price_projection={'priceData': ['EX_BEST_OFFERS']}
    )

    if not market_books:
        raise ValueError(f"Market {request.market_id} not found")

    market = market_books[0]

    result = {
        'market_id': market.market_id,
        'status': market.status,
        'total_matched': float(market.total_matched or 0),
        'in_play': market.inplay
    }

    if request.include_runners:
        result['runners'] = [
            {
                'selection_id': r.selection_id,
                'status': r.status,
                'last_price': float(r.last_price_traded or 0),
                'back': [
                    {'price': p.price, 'size': p.size}
                    for p in (r.ex.available_to_back or [])[:3]
                ],
                'lay': [
                    {'price': p.price, 'size': p.size}
                    for p in (r.ex.available_to_lay or [])[:3]
                ]
            }
            for r in market.runners
        ]

    return result
```

### Tool Categories

**Market Discovery:**
```python
@mcp.tool()
async def list_sports() -> list[dict]:
    """List all available sports/event types"""
    ...

@mcp.tool()
async def list_competitions(sport: str) -> list[dict]:
    """List competitions for a sport"""
    ...

@mcp.tool()
async def search_events(filters: dict) -> list[dict]:
    """Search events with flexible filters"""
    ...
```

**Market Data:**
```python
@mcp.tool()
async def get_market_catalogue(event_id: str) -> list[dict]:
    """Get all markets for an event"""
    ...

@mcp.tool()
async def get_market_prices(market_id: str) -> dict:
    """Get current market prices"""
    ...

@mcp.tool()
async def get_runner_details(selection_id: int) -> dict:
    """Get runner/selection details"""
    ...
```

**Analysis:**
```python
@mcp.tool()
async def analyze_odds_movement(
    market_id: str,
    duration_minutes: int = 60
) -> dict:
    """Analyze how odds have changed over time"""
    ...

@mcp.tool()
async def find_value_bets(
    markets: list[str],
    threshold: float = 1.1
) -> list[dict]:
    """Find potential value betting opportunities"""
    ...
```

---

## Resources Implementation

### Basic Resource

```python
@mcp.resource("betfair://account/balance")
async def account_balance_resource() -> str:
    """Current account balance (updates on each access)"""
    funds = await asyncio.to_thread(
        betfair_client.account.get_account_funds
    )

    return f"""
Account Balance:
- Available: £{funds.available_to_bet_balance:.2f}
- Exposure: £{funds.exposure:.2f}
- Total Balance: £{funds.balance:.2f}
"""
```

### Parameterized Resource

```python
@mcp.resource("betfair://markets/{market_id}")
async def market_resource(market_id: str) -> str:
    """Get market data as a resource"""
    import json

    market_books = await asyncio.to_thread(
        betfair_client.betting.list_market_book,
        market_ids=[market_id]
    )

    if not market_books:
        raise ValueError(f"Market {market_id} not found")

    market = market_books[0]

    data = {
        'market_id': market.market_id,
        'status': market.status,
        'total_matched': float(market.total_matched or 0),
        'runners': [
            {
                'id': r.selection_id,
                'ltp': float(r.last_price_traded or 0)
            }
            for r in market.runners
        ]
    }

    return json.dumps(data, indent=2)
```

### Dynamic Resource List

```python
@mcp.resource("betfair://events/football/today")
async def todays_football_resource() -> str:
    """Today's football events"""
    from datetime import datetime, timedelta

    end_of_day = datetime.utcnow().replace(
        hour=23, minute=59, second=59
    )

    events = await asyncio.to_thread(
        betfair_client.betting.list_events,
        filter={
            'eventTypeIds': ['1'],
            'marketStartTime': {
                'to': end_of_day.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        }
    )

    lines = ["# Today's Football Events\n"]
    for event in events:
        lines.append(
            f"- {event.event.name} ({event.market_count} markets)"
        )

    return "\n".join(lines)
```

### Resource Patterns

**Data Access:**
```
betfair://markets/{market_id}           # Single market
betfair://events/{event_id}/markets     # All markets for event
betfair://account/funds                 # Account balance
betfair://account/statement             # Transaction history
```

**Collections:**
```
betfair://sports                        # All sports
betfair://competitions/football         # Football competitions
betfair://events/today                  # Today's events
```

**Analysis:**
```
betfair://analysis/hot-markets          # Most active markets
betfair://analysis/value-bets           # Identified value bets
```

---

## Prompts Implementation

### Basic Prompt

```python
@mcp.prompt()
async def analyze_market(market_id: str) -> str:
    """
    Generate a prompt for analyzing a specific market.

    Args:
        market_id: Betfair market ID

    Returns:
        str: Analysis prompt
    """
    return f"""
Analyze Betfair market {market_id} and provide:

1. Market overview (status, matched volume, in-play status)
2. Current odds for all runners
3. Liquidity analysis (available volume at each price)
4. Odds movement (if historical data available)
5. Value betting opportunities (highlight any runners with unusually high odds)
6. Risk assessment

Use the following tools:
- get_market_prices({market_id})
- get_market_catalogue({market_id})

Format your analysis clearly with sections and bullet points.
"""
```

### Advanced Prompt with Context

```python
from fastmcp import Message

@mcp.prompt()
async def compare_bookmaker_odds(
    market_id: str,
    bookmakers: list[str]
) -> list[Message]:
    """
    Generate a multi-message prompt for odds comparison.

    Args:
        market_id: Betfair market ID
        bookmakers: List of bookmaker names to compare

    Returns:
        list[Message]: Conversation-style prompt
    """
    return [
        Message(
            role="user",
            content=f"I want to compare Betfair odds with {', '.join(bookmakers)} for market {market_id}"
        ),
        Message(
            role="assistant",
            content="I'll help you compare the odds. Let me fetch the Betfair market data first."
        ),
        Message(
            role="user",
            content=f"""
For each runner in market {market_id}:
1. Get current Betfair back odds (use get_market_prices)
2. Compare with {bookmakers[0]} odds
3. Calculate implied probability for each
4. Identify arbitrage opportunities
5. Recommend best betting exchange

Present results in a comparison table.
"""
        )
    ]
```

### Prompt Templates

**Value Betting:**
```python
@mcp.prompt()
async def find_value_bets_prompt(
    sport: str,
    min_odds: float = 2.0,
    max_odds: float = 10.0
) -> str:
    """Generate prompt for finding value bets in a sport"""
    return f"""
Find value betting opportunities in {sport} with odds between {min_odds} and {max_odds}.

Steps:
1. List upcoming {sport} events (use search_{sport.lower()}_events)
2. For each event, get market catalogue
3. Analyze match odds markets
4. Calculate implied probabilities
5. Compare with your own probability assessment
6. Identify bets where your assessment > market implied probability
7. Rank opportunities by expected value

Return top 5 value bets with:
- Event name
- Runner name
- Current odds
- Your probability estimate
- Expected value
- Recommended stake (Kelly criterion)
"""
```

**Market Summary:**
```python
@mcp.prompt()
async def daily_market_summary() -> str:
    """Generate prompt for daily market summary"""
    return """
Create a daily summary of Betfair markets:

1. **Most Active Markets**
   - Top 10 by trading volume
   - Sport breakdown

2. **Upcoming Events** (next 24 hours)
   - By sport
   - Highlight major events

3. **In-Play Markets**
   - Currently active
   - Interesting price movements

4. **Value Opportunities**
   - Potential value bets identified
   - Risk/reward analysis

Use tools: list_sports, search_events, get_market_prices

Format as a readable report with clear sections.
"""
```

---

## Context & Logging

### Using Context in Tools

```python
from fastmcp import Context

@mcp.tool()
async def search_markets_with_progress(
    event_id: str,
    ctx: Context
) -> list[dict]:
    """
    Search markets with progress reporting.

    Args:
        event_id: Event ID to search
        ctx: MCP context for logging and progress

    Returns:
        list[dict]: Markets found
    """
    # Log to client
    ctx.info(f"Searching markets for event {event_id}")

    # Report progress
    await ctx.report_progress(0, 100, "Starting search...")

    try:
        # Fetch data
        markets = await asyncio.to_thread(
            betfair_client.betting.list_market_catalogue,
            filter={'eventIds': [event_id]},
            max_results=100
        )

        await ctx.report_progress(50, 100, f"Found {len(markets)} markets")

        # Process results
        results = []
        for i, market in enumerate(markets):
            results.append({
                'market_id': market.market_id,
                'name': market.market_name,
                'start_time': str(market.market_start_time)
            })

            # Update progress
            progress = 50 + (i + 1) / len(markets) * 50
            await ctx.report_progress(
                progress, 100,
                f"Processing {i+1}/{len(markets)}"
            )

        ctx.info(f"Completed search: {len(results)} markets")
        return results

    except Exception as e:
        ctx.error(f"Search failed: {str(e)}")
        raise
```

### Context Methods

**Logging:**
```python
ctx.debug("Debug message")
ctx.info("Info message")
ctx.warning("Warning message")
ctx.error("Error message")
```

**Progress Reporting:**
```python
await ctx.report_progress(
    progress=50,        # Current progress (0-100)
    total=100,          # Total (optional)
    message="Processing..."  # Status message
)
```

**LLM Sampling (Advanced):**
```python
# Ask the client's LLM a question
response = await ctx.sample(
    messages=[{"role": "user", "content": "Analyze this data..."}],
    max_tokens=500
)
```

**Resource Access:**
```python
# Read another resource from within a tool
data = await ctx.read_resource("betfair://markets/1.234567")
```

---

## Async/Sync Bridge

### Core Pattern: asyncio.to_thread()

```python
import asyncio

# ❌ WRONG - Blocking async function
@mcp.tool()
async def get_balance_wrong():
    # This blocks the event loop!
    return betfair_client.account.get_account_funds()

# ✅ CORRECT - Run in thread pool
@mcp.tool()
async def get_balance_correct():
    return await asyncio.to_thread(
        betfair_client.account.get_account_funds
    )
```

### Thread Pool Executor (Alternative)

```python
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=10)

@mcp.tool()
async def get_balance_with_executor():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        betfair_client.account.get_account_funds
    )
```

### Batch Operations

```python
@mcp.tool()
async def get_multiple_markets(market_ids: list[str]) -> list[dict]:
    """Get multiple markets efficiently"""

    # Run all requests concurrently (but each in thread pool)
    tasks = [
        asyncio.to_thread(
            betfair_client.betting.list_market_book,
            market_ids=[mid]
        )
        for mid in market_ids
    ]

    results = await asyncio.gather(*tasks)

    return [
        {
            'market_id': r[0].market_id,
            'status': r[0].status,
            'total_matched': float(r[0].total_matched or 0)
        }
        for r in results if r
    ]
```

---

## Streaming Integration

### Background Stream Task

```python
import queue
from betfairlightweight.streaming import StreamListener

# Global state
market_cache = {}
stream_queue = queue.Queue()

async def start_background_stream():
    """Start streaming in background task"""
    # Create stream
    listener = StreamListener(output_queue=stream_queue)
    stream = betfair_client.streaming.create_stream(
        unique_id=1,
        listener=listener
    )

    # Subscribe
    market_filter = betfairlightweight.filters.streaming_market_filter(
        event_type_ids=['1']  # Football
    )
    stream.subscribe_to_markets(
        market_filter=market_filter,
        conflate_ms=1000
    )

    # Start in thread
    await asyncio.to_thread(stream.start, async_=False)

    # Process updates
    while True:
        try:
            # Get updates (non-blocking with timeout)
            updates = await asyncio.to_thread(
                stream_queue.get,
                timeout=1
            )

            # Update cache
            for market_book in updates:
                market_cache[market_book.market_id] = {
                    'status': market_book.status,
                    'total_matched': market_book.total_matched,
                    'last_update': time.time()
                }

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Stream error: {e}")
            await asyncio.sleep(5)  # Retry delay
```

### MCP Tool Using Cached Stream Data

```python
@mcp.tool()
async def get_live_market_data(market_id: str) -> dict:
    """
    Get live market data from streaming cache.

    This is faster than querying the API as data is pre-cached.

    Args:
        market_id: Market ID

    Returns:
        dict: Cached market data
    """
    if market_id in market_cache:
        data = market_cache[market_id].copy()
        data['age_seconds'] = time.time() - data['last_update']
        return data
    else:
        return {"error": "Market not in stream cache"}
```

### Server Lifecycle Hooks

```python
async def on_server_start():
    """Called when MCP server starts"""
    # Login to Betfair
    await asyncio.to_thread(betfair_client.login)

    # Start background streaming
    asyncio.create_task(start_background_stream())

    print("Betfair MCP server started")

async def on_server_shutdown():
    """Called when MCP server stops"""
    # Cleanup
    await asyncio.to_thread(betfair_client.logout)
    print("Betfair MCP server stopped")

# Register hooks
mcp.on_startup(on_server_start)
mcp.on_shutdown(on_server_shutdown)
```

---

## Error Handling

### Tool-Level Error Handling

```python
from betfairlightweight.exceptions import APINGException, LoginError

@mcp.tool()
async def safe_get_markets(event_id: str) -> dict:
    """Get markets with comprehensive error handling"""
    try:
        markets = await asyncio.to_thread(
            betfair_client.betting.list_market_catalogue,
            filter={'eventIds': [event_id]}
        )

        return {
            "success": True,
            "count": len(markets),
            "markets": [m.market_id for m in markets]
        }

    except APINGException as e:
        return {
            "success": False,
            "error": "Betfair API Error",
            "code": e.error_code,
            "details": e.error_details
        }

    except LoginError as e:
        return {
            "success": False,
            "error": "Authentication Error",
            "message": "Session expired. Please restart server."
        }

    except Exception as e:
        return {
            "success": False,
            "error": "Unknown Error",
            "message": str(e)
        }
```

### Global Error Handler

```python
@mcp.error_handler
async def handle_errors(error: Exception, context: dict):
    """Global error handler for all tools"""
    import traceback

    print(f"Error in {context.get('tool_name', 'unknown')}: {error}")
    print(traceback.format_exc())

    # Could log to external service here
    # logger.error(...)

    # Return user-friendly error
    return {
        "error": type(error).__name__,
        "message": str(error),
        "tool": context.get('tool_name')
    }
```

---

## Complete Server Example

```python
# src/betfair_mcp/server.py

import asyncio
import os
from fastmcp import FastMCP
import betfairlightweight

# Initialize FastMCP
mcp = FastMCP(
    name="betfair",
    version="0.1.0",
    description="Betfair Exchange MCP Server"
)

# Initialize Betfair client (singleton)
betfair_client = betfairlightweight.APIClient(
    username=os.getenv('BETFAIR_USERNAME'),
    password=os.getenv('BETFAIR_PASSWORD'),
    app_key=os.getenv('BETFAIR_APP_KEY'),
    certs=os.getenv('BETFAIR_CERTS_PATH')
)

# Startup hook
@mcp.on_startup
async def startup():
    """Initialize Betfair connection"""
    await asyncio.to_thread(betfair_client.login)
    print("✅ Betfair MCP server started")

# Shutdown hook
@mcp.on_shutdown
async def shutdown():
    """Cleanup Betfair connection"""
    await asyncio.to_thread(betfair_client.logout)
    print("👋 Betfair MCP server stopped")

# Tools
@mcp.tool()
async def get_account_balance() -> dict:
    """Get current account balance"""
    funds = await asyncio.to_thread(
        betfair_client.account.get_account_funds
    )
    return {
        "available": float(funds.available_to_bet_balance),
        "exposure": float(funds.exposure)
    }

@mcp.tool()
async def list_football_events(country: str = "GB") -> list[dict]:
    """List upcoming football events"""
    events = await asyncio.to_thread(
        betfair_client.betting.list_events,
        filter={
            'eventTypeIds': ['1'],
            'marketCountries': [country]
        }
    )
    return [
        {
            'id': e.event.id,
            'name': e.event.name,
            'markets': e.market_count
        }
        for e in events
    ]

# Resources
@mcp.resource("betfair://account/balance")
async def balance_resource() -> str:
    """Account balance as resource"""
    funds = await asyncio.to_thread(
        betfair_client.account.get_account_funds
    )
    return f"Balance: £{funds.available_to_bet_balance:.2f}"

# Prompts
@mcp.prompt()
async def analyze_event(event_id: str) -> str:
    """Generate event analysis prompt"""
    return f"""
Analyze Betfair event {event_id}:
1. List all markets
2. Get current odds for main markets
3. Identify value betting opportunities
4. Provide betting recommendations

Use tools: list_markets, get_market_prices
"""

# Run server
if __name__ == "__main__":
    mcp.run()
```

**Run:**
```bash
uv run python src/betfair_mcp/server.py
```

---

## References

### FastMCP Resources
- [GitHub Repository](https://github.com/jlowin/fastmcp)
- [PyPI Package](https://pypi.org/project/fastmcp/)
- [Documentation](https://gofastmcp.com)
- [Tutorial](https://www.datacamp.com/tutorial/building-mcp-server-client-fastmcp)

### Related Research Documents
- [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md) - SDK integration
- [RESEARCH_03_STREAMING_API.md](./RESEARCH_03_STREAMING_API.md) - Streaming with MCP
- [RESEARCH_06_USE_CASES.md](./RESEARCH_06_USE_CASES.md) - What tools to build

---

**Next Document:** [RESEARCH_06_USE_CASES.md](./RESEARCH_06_USE_CASES.md)
**Previous Document:** [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
