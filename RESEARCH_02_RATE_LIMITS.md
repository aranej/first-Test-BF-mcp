# Betfair MCP Server - Rate Limits & Throttling Research

**Document:** RESEARCH_02_RATE_LIMITS.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Betfair Rate Limit Architecture](#betfair-rate-limit-architecture)
3. [Specific API Rate Limits](#specific-api-rate-limits)
4. [Error Codes & Responses](#error-codes--responses)
5. [Retry Strategies](#retry-strategies)
6. [Client-Side Rate Limiting](#client-side-rate-limiting)
7. [Best Practices](#best-practices)
8. [Implementation for MCP Server](#implementation-for-mcp-server)
9. [Monitoring & Alerting](#monitoring--alerting)
10. [References](#references)

---

## Executive Summary

**Key Finding:** Betfair has **NO general API throttling**, only specific operation limits.

**Critical Limits:**
- 🔴 **Login:** 100 successful logins/minute → 20-minute ban
- 🟡 **listMarketBook:** 5 requests/second per MarketID
- 🟡 **Betting Operations:** 1,000 transactions/second (placeOrders, cancelOrders, etc.)
- 🟡 **Market Data Weight:** Max 200 points per request
- 🟡 **Historical Data API:** 100 requests per 10 seconds

**Recommended Strategy:**
- ✅ Implement exponential backoff with jitter for 429 errors
- ✅ Client-side rate limiting (token bucket algorithm)
- ✅ Connection pooling with `keep-alive` headers
- ✅ Respect `Retry-After` headers
- ✅ Monitor and log rate limit errors

---

## Betfair Rate Limit Architecture

### General Throttling Policy

**Official Statement:**
> "There is currently no general throttling on the API, only limits on some requests."

This means:
- ✅ Most API operations have NO hard rate limits
- ⚠️ Specific operations have targeted limits (see below)
- 🎯 Fair use policy applies (excessive usage may be flagged)

### Rate Limit Philosophy

Betfair's approach:
1. **Operation-specific limits** - Protect critical systems (betting, market data)
2. **Weight-based limits** - Prevent data-heavy requests
3. **Account-level limits** - Prevent abuse (login throttling)
4. **No blanket throttling** - Allow legitimate high-frequency usage

---

## Specific API Rate Limits

### 1. Login Operations

**Limit:** 100 successful logins per minute
**Consequence:** 20-minute temporary ban (`TEMPORARY_BAN_TOO_MANY_REQUESTS`)

**Error Response:**
```json
{
  "faultcode": "Client",
  "faultstring": "ANGX-0004",
  "detail": {
    "LoginException": {
      "errorCode": "TEMPORARY_BAN_TOO_MANY_REQUESTS"
    }
  }
}
```

**Mitigation:**
- Use `keep_alive()` instead of repeated logins
- Single session for all operations
- Session pooling for multi-threaded applications
- Never login per-request (critical!)

**Example Safe Pattern:**
```python
# ❌ WRONG - Login per request
def get_markets():
    client.login()  # DON'T DO THIS!
    return client.betting.list_market_catalogue()

# ✅ CORRECT - Single session
client.login()  # Once at startup
# ... later in code
def get_markets():
    return client.betting.list_market_catalogue()  # Reuse session
```

---

### 2. Market Data Operations

#### listMarketBook

**Limit:** 5 requests per second **per MarketID**

**What this means:**
- Same MarketID: Max 5 req/sec
- Different MarketIDs: No combined limit

**Example:**
```python
# ✅ OK - Different market IDs
for market_id in ['1.234', '1.235', '1.236']:
    client.betting.list_market_book(market_ids=[market_id])
    # No delay needed

# ⚠️ THROTTLED - Same market ID repeatedly
market_id = '1.234'
for _ in range(10):
    client.betting.list_market_book(market_ids=[market_id])
    # Will hit rate limit after 5th request
```

**MCP Server Implication:**
- Cache market book data for frequently accessed markets
- Implement per-market-ID rate limiting
- Use streaming API for real-time updates (no polling needed)

#### listMarketCatalogue

**Limit:** Subject to weight-based limiting (see below)

#### listMarketProfitAndLoss

**Limit:** Subject to weight-based limiting (see below)

---

### 3. Weight-Based Limits

**Formula:** `SUM(Weight × Number of Market IDs) ≤ 200 points per request`

**Market Data Weights:**

| Data Type | Weight per Market |
|-----------|-------------------|
| EX_BEST_OFFERS | 1 |
| EX_ALL_OFFERS | 2 |
| EX_TRADED | 3 |
| SP_AVAILABLE | 1 |
| SP_TRADED | 1 |

**Example Calculation:**
```python
# Request: 50 markets with EX_ALL_OFFERS
weight = 50 × 2 = 100 points  # ✅ OK (< 200)

# Request: 150 markets with EX_ALL_OFFERS
weight = 150 × 2 = 300 points  # ❌ TOO_MUCH_DATA error
```

**Error Response:**
```json
{
  "faultcode": "Server",
  "faultstring": "DSC-0018",
  "detail": {
    "APINGException": {
      "errorCode": "TOO_MUCH_DATA",
      "errorDetails": "Request exceeds maximum data weight"
    }
  }
}
```

**Mitigation Strategy:**
```python
def batch_markets_by_weight(market_ids, data_type='EX_BEST_OFFERS'):
    """Split market requests to stay under 200-point limit"""
    weights = {
        'EX_BEST_OFFERS': 1,
        'EX_ALL_OFFERS': 2,
        'EX_TRADED': 3,
        'SP_AVAILABLE': 1,
        'SP_TRADED': 1
    }

    weight_per_market = weights.get(data_type, 1)
    max_markets = 200 // weight_per_market

    # Split into batches
    batches = []
    for i in range(0, len(market_ids), max_markets):
        batches.append(market_ids[i:i + max_markets])

    return batches

# Usage
market_ids = ['1.234', '1.235', ...]  # 300 markets
batches = batch_markets_by_weight(market_ids, 'EX_ALL_OFFERS')
# Returns: [[1.234...1.333], [1.334...1.433], [1.434...1.533]]
```

---

### 4. Betting Operations

**Limit:** 1,000 individual transactions per second

**Applies to:**
- `placeOrders`
- `cancelOrders`
- `updateOrders`
- `replaceOrders`

**Important:** Limit is on **individual transactions**, not requests.

**Example:**
```python
# Single request with 1,500 bet instructions
place_orders_request = {
    'marketId': '1.234',
    'instructions': [... 1500 bets ...]  # ❌ Exceeds 1,000/sec
}
# Error: TOO_MANY_REQUESTS

# Solution: Batch into multiple requests
batch_1 = instructions[0:1000]   # 1,000 bets
batch_2 = instructions[1000:1500]  # 500 bets
# Send separately
```

**MCP Server Consideration:**
- Read-only MVP: Not applicable
- Future betting features: Implement batching + rate limiting

---

### 5. Historical Data API

**Limit:** 100 requests per 10 seconds

**Error:** HTTP 429 Too Many Requests

**Endpoint:** `https://historicdata.betfair.com/api`

**Mitigation:**
```python
import time
from collections import deque

class HistoricalDataRateLimiter:
    def __init__(self, max_requests=100, time_window=10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_times = deque(maxlen=max_requests)

    def wait_if_needed(self):
        """Block if we've hit the rate limit"""
        now = time.time()

        # Remove requests older than time_window
        while self.request_times and now - self.request_times[0] > self.time_window:
            self.request_times.popleft()

        # If at limit, wait until oldest request expires
        if len(self.request_times) >= self.max_requests:
            sleep_time = self.time_window - (now - self.request_times[0]) + 0.1
            time.sleep(sleep_time)

        self.request_times.append(time.time())
```

---

## Error Codes & Responses

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Continue normally |
| 400 | Bad Request | Fix request parameters |
| 429 | Too Many Requests | Implement backoff |
| 503 | Service Unavailable | Retry with backoff |

### Betfair-Specific Error Codes

| Error Code | Description | Mitigation |
|------------|-------------|------------|
| `TOO_MANY_REQUESTS` | Exceeded betting operations limit | Batch requests, add delays |
| `TOO_MUCH_DATA` | Exceeded weight limit (200 points) | Reduce market count or data granularity |
| `TEMPORARY_BAN_TOO_MANY_REQUESTS` | Exceeded login limit | Use keep_alive(), single session |
| `TIMEOUT_ERROR` | Request timed out | Retry with exponential backoff |

### Error Response Structure

**Standard APINGException:**
```json
{
  "detail": {
    "exceptionname": "APINGException",
    "APINGException": {
      "errorCode": "TOO_MANY_REQUESTS",
      "errorDetails": "Transaction limit exceeded",
      "requestUUID": "prdang-12345-67890"
    }
  },
  "faultcode": "Server",
  "faultstring": "ANGX-0010"
}
```

**Login Exception:**
```json
{
  "detail": {
    "LoginException": {
      "errorCode": "TEMPORARY_BAN_TOO_MANY_REQUESTS"
    }
  },
  "faultcode": "Client",
  "faultstring": "ANGX-0004"
}
```

---

## Retry Strategies

### 1. Check for Retry-After Header

**HTTP 429 Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**Always respect this header:**
```python
import requests
import time

response = requests.get(url)
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    # Retry request
```

---

### 2. Exponential Backoff with Jitter

**Algorithm:** Truncated exponential backoff with full jitter

**Formula:**
```
wait_time = random(1, min(2^tries, 60))
```

**Implementation:**
```python
import random
import time

def exponential_backoff_retry(func, max_retries=5):
    """Retry with exponential backoff + jitter"""
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code != 429:
                raise  # Don't retry non-429 errors

            if attempt == max_retries - 1:
                raise  # Final attempt failed

            # Calculate backoff with jitter
            max_wait = min(2 ** attempt, 60)  # Cap at 60 seconds
            wait_time = random.uniform(1, max_wait)

            print(f"Rate limited. Retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
```

**Why Jitter?**
- Prevents thundering herd problem
- Distributes retry timing across multiple clients
- Reduces collision probability

---

### 3. Circuit Breaker Pattern

For persistent rate limit errors, implement circuit breaker:

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None

    def call(self, func):
        if self.state == CircuitState.OPEN:
            # Check if timeout elapsed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED

    def on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

---

## Client-Side Rate Limiting

### Token Bucket Algorithm

**Concept:** You have `n` tokens to spend over a time window.

**Implementation:**
```python
import time
from threading import Lock

class TokenBucket:
    """Thread-safe token bucket rate limiter"""

    def __init__(self, tokens, refill_time):
        """
        Args:
            tokens: Number of tokens in bucket
            refill_time: Seconds to fully refill bucket
        """
        self.capacity = tokens
        self.tokens = tokens
        self.refill_rate = tokens / refill_time
        self.last_refill = time.time()
        self.lock = Lock()

    def consume(self, tokens=1):
        """
        Attempt to consume tokens. Blocks if insufficient tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False otherwise
        """
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                # Calculate wait time
                needed = tokens - self.tokens
                wait_time = needed / self.refill_rate
                time.sleep(wait_time)

                self._refill()
                self.tokens -= tokens
                return True

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

# Usage for listMarketBook (5 req/sec per market)
market_rate_limiter = TokenBucket(tokens=5, refill_time=1.0)

def get_market_book(market_id):
    market_rate_limiter.consume(1)  # Wait if needed
    return client.betting.list_market_book(market_ids=[market_id])
```

---

## Best Practices

### 1. Connection Management

**Use persistent connections:**
```python
import requests

# ✅ Create session once
session = requests.Session()
session.headers.update({
    'X-Application': app_key,
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate'
})

# Reuse for all requests
response = session.post(url, json=data)
```

**Benefits:**
- Reduces latency (no SSL handshake per request)
- Server-friendly (fewer connections)
- Better rate limit efficiency

---

### 2. Request Compression

**Always send compression headers:**
```http
Accept-Encoding: gzip, deflate
```

**Implementation (betfairlightweight handles this automatically):**
```python
# Already configured in betfairlightweight
client = betfairlightweight.APIClient(...)
# Automatically sends Accept-Encoding header
```

**Benefits:**
- Smaller payloads
- Faster transmission
- Less bandwidth usage
- May improve effective rate limits

---

### 3. Idempotent Request Design

**Make requests safe to retry:**
```python
# ❌ NON-IDEMPOTENT - Creates new bet each retry
def place_bet():
    return client.betting.place_orders(instructions=[...])

# ✅ IDEMPOTENT - Uses customer_ref to prevent duplicates
def place_bet_safe():
    customer_ref = f"bet-{uuid.uuid4()}"  # Unique ID
    return client.betting.place_orders(
        instructions=[{
            'selectionId': 12345,
            'customerRef': customer_ref,  # Prevents duplicate bets
            # ... other params
        }]
    )
```

---

### 4. Logging & Monitoring

**Log rate limit events:**
```python
import logging

logger = logging.getLogger(__name__)

def handle_rate_limit_error(error, request_info):
    logger.warning(
        "Rate limit hit",
        extra={
            'error_code': error.error_code,
            'endpoint': request_info['endpoint'],
            'timestamp': time.time(),
            'retry_after': error.retry_after
        }
    )
```

**Metrics to track:**
- 429 error frequency
- Retry success rate
- Average wait times
- Circuit breaker state changes
- Token bucket utilization

---

## Implementation for MCP Server

### Rate Limiter Module

**File:** `src/betfair_mcp/rate_limiter.py`

```python
"""
Rate limiting for Betfair MCP Server
"""
import time
from collections import deque
from threading import Lock
from typing import Dict

class BetfairRateLimiter:
    """Comprehensive rate limiter for Betfair API"""

    def __init__(self):
        # Per-market rate limiting (5 req/sec per market)
        self.market_limiters: Dict[str, TokenBucket] = {}
        self.market_lock = Lock()

        # Global login protection (100/min)
        self.login_limiter = SlidingWindowLimiter(
            max_requests=100,
            window_seconds=60
        )

    def check_market_request(self, market_id: str):
        """Rate limit for listMarketBook per market"""
        with self.market_lock:
            if market_id not in self.market_limiters:
                # 5 tokens, refill every 1 second
                self.market_limiters[market_id] = TokenBucket(5, 1.0)

        self.market_limiters[market_id].consume(1)

    def check_login(self):
        """Rate limit for login operations"""
        if not self.login_limiter.allow():
            raise RateLimitError("Login rate limit exceeded (100/min)")

class SlidingWindowLimiter:
    """Sliding window rate limiter"""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = Lock()

    def allow(self) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()

            # Remove old requests outside window
            while self.requests and now - self.requests[0] > self.window_seconds:
                self.requests.popleft()

            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False
```

### Integration with MCP Tools

```python
# src/betfair_mcp/tools/market_data.py
from fastmcp import FastMCP
from ..rate_limiter import BetfairRateLimiter

mcp = FastMCP("betfair")
rate_limiter = BetfairRateLimiter()

@mcp.tool()
def get_market_prices(market_id: str) -> dict:
    """Get current prices for a market (rate-limited)"""

    # Apply rate limiting
    rate_limiter.check_market_request(market_id)

    # Make API request
    try:
        market_book = client.betting.list_market_book(
            market_ids=[market_id]
        )
        return market_book[0]
    except APINGException as e:
        if e.error_code == 'TOO_MANY_REQUESTS':
            # Implement backoff
            return exponential_backoff_retry(
                lambda: client.betting.list_market_book(market_ids=[market_id])
            )
        raise
```

---

## Monitoring & Alerting

### Metrics Dashboard

**Key Metrics:**
1. **Request Rate:** Requests/second per endpoint
2. **Error Rate:** 429 errors per minute
3. **Retry Rate:** Percentage of requests retried
4. **Latency:** P50, P95, P99 response times
5. **Circuit Breaker State:** Open/Closed/Half-Open

**Prometheus Metrics Example:**
```python
from prometheus_client import Counter, Histogram

# Define metrics
rate_limit_errors = Counter(
    'betfair_rate_limit_errors_total',
    'Total rate limit errors',
    ['endpoint']
)

request_duration = Histogram(
    'betfair_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

# Instrument code
@request_duration.labels(endpoint='listMarketBook').time()
def get_market_book(market_id):
    try:
        return client.betting.list_market_book(market_ids=[market_id])
    except RateLimitError:
        rate_limit_errors.labels(endpoint='listMarketBook').inc()
        raise
```

### Alerting Rules

**Alert on:**
- Rate limit errors > 10/minute (sustained 5 min)
- Circuit breaker open for > 2 minutes
- Login failures approaching limit (> 80 logins/min)
- Token bucket frequently empty (> 50% of time)

---

## References

### Official Documentation
- [Betfair Best Practices](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Best+Practice)
- [Market Data Request Limits](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Market+Data+Request+Limits)
- [Betting Exceptions](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Betting+Exceptions)

### Related Research Documents
- [RESEARCH_01_AUTHENTICATION.md](./RESEARCH_01_AUTHENTICATION.md) - Login rate limits
- [RESEARCH_03_STREAMING_API.md](./RESEARCH_03_STREAMING_API.md) - Alternative to polling
- [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md) - SDK rate limit handling

---

**Next Document:** [RESEARCH_03_STREAMING_API.md](./RESEARCH_03_STREAMING_API.md)
**Previous Document:** [RESEARCH_01_AUTHENTICATION.md](./RESEARCH_01_AUTHENTICATION.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
