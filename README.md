# Betfair MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with the Betfair Exchange betting platform. This server provides read-only access to betting markets, live odds, account information, and sporting events.

## Features

- **Account Management**: Query account balance, funds, and details
- **Event Discovery**: Browse sports, competitions, and events
- **Market Intelligence**: Access betting markets and live odds
- **Real-time Data**: Get current prices and market information
- **Type-safe**: Full type hints and Pydantic validation
- **Enterprise-ready**: Production-grade error handling and logging

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Betfair account with API access
- Application key from [Betfair Developer Portal](https://developer.betfair.com/)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/aranej/first-Test-BF-mcp.git
   cd first-Test-BF-mcp
   ```

2. **Install dependencies using uv** (recommended):
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

   Or using pip:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e .
   ```

3. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Betfair credentials
   ```

### Configuration

Edit `.env` with your Betfair credentials:

```env
BETFAIR_USERNAME=your_username
BETFAIR_PASSWORD=your_password
BETFAIR_APP_KEY=your_app_key

# Optional: Certificate authentication (recommended for production)
BETFAIR_CERT_FILE=/path/to/client-2048.crt
BETFAIR_KEY_FILE=/path/to/client-2048.key

# Server settings
LOG_LEVEL=INFO
```

Get your credentials:
- **Application Key**: [Betfair Account Portal](https://myaccount.betfair.com/account/token)
- **Certificates**: [Betfair Certificate Guide](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Certificate+Generation+With+XCA)

## Usage

### Running the Server

Start the MCP server:

```bash
python -m betfair_mcp.server
```

Or using FastMCP CLI:

```bash
fastmcp run src/betfair_mcp/server.py
```

### Available Tools

The server provides the following MCP tools:

#### Account Tools

**`get_account_balance`**
- Get current account balance and available funds
- Returns: available to bet, exposure, limits

**`get_account_details`**
- Get account information and settings
- Returns: name, currency, timezone, points balance

#### Event Tools

**`list_event_types`**
- List all available sports
- Returns: sport IDs and names (Soccer, Tennis, etc.)

**`list_events`**
- List sporting events with filtering
- Args: `event_type_id`, `competition_id`, `text_query`
- Returns: events with IDs, names, dates

**`list_competitions`**
- List competitions/leagues for a sport
- Args: `event_type_id`
- Returns: competition IDs and names

#### Market Tools

**`list_market_catalogue`**
- List betting markets with filtering
- Args: `event_id`, `event_type_id`, `competition_id`, `market_type_codes`, `max_results`
- Returns: markets with runners and descriptions

**`get_market_prices`**
- Get live odds for markets
- Args: `market_ids` (list, max 250)
- Returns: back/lay prices, matched amounts

### Example Queries

Here are example natural language queries you can ask an AI assistant using this MCP server:

```
"What's my current Betfair account balance?"

"Show me upcoming Premier League matches"

"What are the odds for the next Manchester United game?"

"List all tennis events happening today"

"What markets are available for the Champions League final?"
```

## Project Structure

```
betfair-mcp/
├── src/
│   └── betfair_mcp/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # FastMCP server & tool registration
│       ├── auth.py              # Session management
│       ├── tools/               # MCP tool implementations
│       │   ├── __init__.py
│       │   ├── account.py       # Account-related tools
│       │   ├── events.py        # Event discovery tools
│       │   └── markets.py       # Market data tools
│       └── utils/               # Utility modules
│           └── __init__.py
├── pyproject.toml               # Project dependencies
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Research Documentation

This project includes comprehensive research documentation:

- **[BETFAIR_MCP_BRAINSTORM_PLAN.md](BETFAIR_MCP_BRAINSTORM_PLAN.md)**: Strategic overview and roadmap
- **[RESEARCH_INDEX.md](RESEARCH_INDEX.md)**: Master navigation for all research
- **[RESEARCH_01_AUTHENTICATION.md](RESEARCH_01_AUTHENTICATION.md)**: Authentication deep dive
- **[RESEARCH_02_RATE_LIMITS.md](RESEARCH_02_RATE_LIMITS.md)**: Rate limiting strategies
- **[RESEARCH_03_STREAMING_API.md](RESEARCH_03_STREAMING_API.md)**: Real-time streaming guide
- **[RESEARCH_04_BETFAIRLIGHTWEIGHT.md](RESEARCH_04_BETFAIRLIGHTWEIGHT.md)**: SDK integration patterns
- **[RESEARCH_05_FASTMCP_INTEGRATION.md](RESEARCH_05_FASTMCP_INTEGRATION.md)**: MCP implementation guide
- **[RESEARCH_06_USE_CASES.md](RESEARCH_06_USE_CASES.md)**: User personas and scenarios
- **[RESEARCH_07_COMPLIANCE.md](RESEARCH_07_COMPLIANCE.md)**: Legal and ethical guidelines
- **[RESEARCH_08_PRODUCTION_DEPLOYMENT.md](RESEARCH_08_PRODUCTION_DEPLOYMENT.md)**: Production deployment guide

## Development Roadmap

This is Phase 1 (MVP) implementation. Future phases planned:

- **Phase 2**: Streaming API integration for real-time updates
- **Phase 3**: Advanced analytics and value betting tools
- **Phase 4**: Responsible gambling monitoring
- **Phase 5**: Production hardening and observability

See [BETFAIR_MCP_BRAINSTORM_PLAN.md](BETFAIR_MCP_BRAINSTORM_PLAN.md) for details.

## Compliance & Responsible Use

**Important**: This server is designed for **read-only intelligence** and does **NOT** support placing bets. It provides market data and account information only.

### Permitted Use
- Market research and analysis
- Price comparison and value identification
- Educational and research purposes
- Integration with AI assistants for information queries

### Prohibited Use
- Automated betting or gambling
- High-frequency trading strategies
- Circumventing Betfair rate limits
- Sharing account credentials

**Responsible Gambling**: If you or someone you know has a gambling problem, seek help:
- UK: [GamCare](https://www.gamcare.org.uk/) - 0808 8020 133
- International: [Gambling Therapy](https://www.gamblingtherapy.org/)

See [RESEARCH_07_COMPLIANCE.md](RESEARCH_07_COMPLIANCE.md) for full compliance guidelines.

## Betfair Terms of Service

This MCP server uses the official Betfair API, which **explicitly permits** programmatic access:

> "You may use software programs with your Betfair account provided that they interact with Betfair via the API"
> — [Betfair Terms of Service](https://www.betfair.com/aboutUs/Terms.and.Conditions/)

However, you must:
- Use your own Betfair account
- Comply with Betfair's API policies
- Not exceed rate limits
- Not engage in prohibited activities

## Rate Limits

Betfair does **not** have general API throttling, but specific limits apply:

- **Login**: 100 requests per minute (hard limit)
- **Per-market**: 5 requests per second per market ID
- **Keep-alive**: Recommended every 30 minutes

The server automatically handles session keep-alive. See [RESEARCH_02_RATE_LIMITS.md](RESEARCH_02_RATE_LIMITS.md) for details.

## Troubleshooting

### Login Issues

**Problem**: `LOGIN_FAILED` error

**Solutions**:
- Verify credentials in `.env` are correct
- Check if your Betfair account is active
- Ensure you're not exceeding 100 logins/minute
- Try certificate authentication for production use

### Certificate Authentication

**Problem**: Certificate files not found

**Solutions**:
- Generate certificates using [Betfair's guide](https://docs.developer.betfair.com/display/1smk3cen4v3lu3yomq5qye0ni/Certificate+Generation+With+XCA)
- Update `BETFAIR_CERT_FILE` and `BETFAIR_KEY_FILE` paths in `.env`
- Ensure certificate files have correct permissions

### API Errors

**Problem**: `THROTTLED` or rate limit errors

**Solutions**:
- Reduce request frequency
- Use delayed app key (not instant key)
- Implement exponential backoff
- See [RESEARCH_02_RATE_LIMITS.md](RESEARCH_02_RATE_LIMITS.md)

## Contributing

Contributions are welcome! Please:

1. Review research documentation first
2. Follow existing code patterns
3. Add tests for new features
4. Update documentation

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/aranej/first-Test-BF-mcp/issues)
- **Betfair API Docs**: [developer.betfair.com](https://developer.betfair.com/)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

## Acknowledgments

Built with:
- [FastMCP](https://github.com/jlowin/fastmcp) - Pythonic MCP framework
- [betfairlightweight](https://github.com/liampauling/betfair) - Official Betfair Python SDK
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic's AI integration standard

---

**Disclaimer**: This is an independent project and is not affiliated with, endorsed by, or sponsored by Betfair. Use at your own risk.
