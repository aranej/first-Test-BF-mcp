# Betfair MCP Server - Authentication Research

**Document:** RESEARCH_01_AUTHENTICATION.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Authentication Architecture](#authentication-architecture)
3. [Application Keys (App Keys)](#application-keys-app-keys)
4. [Session Tokens](#session-tokens)
5. [Certificate-Based Authentication](#certificate-based-authentication)
6. [Session Management](#session-management)
7. [Best Practices for MCP Server](#best-practices-for-mcp-server)
8. [Security Considerations](#security-considerations)
9. [Implementation Recommendations](#implementation-recommendations)
10. [References](#references)

---

## Executive Summary

Betfair Exchange API uses a **two-tier authentication system**:
- **Application Keys (App Keys)** - Identify your application (16-character identifier)
- **Session Tokens** - Authenticate individual sessions (time-limited, renewable)

For automated systems like our MCP server, **certificate-based authentication** provides enhanced security and reliability.

**Key Findings:**
- ✅ Two app key types: Delayed (dev/testing) and Live (production)
- ✅ Session tokens expire between 20 minutes and 24 hours (default: 24h)
- ✅ `keep_alive()` extends sessions without re-login
- ✅ SSL certificates enable non-interactive authentication for bots
- ✅ Rate limit: Max 100 logins per minute → 20-minute temporary ban

---

## Authentication Architecture

### Two-Level Security Model

```
┌─────────────────────────────────────────┐
│         Betfair API Request             │
├─────────────────────────────────────────┤
│  Header: X-Application: <APP_KEY>       │ ← Level 1: App Identification
│  Header: X-Authentication: <SESSION>    │ ← Level 2: Session Auth
└─────────────────────────────────────────┘
```

**Level 1: Application Keys**
- Identifies which application is making requests
- Included in EVERY API request header
- Obtained once, reused indefinitely
- Two types per account: Delayed (active) and Live (inactive by default)

**Level 2: Session Tokens**
- Authenticates the current user session
- Time-limited (configurable expiry)
- Renewable via `keep_alive` endpoint
- Must be refreshed before expiry

---

## Application Keys (App Keys)

### Overview

Application Keys are **16-character identifiers** required for all Betfair API requests.

**Structure:**
```
X-Application: AbCd1234EfGh5678
                └─────┬─────┘
              16 characters
```

### Two Key Types

Every Betfair account receives **two Application Keys**:

| Key Type | Status | Purpose | Use Case |
|----------|--------|---------|----------|
| **Delayed Key** | Active by default | Development & Testing | Non-production environments, testing MCP server |
| **Live Key** | Inactive (requires application) | Production betting | Real money betting, production MCP deployment |

**Important:** Delayed keys may have behavioral differences compared to live keys (e.g., data latency, market availability).

### Creating App Keys

**Method 1: Accounts API Demo Tool**
1. Navigate to Betfair Accounts API Demo Tool
2. Select `createDeveloperAppKeys` operation
3. Login to www.betfair.com in separate browser tab
4. Refresh Demo Tool page (auto-fills session token)
5. Execute request

**Method 2: Programmatic Creation**
```python
# Using betfairlightweight
trading.account.create_developer_app_keys()
```

### Retrieving Existing App Keys

**Via API:**
```python
trading.account.get_developer_app_keys()
```

**Returns:**
```json
[
  {
    "app_name": "my-mcp-server",
    "app_id": 1234,
    "app_versions": [
      {
        "version_id": 5678,
        "version": "1.0",
        "application_key": "AbCd1234EfGh5678",
        "delay_data": true,  // Delayed Key
        "subscription_required": false,
        "owner": "username",
        "owner_managed": true
      }
    ]
  }
]
```

### Activating Live Keys

Live keys require **application to Betfair** with justification for production use. This typically involves:
- Demonstrating application functionality
- Providing use case details
- Agreeing to terms of service
- Potential vendor certification (for commercial applications)

---

## Session Tokens

### Overview

Session tokens authenticate individual API sessions and must be obtained via login before making requests.

**Characteristics:**
- Unique per session
- Time-limited (configurable expiry)
- Can be extended via `keep_alive()`
- Automatically invalidated on logout

### Obtaining Session Tokens

**Three Login Methods:**

#### 1. Interactive Login (Web-Based)
Most common for manual testing:

```python
import betfairlightweight

trading = betfairlightweight.APIClient(
    username='your_username',
    password='your_password',
    app_key='your_app_key'
)

trading.login()  # Returns session token
```

**API Endpoint:** `https://identitysso.betfair.com/api/login`

**HTTP Method:** POST

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "sessionToken": "abc123def456...",
  "loginStatus": "SUCCESS"
}
```

#### 2. Non-Interactive Login (Certificate-Based)
Preferred for automated systems:

```python
trading = betfairlightweight.APIClient(
    username='your_username',
    password='your_password',
    app_key='your_app_key',
    certs='/path/to/certs'  # SSL certificate directory
)

trading.login()
```

**API Endpoint:** `https://identitysso-cert.betfair.com/api/certlogin`

**Requires:** Client SSL certificate (.crt) and private key (.key)

#### 3. Browser Session Extraction (Testing Only)
For development, you can extract session token from browser cookies while logged into www.betfair.com:
- Cookie name: `ssoid`
- **Warning:** Expires quickly, not suitable for production

### Session Expiry

**Configurable Expiry Times:**
- Minimum: **20 minutes**
- Maximum: **24 hours**
- Default: **24 hours**

**Expiry varies based on:**
- User preferences
- Jurisdiction regulations
- Account type (personal vs. vendor)

### Extending Sessions: `keep_alive()`

Instead of re-logging in, extend existing sessions:

```python
# Refresh session before expiry
trading.keep_alive()
```

**API Endpoint:** `https://identitysso.betfair.com/api/keepAlive`

**Best Practice:** Call `keep_alive()` every 12 hours for 24-hour sessions.

**betfairlightweight Automatic Handling:**
The library tracks session expiry internally and can auto-refresh if configured:

```python
# Session considered expired if:
# - login_time is not set, OR
# - seconds since login > (session_timeout / 2)

# Default timeout: 12 hours
```

---

## Certificate-Based Authentication

### Why Certificates?

For MCP servers and automated systems, **certificate-based authentication** offers:

✅ **Non-interactive** - No username/password in code
✅ **Higher security** - mTLS (mutual TLS)
✅ **Bot/Vendor tier** - Enhanced permissions
✅ **Production-ready** - Industry standard for APIs

### Obtaining SSL Certificates

**Step 1: Generate Certificate Signing Request (CSR)**
```bash
openssl req -new -newkey rsa:2048 -nodes \
  -keyout client-2048.key \
  -out client-2048.csr
```

**Step 2: Submit CSR to Betfair**
- Login to Betfair Developer Portal
- Navigate to Certificate Management
- Upload CSR file
- Await approval (typically 1-2 business days)

**Step 3: Download Signed Certificate**
Betfair returns:
- `client-2048.crt` - Your signed certificate
- `ca-bundle.crt` - Certificate Authority bundle (optional)

**Step 4: Configure betfairlightweight**
```python
trading = betfairlightweight.APIClient(
    username='your_username',
    password='your_password',
    app_key='your_app_key',
    certs='/path/to/certs/'  # Directory containing .crt and .key files
)
```

**Certificate Directory Structure:**
```
/path/to/certs/
├── client-2048.crt
├── client-2048.key
└── ca-bundle.crt (optional)
```

### Certificate Rotation

**Best Practices:**
- Rotate certificates annually
- Maintain backup certificates (overlap period)
- Monitor certificate expiry dates
- Automate rotation where possible

---

## Session Management

### Session Lifecycle

```
┌──────────┐   login()    ┌───────────┐   keep_alive()   ┌────────────┐
│  No      │  ────────>   │  Active   │  ─────────────>  │  Extended  │
│ Session  │              │  Session  │   (every 12h)    │  Session   │
└──────────┘              └───────────┘                  └────────────┘
                               │                               │
                               │ logout()                      │ logout()
                               ▼                               ▼
                          ┌──────────┐                    ┌──────────┐
                          │ Logged   │                    │ Logged   │
                          │   Out    │                    │   Out    │
                          └──────────┘                    └──────────┘
```

### Concurrent Sessions

**Important:** A single session token can be used across **multiple concurrent API calls and threads**.

**Best Practice for MCP Server:**
- ✅ Single session shared across all MCP tool calls
- ✅ Use connection pooling (requests.Session)
- ✅ Implement thread-safe session management
- ❌ Don't create new session per request (rate limit abuse)

**Example (betfairlightweight):**
```python
import betfairlightweight
from threading import Lock

class BetfairSessionManager:
    def __init__(self, username, password, app_key, certs=None):
        self.client = betfairlightweight.APIClient(
            username=username,
            password=password,
            app_key=app_key,
            certs=certs
        )
        self.lock = Lock()
        self.session_active = False

    def ensure_logged_in(self):
        with self.lock:
            if not self.session_active:
                self.client.login()
                self.session_active = True

    def keep_alive(self):
        with self.lock:
            if self.session_active:
                self.client.keep_alive()
```

---

## Best Practices for MCP Server

### 1. Environment-Based Credentials

**Never hardcode credentials.** Use environment variables:

```python
import os
import betfairlightweight

trading = betfairlightweight.APIClient(
    username=os.getenv('BETFAIR_USERNAME'),
    password=os.getenv('BETFAIR_PASSWORD'),
    app_key=os.getenv('BETFAIR_APP_KEY'),
    certs=os.getenv('BETFAIR_CERTS_PATH')  # Optional
)
```

**MCP Server Configuration:**
```json
{
  "mcpServers": {
    "betfair": {
      "command": "uv",
      "args": ["run", "betfair-mcp"],
      "env": {
        "BETFAIR_USERNAME": "${BETFAIR_USER}",
        "BETFAIR_PASSWORD": "${BETFAIR_PASS}",
        "BETFAIR_APP_KEY": "${BETFAIR_KEY}",
        "BETFAIR_CERTS_PATH": "${BETFAIR_CERTS}"
      }
    }
  }
}
```

### 2. Session Token Refresh Strategy

**Automatic Refresh Before Expiry:**
```python
import time
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, client):
        self.client = client
        self.login_time = None
        self.session_duration = timedelta(hours=24)

    def login(self):
        self.client.login()
        self.login_time = datetime.now()

    def refresh_if_needed(self):
        """Refresh session if > 12 hours old (half of 24h default)"""
        if self.login_time is None:
            self.login()
            return

        elapsed = datetime.now() - self.login_time
        if elapsed > timedelta(hours=12):
            self.client.keep_alive()
            self.login_time = datetime.now()  # Reset timer
```

### 3. Login Rate Limit Protection

**Critical:** Max **100 successful logins per minute** → 20-minute temporary ban.

**Protection Strategy:**
```python
import time
from collections import deque

class RateLimitedAuth:
    def __init__(self, client):
        self.client = client
        self.login_times = deque(maxlen=100)

    def safe_login(self):
        """Ensure we don't exceed 100 logins/minute"""
        now = time.time()

        # Remove login times older than 60 seconds
        while self.login_times and now - self.login_times[0] > 60:
            self.login_times.popleft()

        # If we have 100 logins in last 60s, wait
        if len(self.login_times) >= 100:
            sleep_time = 60 - (now - self.login_times[0])
            time.sleep(sleep_time + 1)  # +1 for safety margin

        self.client.login()
        self.login_times.append(time.time())
```

**Better Approach:** Use `keep_alive()` instead of frequent re-logins.

---

## Security Considerations

### 1. Credential Storage

**❌ NEVER:**
- Hardcode credentials in source code
- Commit credentials to version control
- Log credentials in plaintext
- Store credentials in client-side code

**✅ ALWAYS:**
- Use environment variables
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Encrypt credentials at rest
- Use OS keychain integration when possible

### 2. Session Token Protection

**Risks:**
- Session hijacking if token leaked
- Unauthorized API access
- Potential financial loss (if betting enabled)

**Mitigations:**
- ✅ Use HTTPS only (never HTTP)
- ✅ Don't log session tokens
- ✅ Sanitize logs/errors before output
- ✅ Implement session token rotation
- ✅ Use certificate auth for production

### 3. Multi-Environment Strategy

**Development:**
```
BETFAIR_APP_KEY=<Delayed Key>
BETFAIR_ENV=non_production
```

**Production:**
```
BETFAIR_APP_KEY=<Live Key>
BETFAIR_ENV=production
BETFAIR_CERTS_PATH=/secure/certs/
```

**Separate credentials entirely** - never use production credentials in development.

---

## Implementation Recommendations

### For betfair-mcp Server

**1. Initialization Phase**
```python
# src/betfair_mcp/auth.py

class BetfairAuthenticator:
    def __init__(self):
        self.username = os.getenv('BETFAIR_USERNAME')
        self.password = os.getenv('BETFAIR_PASSWORD')
        self.app_key = os.getenv('BETFAIR_APP_KEY')
        self.certs_path = os.getenv('BETFAIR_CERTS_PATH')

        # Validate required credentials
        if not all([self.username, self.password, self.app_key]):
            raise ValueError("Missing required Betfair credentials")

        self.client = betfairlightweight.APIClient(
            username=self.username,
            password=self.password,
            app_key=self.app_key,
            certs=self.certs_path
        )

    def authenticate(self):
        """Perform initial authentication"""
        try:
            self.client.login()
            return True
        except Exception as e:
            # Log error (sanitized)
            logger.error(f"Betfair authentication failed: {type(e).__name__}")
            raise
```

**2. Lifecycle Management**
```python
# MCP Server startup hook
async def on_startup():
    authenticator = BetfairAuthenticator()
    authenticator.authenticate()

    # Start background task for session renewal
    asyncio.create_task(keep_alive_loop(authenticator.client))

async def keep_alive_loop(client):
    """Background task to refresh session every 12 hours"""
    while True:
        await asyncio.sleep(12 * 60 * 60)  # 12 hours
        try:
            client.keep_alive()
            logger.info("Betfair session refreshed")
        except Exception as e:
            logger.error(f"Session refresh failed: {e}")
```

**3. Error Handling**
```python
def handle_auth_error(exception):
    """Map Betfair auth errors to user-friendly messages"""
    error_map = {
        'INVALID_USERNAME_OR_PASSWORD': 'Invalid Betfair credentials',
        'TEMPORARY_BAN_TOO_MANY_REQUESTS': 'Rate limit exceeded (20min ban)',
        'CERT_AUTH_REQUIRED': 'Certificate authentication required',
        'INVALID_APP_KEY': 'Invalid Application Key'
    }

    error_code = getattr(exception, 'error_code', None)
    return error_map.get(error_code, f'Authentication error: {exception}')
```

---

## References

### Official Documentation
- [Betfair Application Keys](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Application+Keys)
- [Login & Session Management](https://docs.developer.betfair.com/pages/viewpage.action?pageId=3834909)
- [Interactive Login API](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Interactive+Login+-+API+Endpoint)

### betfairlightweight
- [GitHub Repository](https://github.com/betcode-org/betfair)
- [QuickStart Guide](https://betcode-org.github.io/betfair/quickstart/)
- [PyPI Package](https://pypi.org/project/betfairlightweight/)

### Related Research Documents
- [RESEARCH_02_RATE_LIMITS.md](./RESEARCH_02_RATE_LIMITS.md) - Rate limiting and throttling
- [RESEARCH_04_BETFAIRLIGHTWEIGHT.md](./RESEARCH_04_BETFAIRLIGHTWEIGHT.md) - SDK deep dive
- [RESEARCH_07_COMPLIANCE.md](./RESEARCH_07_COMPLIANCE.md) - Security compliance

---

**Next Document:** [RESEARCH_02_RATE_LIMITS.md](./RESEARCH_02_RATE_LIMITS.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
