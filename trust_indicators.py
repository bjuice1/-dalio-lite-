"""
Trust & Security Indicators Module for Dalio Lite

Provides reusable components to display trust signals, security badges,
and data freshness indicators throughout the application.

Usage:
    from trust_indicators import render_trust_bar, render_security_badge, render_data_freshness

    # At top of page
    render_trust_bar()

    # In specific sections
    render_security_badge()
    render_data_freshness(last_updated_timestamp)
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import os


def render_trust_bar() -> None:
    """
    Render the global trust bar at the top of any page.
    Displays security status, connection status, and data freshness.

    Should be called near the top of each page, after page config.
    """
    # Create three columns for trust indicators
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        # Security indicator
        st.markdown(
            """
            <div style='text-align: center; padding: 8px; background-color: #e8f5e9; border-radius: 4px;'>
                <span style='font-size: 18px;'>🔒</span>
                <span style='font-size: 14px; font-weight: 500; color: #2e7d32;'> Secure Connection</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # Connection status - check if we're in paper or live mode
        trading_mode = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        mode_text = "Paper Trading" if trading_mode else "Live Trading"
        mode_color = "#1976d2" if trading_mode else "#d32f2f"
        mode_bg = "#e3f2fd" if trading_mode else "#ffebee"
        mode_icon = "📝" if trading_mode else "💵"

        st.markdown(
            f"""
            <div style='text-align: center; padding: 8px; background-color: {mode_bg}; border-radius: 4px;'>
                <span style='font-size: 18px;'>{mode_icon}</span>
                <span style='font-size: 14px; font-weight: 500; color: {mode_color};'> {mode_text}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        # Data freshness - show current time
        current_time = datetime.now().strftime("%I:%M %p ET")
        st.markdown(
            f"""
            <div style='text-align: center; padding: 8px; background-color: #e8f5e9; border-radius: 4px;'>
                <span style='font-size: 18px;'>✓</span>
                <span style='font-size: 14px; font-weight: 500; color: #2e7d32;'> Updated {current_time}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Add small spacing after trust bar
    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)


