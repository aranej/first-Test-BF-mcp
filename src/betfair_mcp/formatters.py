"""
Response formatting utilities for MCP tools.

This module provides utilities to format tool responses in both
Markdown (human-friendly) and JSON (machine-readable) formats.
"""

from typing import Any, Dict, List


def format_account_balance(data: Dict[str, Any]) -> str:
    """
    Format account balance data as Markdown.

    Args:
        data: Account balance dict from get_account_balance

    Returns:
        Markdown-formatted summary
    """
    return f"""## Account Balance

**Available to Bet:** £{data['available_to_bet']:.2f}
**Current Exposure:** £{data['exposure']:.2f}
**Exposure Limit:** £{data['exposure_limit']:.2f}
**Wallet:** {data['wallet']}
**Discount Rate:** {data['discount_rate']:.1%}
"""


def format_account_details(data: Dict[str, Any]) -> str:
    """
    Format account details as Markdown.

    Args:
        data: Account details dict from get_account_details

    Returns:
        Markdown-formatted summary
    """
    return f"""## Account Details

**Name:** {data['first_name']} {data['last_name']}
**Currency:** {data['currency_code']}
**Timezone:** {data['timezone']}
**Locale:** {data['locale_code']}
**Betfair Points:** {data['points_balance']:,}
**Discount Rate:** {data['discount_rate']:.1%}
"""


def format_event_types(data: List[Dict[str, Any]]) -> str:
    """
    Format event types list as Markdown.

    Args:
        data: List of event types from list_event_types

    Returns:
        Markdown-formatted table
    """
    if not data:
        return "## Event Types\n\nNo event types found."

    lines = ["## Event Types", "", "| ID | Sport | Markets |", "|---|---|---:|"]
    for et in sorted(data, key=lambda x: x["event_type_name"]):
        lines.append(
            f"| {et['event_type_id']} | {et['event_type_name']} | {et['market_count']:,} |"
        )

    return "\n".join(lines)


def format_events(data: List[Dict[str, Any]]) -> str:
    """
    Format events list as Markdown.

    Args:
        data: List of events from list_events

    Returns:
        Markdown-formatted summary
    """
    if not data:
        return "## Events\n\nNo events found."

    lines = [f"## Events ({len(data)} found)", ""]
    for event in data[:10]:  # Limit to first 10 for summary
        date = event.get("open_date", "Unknown")
        lines.append(f"**{event['event_name']}**")
        lines.append(f"- Event ID: `{event['event_id']}`")
        lines.append(f"- Start: {date}")
        lines.append(f"- Country: {event.get('country_code', 'N/A')}")
        lines.append(f"- Markets: {event['market_count']}")
        lines.append("")

    if len(data) > 10:
        lines.append(f"*...and {len(data) - 10} more events*")

    return "\n".join(lines)


def format_competitions(data: List[Dict[str, Any]]) -> str:
    """
    Format competitions list as Markdown.

    Args:
        data: List of competitions from list_competitions

    Returns:
        Markdown-formatted table
    """
    if not data:
        return "## Competitions\n\nNo competitions found."

    lines = [
        f"## Competitions ({len(data)} found)",
        "",
        "| ID | Competition | Markets |",
        "|---|---|---:|",
    ]
    for comp in sorted(data, key=lambda x: -x["market_count"]):
        lines.append(
            f"| {comp['competition_id']} | {comp['competition_name']} | {comp['market_count']:,} |"
        )

    return "\n".join(lines)


def format_market_catalogue(data: List[Dict[str, Any]]) -> str:
    """
    Format market catalogue as Markdown.

    Args:
        data: List of markets from list_market_catalogue

    Returns:
        Markdown-formatted summary
    """
    if not data:
        return "## Markets\n\nNo markets found."

    lines = [f"## Markets ({len(data)} found)", ""]
    for market in data[:10]:  # Limit to first 10
        lines.append(f"**{market['market_name']}** ({market['market_type']})")
        lines.append(f"- Market ID: `{market['market_id']}`")
        lines.append(f"- Event: {market.get('event_name', 'N/A')}")
        if market.get("competition_name"):
            lines.append(f"- Competition: {market['competition_name']}")
        lines.append(f"- Total Matched: £{market.get('total_matched', 0):,.2f}")

        runners = market.get("runners", [])
        if runners:
            lines.append(f"- Runners ({len(runners)}):")
            for runner in runners[:5]:  # Show first 5 runners
                lines.append(f"  - {runner['runner_name']} (ID: {runner['selection_id']})")
            if len(runners) > 5:
                lines.append(f"  - *...and {len(runners) - 5} more*")
        lines.append("")

    if len(data) > 10:
        lines.append(f"*...and {len(data) - 10} more markets*")

    return "\n".join(lines)


def format_market_prices(data: List[Dict[str, Any]]) -> str:
    """
    Format market prices as Markdown.

    Args:
        data: List of market prices from get_market_prices

    Returns:
        Markdown-formatted summary with odds
    """
    if not data:
        return "## Market Prices\n\nNo market data found."

    lines = [f"## Market Prices ({len(data)} markets)", ""]
    for market in data:
        status = market.get("status", "UNKNOWN")
        matched = market.get("total_matched", 0)
        lines.append(f"**Market {market['market_id']}** ({status})")
        lines.append(f"- Total Matched: £{matched:,.2f}")
        lines.append("")

        runners = market.get("runners", [])
        if runners:
            lines.append("| Runner | Last Price | Back | Lay |")
            lines.append("|---|---:|---|---|")
            for runner in runners:
                sel_id = runner.get("selection_id", "?")
                last = runner.get("last_price_traded")
                last_str = f"{last:.2f}" if last else "—"

                backs = runner.get("back_prices", [])
                back_str = (
                    f"{backs[0]['price']:.2f} (£{backs[0]['size']:.0f})"
                    if backs
                    else "—"
                )

                lays = runner.get("lay_prices", [])
                lay_str = (
                    f"{lays[0]['price']:.2f} (£{lays[0]['size']:.0f})" if lays else "—"
                )

                lines.append(f"| {sel_id} | {last_str} | {back_str} | {lay_str} |")
        lines.append("")

    return "\n".join(lines)
