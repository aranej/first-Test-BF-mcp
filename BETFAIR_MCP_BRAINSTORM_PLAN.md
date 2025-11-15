# Betfair MCP Server - Deep Dive Brainstorming & Research Plan

**Project:** betfair-mcp
**Date:** 2025-11-15
**Status:** Research & Planning Phase
**Team:** aranej (Product Owner) + Claude Code (Architect & Developer)

---

## 🎯 Executive Summary

**Vision:** Create a production-ready MCP (Model Context Protocol) server that provides AI assistants (Claude, etc.) with secure, real-time access to Betfair Exchange market data, account management, and betting intelligence.

**Key Differentiators:**
- Production-grade architecture (vs. existing experimental projects)
- Comprehensive security & authentication
- Real-time streaming support
- Modular, extensible design
- Clear separation: read-only intelligence vs. transaction capabilities

---

## 📊 Existing Projects Analysis

### Project 1: mannickutd/mcp-betfair

**Repository:** https://github.com/mannickutd/mcp-betfair
**Created:** June 14, 2025
**Status:** 7 commits, 0 stars, experimental

**Technology Stack:**
- Python (82.0%)
- HTML (9.6%) - Web UI included
- TypeScript (7.2%)
- UV package manager
- Docker support

**Architecture:**
```
mcp_betfair/       # Core MCP server
memory_server/     # Memory management
public/            # Frontend assets
app.py             # Entry point
```

**Key Features:**
- Web interface at localhost:8000
- Non-production Betfair environment
- Market booking operations

**Strengths:**
✅ Web UI for visualization
✅ Docker containerization
✅ Memory management component

**Weaknesses:**
❌ Non-production only
❌ Limited documentation
❌ No clear MCP primitives exposed
❌ Zero community adoption

**Learnings:**
- Web UI could be valuable for debugging/monitoring
- Memory management suggests stateful operations
- Docker deployment is essential

---

### Project 2: craig1901/Betfair-MCP-Server

**Repository:** https://github.com/craig1901/Betfair-MCP-Server
**Technology:** FastMCP (Python 3.8+)
**Approach:** Read-only market intelligence

**Exposed Tools (5 total):**

1. **get_account_funds()**
   - Retrieves current account balance
   - No parameters

2. **list_event_types(locale: Optional[str])**
   - Returns available sports categories
   - Supports localization

3. **list_events(event_type_ids: List[str])**
   - Fetches events filtered by sport type
   - Multiple event types supported

4. **list_market_catalogue(event_ids: List[str], max_results: Optional[int])**
   - Retrieves market data for events
   - Configurable result limits

5. **list_market_book(market_ids: List[str])**
   - Live market dynamics
   - Prices, volumes, status indicators

**Dependencies:**
- `fastmcp` - MCP framework
- `betfairlightweight` - Official Python SDK
- `uv` - Package manager

**Authentication (Environment Variables):**
```bash
BETFAIR_USERNAME
BETFAIR_PASSWORD
BETFAIR_APP_KEY
BETFAIR_CERTS_PATH  # Optional SSL certs
```

**Deployment:**
- Standalone: `python server.py`
- CLI integration via `settings.json`

**Strengths:**
✅ Clean, focused implementation
✅ Uses official betfairlightweight SDK
✅ FastMCP framework (modern, pythonic)
✅ Clear tool definitions
✅ Read-only safety

**Weaknesses:**
❌ Limited to 5 basic tools
❌ No streaming API support
❌ No resources or prompts defined
❌ No error handling details
❌ Basic authentication only

**Learnings:**
- FastMCP is the right framework choice
- betfairlightweight is battle-tested
- Read-only mode is safer for MVP
- Tool-focused approach works well

---

## 🔌 Betfair API Capabilities Deep Dive

### Authentication Architecture

**Two-Level Security:**

1. **Application Keys (App Keys)**
   - 16-character identifier
   - Two types per account:
     - **Delayed Key** (Active) - Development/testing
     - **Live Key** (Inactive) - Production (requires application)
   - Header: `X-Application: APP_KEY`

