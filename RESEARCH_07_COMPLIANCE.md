# Betfair MCP Server - Compliance & Responsible Gambling

**Document:** RESEARCH_07_COMPLIANCE.md
**Part of:** Betfair MCP Server Research Series
**Status:** ✅ Complete
**Last Updated:** 2025-11-16

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Betfair Terms of Service](#betfair-terms-of-service)
3. [Regulatory Landscape](#regulatory-landscape)
4. [Responsible Gambling Framework](#responsible-gambling-framework)
5. [AI-Specific Considerations](#ai-specific-considerations)
6. [Data Privacy & GDPR](#data-privacy--gdpr)
7. [Stake Limits & Controls](#stake-limits--controls)
8. [Audit & Transparency](#audit--transparency)
9. [Implementation Checklist](#implementation-checklist)
10. [References](#references)

---

## Executive Summary

**Building a betting AI assistant comes with serious legal and ethical responsibilities.**

**Critical Compliance Areas:**
1. ✅ **Betfair ToS** - API usage permitted with restrictions
2. ✅ **Responsible Gambling** - AI must not encourage problem gambling
3. ✅ **Regulatory Compliance** - Varies by jurisdiction
4. ✅ **Data Privacy** - GDPR for EU users
5. ✅ **Transparency** - Users must understand AI limitations

**Key Findings:**
- **Betfair allows bots** through official API (with integrity protections)
- **97% accuracy** in AI problem gambling detection (2025 data)
- **Proposed SAFE Bet Act** (US) bans AI tracking for marketing
- **Self-exclusion programs** increasingly use facial recognition AI
- **Mandatory affordability checks** for high-spending customers

**Our Approach:**
- **Read-only MVP** minimizes risk (no automated betting)
- **Educational focus** on data-driven decisions, not gambling promotion
- **Responsible gambling tools** built-in from day one
- **Transparent AI** - clear about limitations and risks
- **User control** - AI assists, user decides

---

## Betfair Terms of Service

### API Usage - Official Stance

**From Betfair ToS:**
> "Betfair acknowledges that customers use programs designed to automatically place bets within certain parameters (e.g., to back or lay at a certain price), which they call 'bots'."

**Permitted:**
✅ Using Betfair API for automated data access
✅ Building tools that analyze markets
✅ Creating bots that place bets via API
✅ Personal use for own account

**Restricted/Prohibited:**
❌ Bots that manipulate markets
❌ Bots that adversely affect Exchange integrity
❌ Commercial bot services without vendor certification
❌ Sharing account credentials
❌ Accessing from restricted locations

### Betfair's Discretion

**From ToS:**
> "Betfair may restrict users from using bots either generally or in relation to any specific bot if they believe the bot has been used to place bets on, or manipulate, any Market which adversely affects the integrity of the Exchange."

**What this means:**
- Betfair monitors bot activity
- They can suspend accounts showing suspicious patterns
- Integrity of exchange is paramount
- Transparency helps avoid issues

### Our MCP Server Position

**We are compliant because:**
1. ✅ Using official Betfair API (not scraping or unauthorized access)
2. ✅ Read-only MVP (no market manipulation risk)
3. ✅ Personal use (not commercial bot service)
4. ✅ Transparent operation (logged, auditable)
5. ✅ User-controlled (AI assists, user executes)

**Future betting features:**
- Require explicit user confirmation per bet
- Log all bet instructions
- Respect Betfair rate limits
- No high-frequency manipulation
- Designed for individual decision support, not automated trading systems

---

## Regulatory Landscape

### United Kingdom (Primary Market)

**Regulator:** UK Gambling Commission (UKGC)

**Key Requirements:**
- ✅ Age verification (18+)
- ✅ Affordability checks for high spenders
- ✅ Self-exclusion support (GAMSTOP integration)
- ✅ Stake limits (£5 max on slot spins, but not exchange betting)
- ✅ Advertising restrictions
- ✅ Protection of customer funds

**AI-Specific:**
- Operators must use AI to identify problem gambling patterns
- Mandatory intervention when harmful behavior detected
- Customer data used for risk assessments

**Relevance to MCP Server:**
- We don't hold customer funds (Betfair does)
- We should detect concerning patterns and warn users
- No advertising or promotional features
- Educational and analytical focus

---

### United States

**Status:** Fragmented state-by-state regulation

**Proposed Federal Legislation - SAFE Bet Act (2025):**
- ❌ Ban on AI tracking for marketing purposes
- ✅ Mandatory affordability checks for high spenders
- ✅ National self-exclusion database
- ✅ Limits on VIP membership schemes

**Key States:**
- **New Jersey:** Legal online betting, strict responsible gambling
- **Nevada:** Legal, casino-focused
- **New York:** Legal, high tax rates
- **California, Texas, Florida:** Currently illegal

**Geographic Restrictions:**
- Betfair API returns `BETTING_RESTRICTED_LOCATION` error for restricted regions
- MCP server should detect this and inform user
- Don't encourage VPN usage to bypass restrictions

---

### European Union

**Regulations:**
- ✅ GDPR (General Data Protection Regulation)
- ✅ Individual member state gambling licenses
- ✅ Anti-money laundering (AML) directives
- ✅ Responsible gambling requirements

**GDPR Implications:**
- User consent required for data processing
- Right to data access and deletion
- Cannot store sensitive data without justification
- Data minimization principle

---

### Australia

**Regulator:** Various state bodies + federal oversight

**Key Points:**
- Betfair operates in Australia (licensed)
- Strong responsible gambling framework
- Self-exclusion programs (BetStop)
- Advertising restrictions (no ads during live sports)

---

## Responsible Gambling Framework

### AI-Powered Detection (2025 State of the Art)

**Effectiveness:**
- **97% accuracy** in predicting problem gambling using short-term data
- AI analyzes: betting patterns, play frequency, session duration, stake escalation
- Real-time alerts to both players and operators

**Intervention Tiers:**

**Low Risk:**
- Pop-up reminders ("You've been playing for 2 hours")
- Session time limits
- Reality checks

**Moderate Risk:**
- Tailored advice messages
- Suggested temporary timeouts
- Deposit limit recommendations

**High Risk:**
- Personalized care calls
- Mandatory exclusion options
- Referrals to online behavioral counseling
- Account locks

### Our MCP Server Implementation

**Built-in Safeguards:**

```python
class ResponsibleGamblingMonitor:
    """Monitor user behavior and flag concerning patterns"""

    def __init__(self):
        self.session_start = None
        self.queries_count = 0
        self.markets_analyzed = 0
        self.high_stake_queries = 0

    def track_activity(self, query_type: str, context: dict):
        """Track user activity"""
        self.queries_count += 1

        # Check session duration
        if self.session_start:
            duration = time.time() - self.session_start
            if duration > 2 * 3600:  # 2 hours
                self.warn_session_length()

        # Check query patterns
        if query_type == 'high_stake_analysis':
            self.high_stake_queries += 1
            if self.high_stake_queries > 10:
                self.warn_excessive_high_stakes()

    def warn_session_length(self):
        """Warn about long session"""
        return {
            'warning': 'You have been using this assistant for over 2 hours.',
            'recommendation': 'Consider taking a break.',
            'resources': 'https://www.gambleaware.org'
        }

    def warn_excessive_high_stakes(self):
        """Warn about high-risk behavior"""
        return {
            'warning': 'You have been analyzing high-stake bets frequently.',
            'recommendation': 'Please gamble responsibly. Only bet what you can afford to lose.',
            'resources': {
                'GambleAware': 'https://www.gambleaware.org',
                'GAMSTOP': 'https://www.gamstop.co.uk',
                'National Problem Gambling Helpline': '0808 8020 133'
            }
        }
```

---

### Self-Exclusion Integration

**GAMSTOP (UK):**
- National self-exclusion scheme
- Users can ban themselves for 6 months, 1 year, or 5 years
- Applies across all UK-licensed operators

**Our Responsibility:**
```python
@mcp.tool()
async def responsible_gambling_resources() -> dict:
    """Get responsible gambling resources and self-exclusion info"""
    return {
        'self_exclusion': {
            'UK_GAMSTOP': {
                'url': 'https://www.gamstop.co.uk',
                'description': 'Free self-exclusion service for UK online gambling',
                'duration_options': ['6 months', '1 year', '5 years']
            },
            'Betfair_timeout': {
                'url': 'https://www.betfair.com/responsible-gambling',
                'description': 'Set a timeout or self-exclude directly on Betfair'
            }
        },
        'support': {
            'GambleAware': {
                'url': 'https://www.gambleaware.org',
                'phone': '0808 8020 133',
                'description': 'Free confidential advice and support'
            },
            'BeGambleAware': {
                'url': 'https://www.begambleaware.org',
                'description': 'Information and tools for safer gambling'
            },
            'Gamblers_Anonymous': {
                'url': 'https://www.gamblersanonymous.org.uk',
                'description': 'Fellowship of compulsive gamblers'
            }
        },
        'tools': {
            'reality_check': 'Set reminders to check how long you have been betting',
            'deposit_limits': 'Set daily, weekly, or monthly deposit limits',
            'loss_limits': 'Set maximum loss limits',
            'time_limits': 'Set maximum session duration'
        }
    }
```

---

### Mandatory Warnings

**Display before first use:**
```
┌────────────────────────────────────────────────────────┐
│              RESPONSIBLE GAMBLING NOTICE                │
├────────────────────────────────────────────────────────┤
│                                                         │
│  This AI assistant provides betting analysis and        │
│  information only. It does not guarantee profits.       │
│                                                         │
│  • Gambling can be addictive                           │
│  • Only bet what you can afford to lose                │
│  • Set deposit and loss limits                         │
│  • Take regular breaks                                 │
│                                                         │
│  If you or someone you know has a gambling problem:    │
│                                                         │
│  UK: Call National Gambling Helpline 0808 8020 133     │
│  US: Call 1-800-GAMBLER                                │
│  Or visit: https://www.gambleaware.org                 │
│                                                         │
│  Self-Exclusion: https://www.gamstop.co.uk (UK)        │
│                                                         │
└────────────────────────────────────────────────────────┘

Type 'I understand' to continue
```

---

## AI-Specific Considerations

### Transparency & Explainability

**Problem:** AI recommendations can seem authoritative, leading users to over-trust them

**Solution:** Always clarify AI limitations

```python
@mcp.tool()
async def analyze_value_bet(market_id: str) -> dict:
    """Analyze potential value bet"""

    analysis = perform_analysis(market_id)

    return {
        **analysis,
        'disclaimer': {
            'ai_limitations': [
                'This analysis is based on historical data and statistical models',
                'Past performance does not guarantee future results',
                'The AI cannot account for late-breaking news or insider information',
                'Betting always carries risk - you may lose money'
            ],
            'recommendation': 'Use this as one input among many for your decision',
            'your_responsibility': 'You are solely responsible for your betting decisions'
        }
    }
```

---

### Preventing Addictive Patterns

**AI should NOT:**
- ❌ Encourage chasing losses ("Bet more to recover!")
- ❌ Create urgency ("Bet now before odds change!")
- ❌ Use emotional manipulation ("You're on a winning streak!")
- ❌ Suggest increasing stakes after losses
- ❌ Gamify analysis (points, achievements, leaderboards)

**AI SHOULD:**
- ✅ Provide objective, data-driven analysis
- ✅ Remind users of risks
- ✅ Suggest breaks during long sessions
- ✅ Flag concerning patterns
- ✅ Promote responsible gambling resources

**Example - Responsible Framing:**
```
❌ BAD: "You're on fire! The odds are in your favor - bet big!"

✅ GOOD: "Based on historical data, this market shows a 12% value edge.
         However, remember that all bets carry risk. Consider your
         bankroll and only bet what you can afford to lose."
```

---

### Vulnerable Populations

**Enhanced Protections for:**
- Young adults (18-25) - higher risk of problem gambling
- People with prior gambling issues
- Users showing escalating behavior patterns
- Users in financial distress

**Detection Signals:**
- Rapidly increasing stake sizes
- Frequent late-night/early-morning sessions
- Chasing losses (betting more after losing)
- Ignoring responsible gambling warnings
- Expressions of desperation in queries

**Intervention:**
```python
def detect_vulnerable_pattern(user_history: dict) -> dict:
    """Detect vulnerable gambling patterns"""

    warnings = []

    # Check stake escalation
    if user_history['average_stake_last_week'] > user_history['average_stake_previous_month'] * 2:
        warnings.append({
            'type': 'stake_escalation',
            'message': 'Your average stake has doubled. This can be a sign of chasing losses.',
            'action': 'Consider setting a loss limit or taking a break.'
        })

    # Check session timing
    late_night_sessions = sum(1 for s in user_history['sessions'] if 0 <= s['hour'] < 6)
    if late_night_sessions > 5:
        warnings.append({
            'type': 'unusual_hours',
            'message': 'You have been gambling during unusual hours frequently.',
            'action': 'This may indicate problematic behavior. Please consider self-exclusion options.'
        })

    return {
        'risk_level': 'high' if len(warnings) > 2 else 'moderate' if warnings else 'low',
        'warnings': warnings,
        'resources': get_help_resources()
    }
```

---

## Data Privacy & GDPR

### Data Collection Principles

**What we collect:**
- API requests/responses (for caching, analysis)
- User query patterns (for responsible gambling monitoring)
- Session metadata (duration, frequency)

**What we DON'T collect:**
- Personal identifying information (unless user provides)
- Financial information (Betfair handles this)
- Location data (beyond what Betfair API provides)
- Behavioral profiling for marketing

### GDPR Compliance

**User Rights:**
1. **Right to Access** - Users can request all data we store
2. **Right to Deletion** - Users can request data deletion
3. **Right to Portability** - Users can export their data
4. **Right to Rectification** - Users can correct inaccurate data

**Implementation:**
```python
@mcp.tool()
async def export_my_data(ctx: Context) -> dict:
    """Export all user data (GDPR compliance)"""
    user_id = ctx.user_id

    return {
        'query_history': get_user_queries(user_id),
        'session_data': get_user_sessions(user_id),
        'preferences': get_user_preferences(user_id),
        'responsible_gambling_interactions': get_rg_warnings(user_id),
        'format': 'JSON',
        'export_date': datetime.utcnow().isoformat(),
        'deletion_instructions': 'To delete this data, use the delete_my_data tool'
    }

@mcp.tool()
async def delete_my_data(ctx: Context, confirmation: str) -> dict:
    """Delete all user data (GDPR Right to Erasure)"""
    if confirmation != "I CONFIRM DELETION":
        return {'error': 'Please confirm deletion by typing "I CONFIRM DELETION"'}

    user_id = ctx.user_id

    # Delete all user data
    delete_user_queries(user_id)
    delete_user_sessions(user_id)
    delete_user_preferences(user_id)
    delete_user_cache(user_id)

    return {
        'status': 'success',
        'message': 'All your data has been permanently deleted',
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Cookie & Tracking Policy

**No tracking cookies** - MCP server runs locally (stdio transport)
**Session cookies only** - For Betfair API authentication
**No third-party analytics** - User privacy is paramount

---

## Stake Limits & Controls

### Configurable Limits

**For future betting features:**

```python
class StakeLimitConfig:
    """User-defined stake limits"""

    def __init__(self):
        self.max_single_bet = 10.0  # £10 default max
        self.daily_limit = 50.0     # £50 daily
        self.weekly_limit = 200.0   # £200 weekly
        self.monthly_limit = 500.0  # £500 monthly

    def check_bet_allowed(self, stake: float) -> dict:
        """Check if bet is within limits"""
        if stake > self.max_single_bet:
            return {
                'allowed': False,
                'reason': f'Stake £{stake} exceeds single bet limit £{self.max_single_bet}'
            }

        # Check daily spend
        today_spent = get_today_total_staked()
        if today_spent + stake > self.daily_limit:
            return {
                'allowed': False,
                'reason': f'Would exceed daily limit (£{today_spent + stake:.2f} / £{self.daily_limit})',
                'spent_today': today_spent
            }

        return {'allowed': True}

@mcp.tool()
async def set_stake_limits(
    max_single: float = 10.0,
    daily: float = 50.0,
    weekly: float = 200.0,
    monthly: float = 500.0
) -> dict:
    """Set personal stake limits for responsible gambling"""
    limits = StakeLimitConfig()
    limits.max_single_bet = max_single
    limits.daily_limit = daily
    limits.weekly_limit = weekly
    limits.monthly_limit = monthly

    save_user_limits(limits)

    return {
        'status': 'Limits set successfully',
        'limits': {
            'single_bet': f'£{max_single}',
            'daily': f'£{daily}',
            'weekly': f'£{weekly}',
            'monthly': f'£{monthly}'
        },
        'note': 'These limits will be enforced on all betting requests'
    }
```

---

### Loss Limits

```python
class LossLimitTracker:
    """Track losses and enforce limits"""

    def __init__(self):
        self.daily_loss_limit = 100.0
        self.weekly_loss_limit = 500.0

    def check_current_loss(self) -> dict:
        """Check current loss against limits"""
        today_loss = calculate_today_net_loss()
        week_loss = calculate_week_net_loss()

        warnings = []

        if today_loss > self.daily_loss_limit * 0.8:  # 80% threshold
            warnings.append({
                'severity': 'high',
                'message': f'You have lost £{today_loss:.2f} today (limit: £{self.daily_loss_limit})',
                'recommendation': 'Consider stopping for today'
            })

        if week_loss > self.weekly_loss_limit * 0.8:
            warnings.append({
                'severity': 'high',
                'message': f'You have lost £{week_loss:.2f} this week (limit: £{self.weekly_loss_limit})',
                'recommendation': 'Consider self-exclusion options'
            })

        return {
            'today_loss': today_loss,
            'daily_limit': self.daily_loss_limit,
            'week_loss': week_loss,
            'weekly_limit': self.weekly_loss_limit,
            'warnings': warnings
        }
```

---

## Audit & Transparency

### Logging All Interactions

**What to log:**
- Every tool call (timestamp, user, parameters)
- AI recommendations given
- Responsible gambling warnings shown
- User acknowledgments
- Stake limit checks
- Any bet placements (if enabled)

**Log Format:**
```json
{
  "timestamp": "2025-11-16T14:30:45Z",
  "user_id": "user_123",
  "tool": "analyze_value_bet",
  "parameters": {
    "market_id": "1.234567"
  },
  "ai_recommendation": {
    "value_edge": 12.5,
    "recommended_stake": 10.0,
    "confidence": 0.65
  },
  "disclaimer_shown": true,
  "user_action": "acknowledged",
  "responsible_gambling_check": {
    "session_duration_minutes": 45,
    "warnings_shown": 0,
    "within_limits": true
  }
}
```

---

### Monthly Transparency Reports

**Auto-generated for users:**
```python
@mcp.tool()
async def generate_monthly_report(month: str) -> dict:
    """Generate transparency report for a month"""
    return {
        'month': month,
        'usage_statistics': {
            'total_sessions': 24,
            'avg_session_duration_minutes': 32,
            'total_queries': 156,
            'most_used_tools': [
                'get_market_prices',
                'search_events',
                'analyze_value_bet'
            ]
        },
        'responsible_gambling': {
            'warnings_shown': 3,
            'longest_session_hours': 2.5,
            'late_night_sessions': 2,
            'resources_accessed': 1
        },
        'financial': {
            'note': 'This MCP server does not handle financial transactions',
            'betfair_statement': 'View your complete financial history on Betfair.com'
        },
        'data_usage': {
            'queries_cached': 45,
            'api_calls_made': 111,
            'data_stored_mb': 2.3
        }
    }
```

---

## Implementation Checklist

### Pre-Launch

**Legal:**
- [ ] Review Betfair Terms of Service
- [ ] Consult legal counsel on gambling laws in target jurisdictions
- [ ] Draft Terms of Use for MCP server
- [ ] Create Privacy Policy (GDPR compliant)
- [ ] Implement age verification prompts

**Responsible Gambling:**
- [ ] Implement responsible gambling monitor
- [ ] Add warnings before first use
- [ ] Create help resources tool
- [ ] Build session duration tracking
- [ ] Add self-exclusion resource links

**Data Privacy:**
- [ ] Implement GDPR data export tool
- [ ] Implement GDPR data deletion tool
- [ ] Create data retention policy (e.g., 90 days)
- [ ] Add consent mechanisms
- [ ] Document data collection practices

**Transparency:**
- [ ] Implement comprehensive logging
- [ ] Create audit trail system
- [ ] Build monthly transparency reports
- [ ] Document AI decision-making process

---

### Ongoing Compliance

**Monthly:**
- [ ] Review logged interactions for concerning patterns
- [ ] Generate transparency reports
- [ ] Update responsible gambling resources
- [ ] Check for ToS changes from Betfair

**Quarterly:**
- [ ] Legal compliance audit
- [ ] Review effectiveness of responsible gambling measures
- [ ] Update privacy policy if needed
- [ ] Security review

**Annually:**
- [ ] Comprehensive legal review
- [ ] Responsible gambling framework assessment
- [ ] User feedback survey on safety measures
- [ ] Third-party security audit (if commercial)

---

## References

### Regulatory Bodies
- [UK Gambling Commission](https://www.gamblingcommission.gov.uk/)
- [Betfair Terms and Conditions](https://www.betfair.com/aboutUs/Terms.and.Conditions/)
- [GDPR Official Text](https://gdpr-info.eu/)

### Responsible Gambling
- [GambleAware](https://www.gambleaware.org/)
- [GAMSTOP (UK Self-Exclusion)](https://www.gamstop.co.uk/)
- [National Council on Problem Gambling (US)](https://www.ncpgambling.org/)
- [AI-Powered Responsible Gambling Tools](https://www.business2community.com/igaming-news/ai-responsible-gambling-tools-2025/)

### Research & Studies
- [AI in Sports Betting: Responsible Gambling](https://mnapg.org/betting-on-safety-how-ai-can-power-responsible-gambling-programs/)
- [SAFE Bet Act Legislation](https://gamblingharm.org/sports-betting-artificial-intelligence-ai-legislation-tracker/)

### Related Research Documents
- [RESEARCH_06_USE_CASES.md](./RESEARCH_06_USE_CASES.md) - User scenarios and ethical design
- [RESEARCH_01_AUTHENTICATION.md](./RESEARCH_01_AUTHENTICATION.md) - Secure access control
- [RESEARCH_08_PRODUCTION_DEPLOYMENT.md](./RESEARCH_08_PRODUCTION_DEPLOYMENT.md) - Security measures

---

**Next Document:** [RESEARCH_08_PRODUCTION_DEPLOYMENT.md](./RESEARCH_08_PRODUCTION_DEPLOYMENT.md)
**Previous Document:** [RESEARCH_06_USE_CASES.md](./RESEARCH_06_USE_CASES.md)
**Back to:** [RESEARCH_INDEX.md](./RESEARCH_INDEX.md)
