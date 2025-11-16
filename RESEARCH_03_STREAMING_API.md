# Betfair MCP Server - Streaming API Research

**Document:** RESEARCH_03_STREAMING_API.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Why Streaming vs Polling](#why-streaming-vs-polling)
3. [Betfair Exchange Stream API Overview](#betfair-exchange-stream-api-overview)
4. [Stream Types](#stream-types)
5. [Protocol & Transport](#protocol--transport)
6. [Subscription Management](#subscription-management)
7. [Data Structures](#data-structures)
8. [betfairlightweight Streaming Implementation](#betfairlightweight-streaming-implementation)
9. [Reconnection Strategies](#reconnection-strategies)
10. [MCP Integration Patterns](#mcp-integration-patterns)
11. [Performance Optimization](#performance-optimization)
12. [References](#references)

---

## Executive Summary

**The Betfair Exchange Stream API is our MCP server's killer feature.**

**Key Benefits:**
- ✅ **Sub-second latency** - Real-time market updates
- ✅ **No polling overhead** - Push-based updates
- ✅ **Efficient bandwidth** - Only changes sent (delta updates)
- ✅ **Two stream types** - Market data + Order tracking
- ✅ **Production endpoints** - `stream-api.betfair.com` (live) vs. `stream-api-integration.betfair.com` (test)

**Critical Findings:**
- Protocol: SSL sockets with CRLF-delimited JSON (JSON-RPC-like)
- ~1.5TB historical data available
- Requires app key activated for streaming
- betfairlightweight provides production-ready streaming client
- Conflate settings control update frequency (e.g., 1000ms = 1 update/sec)

**MCP Server Implication:**
Streaming enables **AI assistants to observe markets in real-time** without constant polling, dramatically reducing rate limit pressure and enabling live analysis.

---

## Why Streaming vs Polling

### Polling Approach (Traditional)

```
┌─────────┐     GET market data     ┌──────────┐
│   MCP   │  ──────────────────>   │ Betfair  │
│ Server  │                         │   API    │
│         │  <──────────────────    │          │
└─────────┘     Return data         └──────────┘
     │
     │ (wait 1 second)
     ▼
┌─────────┐     GET market data     ┌──────────┐
│   MCP   │  ──────────────────>   │ Betfair  │
│ Server  │                         │   API    │
│         │  <──────────────────    │          │
└─────────┘     Return data         └──────────┘
```

**Problems:**
- ❌ Constant API requests (hits rate limits)
- ❌ Data can be stale between polls
- ❌ Inefficient (sends full data each time)
- ❌ High latency (up to poll interval)
- ❌ Wastes bandwidth

### Streaming Approach (Modern)

```
┌─────────┐    SUBSCRIBE markets    ┌──────────┐
│   MCP   │  ──────────────────>   │ Betfair  │
│ Server  │                         │  Stream  │
│         │  <══════════════════    │   API    │
└─────────┘   Push updates (live)   └──────────┘
              Only changed data
              Sub-second latency
```

**Benefits:**
- ✅ Single subscription, continuous updates
- ✅ Real-time data (sub-second)
- ✅ Delta updates (only changes sent)
- ✅ No rate limit pressure
- ✅ Lower latency, lower bandwidth

### Performance Comparison

| Metric | Polling (1 sec) | Streaming |
|--------|----------------|-----------|
| **Latency** | 0-1000ms | <100ms |
| **Bandwidth** | High (full payload) | Low (deltas only) |
| **API Calls** | 60/min per market | 0 (after subscribe) |
| **Freshness** | Up to 1s stale | Real-time |
| **Rate Limits** | Hits limits | Minimal impact |

**Conclusion:** Streaming is **essential** for real-time AI market analysis.

---

## Betfair Exchange Stream API Overview

### Endpoints

**Production:**
```
wss://stream-api.betfair.com/api/betting/stream
```

**Integration/Testing:**
```
wss://stream-api-integration.betfair.com/api/betting/stream
```

### Protocol

**Transport:** SSL sockets (WSS - WebSocket Secure equivalent)
**Message Format:** CRLF-delimited JSON (one JSON object per line)
**Authentication:** Session token + app key (must be streaming-enabled)

### Message Types

**Client → Server (Requests):**
- `authentication` - Authenticate session
- `marketSubscription` - Subscribe to market data
- `orderSubscription` - Subscribe to order updates
- `heartbeat` - Keep connection alive

**Server → Client (Responses):**
- `connection` - Connection acknowledgment
- `status` - Subscription status
- `mcm` (Market Change Message) - Market data updates
- `ocm` (Order Change Message) - Order updates

### Data Volume

**Historical Data:** ~1.5TB available for download
**Live Data:** Thousands of markets streaming simultaneously
**Update Frequency:** Configurable (conflate parameter)

---

## Stream Types

### 1. Market Stream

**Purpose:** Real-time market data (prices, volumes, status)

**What you get:**
- Runner prices (back/lay odds)
- Available liquidity at each price
- Traded volumes
- Market status (OPEN, SUSPENDED, CLOSED)
- Last price matched (LPM)

**Use cases for MCP:**
- Monitor odds movements
- Detect value betting opportunities
- Track market liquidity
- Alert on significant price changes

### 2. Order Stream

**Purpose:** Real-time order/bet tracking

**What you get:**
- Bet status (MATCHED, UNMATCHED, CANCELLED)
- Size matched/unmatched
- Average price matched
- Order updates (fills, cancellations)

**Use cases for MCP:**
- Track bet execution
- Monitor bet status
- Calculate P&L in real-time
- Alert on bet fills

### Comparison

| Feature | Market Stream | Order Stream |
|---------|---------------|--------------|
| **Authentication** | Session token | Session token |
| **Data** | Public market data | Private order data |
| **Read-only MCP** | ✅ Essential | ❌ Optional (no betting in MVP) |
| **Update frequency** | High (prices change fast) | Lower (only your bets) |

**For read-only MVP:** Focus on **Market Stream** only.

---

## Protocol & Transport

### Connection Flow

```
1. CONNECT to stream-api.betfair.com (SSL socket)
   │
   ▼
2. SEND authentication message
   {
     "op": "authentication",
     "appKey": "your_app_key",
     "session": "your_session_token"
   }
   │
   ▼
3. RECEIVE connection message
   {
     "op": "connection",
     "connectionId": "001-123456789-123456"
   }
   │
   ▼
4. SEND marketSubscription
   {
     "op": "marketSubscription",
     "marketFilter": { ... },
     "marketDataFilter": { ... },
     "conflateMs": 1000
   }
   │
   ▼
5. RECEIVE status message
   {
     "op": "status",
     "statusCode": "SUCCESS"
   }
   │
   ▼
6. RECEIVE continuous mcm (Market Change Messages)
   {
     "op": "mcm",
     "clk": "AAAAA",
     "pt": 1234567890,
     "mc": [ ... market changes ... ]
   }
```

### Message Format

**CRLF-Delimited JSON:**
Each message is a single line terminated by `\r\n`:

```
{"op":"authentication","appKey":"abc123"}\r\n
{"op":"connection","connectionId":"001-123"}\r\n
{"op":"mcm","clk":"AAAAA","mc":[...]}\r\n
```

**Important:** Messages must NOT contain embedded newlines within JSON.

### Authentication Message

```json
{
  "op": "authentication",
  "id": 1,
  "appKey": "your_app_key",
  "session": "your_session_token"
}
```

**Response:**
```json
{
  "op": "connection",
  "connectionId": "001-1234567890-123456"
}
```

**Error Response:**
```json
{
  "op": "status",
  "id": 1,
  "statusCode": "FAILURE",
  "errorCode": "INVALID_SESSION_INFORMATION",
  "errorMessage": "The session token is invalid"
}
```

---

## Subscription Management

### Market Subscription

**Basic Subscription (All Markets):**
```json
{
  "op": "marketSubscription",
  "id": 2,
  "marketFilter": {},
  "marketDataFilter": {
    "fields": [
      "EX_BEST_OFFERS",
      "EX_MARKET_DEF",
      "EX_TRADED_VOL"
    ]
  },
  "conflateMs": 1000
}
```

### Market Filter Options

**Filter by Event Type (e.g., Football):**
```json
{
  "marketFilter": {
    "eventTypeIds": ["1"]  // 1 = Football
  }
}
```

**Filter by Market IDs:**
```json
{
  "marketFilter": {
    "marketIds": ["1.234567", "1.234568"]
  }
}
```

**Filter by Countries:**
```json
{
  "marketFilter": {
    "countryCodes": ["GB", "IE"]
  }
}
```

**Filter by Market Types:**
```json
{
  "marketFilter": {
    "marketTypes": ["MATCH_ODDS", "OVER_UNDER_25"]
  }
}
```

### Market Data Filter (Fields)

**Available Fields:**

| Field | Description |
|-------|-------------|
| `EX_BEST_OFFERS` | Best 3 back/lay prices |
| `EX_ALL_OFFERS` | Full price ladder |
| `EX_TRADED` | Traded volume |
| `EX_TRADED_VOL` | Traded volume (simplified) |
| `EX_LTP` | Last traded price |
| `EX_MARKET_DEF` | Market definition (runners, etc.) |
| `SP_TRADED` | Starting price traded |
| `SP_PROJECTED` | Starting price projection |

**Minimal Subscription (Lowest bandwidth):**
```json
{
  "marketDataFilter": {
    "fields": ["EX_BEST_OFFERS", "EX_LTP"]
  }
}
```

**Full Subscription (Maximum data):**
```json
{
  "marketDataFilter": {
    "fields": [
      "EX_ALL_OFFERS",
      "EX_TRADED",
      "EX_MARKET_DEF",
      "SP_TRADED",
      "SP_PROJECTED"
    ]
  }
}
```

### Conflate Setting

**`conflateMs`** - Minimum time between updates (milliseconds)

```json
{
  "conflateMs": 1000  // Updates at most once per second
}
```

**Options:**
- `0` - No conflation (every change sent immediately) ⚠️ High volume
- `500` - Updates every 500ms (2 updates/sec)
- `1000` - Updates every 1 second (recommended for most use cases)
- `5000` - Updates every 5 seconds (low-frequency monitoring)

**Trade-offs:**

| conflateMs | Latency | Bandwidth | Use Case |
|------------|---------|-----------|----------|
| 0 | Lowest | Highest | High-frequency trading |
| 500 | Very Low | High | Active monitoring |
| 1000 | Low | Medium | **Recommended for MCP** |
| 5000 | Medium | Low | Background monitoring |

### Resubscription with Clk (Resume from Checkpoint)

**Initial Subscription:**
```json
{
  "op": "marketSubscription",
  "id": 2
}
```

**Receive clk in updates:**
```json
{
  "op": "mcm",
  "clk": "AAAAA",  // ← Save this
  "mc": [...]
}
```

**Reconnect with clk (no full image needed):**
```json
{
  "op": "marketSubscription",
  "id": 2,
  "clk": "AAAAA",  // Resume from here
  "initialClk": "AAAAA"
}
```

**Benefit:** Avoids full market snapshot, receives only changes since disconnect.

---

## Data Structures

### Market Change Message (MCM)

**Structure:**
```json
{
  "op": "mcm",
  "id": 2,
  "clk": "AAAAA",
  "pt": 1234567890123,
  "ct": "SUB_IMAGE",
  "mc": [
    {
      "id": "1.234567",
      "marketDefinition": { ... },
      "rc": [
        {
          "id": 12345,
          "ltp": 3.5,
          "tv": 10000.50,
          "atb": [[3.5, 100], [3.45, 200]],
          "atl": [[3.55, 150], [3.6, 250]]
        }
      ]
    }
  ]
}
```

**Fields:**
- `op` - Operation (always "mcm")
- `id` - Subscription ID
- `clk` - Clock value (checkpoint for reconnection)
- `pt` - Publish time (milliseconds since epoch)
- `ct` - Change type (`SUB_IMAGE`, `RESUB_DELTA`, `HEARTBEAT`)
- `mc` - Market changes (array)

### Market Change (mc)

```json
{
  "id": "1.234567",           // Market ID
  "marketDefinition": { ... }, // Market metadata (sent once or on change)
  "rc": [ ... ],               // Runner changes
  "img": true,                 // True if full image (not delta)
  "tv": 50000.00              // Total matched volume
}
```

### Runner Change (rc)

```json
{
  "id": 12345,                 // Selection ID (runner)
  "ltp": 3.5,                  // Last traded price
  "tv": 10000.50,              // Traded volume on this runner
  "atb": [                     // Available to back (best 3 prices)
    [3.5, 100],                // [price, volume]
    [3.45, 200],
    [3.4, 300]
  ],
  "atl": [                     // Available to lay
    [3.55, 150],
    [3.6, 250],
    [3.65, 350]
  ],
  "batb": [[3.5, 50]],         // Best available to back (top 1)
  "batl": [[3.55, 75]],        // Best available to lay (top 1)
  "spn": 3.52,                 // Starting price (near)
  "spf": 3.50                  // Starting price (far)
}
```

### Market Definition

**Sent once at subscription (or when changed):**
```json
{
  "marketDefinition": {
    "marketId": "1.234567",
    "eventId": "12345678",
    "eventTypeId": "1",         // 1 = Football
    "eventName": "Man Utd vs Liverpool",
    "marketType": "MATCH_ODDS",
    "marketTime": "2025-11-17T15:00:00.000Z",
    "runners": [
      {
        "id": 12345,
        "name": "Man Utd",
        "sortPriority": 1
      },
      {
        "id": 12346,
        "name": "Liverpool",
        "sortPriority": 2
      },
      {
        "id": 12347,
        "name": "The Draw",
        "sortPriority": 3
      }
    ],
    "status": "OPEN",           // INACTIVE, OPEN, SUSPENDED, CLOSED
    "inPlay": false,
    "betDelay": 0,
    "bspMarket": false,
    "complete": true,
    "crossMatching": true,
    "runnersVoidable": false,
    "numberOfActiveRunners": 3,
    "numberOfWinners": 1,
    "totalMatched": 50000.00
  }
}
```

---

## betfairlightweight Streaming Implementation

### Basic Setup

```python
import betfairlightweight
from betfairlightweight.streaming import StreamListener
import queue
import threading

# 1. Create API client
trading = betfairlightweight.APIClient(
    username='your_username',
    password='your_password',
    app_key='your_app_key'  # Must be streaming-enabled
)

# 2. Login
trading.login()

# 3. Create output queue
output_queue = queue.Queue()

# 4. Create stream listener
listener = StreamListener(output_queue=output_queue)

# 5. Create streaming unique ID
stream_unique_id = 1

# 6. Start streaming
betfair_stream = trading.streaming.create_stream(
    unique_id=stream_unique_id,
    listener=listener
)
```

### Subscribe to Markets

```python
# Define market filter
market_filter = betfairlightweight.filters.streaming_market_filter(
    event_type_ids=['1'],  # Football
    country_codes=['GB'],
    market_types=['MATCH_ODDS']
)

# Define data filter
market_data_filter = betfairlightweight.filters.streaming_market_data_filter(
    fields=['EX_BEST_OFFERS', 'EX_MARKET_DEF', 'EX_LTP'],
    ladder_levels=3  # Best 3 price levels
)

# Subscribe
betfair_stream.subscribe_to_markets(
    market_filter=market_filter,
    market_data_filter=market_data_filter,
    conflate_ms=1000,  # 1 update per second
    initial_clk=None,   # None for initial subscription
    clk=None
)

# Start streaming (async=True runs in background thread)
betfair_stream.start(async_=True)
```

### Process Updates

```python
def process_stream_updates():
    """Process updates from queue"""
    while True:
        # Get update from queue (blocks until available)
        market_books = output_queue.get()

        for market_book in market_books:
            print(f"Market: {market_book.market_id}")
            print(f"  Status: {market_book.status}")
            print(f"  Total Matched: {market_book.total_matched}")

            for runner in market_book.runners:
                print(f"  Runner {runner.selection_id}:")
                print(f"    LTP: {runner.last_price_traded}")
                print(f"    Available to Back: {runner.ex.available_to_back}")
                print(f"    Available to Lay: {runner.ex.available_to_lay}")

# Start processing in separate thread
processing_thread = threading.Thread(target=process_stream_updates, daemon=True)
processing_thread.start()
```

### Production Example with Error Handling

```python
import logging
from betfairlightweight.exceptions import BetfairError

logger = logging.getLogger(__name__)

class BetfairStreamer:
    def __init__(self, trading_client):
        self.trading = trading_client
        self.output_queue = queue.Queue()
        self.listener = StreamListener(output_queue=self.output_queue)
        self.stream = None
        self.running = False

    def start_market_stream(self, market_ids=None, event_type_ids=None):
        """Start streaming market data"""
        try:
            # Create stream
            self.stream = self.trading.streaming.create_stream(
                unique_id=1,
                listener=self.listener
            )

            # Market filter
            market_filter = betfairlightweight.filters.streaming_market_filter(
                market_ids=market_ids,
                event_type_ids=event_type_ids
            )

            # Data filter (minimal for efficiency)
            data_filter = betfairlightweight.filters.streaming_market_data_filter(
                fields=['EX_BEST_OFFERS', 'EX_LTP']
            )

            # Subscribe
            self.stream.subscribe_to_markets(
                market_filter=market_filter,
                market_data_filter=data_filter,
                conflate_ms=1000
            )

            # Start
            self.stream.start(async_=True)
            self.running = True

            logger.info("Market stream started successfully")

        except BetfairError as e:
            logger.error(f"Failed to start stream: {e}")
            raise

    def stop(self):
        """Stop streaming"""
        if self.stream:
            self.stream.stop()
            self.running = False
            logger.info("Market stream stopped")

    def get_latest_updates(self, timeout=1):
        """Get latest updates from queue (non-blocking)"""
        try:
            return self.output_queue.get(timeout=timeout)
        except queue.Empty:
            return None
```

---

## Reconnection Strategies

### Challenge: Connection Drops

**Causes:**
- Network issues
- Server maintenance
- Idle timeout
- Session expiry

**Without reconnection:** Data loss, stale information

### Strategy 1: Auto-Reconnect with Exponential Backoff

```python
import time
import random

class AutoReconnectStreamer(BetfairStreamer):
    def __init__(self, trading_client, max_retries=5):
        super().__init__(trading_client)
        self.max_retries = max_retries
        self.last_clk = None  # Save checkpoint

    def start_with_reconnect(self, market_ids=None):
        """Start with auto-reconnect"""
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Start stream
                self.start_market_stream(market_ids=market_ids)

                # Monitor stream health
                while self.running:
                    updates = self.get_latest_updates(timeout=5)

                    if updates:
                        # Save clk for reconnection
                        for update in updates:
                            if hasattr(update, 'publish_time'):
                                self.last_clk = getattr(update, 'clk', None)

                    # Check if stream is still alive
                    if not self.stream or not self.stream.running:
                        raise ConnectionError("Stream died")

            except (ConnectionError, BetfairError) as e:
                retry_count += 1
                logger.warning(f"Stream error: {e}. Retry {retry_count}/{self.max_retries}")

                # Exponential backoff with jitter
                wait_time = min(2 ** retry_count, 60) + random.uniform(0, 1)
                time.sleep(wait_time)

                # Attempt reconnection with last clk
                logger.info(f"Reconnecting with clk: {self.last_clk}")

        logger.error("Max retries exceeded. Stream failed.")
```

### Strategy 2: Heartbeat Monitoring

```python
import time
from datetime import datetime, timedelta

class HeartbeatMonitor:
    def __init__(self, stream, timeout_seconds=30):
        self.stream = stream
        self.timeout = timeout_seconds
        self.last_heartbeat = datetime.now()

    def check_heartbeat(self):
        """Check if stream is still alive"""
        # Update last heartbeat from stream
        if self.stream.running:
            self.last_heartbeat = datetime.now()

        # Check timeout
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        if elapsed > self.timeout:
            logger.warning(f"No heartbeat for {elapsed}s. Reconnecting...")
            return False

        return True

    def monitor_loop(self):
        """Background monitoring"""
        while True:
            if not self.check_heartbeat():
                # Trigger reconnection
                self.stream.stop()
                # ... reconnection logic

            time.sleep(10)  # Check every 10 seconds
```

---

## MCP Integration Patterns

### Challenge: MCP is Request/Response, Streaming is Push-Based

**Problem:** MCP tools are synchronous functions, but streaming provides asynchronous updates.

**Solution:** Hybrid architecture with background streaming + cached state.

### Pattern 1: Background Streamer + State Cache

```python
import asyncio
from fastmcp import FastMCP

mcp = FastMCP("betfair")

# Global state cache
market_cache = {}
cache_lock = asyncio.Lock()

# Background streaming task
async def stream_market_data():
    """Background task that updates cache"""
    streamer = BetfairStreamer(trading_client)
    streamer.start_market_stream(event_type_ids=['1'])  # Football

    while True:
        updates = await asyncio.to_thread(streamer.get_latest_updates)

        if updates:
            async with cache_lock:
                for market_book in updates:
                    market_cache[market_book.market_id] = {
                        'status': market_book.status,
                        'total_matched': market_book.total_matched,
                        'runners': [
                            {
                                'id': r.selection_id,
                                'ltp': r.last_price_traded,
                                'back': r.ex.available_to_back[:3],
                                'lay': r.ex.available_to_lay[:3]
                            }
                            for r in market_book.runners
                        ],
                        'last_update': time.time()
                    }

# MCP Tool: Query cached data
@mcp.tool()
async def get_live_market_prices(market_id: str) -> dict:
    """Get real-time market prices (from streaming cache)"""
    async with cache_lock:
        if market_id in market_cache:
            return market_cache[market_id]
        else:
            return {"error": "Market not found in stream"}

# Start background streamer on MCP server startup
async def on_startup():
    asyncio.create_task(stream_market_data())
```

### Pattern 2: Subscription Management via MCP Tools

```python
@mcp.tool()
async def subscribe_to_market(market_id: str) -> dict:
    """Subscribe to real-time updates for a market"""
    # Add market to streaming subscription
    streamer.add_market(market_id)
    return {"status": "subscribed", "market_id": market_id}

@mcp.tool()
async def unsubscribe_from_market(market_id: str) -> dict:
    """Unsubscribe from market updates"""
    streamer.remove_market(market_id)
    return {"status": "unsubscribed", "market_id": market_id}

@mcp.tool()
async def get_streaming_stats() -> dict:
    """Get streaming statistics"""
    return {
        "active_markets": len(market_cache),
        "updates_received": streamer.total_updates,
        "stream_uptime": streamer.uptime_seconds(),
        "last_update": max(m['last_update'] for m in market_cache.values())
    }
```

### Pattern 3: MCP Resources for Streaming Data

```python
@mcp.resource("betfair://stream/markets")
async def list_streaming_markets() -> str:
    """List all markets currently being streamed"""
    async with cache_lock:
        markets = [
            {
                'market_id': market_id,
                'last_update_age': time.time() - data['last_update']
            }
            for market_id, data in market_cache.items()
        ]
    return json.dumps(markets, indent=2)

@mcp.resource("betfair://stream/market/{market_id}")
async def get_streaming_market(market_id: str) -> str:
    """Get streaming data for specific market"""
    async with cache_lock:
        data = market_cache.get(market_id)
    if data:
        return json.dumps(data, indent=2)
    else:
        raise ValueError(f"Market {market_id} not in stream")
```

---

## Performance Optimization

### 1. Conflate Setting Tuning

**High-frequency (HFT):**
```python
conflate_ms=0  # Every update (⚠️ very high volume)
```

**Active monitoring:**
```python
conflate_ms=500  # 2 updates/second
```

**MCP Server (recommended):**
```python
conflate_ms=1000  # 1 update/second (good balance)
```

**Background monitoring:**
```python
conflate_ms=5000  # 1 update per 5 seconds
```

### 2. Field Selection

**Minimal (lowest bandwidth):**
```python
fields=['EX_BEST_OFFERS']  # Only best back/lay prices
```

**Balanced:**
```python
fields=['EX_BEST_OFFERS', 'EX_LTP', 'EX_TRADED_VOL']
```

**Full (highest bandwidth):**
```python
fields=['EX_ALL_OFFERS', 'EX_TRADED', 'EX_MARKET_DEF', 'SP_TRADED']
```

### 3. Market Filtering

**Don't subscribe to ALL markets - filter intelligently:**

```python
# ❌ BAD - Subscribes to thousands of markets
market_filter = {}  # No filter

# ✅ GOOD - Specific event types
market_filter = {
    'event_type_ids': ['1', '2'],  # Football, Tennis only
    'market_types': ['MATCH_ODDS'],
    'in_play_only': True
}
```

### 4. Queue Management

**Prevent queue overflow:**

```python
# Limited queue size
output_queue = queue.Queue(maxsize=1000)

# Process updates fast enough
def fast_processor():
    while True:
        updates = output_queue.get()
        # Quick processing only
        # Don't do heavy computation here
```

### 5. Batching Updates

**Don't process every individual update - batch them:**

```python
def batch_processor(batch_size=10, timeout=1):
    """Process updates in batches"""
    batch = []

    while True:
        try:
            update = output_queue.get(timeout=timeout)
            batch.append(update)

            if len(batch) >= batch_size:
                process_batch(batch)
                batch = []

        except queue.Empty:
            if batch:
                process_batch(batch)
                batch = []
```

---

## References

### Official Documentation
- [Exchange Stream API](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Exchange+Stream+API)
- [Stream API Sample Code](https://github.com/betfair/stream-api-sample-code)
- [Market Data from Stream API](https://support.developer.betfair.com/hc/en-us/articles/6540502258077)

### betfairlightweight
- [Streaming Documentation](https://betcode-org.github.io/betfair/streaming/)
- [Example Streaming Code](https://github.com/betcode-org/betfair/blob/master/examples/examplestreaming.py)
- [Error Handling Example](https://github.com/betcode-org/betfair/blob/master/examples/examplestreamingerrhandling.py)

### Related Research Documents
- [RESEARCH_02_RATE_LIMITS.md](./RESEARCH_02_RATE_LIMITS.md) - Why streaming avoids rate limits
- [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md) - SDK streaming internals
- [RESEARCH_05_FASTMCP_INTEGRATION.md](./RESEARCH_05_FASTMCP_INTEGRATION.md) - MCP integration patterns

---

**Next Document:** [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md)
**Previous Document:** [RESEARCH_02_RATE_LIMITS.md](./RESEARCH_02_RATE_LIMITS.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