2. **Session Tokens**
   - Methods:
     - Interactive login (web-based)
     - Non-interactive login (API)
     - Bot/Vendor login (certificates)
   - Expiry: 20 minutes to 24 hours (configurable)
   - Default: 24 hours

**Certificate-Based Auth:**
- SSL certificates for automated systems
- Higher security tier
- Required for vendor/bot APIs

### API Components

**1. Exchange API (Core Betting)**
- Market data (listMarketBook, listMarketCatalogue)
- Event types (Football, Tennis, Horse Racing, etc.)
- Betting operations (placeOrders, cancelOrders, replaceOrders)
- Market search and filtering

**2. Accounts API**
- Balance queries (getAccountFunds)
- Statement history
- Developer app key management
- Transfer operations

**3. Exchange Stream API** ⭐ **CRITICAL**
- **Low-latency real-time data**
- Market subscriptions
- Order subscriptions
- SSL socket-based (CRLF JSON protocol)
- Production: `stream-api.betfair.com`
- Testing: `stream-api-integration.betfair.com`
- ~1.5TB historical data available

**4. Vendor Services API**
- Advanced features for licensed vendors
- Higher rate limits
- Extended permissions

### Data Types & Structures

**Event Hierarchy:**
```
Event Type (Sport)
  └─ Competition (League/Tournament)
      └─ Event (Match/Game)
          └─ Market (Win/Place, Over/Under, etc.)
              └─ Runners (Teams/Players)
                  └─ Prices & Volumes
```

**Market States:**
- INACTIVE
- OPEN (accepting bets)
- SUSPENDED
- CLOSED (settled)

**Price Data:**
- Back prices (betting on outcome)
- Lay prices (betting against outcome)
- Available liquidity at each price point
- Matched amounts

### Rate Limits & Performance
- Standard API: Moderate latency (~100-500ms)
- Stream API: Sub-second latency
- Data volume: 1.5TB historical markets
- Concurrent connections: Varies by account tier

---

## 🏗️ MCP Architecture Considerations

### Core Primitives Strategy

**1. Tools (Functions AI Can Execute)**

**Read-Only Intelligence Tier:**
- `get_account_balance()` - Current funds
- `list_sports()` - Available event types
- `search_events(sport, date_range, keywords)` - Find markets
- `get_market_details(market_id)` - Comprehensive market data
- `get_live_prices(market_id)` - Current odds snapshot
- `analyze_market_liquidity(market_id)` - Volume analysis
- `get_runner_stats(runner_id)` - Historical performance

**Market Intelligence Tier:**
- `compare_odds_movement(market_id, time_range)` - Price trends
- `identify_value_bets(markets, threshold)` - Odds analysis
- `summarize_market_activity(event_id)` - Trading volume insights

**Streaming Tier (Advanced):**
- `subscribe_market_stream(market_ids)` - Real-time updates
- `subscribe_order_stream()` - Live bet tracking

**Transaction Tier (Future/Optional):**
- `place_bet(market_id, selection, stake, odds)` - Execute bet
- `cancel_bet(bet_id)` - Cancel pending bet
- `replace_bet(bet_id, new_odds)` - Modify bet

**2. Resources (Contextual Data)**

```
betfair://markets/{market_id}           # Market snapshot
betfair://events/{event_id}/markets     # All markets for event
betfair://runners/{runner_id}/history   # Runner performance
betfair://account/statement             # Transaction history
betfair://account/funds                 # Current balance
```

**3. Prompts (Templates)**

```
analyze_betting_opportunity:
  description: "Analyze a market for value betting opportunities"
  arguments: [market_id, stake_limit]

summarize_day_markets:
  description: "Summarize all markets for a given date"
  arguments: [date, sport_filter]

compare_bookmaker_odds:
  description: "Compare Betfair odds with bookmaker odds"
  arguments: [market_id, bookmaker_list]
```

### Transport Decision

**Recommended: stdio (for MVP)**
- Simpler setup
- Lower latency for local operations
- Better for Claude Desktop integration
- Subprocess lifecycle management

