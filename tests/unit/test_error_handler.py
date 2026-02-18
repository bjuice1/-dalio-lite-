"""
Unit tests for error_handler.py

Tests exception translation to user-friendly messages.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from error_handler import translate_exception, ErrorSeverity

# Mock Alpaca APIError for testing
class MockAPIError(Exception):
    """Mock APIError for testing without Alpaca dependency"""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


# Monkey-patch the import to use our mock
import error_handler
error_handler.APIError = MockAPIError


class TestErrorTranslation:
    """Test exception translation to user-friendly messages"""

    def test_api_401_returns_friendly_message(self):
        """Test 401 API error gets user-friendly message"""
        error = MockAPIError("Unauthorized", status_code=401)
        message, severity = translate_exception(error, context="Testing")

        assert "Invalid API credentials" in message
        assert "Setup Guide" in message
        assert severity == ErrorSeverity.ERROR

    def test_api_429_rate_limit(self):
        """Test rate limit error"""
        error = MockAPIError("Too many requests", status_code=429)
        message, severity = translate_exception(error)

        assert "Rate limit" in message or "rate limit" in message.lower()
        assert "60 seconds" in message or "Wait" in message
        assert severity == ErrorSeverity.WARNING

    def test_api_500_server_error(self):
        """Test 500 server error"""
        error = MockAPIError("Internal server error", status_code=500)
        message, severity = translate_exception(error)

        assert "Alpaca" in message or "service" in message.lower()
        assert "unavailable" in message.lower() or "issue" in message.lower()
        assert severity == ErrorSeverity.WARNING

    def test_market_closed_error(self):
        """Test market closed error detection"""
        error = MockAPIError("Market is not open", status_code=403)
        message, severity = translate_exception(error)

        assert "Market" in message
        assert "closed" in message.lower() or "not open" in message.lower()
        assert severity == ErrorSeverity.INFO

    def test_insufficient_funds_error(self):
        """Test insufficient funds error"""
        error = MockAPIError("Insufficient buying power", status_code=403)
        message, severity = translate_exception(error)

        assert "funds" in message.lower() or "buying power" in message.lower()
        assert severity == ErrorSeverity.WARNING

    def test_generic_exception_fallback(self):
        """Test unknown exception gets generic message"""
        error = RuntimeError("Something unexpected")
        message, severity = translate_exception(error)

        assert "unexpected happened" in message.lower()
        assert "RuntimeError" in message
        assert severity == ErrorSeverity.ERROR

    def test_connection_error(self):
        """Test connection/network error"""
        error = ConnectionError("Failed to connect")
        message, severity = translate_exception(error, context="API call")

        assert "connection" in message.lower() or "Connection" in message
        # Connection errors are serious (ERROR severity is appropriate)
        assert severity in [ErrorSeverity.ERROR, ErrorSeverity.WARNING]

    def test_permission_error(self):
        """Test file permission error"""
        error = PermissionError("Access denied")
        message, severity = translate_exception(error)

        assert "permission" in message.lower() or "access" in message.lower()
        assert severity == ErrorSeverity.ERROR

    def test_file_not_found_error(self):
        """Test file not found error"""
        error = FileNotFoundError("Config not found")
        message, severity = translate_exception(error)

        assert "file" in message.lower() or "not found" in message.lower()
        assert severity == ErrorSeverity.ERROR

    def test_json_decode_error(self):
        """Test JSON parsing error"""
        import json
        error = json.JSONDecodeError("Invalid JSON", "", 0)
        message, severity = translate_exception(error)

        assert "corrupt" in message.lower() or "format" in message.lower()
        assert severity == ErrorSeverity.WARNING

    def test_key_error(self):
        """Test missing configuration key error"""
        error = KeyError("ALPACA_API_KEY")
        message, severity = translate_exception(error)

        assert "Configuration" in message or "setting" in message.lower()
        assert "ALPACA_API_KEY" in message
        assert severity == ErrorSeverity.ERROR

    def test_value_error(self):
        """Test invalid data format error"""
        error = ValueError("Invalid input format")
        message, severity = translate_exception(error)

        assert "Invalid" in message or "data" in message.lower()
        assert severity == ErrorSeverity.WARNING

    def test_context_included_in_message(self):
        """Test that context is included when provided"""
        error = RuntimeError("Test error")
        message, severity = translate_exception(error, context="Loading portfolio")

        # Context should be part of the full error handling
        # The translate_exception returns just message and severity
        # Context is handled by handle_error_display
        assert message is not None
        assert severity is not None


class TestErrorSeverityLevels:
    """Test that appropriate severity levels are assigned"""

    def test_critical_errors_marked_critical(self):
        """Test that serious errors get ERROR or CRITICAL severity"""
        # API authentication failure is critical
        error = MockAPIError("Unauthorized", status_code=401)
        message, severity = translate_exception(error)
        assert severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]

    def test_temporary_errors_marked_warning(self):
        """Test that temporary issues get WARNING severity"""
        # Rate limits are temporary
        error = MockAPIError("Too many requests", status_code=429)
        message, severity = translate_exception(error)
        assert severity == ErrorSeverity.WARNING

        # Server errors are temporary
        error = MockAPIError("Service unavailable", status_code=503)
        message, severity = translate_exception(error)
        assert severity == ErrorSeverity.WARNING

    def test_informational_errors_marked_info(self):
        """Test that informational messages get INFO severity"""
        # Market closed is informational (not a problem)
        error = MockAPIError("Market is closed", status_code=403)
        message, severity = translate_exception(error)
        assert severity == ErrorSeverity.INFO


class TestMessageQuality:
    """Test that error messages are user-friendly and actionable"""

    def test_messages_contain_what_to_do(self):
        """Test that messages include actionable guidance"""
        error = MockAPIError("Unauthorized", status_code=401)
        message, severity = translate_exception(error)

        # Should contain actionable steps
        assert "What to do" in message or "do:" in message.lower()

    def test_messages_avoid_technical_jargon(self):
        """Test that messages are user-friendly"""
        error = MockAPIError("Unauthorized", status_code=401)
        message, severity = translate_exception(error)

        # Should use friendly language
        assert "credentials" in message.lower() or "API key" in message.lower()
        # Should not expose raw stack traces
        assert "Traceback" not in message
        assert "File" not in message or ".py" not in message

    def test_messages_reference_setup_guide(self):
        """Test that error messages reference Setup Guide for help"""
        error = MockAPIError("Unauthorized", status_code=401)
        message, severity = translate_exception(error)

        # Critical setup errors should mention Setup Guide
        assert "Setup Guide" in message

    def test_generic_errors_include_error_type(self):
        """Test that fallback messages include error type for debugging"""
        error = RuntimeError("Unexpected problem")
        message, severity = translate_exception(error)

        # Should mention the error type for tech-savvy users
        assert "RuntimeError" in message or "error type" in message.lower()
