# Error Handling Specification

**Document:** 01-error-handling-specification.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document defines the user-friendly error handling system for Dalio Lite. Currently, the application exposes raw Python exceptions to users (e.g., "HTTPSConnectionPool(host='api.alpaca.markets', port=443): Max retries exceeded..."), which destroys trust in a financial application. This specification maps all technical exceptions to clear, actionable, user-friendly messages.

**Why this exists:** Error messages are the most visible indicator of software quality. In a financial application handling real money, technical error messages make users think the system is broken or unprofessional. Modern robo-advisors (Betterment, Wealthfront) never show stack traces—they show helpful guidance.

**Scope:** All error handling in `dashboard.py` and `pages/*.py` files (10+ locations identified in audit1).

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────┐
│           Streamlit UI Layer                │
│  (dashboard.py, pages/*.py)                 │
└─────────────────┬───────────────────────────┘
                  │
                  │ try/except blocks
                  ↓
┌─────────────────────────────────────────────┐
│      Error Translation Layer (NEW)          │
│  - translate_exception()                    │
│  - get_user_friendly_message()              │
│  - log_technical_error()                    │
└─────────────────┬───────────────────────────┘
                  │
                  │ technical error logged
                  ↓
┌─────────────────────────────────────────────┐
│         Backend / Logging System            │
│  (dalio_lite.py, logs/)                     │
└─────────────────────────────────────────────┘
```

### Dependencies

**Input:** Python exceptions from:
- Alpaca API calls (alpaca-py library)
- File I/O operations (state files, config files)
- Data processing (pandas, json)
- Streamlit session state operations

**Output:**
- User-friendly messages displayed via `st.error()`, `st.warning()`, `st.info()`
- Technical errors logged to `logs/dalio_lite.log`

### Data Flow

1. **Exception occurs** in UI layer (e.g., Alpaca API timeout)
2. **Exception caught** by try/except block
3. **Error translation layer** maps exception type/message to user-friendly text
4. **User sees** friendly message via Streamlit
5. **Technical details logged** server-side for debugging

---

## Specification

### Error Categories

We define 6 error categories with specific handling:

#### 1. **Connection Errors** (Alpaca API)
- **Technical:** `HTTPError`, `ConnectionError`, `Timeout`, `SSLError`
- **User-friendly pattern:** "🔌 [What failed] — [Why] — [What to do]"

#### 2. **Authentication Errors** (API Keys)
- **Technical:** `401 Unauthorized`, `403 Forbidden`, API key validation failures
- **User-friendly pattern:** "🔐 [Access denied] — [Check credentials] — [Where to fix]"

#### 3. **Rate Limiting Errors**
- **Technical:** `429 Too Many Requests`, Alpaca rate limit responses
- **User-friendly pattern:** "⏱️ [Service busy] — [Wait time] — [Why it happened]"

#### 4. **Data Errors** (File/Config Issues)
- **Technical:** `FileNotFoundError`, `json.JSONDecodeError`, `yaml.YAMLError`, `KeyError`
- **User-friendly pattern:** "📁 [Missing/corrupt data] — [Impact] — [How to fix]"

#### 5. **Business Logic Errors** (Circuit Breakers, Validation)
- **Technical:** Custom exceptions from `dalio_lite.py`
- **User-friendly pattern:** "⚠️ [Protection triggered] — [Reason] — [When it clears]"

#### 6. **Unknown Errors** (Catch-all)
- **Technical:** Any unhandled exception
- **User-friendly pattern:** "❌ [Generic issue] — [Report to support] — [Temporary workaround]"

---

### Error Translation Map

| Location | Current Code | Technical Error | User-Friendly Message | Severity |
|----------|--------------|-----------------|----------------------|----------|
| `dashboard.py:292` | `st.error(f"Connection failed: {str(e)}")` | Alpaca API connection failure | "🔌 **Unable to connect to Alpaca**<br><br>We couldn't reach your brokerage account. This is usually temporary.<br><br>**What to try:**<br>• Wait 1 minute and click 'Connect' again<br>• Check your internet connection<br>• Verify Alpaca.markets is online (status.alpaca.markets)" | Error |
| `dashboard.py:292` | Same | SSL certificate error | "🔐 **Connection security issue**<br><br>There's a problem with secure communication to Alpaca. This often happens with corporate networks or VPNs.<br><br>**What to try:**<br>• Disconnect from VPN and retry<br>• Check with your IT department about SSL inspection<br>• Try from a different network" | Error |
| `dashboard.py:292` | Same | API key authentication failure (401) | "🔐 **Invalid API credentials**<br><br>Your Alpaca API keys aren't working. They may have been regenerated or entered incorrectly.<br><br>**How to fix:**<br>1. Go to [Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)<br>2. Navigate to 'Your API Keys'<br>3. Copy your Paper Trading keys<br>4. Update your `.env` file<br>5. Reconnect" | Error |
| `dashboard.py:508` | `st.error(f"⚠️ Error fetching account data: {str(e)}")` | Alpaca API timeout | "⏱️ **Request timed out**<br><br>Alpaca didn't respond in time. This usually happens during high market activity.<br><br>**What to do:** Wait 30 seconds and refresh the page. Your account is fine—we just couldn't fetch the latest data." | Warning |
| `dashboard.py:508` | Same | Rate limit exceeded (429) | "⏱️ **Too many requests**<br><br>We're checking your portfolio too frequently. Alpaca limits requests to prevent system overload.<br><br>**What to do:** Wait 1 minute before trying again. Consider reducing refresh frequency." | Warning |
| `dashboard.py:589` | `st.error(f"⚠️ Error loading portfolio data: {str(e)}")` | Empty positions | "📊 **No positions found**<br><br>Your portfolio doesn't have any holdings yet.<br><br>**Next step:** Run your first rebalance to establish your All Weather allocation." | Info |
| `dashboard.py:589` | Same | Data parsing error | "📊 **Portfolio data unavailable**<br><br>We received unexpected data from Alpaca. This is usually temporary.<br><br>**What to do:** Refresh the page. If this persists for >5 minutes, contact support." | Warning |
| `dashboard.py:605` | `st.error(f"❌ Check failed: {str(e)}")` | Circuit breaker triggered | "🛑 **Safety check triggered**<br><br>Your portfolio dropped significantly today. Our safety system prevented rebalancing to protect you from panic-selling during volatility.<br><br>**What happens next:** System will check again in 24 hours. You can override with 'Force Rebalance' if you understand the risks." | Warning |
| `dashboard.py:605` | Same | Generic rebalance failure | "❌ **Rebalance check failed**<br><br>We couldn't complete the daily check. Your portfolio is safe—no trades were made.<br><br>**What to do:** Try again in 5 minutes. If problem persists, check Alpaca status." | Error |
| `dashboard.py:617` | `st.error(f"❌ Dry run failed: {str(e)}")` | Dry run simulation error | "🧪 **Simulation failed**<br><br>The test run encountered an issue. No real trades were attempted.<br><br>**What to do:** This is informational only. If you see this repeatedly, there may be a data issue to investigate." | Warning |
| `dashboard.py:627` | `st.error(f"❌ Report failed: {str(e)}")` | Report generation error | "📊 **Report unavailable**<br><br>We couldn't generate the performance report right now.<br><br>**What to do:** This doesn't affect trading. You can view basic metrics on the main dashboard." | Info |
| `dashboard.py:654` | `st.error(f"Error checking status: {str(e)}")` | Status check failure | "⚠️ **Status check unavailable**<br><br>We couldn't verify your current portfolio status.<br><br>**What to do:** Your portfolio is safe. Refresh the page to retry." | Warning |
| `dashboard.py:671` | `st.error(f"❌ Failed: {str(e)}")` | Force rebalance failure | "❌ **Rebalance failed**<br><br>We couldn't complete the rebalancing operation. No trades were executed.<br><br>**Possible reasons:**<br>• Market is closed (trades only during 9:30 AM - 4:00 PM ET)<br>• Insufficient buying power<br>• Alpaca API issue<br><br>Check the activity log below for details." | Error |
| `dashboard.py:689` | `st.error(f"Error reading log: {str(e)}")` | Log file read error | "📜 **Activity log unavailable**<br><br>We couldn't load recent activity. This doesn't affect trading.<br><br>**What to do:** Check the `logs/` folder directly if you need to see log files." | Info |
| `pages/5_📊_Monitoring.py:57` | `st.error(f"Health check failed: {e}")` | Health check system error | "🏥 **Health check unavailable**<br><br>The monitoring system couldn't run health checks. Your portfolio continues to operate normally.<br><br>**What to do:** This is informational. Manual checks (Run Daily Check) still work." | Info |
| `pages/5_📊_Monitoring.py:233` | `st.error(f"Error loading metrics: {e}")` | Metrics file missing/corrupt | "📈 **Metrics unavailable**<br><br>Performance metrics haven't been recorded yet. They'll appear after your first rebalance operation.<br><br>**What to do:** Nothing—metrics will populate automatically." | Info |

---

### Implementation Pattern

Create a new module: `error_handler.py`

```python
"""User-friendly error handling for Dalio Lite UI."""

import logging
from typing import Tuple
from alpaca.common.exceptions import APIError

logger = logging.getLogger(__name__)

class ErrorSeverity:
    """Display severity levels."""
    ERROR = "error"     # st.error() - red, serious issue
    WARNING = "warning" # st.warning() - yellow, caution
    INFO = "info"       # st.info() - blue, informational

def translate_exception(exception: Exception, context: str = "") -> Tuple[str, str]:
    """
    Translate a technical exception to user-friendly message.

    Args:
        exception: The caught exception
        context: Where the error occurred (e.g., "connecting_to_alpaca")

    Returns:
        Tuple of (user_message, severity)
    """
    # Log technical details
    logger.error(f"Exception in {context}: {type(exception).__name__}: {str(exception)}")

    # Check exception type and message for patterns
    error_str = str(exception).lower()

    # Authentication errors
    if isinstance(exception, APIError) and exception.status_code == 401:
        return (
            "🔐 **Invalid API credentials**\n\n"
            "Your Alpaca API keys aren't working. They may have been regenerated or entered incorrectly.\n\n"
            "**How to fix:**\n"
            "1. Go to [Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)\n"
            "2. Navigate to 'Your API Keys'\n"
            "3. Copy your Paper Trading keys\n"
            "4. Update your `.env` file\n"
            "5. Reconnect",
            ErrorSeverity.ERROR
        )

    # Rate limiting
    if isinstance(exception, APIError) and exception.status_code == 429:
        return (
            "⏱️ **Too many requests**\n\n"
            "We're checking your portfolio too frequently. Alpaca limits requests to prevent system overload.\n\n"
            "**What to do:** Wait 1 minute before trying again. Consider reducing refresh frequency.",
            ErrorSeverity.WARNING
        )

    # SSL/Certificate errors
    if "ssl" in error_str or "certificate" in error_str:
        return (
            "🔐 **Connection security issue**\n\n"
            "There's a problem with secure communication to Alpaca. This often happens with corporate networks or VPNs.\n\n"
            "**What to try:**\n"
            "• Disconnect from VPN and retry\n"
            "• Check with your IT department about SSL inspection\n"
            "• Try from a different network",
            ErrorSeverity.ERROR
        )

    # Connection/timeout errors
    if "timeout" in error_str or "timed out" in error_str:
        return (
            "⏱️ **Request timed out**\n\n"
            "Alpaca didn't respond in time. This usually happens during high market activity.\n\n"
            "**What to do:** Wait 30 seconds and refresh the page. Your account is fine—we just couldn't fetch the latest data.",
            ErrorSeverity.WARNING
        )

    if "connection" in error_str or "network" in error_str:
        return (
            "🔌 **Unable to connect to Alpaca**\n\n"
            "We couldn't reach your brokerage account. This is usually temporary.\n\n"
            "**What to try:**\n"
            "• Wait 1 minute and try again\n"
            "• Check your internet connection\n"
            "• Verify Alpaca.markets is online (status.alpaca.markets)",
            ErrorSeverity.ERROR
        )

    # File/data errors
    if isinstance(exception, FileNotFoundError):
        return (
            "📁 **Configuration missing**\n\n"
            "A required file wasn't found. This might be your first time running the system.\n\n"
            "**What to do:** Check that your `.env` file exists with Alpaca API keys.",
            ErrorSeverity.ERROR
        )

    if isinstance(exception, (ValueError, KeyError)) and context == "parsing_portfolio":
        return (
            "📊 **Portfolio data unavailable**\n\n"
            "We received unexpected data from Alpaca. This is usually temporary.\n\n"
            "**What to do:** Refresh the page. If this persists for >5 minutes, contact support.",
            ErrorSeverity.WARNING
        )

    # Market closed
    if "market" in error_str and "closed" in error_str:
        return (
            "🕐 **Market is closed**\n\n"
            "Trades can only be executed during market hours: 9:30 AM - 4:00 PM ET, Monday-Friday.\n\n"
            "**What to do:** Try again when market opens, or use 'Dry Run' to test without executing.",
            ErrorSeverity.INFO
        )

    # Circuit breaker (custom exception from dalio_lite.py)
    if "circuit breaker" in error_str:
        return (
            "🛑 **Safety check triggered**\n\n"
            "Your portfolio dropped significantly today. Our safety system prevented rebalancing to protect you from panic-selling during volatility.\n\n"
            "**What happens next:** System will check again in 24 hours. You can override with 'Force Rebalance' if you understand the risks.",
            ErrorSeverity.WARNING
        )

    # Generic fallback
    return (
        "❌ **Something went wrong**\n\n"
        "We encountered an unexpected issue. Your portfolio is safe—no trades were made.\n\n"
        "**What to do:**\n"
        "• Refresh the page and try again\n"
        "• Check the Activity Log for details\n"
        "• If problem persists, contact support with timestamp: " +
        f"{logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}",
        ErrorSeverity.ERROR
    )

def display_error(exception: Exception, context: str = "", streamlit_container=None):
    """
    Convenience function to translate and display error in Streamlit.

    Args:
        exception: The caught exception
        context: Where the error occurred
        streamlit_container: Streamlit container (st, or specific column/expander)
    """
    import streamlit as st

    container = streamlit_container or st
    message, severity = translate_exception(exception, context)

    if severity == ErrorSeverity.ERROR:
        container.error(message)
    elif severity == ErrorSeverity.WARNING:
        container.warning(message)
    else:
        container.info(message)
```

---

### Usage in UI Files

**Before (dashboard.py:292):**
```python
except Exception as e:
    st.error(f"Connection failed: {str(e)}")
```

**After (dashboard.py:292):**
```python
from error_handler import display_error

except Exception as e:
    display_error(e, context="connecting_to_alpaca")
```

---

## Verification Strategy

### Unit Tests

Create `tests/test_error_handler.py`:

```python
def test_authentication_error():
    """Test 401 error mapping."""
    from alpaca.common.exceptions import APIError
    error = APIError({"message": "unauthorized"}, status_code=401)
    message, severity = translate_exception(error, "test")
    assert "Invalid API credentials" in message
    assert severity == ErrorSeverity.ERROR

def test_rate_limit_error():
    """Test 429 error mapping."""
    error = APIError({"message": "rate limit exceeded"}, status_code=429)
    message, severity = translate_exception(error, "test")
    assert "Too many requests" in message
    assert severity == ErrorSeverity.WARNING

def test_ssl_error():
    """Test SSL certificate error mapping."""
    error = Exception("SSLCertVerificationError")
    message, severity = translate_exception(error, "test")
    assert "Connection security issue" in message
    assert "VPN" in message

def test_generic_fallback():
    """Test unknown error fallback."""
    error = Exception("Something completely unexpected")
    message, severity = translate_exception(error, "test")
    assert "Something went wrong" in message
    assert "portfolio is safe" in message
```

### Integration Tests

1. **Test with real Alpaca API:**
   - Intentionally use invalid API keys → Should show auth error message
   - Make rapid repeated calls → Should show rate limit message
   - Test during market closed hours → Should show market closed message

2. **Test with mock failures:**
   - Mock `alpaca.trading.client.TradingClient` to raise various exceptions
   - Verify correct user messages appear
   - Verify technical details logged to file

### Manual Verification

**Checklist:**
- [ ] Disconnect internet, try to connect → Shows connection error
- [ ] Use invalid API keys → Shows authentication error (not stack trace)
- [ ] Trigger rate limit → Shows rate limit error with wait time
- [ ] Delete `.env` file → Shows config missing error
- [ ] Try rebalance when market closed → Shows market hours message
- [ ] Check logs after each error → Technical details present

---

## Benefits

### Why This Approach

1. **Centralized error handling:** All error translation in one module, easy to maintain
2. **Consistent UX:** All errors follow the same pattern (emoji + problem + solution)
3. **Preserve technical details:** Developers can still debug via logs
4. **Future-proof:** Easy to add new error types as we discover them
5. **Testable:** Unit tests verify correct message mapping

### Alternatives Considered

**Alternative 1: Error messages in UI files**
- ❌ Rejected: Would duplicate error handling logic across 10+ locations
- ❌ Rejected: Hard to maintain consistency

**Alternative 2: Show technical errors but "prettify" them**
- ❌ Rejected: Users don't want to see "HTTPConnectionPool" even if formatted nicely
- ❌ Rejected: Doesn't guide users to solutions

**Alternative 3: Just say "Error occurred, try again"**
- ❌ Rejected: Too vague, doesn't help users understand what went wrong

---

## Expectations

### Success Metrics

**Quantitative:**
- 100% of exceptions caught and translated (no raw stack traces visible)
- Error messages include actionable next steps (100% coverage)
- Technical error logging maintained (verify in logs/)

**Qualitative:**
- User feedback shifts from "tacky error messages" to "clear guidance"
- Support requests decrease (users can self-resolve issues)
- Trust indicators improve (users feel system is professional)

### What Success Looks Like

**Before:** User sees this and panics:
```
❌ Connection failed: HTTPSConnectionPool(host='api.alpaca.markets', port=443):
Max retries exceeded with url: /v2/account (Caused by SSLError(SSLCertVerificationError(1,
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer
certificate (_ssl.c:1129)')))
```

**After:** User sees this and knows what to do:
```
🔐 Connection security issue

There's a problem with secure communication to Alpaca. This often happens with
corporate networks or VPNs.

What to try:
• Disconnect from VPN and retry
• Check with your IT department about SSL inspection
• Try from a different network
```

---

## Risks & Mitigations

### Technical Risks

**Risk 1: New exception types we haven't mapped**
- **Likelihood:** Medium (Alpaca API could return new error codes)
- **Impact:** Medium (users see generic fallback message, not perfect but acceptable)
- **Mitigation:** Generic fallback message is friendly. Monitor logs for unmapped exceptions, add them iteratively.

**Risk 2: Error messages become outdated**
- **Likelihood:** Low (Alpaca API is stable)
- **Impact:** Low (instructions might not match current Alpaca UI)
- **Mitigation:** Include links to Alpaca docs, keep instructions high-level

**Risk 3: Over-helpful messages expose security info**
- **Likelihood:** Low (we're careful in specification)
- **Impact:** High (could help attackers)
- **Mitigation:** Never include actual API keys, account numbers, or sensitive data in error messages. Only show "API key is invalid" not "API key ABC123 is invalid"

### Implementation Risks

**Risk 1: Developers bypass error_handler module**
- **Likelihood:** Medium (quick fixes might use old pattern)
- **Impact:** Medium (inconsistent error UX)
- **Mitigation:** Code review checklist, linter rule to catch raw `st.error(str(e))`

**Risk 2: Translation function becomes bloated**
- **Likelihood:** Medium (could grow to 500+ lines)
- **Impact:** Low (still maintainable, just long)
- **Mitigation:** Split into multiple functions by category if >200 lines

---

## Results Criteria

### Acceptance Criteria (Must-Haves)

- [ ] All 14 error locations identified in audit1 use `error_handler.py`
- [ ] No raw exceptions visible to users in any scenario
- [ ] Every error message includes:
  - [ ] Clear description of what went wrong (no jargon)
  - [ ] Why it happened (context)
  - [ ] What to do next (actionable steps)
  - [ ] Appropriate emoji for visual scanning
- [ ] Technical details logged to `logs/dalio_lite.log` for debugging
- [ ] Unit tests cover all exception types (100% coverage of error_handler.py)
- [ ] Manual testing passes (see verification checklist above)

### Success Metrics

**Deployment Success:**
- Zero raw exceptions visible in production after deployment
- Error logs show technical details are preserved
- User feedback mentions improved error messages

**Long-term Success:**
- <5% of support requests are "I don't understand this error"
- Error message updates based on user feedback (iterative improvement)
- New developers can easily add error types to `error_handler.py`

---

## Domain-Specific Considerations

### Financial Application Context

**Special handling for money-related errors:**
- Always clarify: "Your portfolio is safe" or "No trades were made" in error messages
- For trade failures, explain: "Your money hasn't moved" to reduce anxiety
- For market closed errors, show next open time (market hours are critical context)

**Regulatory considerations:**
- Error messages must not mislead users about trade execution
- Failed trades must be clearly communicated (not hidden)
- Circuit breaker triggers should explain they're a safety feature, not a malfunction

### User Personas

**Target users:** Individual investors with $10K-50K accounts, varying technical expertise

**Error message tone:**
- Calm and reassuring (financial errors cause anxiety)
- Educational (explain why errors happen)
- Action-oriented (users want to know how to fix)
- No blame (don't make users feel they did something wrong)

---

## Cross-References

- **Depends on:** None (standalone)
- **Referenced by:**
  - `05-onboarding-flow.md` uses error patterns for setup failures
  - `06-implementation-guide.md` includes error handler deployment in Phase 1

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial specification |

---

**Status:** ✅ Complete and ready for implementation