**Future: HTTP/SSE**
- Multiple concurrent clients
- Remote deployment
- Scalability for team usage
- Health monitoring endpoints

### State Management

**Stateless Operations:**
- Market queries
- Price lookups
- Balance checks

**Stateful Operations:**
- Streaming subscriptions
- Session token renewal
- Price alert monitoring

**Design Choice:**
- Stateless tools where possible
- Session pooling for performance
- Automatic token refresh logic

---

## 🔒 Security & Authentication Strategy

### Threat Model

**Critical Risks:**
1. **Credential Exposure**
   - Plain-text passwords in configs
   - Session tokens leaked in logs

2. **Unauthorized Betting**
   - AI accidentally placing bets
   - Malicious prompt injection

3. **Account Compromise**
   - Stolen app keys
   - Certificate theft

4. **Data Privacy**
   - Sensitive account data in LLM context
   - GDPR compliance

### Security Controls

**Tier 1: Authentication**
```python
# Environment-based secrets
BETFAIR_USERNAME (env)
BETFAIR_PASSWORD (env)
BETFAIR_APP_KEY (env)
BETFAIR_CERTS_PATH (env, optional)
```

**Tier 2: Authorization**
- Read-only mode by default
- Transaction capabilities: opt-in flag
- Stake limits (configurable)
- Market type whitelist/blacklist

**Tier 3: Isolation**
- Separate production vs. test credentials
- Dedicated app keys per MCP instance
- No credential logging (sanitized logs)

**Tier 4: Audit**
- All tool calls logged with timestamps
- Bet placement requires explicit confirmation
- Daily activity summaries

**Tier 5: Certificate-Based Auth (Production)**
- SSL certificates for bot accounts
- mTLS for enhanced security
- Certificate rotation policy

### Best Practices Implementation

**CVE-2025-49596 Lessons (MCP Inspector):**
- ❌ No 0.0.0.0 binding without auth
- ✅ localhost-only by default
- ✅ CSRF protection for web endpoints

**OAuth Proxy Vulnerabilities:**
- ✅ Short-lived session tokens
- ✅ Token rotation every 12 hours
- ✅ Secure storage (OS keychain integration)