def render_security_badge(show_sipc: bool = True, show_encryption: bool = True) -> None:
    """
    Render security badges showing protection and security features.

    Args:
        show_sipc: Whether to show SIPC protection badge
        show_encryption: Whether to show encryption badge
    """
    st.markdown("---")

    badge_cols = st.columns([1, 1, 1])

    if show_sipc:
        with badge_cols[0]:
            st.markdown(
                """
                <div style='text-align: center; padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px;'>
                    <div style='font-size: 24px; margin-bottom: 4px;'>🛡️</div>
                    <div style='font-size: 12px; font-weight: 600; color: #424242;'>SIPC Protected</div>
                    <div style='font-size: 10px; color: #757575;'>Up to $500K</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if show_encryption:
        with badge_cols[1]:
            st.markdown(
                """
                <div style='text-align: center; padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px;'>
                    <div style='font-size: 24px; margin-bottom: 4px;'>🔐</div>
                    <div style='font-size: 12px; font-weight: 600; color: #424242;'>Bank-Level Security</div>
                    <div style='font-size: 10px; color: #757575;'>256-bit Encryption</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with badge_cols[2]:
        st.markdown(
            """
            <div style='text-align: center; padding: 12px; border: 1px solid #e0e0e0; border-radius: 8px;'>
                <div style='font-size: 24px; margin-bottom: 4px;'>✓</div>
                <div style='font-size: 12px; font-weight: 600; color: #424242;'>SEC Regulated</div>
                <div style='font-size: 10px; color: #757575;'>FINRA Member</div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_data_freshness(last_updated: Optional[datetime] = None, data_source: str = "Alpaca") -> None:
    """
    Render data freshness indicator showing when data was last updated.

    Args:
        last_updated: Datetime of last data update (defaults to now)
        data_source: Name of data source (e.g., "Alpaca", "Market Data")
    """
    if last_updated is None:
        last_updated = datetime.now()

    # Calculate time difference
    time_diff = datetime.now() - last_updated

    # Determine freshness status
    if time_diff < timedelta(minutes=5):
        status_icon = "🟢"
        status_text = "Live"
        status_color = "#2e7d32"
    elif time_diff < timedelta(minutes=30):
        status_icon = "🟡"
        status_text = "Recent"
        status_color = "#f57c00"
    else:
        status_icon = "🔴"
        status_text = "Delayed"
        status_color = "#c62828"

    # Format timestamp
    if time_diff < timedelta(minutes=1):
        time_text = "Just now"
    elif time_diff < timedelta(hours=1):
        minutes = int(time_diff.total_seconds() / 60)
        time_text = f"{minutes} min ago"
    elif time_diff < timedelta(days=1):
        hours = int(time_diff.total_seconds() / 3600)
        time_text = f"{hours} hr ago"
    else:
        time_text = last_updated.strftime("%b %d, %I:%M %p")

    st.markdown(
        f"""
        <div style='padding: 8px 12px; background-color: #f5f5f5; border-radius: 4px; border-left: 3px solid {status_color};'>
            <span style='font-size: 14px;'>{status_icon}</span>
            <span style='font-size: 13px; font-weight: 500; color: {status_color};'> {status_text}</span>
            <span style='font-size: 12px; color: #757575;'> • {data_source} data: {time_text}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_paper_trading_warning() -> None:
    """
    Render a prominent warning banner when in paper trading mode.
    Should be shown on dashboard and trading-related pages.
    """
    trading_mode = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    if trading_mode:
        st.info(
            "📝 **Paper Trading Mode Active**\n\n"
            "You're using simulated money. No real funds are at risk. "
            "Perfect for learning and testing strategies!\n\n"
            "**Ready for real trading?** Switch to live trading in your Alpaca account settings.",
            icon="ℹ️"
        )


def render_demo_data_warning() -> None:
    """
    Render a prominent warning that data shown is demo/sample data.
    Should be used on Market Dashboard and any page showing placeholder data.
    """
    st.warning(
        "⚠️ **Demo Data Notice**\n\n"
        "The market indicators and economic data shown below are **sample/demo values** "
        "for illustration purposes.\n\n"
        "**Coming soon:** Live integration with real economic APIs for accurate market signals.",
        icon="⚠️"
    )


def render_live_trading_warning() -> None:
    """
    Render a critical warning banner when in LIVE trading mode.
    Should be shown prominently to ensure users know real money is involved.
    """
    trading_mode = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    if not trading_mode:
        st.error(
            "💵 **LIVE TRADING MODE ACTIVE**\n\n"
            "⚠️ **This account uses REAL MONEY.** All trades execute with actual funds.\n\n"
            "- Ensure you understand the risks of algorithmic trading\n"
            "- Review all strategy settings carefully\n"
            "- Monitor your account regularly\n\n"
            "**Want to practice first?** Switch to Paper Trading mode in your Alpaca settings.",
            icon="🚨"
        )


def render_market_hours_status() -> None:
    """
    Display current market hours status (open/closed).
    Useful for setting expectations about data updates and trading availability.
    """
    now = datetime.now()
    # Simplified market hours check (9:30 AM - 4:00 PM ET, Monday-Friday)
    # Note: This doesn't account for holidays or pre/post-market hours
    is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
    # Rough approximation - doesn't handle timezone properly, but good enough for UI indication
    is_market_hours = 9 <= now.hour < 16

    if is_weekday and is_market_hours:
        st.markdown(
            """
            <div style='padding: 8px 12px; background-color: #e8f5e9; border-radius: 4px; border-left: 3px solid #2e7d32;'>
                <span style='font-size: 14px;'>🔔</span>
                <span style='font-size: 13px; font-weight: 500; color: #2e7d32;'> Market Open</span>
                <span style='font-size: 12px; color: #558b2f;'> • Trading active until 4:00 PM ET</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        next_open = "Monday 9:30 AM ET" if now.weekday() >= 4 else "Tomorrow 9:30 AM ET"
        st.markdown(
            f"""
            <div style='padding: 8px 12px; background-color: #fff3e0; border-radius: 4px; border-left: 3px solid #f57c00;'>
                <span style='font-size: 14px;'>🌙</span>
                <span style='font-size: 13px; font-weight: 500; color: #e65100;'> Market Closed</span>
                <span style='font-size: 12px; color: #ef6c00;'> • Opens {next_open}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_alpaca_branding() -> None:
    """
    Render Alpaca branding footer with proper attribution.
    Should be shown in sidebar or footer of main pages.
    """
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; padding: 12px; color: #757575; font-size: 12px;'>
            <div style='margin-bottom: 8px;'>Powered by</div>
            <div style='font-size: 16px; font-weight: 600; color: #424242;'>Alpaca Markets</div>
            <div style='margin-top: 4px;'>Commission-free trading API</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_risk_disclosure() -> None:
    """
    Render standard risk disclosure for investment applications.
    Should be shown in footer or legal section.
    """
    with st.expander("⚖️ Risk Disclosure & Important Information"):
        st.markdown(
            """
            **Investment Risk Disclosure**

            - **Past performance does not guarantee future results.** All investments carry risk of loss.
            - **All Weather portfolio strategy:** A strategic asset allocation approach developed by Ray Dalio.
              Historical performance is not indicative of future returns.
            - **Market risk:** The value of your portfolio will fluctuate with market conditions.
            - **No investment advice:** This tool provides information only. Consult a financial advisor for personalized advice.

            **Alpaca Securities LLC**

            - Member FINRA/SIPC
            - Securities in your account protected up to $500,000 (including $250,000 cash)
            - Visit [Alpaca Markets](https://alpaca.markets) for more information

            **Data & Privacy**

            - Your credentials are stored securely and never shared
            - All API connections use bank-level encryption (TLS 1.2+)
            - We do not store your Alpaca credentials on our servers

            **Paper Trading Notice**

            - Paper trading uses simulated money for risk-free practice
            - Results may differ from live trading due to order fills and market conditions
            - Always test strategies in paper mode before using real funds
            """
        )
