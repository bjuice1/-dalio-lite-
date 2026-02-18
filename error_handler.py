"""
Error Handler Module for Dalio Lite

Translates technical exceptions into user-friendly messages with actionable guidance.
Provides consistent error handling across the entire application.

Usage:
    from error_handler import translate_exception, handle_error_display, ErrorSeverity

    try:
        # risky operation
    except Exception as e:
        message, severity = translate_exception(e, context="API connection")
        handle_error_display(message, severity)
"""

from enum import Enum
from typing import Tuple
import streamlit as st
from alpaca.common.exceptions import APIError


class ErrorSeverity(Enum):
    """Error severity levels for UI display"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


def translate_exception(exception: Exception, context: str = "") -> Tuple[str, ErrorSeverity]:
    """
    Translate technical exception to user-friendly message.

    Args:
        exception: The caught exception
        context: Additional context about where the error occurred

    Returns:
        Tuple of (user_friendly_message, severity_level)
    """

    # Alpaca API Authentication Errors (401)
    if isinstance(exception, APIError) and exception.status_code == 401:
        return (
            "🔐 **Invalid API credentials**\n\n"
            "Your Alpaca API keys appear to be invalid or expired.\n\n"
            "**What to do:**\n"
            "1. Go to the **Setup Guide** page (in the sidebar)\n"
            "2. Verify your API keys in the Alpaca dashboard\n"
            "3. Update your credentials in the `.env` file\n"
            "4. Restart the application\n\n"
            "💡 *Tip: Make sure you're using Paper Trading keys if testing.*",
            ErrorSeverity.ERROR
        )

    # Alpaca API Rate Limiting (429)
    if isinstance(exception, APIError) and exception.status_code == 429:
        return (
            "⏱️ **Rate limit reached**\n\n"
            "We've made too many requests to Alpaca in a short time.\n\n"
            "**What to do:**\n"
            "- Wait 60 seconds and refresh the page\n"
            "- This is temporary and will resolve automatically\n\n"
            "💡 *This helps protect your account and keeps the service stable.*",
            ErrorSeverity.WARNING
        )

    # Alpaca API Server Errors (500, 502, 503, 504)
    if isinstance(exception, APIError) and exception.status_code >= 500:
        return (
            "🌐 **Alpaca service temporarily unavailable**\n\n"
            "Alpaca's servers are experiencing issues. This is not a problem with Dalio Lite.\n\n"
            "**What to do:**\n"
            "- Wait a few minutes and refresh\n"
            "- Check [Alpaca status page](https://status.alpaca.markets/) for updates\n"
            "- Your portfolio data is safe\n\n"
            "💡 *Market data and trading may resume shortly.*",
            ErrorSeverity.WARNING
        )

    # Alpaca API Market Closed (403 or specific message patterns)
    if isinstance(exception, APIError):
        error_message = str(exception).lower()
        if "market" in error_message and ("closed" in error_message or "not open" in error_message):
            return (
                "🕒 **Market is currently closed**\n\n"
                "You attempted an action that requires the market to be open.\n\n"
                "**U.S. Market Hours:**\n"
                "- Monday-Friday: 9:30 AM - 4:00 PM ET\n"
                "- Closed on weekends and holidays\n\n"
                "💡 *You can still view your portfolio and plan strategies while markets are closed.*",
                ErrorSeverity.INFO
            )

    # Alpaca Insufficient Funds
    if isinstance(exception, APIError):
        error_message = str(exception).lower()
        if "insufficient" in error_message or "buying power" in error_message:
            return (
                "💰 **Insufficient funds**\n\n"
                "Your account doesn't have enough buying power for this action.\n\n"
                "**What to do:**\n"
                "- Check your available buying power in the dashboard\n"
                "- For paper trading: Reset your paper account in Alpaca dashboard\n"
                "- For live trading: Add funds to your account\n\n"
                "💡 *Your current portfolio value and buying power are shown on the dashboard.*",
                ErrorSeverity.WARNING
            )

    # Network/Connection Errors
    if "connection" in str(exception).lower() or "network" in str(exception).lower() or "timeout" in str(exception).lower():
        return (
            "📡 **Connection issue**\n\n"
            "We're having trouble connecting to Alpaca's servers.\n\n"
            "**What to do:**\n"
            "1. Check your internet connection\n"
            "2. Refresh the page in 30 seconds\n"
            "3. If the problem persists, check [Alpaca status](https://status.alpaca.markets/)\n\n"
            "💡 *Your portfolio data is cached and remains safe.*",
            ErrorSeverity.WARNING
        )

    # File Permission Errors
    if isinstance(exception, PermissionError):
        return (
            "🔒 **File access denied**\n\n"
            "The application doesn't have permission to access a required file.\n\n"
            "**What to do:**\n"
            "1. Check file permissions in the `state/` directory\n"
            "2. Ensure the application has write access\n"
            "3. Try restarting the application\n\n"
            "🔧 *This usually happens after deployment or permission changes.*",
            ErrorSeverity.ERROR
        )

    # File Not Found Errors
    if isinstance(exception, FileNotFoundError):
        return (
            "📁 **Configuration file missing**\n\n"
            "A required configuration file wasn't found.\n\n"
            "**What to do:**\n"
            "1. Check that all files from setup are present\n"
            "2. Review the Setup Guide for required files\n"
            "3. The file may need to be created: check the documentation\n\n"
            f"🔧 *Missing file: {getattr(exception, 'filename', 'unknown')}*",
            ErrorSeverity.ERROR
        )

    # JSON Decode Errors (corrupted state files)
    if "json" in str(type(exception)).lower() or "decode" in str(exception).lower():
        return (
            "⚠️ **Configuration file corrupted**\n\n"
            "A settings file appears to be corrupted or improperly formatted.\n\n"
            "**What to do:**\n"
            "1. Check the `state/` directory for `.json` files\n"
            "2. The file may need to be reset to defaults\n"
            "3. Backup and delete the problematic file - it will be recreated\n\n"
            "🔧 *Your portfolio data at Alpaca is safe - this only affects local settings.*",
            ErrorSeverity.WARNING
        )

    # Key Errors (missing configuration)
    if isinstance(exception, KeyError):
        missing_key = str(exception).strip("'\"")
        return (
            "⚙️ **Configuration incomplete**\n\n"
            f"Required setting is missing: `{missing_key}`\n\n"
            "**What to do:**\n"
            "1. Review the Setup Guide in the sidebar\n"
            "2. Check your `.env` file for required variables\n"
            "3. Ensure all setup steps are completed\n\n"
            "🔧 *This usually happens during initial setup.*",
            ErrorSeverity.ERROR
        )

    # Value Errors (invalid input/data)
    if isinstance(exception, ValueError):
        return (
            "📊 **Invalid data encountered**\n\n"
            "The application received data in an unexpected format.\n\n"
            "**What to do:**\n"
            "- Refresh the page\n"
            "- If this persists, check your recent inputs\n"
            "- Try clearing your browser cache\n\n"
            f"🔧 *Technical detail: {str(exception)[:100]}*",
            ErrorSeverity.WARNING
        )

    # Generic Alpaca API Error
    if isinstance(exception, APIError):
        return (
            "🔌 **API communication error**\n\n"
            "We encountered an issue communicating with Alpaca.\n\n"
            "**What to do:**\n"
            "- Refresh the page\n"
            "- Check the Setup Guide to verify your configuration\n"
            "- Visit [Alpaca status](https://status.alpaca.markets/) for service updates\n\n"
            f"🔧 *Error code: {getattr(exception, 'status_code', 'unknown')}*",
            ErrorSeverity.ERROR
        )

    # Fallback for unknown errors
    error_type = type(exception).__name__
    error_message = str(exception)[:200]  # Limit length

    return (
        "❌ **Something unexpected happened**\n\n"
        "We encountered an error we didn't anticipate.\n\n"
        "**What to do:**\n"
        "1. Refresh the page and try again\n"
        "2. If this keeps happening, check the Setup Guide\n"
        "3. Your portfolio data at Alpaca remains safe\n\n"
        f"🔧 *Error type: {error_type}*\n"
        f"*Details: {error_message}*",
        ErrorSeverity.ERROR
    )


def handle_error_display(message: str, severity: ErrorSeverity, context: str = "") -> None:
    """
    Display error message in Streamlit UI with appropriate styling.

    Args:
        message: User-friendly error message (from translate_exception)
        severity: Error severity level
        context: Optional additional context to display
    """

    if context:
        message = f"**Context:** {context}\n\n{message}"

    if severity == ErrorSeverity.INFO:
        st.info(message, icon="ℹ️")
    elif severity == ErrorSeverity.WARNING:
        st.warning(message, icon="⚠️")
    elif severity == ErrorSeverity.ERROR:
        st.error(message, icon="❌")
    elif severity == ErrorSeverity.CRITICAL:
        st.error(message, icon="🚨")
        # For critical errors, also show in sidebar
        with st.sidebar:
            st.error("**Critical Error** - Check main page", icon="🚨")


def safe_execute(func, context: str = "", fallback=None, show_error: bool = True):
    """
    Execute a function with automatic error handling and user-friendly display.

    Args:
        func: Callable to execute
        context: Description of what's being attempted (e.g., "Loading portfolio data")
        fallback: Value to return if function fails (default: None)
        show_error: Whether to display error in UI (default: True)

    Returns:
        Result of func() if successful, fallback value if error occurs

    Example:
        portfolio = safe_execute(
            lambda: api.get_portfolio(),
            context="Loading portfolio data",
            fallback={}
        )
    """
    try:
        return func()
    except Exception as e:
        if show_error:
            message, severity = translate_exception(e, context=context)
            handle_error_display(message, severity, context=context)
        return fallback
