# Betfair MCP Server - Use Cases & User Personas

**Document:** RESEARCH_06_USE_CASES.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [User Personas](#user-personas)
3. [Core Use Cases](#core-use-cases)
4. [AI-Powered Market Analysis](#ai-powered-market-analysis)
5. [Value Betting Intelligence](#value-betting-intelligence)
6. [Research & Analytics](#research--analytics)
7. [Conversational Assistant Scenarios](#conversational-assistant-scenarios)
8. [Advanced Use Cases](#advanced-use-cases)
9. [MVP Scope](#mvp-scope)
10. [Future Enhancements](#future-enhancements)
11. [References](#references)

---

## Executive Summary

**Our MCP server enables AI assistants to become intelligent betting research companions.**

**Core Value Proposition:**
> "Ask Claude about Betfair markets in natural language, get instant insights, and make data-driven betting decisions."

**Key Use Cases:**
1. **Market Discovery** - "Show me today's Premier League matches"
2. **Odds Analysis** - "What are the current odds for Man Utd to win?"
3. **Value Identification** - "Find value bets in tennis markets"
4. **Trend Analysis** - "How have odds moved in the last hour?"
5. **Risk Assessment** - "Analyze liquidity for this market"

**Target Users:**
- Sports bettors (casual to professional)
- Trading strategists
- Data analysts/researchers
- Sports enthusiasts

**MVP Focus:** Read-only intelligence (no betting execution)

---

## User Personas

### 1. **The Casual Bettor (Sarah)**

**Profile:**
- Age: 28, Marketing Manager
- Bets occasionally on football weekends
- Budget: £20-50 per weekend
- Technical skill: Low

**Goals:**
- Find good betting opportunities quickly
- Understand odds without complicated analysis
- Get recommendations for weekend matches
- Avoid bad bets

**Pain Points:**
- Overwhelmed by too much data
- Doesn't understand implied probability
- Misses good odds because she checks too late
- Unsure which markets to bet on

**How MCP Server Helps:**
```
Sarah: "Show me this weekend's Premier League matches"
Claude: [Lists 10 matches with current odds]

Sarah: "Which match is most likely to have over 2.5 goals?"
Claude: [Analyzes historical data, current form, provides recommendation]

Sarah: "Are the odds good for Arsenal to win?"
Claude: [Explains odds of 1.8, implied probability 55.6%, value assessment]
```

**Key Tools:**
- `search_football_events()`
- `get_market_prices()`
- `analyze_value_bets()`

---

### 2. **The Sports Trader (James)**

**Profile:**
- Age: 35, Full-time Betfair trader
- Trades markets pre-match and in-play
- Budget: £5,000+ bankroll
- Technical skill: High

**Goals:**
- Identify arbitrage opportunities quickly
- Monitor multiple markets simultaneously
- React to odds movements in real-time
- Maximize edge through data analysis

**Pain Points:**
- Too many markets to monitor manually
- Misses short-lived opportunities
- Needs faster market intelligence
- Wants automated alerts for specific conditions

**How MCP Server Helps:**
```
James: "Monitor all Premier League match odds markets and alert me when odds move >10% in 5 minutes"
Claude: [Sets up streaming subscription, monitors in background]

James: "Show me liquidity for all lay bets under 3.0 odds in the Man City market"
Claude: [Analyzes market depth, shows available liquidity ladder]

James: "Compare current odds with 1 hour ago"
Claude: [Shows odds movement trends, identifies significant shifts]
```

**Key Tools:**
- `subscribe_market_stream()`
- `analyze_odds_movement()`
- `get_market_liquidity()`
- `compare_markets()`

---

### 3. **The Data Analyst (Priya)**

**Profile:**
- Age: 31, Sports Data Scientist
- Builds betting models and strategies
- Budget: Research only (backtesting)
- Technical skill: Very High

**Goals:**
- Access historical market data
- Backtest betting strategies
- Identify statistical patterns
- Validate predictive models

**Pain Points:**
- Manual data collection is time-consuming
- API complexity slows down research
- Needs consistent data format
- Wants programmatic access to insights

**How MCP Server Helps:**
```
Priya: "Download all Match Odds data for Premier League 2024 season"
Claude: [Uses historical data API, formats data for analysis]

Priya: "Calculate ROI for betting on favorites when odds < 1.5"
Claude: [Analyzes historical data, shows ROI breakdown by league, season]

Priya: "What's the correlation between pre-match odds and actual outcomes?"
Claude: [Statistical analysis with correlation coefficients]
```

**Key Tools:**
- `get_historical_data()`
- `backtest_strategy()`
- `calculate_statistics()`
- `export_data()`

---

### 4. **The Informed Enthusiast (Marcus)**

**Profile:**
- Age: 42, Sports Journalist
- Bets for fun, loves analysis
- Budget: £50-100 per month
- Technical skill: Medium

**Goals:**
- Understand market sentiment
- Get context for betting decisions
- Learn about betting strategies
- Make smarter bets based on data

**Pain Points:**
- Doesn't know how to interpret odds movements
- Wants to understand "why" behind odds
- Needs educational content
- Wants transparency in recommendations

**How MCP Server Helps:**
```
Marcus: "Explain why the odds for Liverpool dropped from 2.5 to 2.0"
Claude: [Analyzes matched volume, trading patterns, provides context]

Marcus: "What does implied probability mean for these odds?"
Claude: [Educational explanation with specific examples from current market]

Marcus: "Show me the most actively traded markets today"
Claude: [Lists markets by volume, explains what drives activity]
```

**Key Tools:**
- `get_market_summary()`
- `explain_odds_movement()`
- `get_trading_volume()`
- `analyze_market_sentiment()`

---

## Core Use Cases

### 1. Market Discovery

**Scenario:** User wants to find betting opportunities

**Natural Language Queries:**
- "Show me today's football matches"
- "What tennis tournaments are happening this week?"
- "Find horse races in the next 2 hours"

**AI Workflow:**
```
User: "Show me Premier League matches this weekend"

Claude:
1. Calls: list_events(event_type='football', competition='Premier League')
2. Filters: Matches between today and Sunday
3. Enriches: Gets market count, start times
4. Formats: Table with match names, times, available markets

Response:
┌──────────────────────────────────────────────────────────┐
│ Premier League Matches - This Weekend                    │
├──────────────────────────────────────────────────────────┤
│ Saturday 3:00 PM                                         │
│ • Man Utd vs Liverpool (45 markets)                      │
│ • Arsenal vs Chelsea (52 markets)                        │
│ • Newcastle vs Tottenham (38 markets)                    │
│                                                          │
│ Sunday 4:30 PM                                           │
│ • Man City vs Everton (48 markets)                       │
└──────────────────────────────────────────────────────────┘
```

**MCP Tools Used:**
- `list_event_types()`
- `list_competitions(sport='football')`
- `list_events(filters)`
- `get_market_catalogue(event_id)`

---

### 2. Odds Analysis

**Scenario:** User wants current odds for a specific market

**Natural Language Queries:**
- "What are the odds for Man Utd to win?"
- "Show me over/under 2.5 goals prices"
- "What's the best price for laying the draw?"

**AI Workflow:**
```
User: "What are the current odds for Arsenal vs Chelsea?"

Claude:
1. Calls: search_events(query='Arsenal vs Chelsea')
2. Gets: event_id
3. Calls: get_market_catalogue(event_id, market_type='MATCH_ODDS')
4. Calls: get_market_prices(market_id)
5. Formats: Back/Lay odds with liquidity

Response:
Arsenal vs Chelsea - Match Odds Market
═══════════════════════════════════════

ARSENAL
Back: 2.20 (£2,450) | 2.18 (£1,200) | 2.16 (£800)
Lay:  2.22 (£1,800) | 2.24 (£950)

DRAW
Back: 3.45 (£1,500) | 3.40 (£900)
Lay:  3.50 (£2,100) | 3.55 (£1,400)

CHELSEA
Back: 3.15 (£1,900) | 3.10 (£750)
Lay:  3.20 (£1,650) | 3.25 (£1,100)

Total Matched: £125,450
Market Status: OPEN
```

**MCP Tools Used:**
- `search_events()`
- `get_market_catalogue()`
- `get_market_prices()`
- `get_market_liquidity()`

---

### 3. Value Bet Identification

**Scenario:** User wants to find betting opportunities with positive expected value

**Natural Language Queries:**
- "Find value bets in today's football"
- "Which underdogs have unusually high odds?"
- "Show me markets where the favorite is overpriced"

**AI Workflow:**
```
User: "Find value bets in today's tennis matches"

Claude:
1. Calls: list_events(sport='tennis', date='today')
2. For each match:
   - Gets market odds
   - Calculates implied probability
   - Compares with AI probability estimate
   - Identifies positive expected value
3. Ranks by expected value
4. Formats recommendations

Response:
🎾 Tennis Value Bets - Today

1. ⭐⭐⭐ Novak Djokovic vs Carlos Alcaraz
   Market: Match Winner - Djokovic
   Current Odds: 2.80 (Implied: 35.7%)
   AI Estimate: 45% chance
   Expected Value: +26%
   Reasoning: Djokovic's recent form on hard courts, head-to-head record

2. ⭐⭐ Iga Swiatek vs Aryna Sabalenka
   Market: Over 21.5 Games
   Current Odds: 2.10 (Implied: 47.6%)
   AI Estimate: 55% chance
   Expected Value: +15%
   Reasoning: Both players' playing styles favor long matches

3. ⭐ [Additional recommendations...]
```

**MCP Tools Used:**
- `list_events()`
- `get_market_prices()`
- `calculate_implied_probability()`
- `identify_value_bets()`
- `analyze_h2h_stats()`

---

## AI-Powered Market Analysis

### Real-Time Market Monitoring

**Use Case:** Track odds movements during live events

**Scenario:**
```
User: "Monitor the Man Utd vs Liverpool market and alert me when odds change significantly"

Claude sets up:
1. Market stream subscription
2. Baseline odds snapshot
3. Alert thresholds (e.g., >5% movement)
4. Background monitoring task

When odds move:
🔔 Alert: Man Utd odds dropped from 2.5 to 2.2 (-12%)
   Reason: Goal scored at 23' minute
   Trading Volume: £45,000 matched in last 60 seconds
   Recommendation: Odds likely to settle around 2.1-2.15
```

**Technical Implementation:**
- Background streaming (RESEARCH_03)
- State caching
- Alert logic with thresholds
- Real-time analysis

---

### Liquidity Analysis

**Use Case:** Assess if there's enough liquidity to execute large bets

**Scenario:**
```
User: "Can I place a £1,000 back bet on Arsenal at 2.2 or better?"

Claude analyzes:
1. Current order book depth
2. Available liquidity at target price
3. Historical liquidity patterns
4. Recommendation for order placement

Response:
Liquidity Analysis - Arsenal Back Bet
════════════════════════════════════

Target: £1,000 @ 2.2

Available Liquidity:
• 2.22: £450 ✅
• 2.20: £650 ✅
• 2.18: £400 ⚠️

Recommendation:
You can get £1,100 matched between 2.2-2.22
Average price: ~2.207

Strategy:
1. Place limit order at 2.2 for £650 (will match immediately)
2. Place limit order at 2.22 for £350 (will match immediately)

Alternative: Wait for better liquidity if odds drift to 2.25+
```

---

### Cross-Market Intelligence

**Use Case:** Compare related markets for inconsistencies

**Scenario:**
```
User: "Compare Match Odds with Correct Score markets for Man City vs Everton"

Claude:
1. Gets Match Odds (1X2)
2. Gets Correct Score odds for all outcomes
3. Calculates implied probabilities
4. Identifies arbitrage/inconsistencies

Response:
Market Comparison Analysis
═════════════════════════

Match Odds Implied Probabilities:
• Man City Win: 78%
• Draw: 15%
• Everton Win: 7%

Correct Score Implied (aggregated):
• Man City Win: 75%
• Draw: 16%
• Everton Win: 9%

⚠️ Inconsistency Detected:
Everton Win is 7% in Match Odds but 9% in Correct Score
Potential arbitrage: Back Everton in Match Odds, Lay specific Everton scores

Recommendation: Small edge available, but liquidity may be limited
```

---

## Value Betting Intelligence

### Pattern Recognition

**Use Case:** Identify recurring patterns in odds movements

**AI Capabilities:**
- Machine learning on historical data
- Pattern detection (e.g., "Favorites at home in rain")
- Trend analysis
- Predictive modeling

**Example:**
```
User: "What patterns do you see in Champions League away team performance?"

Claude (after analyzing historical data):

Pattern Analysis - Champions League Away Teams
═════════════════════════════════════════════

1. 📊 Value Pattern Detected:
   When: Away team odds > 5.0 AND team is from Top 5 league
   Historical Win Rate: 18%
   Average Odds: 6.2
   Expected Value: +11.6%
   Sample Size: 147 matches (last 3 seasons)

2. 📈 Trend Identified:
   Away teams performing better in knockout stages vs group stage
   Group Stage Away Win%: 22%
   Knockout Away Win%: 28%

3. 🎯 Current Opportunities:
   • Bayern Munich away at PSG: Odds 6.5 (AI estimate: 20% = fair odds 5.0)
   • Real Madrid away at Man City: Odds 4.2 (AI estimate: 22% = fair odds 4.5)
```

---

### Historical Performance Analysis

**Use Case:** Backtest betting strategies

**Scenario:**
```
User: "Would betting on Premier League favorites at home with odds < 1.8 have been profitable last season?"

Claude:
1. Queries historical data API
2. Filters matches (home favorites, odds < 1.8)
3. Calculates ROI, win rate, Sharpe ratio
4. Provides detailed breakdown

Response:
Backtest Results - Premier League Home Favorites (Odds < 1.8)
════════════════════════════════════════════════════════════

Period: 2024/25 Season
Total Bets: 187
Winners: 142 (75.9%)
Losers: 45 (24.1%)

Financial Performance:
• Total Staked: £1,870 (£10 per bet)
• Total Returns: £2,104
• Net Profit: £234
• ROI: +12.5%

Best Performing Teams:
1. Man City (Home): 18/19 wins (94.7%), +£156 profit
2. Arsenal (Home): 16/17 wins (94.1%), +£141 profit
3. Liverpool (Home): 15/18 wins (83.3%), +£48 profit

Worst Performers:
1. Chelsea (Home): 11/16 wins (68.8%), -£42 loss
2. Tottenham (Home): 12/17 wins (70.6%), -£28 loss

Conclusion: Strategy is profitable but variance is high.
Kelly Criterion Recommendation: Bet 2-3% of bankroll per opportunity
```

---

## Research & Analytics

### Data Export & Visualization

**Use Case:** Export data for external analysis

**Scenario:**
```
User: "Export all Premier League Match Odds data from last month to CSV"

Claude:
1. Queries historical data
2. Formats as CSV
3. Includes: date, match, market_id, odds, volume
4. Saves file

Response:
✅ Exported: premier_league_odds_nov2025.csv
   Rows: 1,247
   Columns: 12
   File Size: 245 KB

   Included Fields:
   - match_date, home_team, away_team
   - market_id, selection_id, selection_name
   - back_odds, lay_odds, matched_volume
   - market_status, result

   Location: /downloads/premier_league_odds_nov2025.csv
```

---

### Statistical Insights

**Use Case:** Calculate betting statistics

**Scenario:**
```
User: "What's the average over/under 2.5 goals hit rate in Serie A?"

Claude analyzes historical data:

Serie A - Over/Under 2.5 Goals Statistics (Last 2 Seasons)
═══════════════════════════════════════════════════════════

Overall Hit Rate:
• Over 2.5: 52.3% (397/759 matches)
• Under 2.5: 47.7% (362/759 matches)

By Team (Top Scorers):
1. Atalanta: 68% Over rate (most goals)
2. Napoli: 61% Over rate
3. Inter: 58% Over rate

By Team (Defensive):
1. Juventus: 38% Over rate (fewest goals)
2. AC Milan: 42% Over rate

Seasonal Trends:
• Early Season (Aug-Oct): 55% Over rate
• Mid Season (Nov-Feb): 50% Over rate
• Late Season (Mar-May): 51% Over rate

Home vs Away:
• Home matches: 54% Over rate
• Away matches: 50% Over rate

Current Season (2025/26 so far):
• Over rate trending at 56% (above historical avg)
• Suggests slight value in Under 2.5 bets
```

---

## Conversational Assistant Scenarios

### Natural Language Exploration

**Example Conversation 1: Market Exploration**
```
User: "I'm looking for a football bet this evening"

Claude: "Let me show you tonight's football markets. I found 12 matches across Premier League, La Liga, and Champions League. Which league interests you?"

User: "Champions League"

Claude: "Tonight's Champions League matches:
1. Bayern Munich vs PSG (8:00 PM) - 78 markets
2. Real Madrid vs Man City (8:00 PM) - 82 markets

Which match would you like to explore?"

User: "Real Madrid vs Man City"

Claude: "Great choice! This is a highly competitive match. Here are the main markets:

Match Odds:
• Real Madrid: 3.15
• Draw: 3.45
• Man City: 2.40

The odds suggest Man City are favorites (41.7% implied probability).

Would you like to see:
- Over/Under goals markets
- Both Teams To Score
- Correct Score odds
- First goalscorer
- Or analyze current odds for value?"

User: "Analyze for value"

Claude: [Performs analysis, provides recommendations...]
```

---

**Example Conversation 2: Odds Explanation**
```
User: "Why are Man United's odds so high against Liverpool?"

Claude: "Great question! Let me break down why Man United are underdogs at 4.5:

1. Recent Form:
   - Man United: 2 wins, 1 draw, 2 losses (last 5)
   - Liverpool: 4 wins, 1 draw (last 5)

2. Head-to-Head:
   - Liverpool won 3 of last 5 meetings
   - Man United haven't won at Anfield in 4 years

3. League Position:
   - Liverpool: 1st (72 points)
   - Man United: 7th (48 points)

4. Market Sentiment:
   - 78% of matched volume on Liverpool
   - Odds have drifted from 4.2 to 4.5 for Man United

5. Injuries/Suspensions:
   - Man United missing 3 key players
   - Liverpool at full strength

The odds of 4.5 imply a 22% chance for Man United, which seems fair given these factors. Historical data shows similar scenarios result in 18-25% away wins.

Would you like me to identify if there's any value in these odds?"
```

---

## Advanced Use Cases

### 1. AI-Powered Arbitrage Detection

**Scenario:** Find risk-free betting opportunities

```
User: "Find arbitrage opportunities in today's markets"

Claude:
- Compares Betfair Exchange odds with bookmaker odds
- Identifies price discrepancies
- Calculates guaranteed profit
- Accounts for commission

Response:
🎯 Arbitrage Opportunity Found

Match: Arsenal vs Chelsea
Market: Match Odds

Betfair Exchange:
• Back Arsenal: 2.20 (after 2% commission: 2.156)

Bookmaker X:
• Lay Arsenal: 2.05

Setup:
1. Back Arsenal on Betfair: £1,000 @ 2.156
2. Lay Arsenal on Bookmaker X: £1,053 @ 2.05

Guaranteed Profit: £3.70 (0.37% ROI)
Capital Required: £2,053

⚠️ Note: Profit margin is small, ensure you can execute both sides quickly
```

---

### 2. Live In-Play Strategy

**Scenario:** Dynamic betting during live matches

```
User: "Monitor the Liverpool match and alert me when they're 1-0 up and odds drift above 1.5"

Claude:
- Subscribes to live scores + market stream
- Monitors match state and odds simultaneously
- Triggers alert on conditions met

[During match]
🔔 Alert: Condition Met!
   Match State: Liverpool 1-0 Newcastle (67')
   Liverpool Win Odds: 1.52 (drifted from 1.35)

   Analysis:
   - Odds suggest 65.8% win probability
   - With 23 minutes left and 1-goal lead, historical data shows 78% hold rate
   - Potential value: +12%

   Recommendation: Back Liverpool now, or wait to see if odds drift further to 1.6+
```

---

### 3. Multi-Market Correlation

**Scenario:** Understand how different markets influence each other

```
User: "If I bet on Over 2.5 goals, what's the probability that Both Teams Score also wins?"

Claude analyzes correlations:

Correlation Analysis: Over 2.5 Goals ↔ Both Teams Score
═══════════════════════════════════════════════════════

Historical Data (Premier League, 1000 matches):

When Over 2.5 hits (523 matches):
• BTTS also hit: 412 matches (78.8%)
• BTTS didn't hit: 111 matches (21.2%)

When Under 2.5 hits (477 matches):
• BTTS still hit: 89 matches (18.7%)
• BTTS didn't hit: 388 matches (81.3%)

Correlation Coefficient: 0.72 (strong positive correlation)

Betting Strategy Implications:
- If you're confident Over 2.5 will hit, BTTS has 79% chance
- Combined bet (Over 2.5 + BTTS) typically offers better value than singles
- Consider accumulators or combo bets

Current Match Odds:
- Over 2.5: 2.10
- BTTS: 1.85
- Over 2.5 + BTTS (combo): 3.20

Implied Combined Probability: 31.25%
Calculated Probability (based on correlation): 35.2%
**Potential Value: +12.6%**
```

---

## MVP Scope

### Phase 1: Read-Only Intelligence (MVP)

**Included:**
✅ Market discovery and search
✅ Current odds retrieval
✅ Account balance checking
✅ Market catalogue browsing
✅ Basic analysis (implied probability, liquidity)
✅ Historical data queries
✅ Conversational interface

**Excluded:**
❌ Bet placement
❌ Order management (cancel, update)
❌ Fund transfers
❌ Real-time streaming (saved for Phase 2)

**Example MVP Session:**
```
User: "Show me tonight's football matches"
Claude: [Lists matches]

User: "What are the odds for Arsenal?"
Claude: [Shows current odds, implied probability]

User: "Is that good value?"
Claude: [Analyzes historical data, provides opinion]

User: "Thanks, I'll place the bet myself on Betfair website"
```

**Key Principle:** AI provides intelligence, user executes bets manually.

---

### Phase 2: Streaming & Alerts

**Added Features:**
✅ Real-time odds monitoring
✅ Custom alerts and notifications
✅ Live market tracking
✅ Automated pattern detection

**Example:**
```
User: "Alert me when Liverpool odds go above 2.5"
Claude: [Sets up streaming monitor, sends alert when condition met]
```

---

### Phase 3: Advanced Analytics (Optional)

**Added Features:**
✅ Machine learning predictions
✅ Strategy backtesting
✅ Portfolio tracking
✅ Risk management tools

---

### Phase 4: Transaction Support (High Risk)

**Added Features:**
⚠️ Bet placement (with heavy safeguards)
⚠️ Order management
⚠️ Stake limits and controls
⚠️ Betting history tracking

**Security Gates:**
- Explicit opt-in: `BETFAIR_ENABLE_BETTING=true`
- Confirmation prompts for all bets
- Maximum stake limits
- Daily/weekly spending limits
- Audit logging
- Responsible gambling checks

---

## Future Enhancements

### 1. Multi-Source Intelligence

**Integrate external data:**
- Weather APIs (for outdoor sports)
- Injury news (from sports APIs)
- Social media sentiment
- Historical performance databases
- Bookmaker odds comparison

---

### 2. Personalized AI Coach

**Learn user preferences:**
- Betting history analysis
- Risk tolerance profiling
- Favorite sports/markets
- Success rate tracking
- Personalized recommendations

**Example:**
```
Claude: "Based on your betting history, you have a 58% success rate on tennis underdogs when odds are between 3.0-5.0. I found 3 similar opportunities today. Would you like to see them?"
```

---

### 3. Social Features

**Community Intelligence:**
- Share analysis with other users
- Follow expert tipsters
- Crowdsourced probability estimates
- Betting syndicate coordination

---

### 4. Voice Interface

**Natural conversation:**
```
User: [Voice] "Hey Claude, what's the best bet today?"
Claude: [Voice] "Based on your preferences and current markets, I recommend backing Liverpool in the over 2.5 goals market at 2.1. They've hit this in 7 of their last 10 home games..."
```

---

## References

### Market Research
- [AI in Sports Betting (Intellias)](https://intellias.com/ai-in-sports-betting/)
- [Machine Learning for Sports Betting](https://intellias.com/machine-learning-for-sports-betting/)
- [AI-Powered Responsible Gambling](https://www.business2community.com/igaming-news/ai-responsible-gambling-tools-2025/)

### Related Research Documents
- [RESEARCH_05_FASTMCP_INTEGRATION.md](./RESEARCH_05_FASTMCP_INTEGRATION.md) - How to implement these use cases
- [RESEARCH_07_COMPLIANCE.md](./RESEARCH_07_COMPLIANCE.md) - Responsible gambling considerations
- [RESEARCH_03_STREAMING_API.md](./RESEARCH_03_STREAMING_API.md) - Real-time features

---

**Next Document:** [RESEARCH_07_COMPLIANCE.md](./RESEARCH_07_COMPLIANCE.md)
**Previous Document:** [RESEARCH_05_FASTMCP_INTEGRATION.md](./RESEARCH_05_FASTMCP_INTEGRATION.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