**Configuration Security:**
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
        "BETFAIR_MODE": "read_only"
      }
    }
  }
}
```

---

## 💻 Technical Stack Decisions

### Language & Framework

**Choice: Python 3.10+ with FastMCP**

**Rationale:**
✅ FastMCP: Modern, pythonic, active development
✅ betfairlightweight: Official SDK, streaming support
✅ Async/await: Handles I/O efficiently
✅ Type hints: Better code quality
✅ UV: Fast dependency management

**Alternatives Considered:**
- TypeScript SDK: Less mature for Betfair
- Plain MCP SDK: More boilerplate

### Dependencies

**Core:**
```toml
[dependencies]
fastmcp = "^2.0.0"
betfairlightweight = "^2.21.0"
pydantic = "^2.0.0"  # Data validation
```

**Optional:**
```toml
[dev-dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.24.0"
black = "^24.0.0"
ruff = "^0.6.0"
mypy = "^1.11.0"
```

**Deployment:**
```toml
[deployment-dependencies]
docker = "*"
uvicorn = "*"  # If HTTP transport
```

### Project Structure

```
betfair-mcp/
├── src/
│   ├── betfair_mcp/
│   │   ├── __init__.py
│   │   ├── server.py           # FastMCP server
│   │   ├── tools/              # MCP tools
│   │   │   ├── market_data.py
│   │   │   ├── account.py
│   │   │   ├── streaming.py
│   │   │   └── betting.py      # Optional, gated
│   │   ├── resources/          # MCP resources
│   │   │   └── market_resources.py
│   │   ├── prompts/            # MCP prompts
│   │   │   └── analysis_prompts.py
│   │   ├── betfair_client.py   # Wrapper around betfairlightweight
│   │   ├── auth.py             # Authentication logic
│   │   ├── config.py           # Configuration management
│   │   └── utils.py            # Helpers
│   └── tests/
│       ├── test_tools.py
│       ├── test_auth.py
│       └── fixtures/
├── .env.example
├── pyproject.toml
├── uv.lock
├── .python-version
├── README.md
├── CLAUDE.md                   # MCP server guide for AI
├── SECURITY.md                 # Security policies
├── docker-compose.yml
├── Dockerfile
└── .claude/
    └── settings.json           # Claude Desktop config
```

### Testing Strategy

**Unit Tests:**
- Mock Betfair API responses
- Test tool parameter validation
- Auth flow testing

**Integration Tests:**
- Non-production Betfair environment
- Real API calls (rate-limited)
- End-to-end tool execution

**MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector uv run betfair-mcp
```

**Manual Testing:**
- Claude Desktop integration
- Cursor IDE integration
- Real market queries

---

## 🚀 Feature Roadmap Ideas

### Phase 1: MVP (Read-Only Intelligence) - Weeks 1-2

**Goals:**
- Secure authentication
- Core market data tools
- Claude Desktop integration
- Documentation

**Tools:**
1. `get_account_funds()` - Balance check
2. `list_event_types()` - Available sports
3. `list_competitions(sport)` - Leagues/tournaments
4. `search_events(filters)` - Find markets
5. `get_market_catalogue(event_id)` - Market details
6. `get_market_prices(market_id)` - Current odds

**Resources:**
- `betfair://account/funds`
- `betfair://markets/{market_id}`

**Deliverables:**
- Working MCP server
- README with setup guide
- .env.example
- Claude Desktop config example

---

### Phase 2: Advanced Intelligence - Weeks 3-4

**Tools:**
7. `analyze_odds_movement(market_id, duration)` - Price trends
8. `compare_markets(market_ids)` - Cross-market analysis
9. `get_runner_history(runner_id)` - Historical performance
10. `calculate_implied_probability(odds)` - Probability calculator

**Resources:**
- `betfair://events/{event_id}/markets` - All markets for event
- `betfair://runners/{runner_id}/history` - Runner stats

**Prompts:**
- `analyze_value_bet` - Value betting analysis template
- `summarize_market` - Market summary template

**Features:**
- Caching layer for frequent queries
- Rate limit handling
- Error recovery

---

### Phase 3: Real-Time Streaming - Weeks 5-6

**Tools:**
11. `subscribe_market_stream(market_ids)` - Live price updates
12. `subscribe_order_stream()` - Live bet tracking (if betting enabled)

**Architecture:**
- Streaming client management
- WebSocket-like updates via SSE
- Subscription lifecycle

**Challenges:**
- Managing long-lived connections
- Memory management
- Reconnection logic

---

### Phase 4: Transaction Capabilities (Optional) - Weeks 7-8

**⚠️ HIGH RISK - Requires extra security measures**

**Tools:**
13. `simulate_bet(market_id, selection, stake, odds)` - Paper trading
14. `place_bet(market_id, selection, stake, odds)` - Real bet (gated)
15. `cancel_bet(bet_id)` - Cancel pending bet
16. `get_bet_history(date_range)` - Historical bets

**Security Gates:**
- `BETFAIR_ENABLE_BETTING=true` (explicit opt-in)
- Stake limits (max €10 by default)
- Confirmation prompts
- Betting cooldown periods

**Audit:**
- All bets logged to separate file
- Daily bet summary emails
- Monthly spend reports

---

### Phase 5: Production Hardening - Week 9+

**Features:**
- HTTP/SSE transport option
- Multi-user support
- Health check endpoints
- Prometheus metrics
- Docker production image
- Kubernetes manifests

**Documentation:**
- API reference
- Architecture diagrams
- Security audit report
- Deployment guide

---

## ❓ Open Research Questions

### Technical

1. **Streaming API Integration:**
   - How does betfairlightweight handle streaming internally?
   - Can we expose real-time updates through MCP?
   - What's the reconnection strategy for dropped streams?

2. **Session Management:**
   - Optimal token refresh interval?
   - How to handle concurrent requests with single session?
   - Session pooling vs. single session?

3. **Rate Limiting:**
   - What are the actual Betfair rate limits?
   - How to implement client-side rate limiting?
   - Retry strategies for 429 errors?

4. **MCP Protocol:**
   - Can MCP handle streaming data elegantly?
   - How to represent real-time updates as resources?
   - Best practices for long-running tool calls?

5. **Error Handling:**
   - Betfair error codes mapping
   - Graceful degradation strategies
   - How to communicate API errors to AI?

### Product

6. **Use Cases:**
   - What are the most valuable AI + Betfair use cases?
   - Pre-match analysis vs. in-play betting?
   - Research/analytics vs. active betting?

7. **User Personas:**
   - Professional traders?
   - Casual bettors?
   - Data scientists/researchers?
   - Sports analysts?

8. **Market Fit:**
   - Is there demand for AI-assisted betting?
   - Competitive landscape?
   - Regulatory considerations?

### Security

9. **Responsible Gambling:**
   - How to prevent AI-driven compulsive betting?
   - Loss limits implementation?
   - Self-exclusion features?

10. **Compliance:**
    - GDPR implications for storing betting data?
    - Financial regulations for automated betting?
    - Terms of Service compliance with Betfair?

---

## 🔍 Next Steps & Action Items

### Immediate (Next Session)

1. **Environment Setup**
   - [ ] Initialize Python project with UV
   - [ ] Install fastmcp + betfairlightweight
   - [ ] Create project structure
   - [ ] Setup .env.example

2. **Authentication Prototype**
   - [ ] Test betfairlightweight login (non-prod)
   - [ ] Verify session token lifecycle
   - [ ] Test app key authentication

3. **First Tool Implementation**
   - [ ] Implement `get_account_funds()`
   - [ ] Test with MCP Inspector
   - [ ] Verify Claude Desktop integration

### Short-Term (Week 1)

4. **Core Tools (5-6 tools)**
   - [ ] Event type listing
   - [ ] Event search
   - [ ] Market catalogue
   - [ ] Market prices
   - [ ] Test all tools end-to-end

5. **Documentation**
   - [ ] README with setup instructions
   - [ ] CLAUDE.md for AI context
   - [ ] Security guidelines
   - [ ] Code comments

### Mid-Term (Weeks 2-4)

6. **Advanced Features**
   - [ ] Caching layer
   - [ ] Error handling
   - [ ] Odds movement analysis
   - [ ] Resources implementation

7. **Testing**
   - [ ] Unit tests (80% coverage)
   - [ ] Integration tests
   - [ ] Manual testing checklist

### Long-Term (Weeks 5+)

8. **Streaming API**
   - [ ] Research betfairlightweight streaming
   - [ ] Design MCP streaming pattern
   - [ ] Implement market stream subscriptions

9. **Production Readiness**
   - [ ] Docker containerization
   - [ ] CI/CD pipeline
   - [ ] Security audit
   - [ ] Performance optimization

---

## 📚 Additional Research Sources

### Official Betfair
- Exchange API Docs: https://docs.developer.betfair.com/
- Developer Forum: https://forum.developer.betfair.com/
- Python Tutorial: https://betfair-datascientists.github.io/api/apiPythontutorial/
- Stream API Samples: https://github.com/betfair/stream-api-sample-code

### betfairlightweight
- Docs: https://betcode-org.github.io/betfair/
- GitHub: https://github.com/betcode-org/betfair
- Advanced Usage: https://betcode-org.github.io/betfair/advanced/

### MCP Resources
- FastMCP Docs: https://github.com/jlowin/fastmcp
- MCP Spec: https://spec.modelcontextprotocol.io/
- MCP Examples: https://modelcontextprotocol.io/examples

### Similar Projects
- Cloudbet Sports MCP: https://cloudbet.github.io/wiki/en/docs/sports/api/mcp_integration/
- Wagyu Sports MCP: https://mcpmarket.com/server/wagyu-sports
- The Odds API MCP: https://playbooks.com/mcp/hrgarber-wagyu-sports

### Security
- OWASP Gen AI Security: https://genai.owasp.org/
- MCP Security Best Practices: https://www.akto.io/blog/mcp-security-best-practices

---

## 🎨 Design Principles

1. **Security First:** Read-only by default, transactions opt-in
2. **User Safety:** Stake limits, confirmations, audit trails
3. **Developer Experience:** Clear errors, good docs, easy setup
4. **Performance:** Caching, connection pooling, async operations
5. **Reliability:** Graceful degradation, retry logic, fallbacks
6. **Extensibility:** Modular tools, clean interfaces, plugin architecture
7. **Transparency:** Logging, monitoring, explainable AI interactions
8. **Compliance:** GDPR, responsible gambling, ToS adherence

---

## 💡 Innovation Opportunities

### Unique Value Propositions

1. **AI-Powered Market Analysis:**
   - Natural language queries: "Show me value bets in Premier League"
   - Trend detection: "Alert me when odds move 20%+"
   - Sentiment integration: Social media + odds correlation

2. **Multi-Market Intelligence:**
   - Cross-sport arbitrage detection
   - Liquidity analysis across markets
   - Historical pattern recognition

3. **Conversational Betting Assistant:**
   - "What are the best matches to bet on today?"
   - "Explain the odds movement in this market"
   - "Compare my betting strategy vs. optimal"

4. **Research & Analytics:**
   - Backtest betting strategies on historical data
   - ROI tracking and analysis
   - Performance attribution

### Technical Innovation

5. **Streaming-First Architecture:**
   - Real-time price feeds into AI context
   - Live event updates during conversations
   - Dynamic prompt adaptation based on market state

6. **Hybrid MCP Server:**
   - Both stdio (local) and HTTP (remote) transports
   - Session sharing across multiple AI clients
   - Collaborative betting analysis

7. **MCP Resource Innovation:**
   - Time-series market data as resources
   - Historical odds archives
   - Betting pattern libraries

---

## 🏁 Success Metrics

### Technical Metrics
- [ ] 99% uptime for core tools
- [ ] <500ms p95 latency for market queries
- [ ] Zero credential leaks in logs
- [ ] 80%+ test coverage

### Product Metrics
- [ ] Successfully execute 100+ AI-driven market queries
- [ ] Support 3+ different AI clients (Claude Desktop, Cursor, etc.)
- [ ] 10+ active users/testers
- [ ] Positive feedback on developer experience

### Security Metrics
- [ ] Zero unauthorized transactions
- [ ] 100% audit trail coverage
- [ ] Passing security review
- [ ] Compliance with Betfair ToS

---

## 🤝 Collaboration Model

**aranej (Product Owner):**
- Define use cases & priorities
- Test user experience
- Provide domain expertise
- Make go/no-go decisions on risky features

**Claude Code (Architect & Developer):**
- Design architecture
- Implement features
- Write tests & documentation
- Ensure security best practices
- Propose technical solutions

**Decision Framework:**
- Technical decisions: Claude proposes, aranej approves
- Product features: aranej defines, Claude estimates effort
- Security policies: Joint decision, conservative by default
- Timeline: Collaborative, flexible based on learning

---

## 📝 Notes & Observations

1. **Existing projects are experimental:** Both GitHub projects are proof-of-concepts, not production-ready. Opportunity to create first serious implementation.

2. **betfairlightweight is mature:** Official SDK with 2.21+ versions, streaming support, active maintenance. Solid foundation.

3. **Security is paramount:** Multiple CVEs in MCP ecosystem 2025. Must be extremely careful with credentials and betting operations.

4. **Streaming API is differentiator:** Most MCP servers are request/response. Real-time streaming could be unique value.

5. **Read-only is safer MVP:** craig1901's approach is wise - prove value with intelligence before adding transaction risk.

6. **FastMCP simplifies development:** Modern framework significantly reduces boilerplate vs. raw MCP SDK.

7. **Community is small but growing:** MCP for sports betting is emerging niche. Early mover advantage.

8. **Regulatory unknowns:** Need to verify Betfair ToS allows AI-assisted betting. Research required.

---

**END OF BRAINSTORM PLAN**

_This document will evolve as we research, prototype, and learn. Treat it as a living roadmap, not a rigid specification._
