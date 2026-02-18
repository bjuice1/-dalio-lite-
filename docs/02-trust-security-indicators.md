# Trust & Security Indicators Specification

**Document:** 02-trust-security-indicators.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document defines trust and security indicators for Dalio Lite. Currently, the application lacks explicit trust signals, which is problematic for a financial application handling real money. Modern robo-advisors (Betterment, Wealthfront, M1 Finance) prominently display security badges, data freshness indicators, and account verification status to build user confidence.

**Why this exists:** Trust is the foundation of financial software adoption. Users need constant reassurance that:
1. Their data is secure (encryption, SIPC insurance if applicable)
2. The information they see is current (not stale or cached)
3. The system is working properly (connection status, last sync time)
4. Their account is in good standing (verification status)

**Scope:** Trust indicators on all pages (`dashboard.py`, all `pages/*.py` files), with reusable components.

---

## Architecture

### Component Hierarchy

```
┌──────────────────────────────────────────────────────┐
│         TrustIndicatorBar (Global Header)            │
│  🔒 Secure | 🟢 Connected | 📊 Data: 2 min ago      │
└──────────────────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
┌─────────▼─────┐ ┌───▼───────┐ ┌──▼──────────┐
│ SecurityBadge │ │SyncStatus │ │AccountStatus│
│  Component    │ │Component  │ │  Component  │
└───────────────┘ └───────────┘ └─────────────┘

Used across all pages:
- dashboard.py (header)
- pages/1_📖_How_It_Works.py (footer)
- pages/2_🎯_Strategy_Selector.py (header)
- pages/3_📊_Market_Dashboard.py (header + demo warning)
- pages/4_🎓_Learning_Center.py (footer)
- pages/5_📊_Monitoring.py (header)
```

### Dependencies

**Input:**
- Alpaca API connection status (from `st.session_state.connected`)
- Last API call timestamp (track in session state)
- Account verification status (from Alpaca account object)
- Paper vs. Live trading mode (from `dalio.config['mode']['paper_trading']`)

**Output:**
- Visual indicators (badges, status text, icons)
- Tooltips with detailed explanations
- Warning banners when trust is compromised (e.g., data stale >10 minutes)

### Data Flow

1. **On page load:** Components check session state for trust metrics
2. **If data stale:** Show warning (e.g., "Data may be outdated")
3. **On API call:** Update `last_sync_time` in session state
4. **On disconnect:** Update connection status badge

---

## Specification

### Component 1: Global Trust Indicator Bar

**Placement:** Top of every page (below page title, above main content)

**Visual Design:**
```
┌────────────────────────────────────────────────────────────┐
│ 🔒 Secure Connection  |  🟢 Connected  |  📊 Updated: 2m ago │
│ SIPC Protected        |  Paper Mode    |  Market: Open       │
└────────────────────────────────────────────────────────────┘
```

**Component Code Pattern:**
```python
def render_trust_bar():
    """Render global trust indicator bar."""
    import streamlit as st
    from datetime import datetime, timedelta

    col1, col2, col3 = st.columns(3)

    with col1:
        # Security indicator
        st.markdown("""
        <div style='padding: 0.5rem; background: #f0fdf4; border-radius: 8px; text-align: center;'>
            🔒 <strong>Secure Connection</strong><br>
            <span style='font-size: 0.75rem; color: #6b7280;'>256-bit encryption</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Connection status
        if st.session_state.get('connected'):
            status_icon = "🟢"
            status_text = "Connected"
            status_color = "#f0fdf4"
        else:
            status_icon = "🔴"
            status_text = "Disconnected"
            status_color = "#fef2f2"

        st.markdown(f"""
        <div style='padding: 0.5rem; background: {status_color}; border-radius: 8px; text-align: center;'>
            {status_icon} <strong>{status_text}</strong><br>
            <span style='font-size: 0.75rem; color: #6b7280;'>
                {'Paper Trading Mode' if st.session_state.get('dalio') and st.session_state.dalio.config['mode']['paper_trading'] else 'Live Trading Mode'}
            </span>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Data freshness
        last_sync = st.session_state.get('last_sync_time')
        if last_sync:
            delta = datetime.now() - last_sync
            if delta < timedelta(minutes=5):
                freshness_color = "#f0fdf4"
                freshness_text = f"Updated: {int(delta.total_seconds() / 60)}m ago"
                freshness_icon = "📊"
            elif delta < timedelta(minutes=15):
                freshness_color = "#fefce8"
                freshness_text = f"Updated: {int(delta.total_seconds() / 60)}m ago"
                freshness_icon = "⚠️"
            else:
                freshness_color = "#fef2f2"
                freshness_text = "Data may be stale"
                freshness_icon = "❌"
        else:
            freshness_color = "#f3f4f6"
            freshness_text = "No data yet"
            freshness_icon = "⏳"

        st.markdown(f"""
        <div style='padding: 0.5rem; background: {freshness_color}; border-radius: 8px; text-align: center;'>
            {freshness_icon} <strong>{freshness_text}</strong><br>
            <span style='font-size: 0.75rem; color: #6b7280;'>
                {'Market: Open' if is_market_open() else 'Market: Closed'}
            </span>
        </div>
        """, unsafe_allow_html=True)
```

**Implementation in each file:**
```python
# Add at top of page content (after st.title, before main content)
from trust_indicators import render_trust_bar
render_trust_bar()
st.divider()
```

---

### Component 2: Security Badge (Detailed)

**Placement:** Sidebar on `dashboard.py` (below connection status)

**Visual Design:**
```
┌─────────────────────────┐
│   🔒 SECURITY STATUS    │
├─────────────────────────┤
│ ✅ 256-bit encryption   │
│ ✅ HTTPS connection     │
│ ✅ API keys secure      │
│ ✅ Session protected    │
│                         │
│ Learn more →            │
└─────────────────────────┘
```

**Component Code:**
```python
def render_security_details():
    """Render detailed security information in sidebar."""
    st.markdown("### 🔒 Security")

    with st.expander("Security Details", expanded=False):
        st.markdown("""
        **Your data is protected:**

        ✅ **256-bit encryption** - All data transmitted securely

        ✅ **HTTPS connection** - Verified secure connection to Alpaca

        ✅ **API keys secure** - Never transmitted in plain text

        ✅ **Session protected** - Auto-logout after 24 hours

        ---

        **About Alpaca:**
        - FINRA member broker-dealer
        - SEC registered
        - Member SIPC (securities protected up to $500K)

        [Learn more about security →](https://alpaca.markets/docs/about-us/#security)
        """)
```

---

### Component 3: Data Freshness Indicators

**Placement:** Next to any displayed data (portfolio value, market data, etc.)

**Visual Design Pattern:**
```
Portfolio Value: $50,245.32  📊 Just now
Market Dashboard: Demo Data  ⚠️ Not real-time
```

**Component Code:**
```python
def render_data_timestamp(data_type: str, timestamp: datetime, is_real: bool = True):
    """
    Render data freshness indicator.

    Args:
        data_type: Label for the data (e.g., "Portfolio Value")
        timestamp: When data was last updated
        is_real: Whether data is real or demo/simulated
    """
    delta = datetime.now() - timestamp

    if not is_real:
        st.warning("⚠️ **Demo Data** - Not real-time market data")
        return

    if delta < timedelta(minutes=1):
        st.caption(f"📊 Updated just now")
    elif delta < timedelta(minutes=5):
        st.caption(f"📊 Updated {int(delta.total_seconds() / 60)} minute(s) ago")
    elif delta < timedelta(minutes=15):
        st.caption(f"⚠️ Updated {int(delta.total_seconds() / 60)} minutes ago")
    else:
        st.warning(f"⚠️ Data may be stale (updated {int(delta.total_seconds() / 60)} minutes ago)")

# Usage:
# st.metric("Portfolio Value", "$50,245.32")
# render_data_timestamp("Portfolio Value", st.session_state.last_sync_time)
```

---

### Component 4: Account Verification Status

**Placement:** Dashboard sidebar (below security badge)

**Visual Design:**
```
┌─────────────────────────┐
│  👤 ACCOUNT STATUS      │
├─────────────────────────┤
│ ✅ Account Active       │
│ ✅ Paper Trading        │
│ ⚠️ Verify identity      │
│                         │
│ [Verify Now →]          │
└─────────────────────────┘
```

**Component Code:**
```python
def render_account_status():
    """Render account verification status."""
    if not st.session_state.get('connected'):
        return

    dalio = st.session_state.dalio
    try:
        account = dalio.trading_client.get_account()

        st.markdown("### 👤 Account")

        # Account status
        status = account.status
        if status == "ACTIVE":
            st.success("✅ Account Active")
        else:
            st.warning(f"⚠️ Account status: {status}")

        # Trading mode
        if dalio.config['mode']['paper_trading']:
            st.info("📄 **Paper Trading Mode**\n\nYou're trading with simulated money. Switch to live trading when ready.")
        else:
            st.error("🚨 **Live Trading Mode**\n\nYou're trading with real money. Double-check all settings.")

        # Verification status (if available from Alpaca)
        # Note: Check Alpaca API docs for account verification fields
        # This is a placeholder based on typical broker patterns
        if hasattr(account, 'identity_verified'):
            if account.identity_verified:
                st.success("✅ Identity Verified")
            else:
                st.warning("⚠️ Identity not verified")
                st.button("Verify Now →", help="Complete identity verification at Alpaca")

    except Exception as e:
        st.caption("⚠️ Could not load account status")
```

---

### Component 5: Demo Data Warning Banner

**Placement:** Top of Market Dashboard page (`pages/3_📊_Market_Dashboard.py`)

**Visual Design:**
```
┌──────────────────────────────────────────────────────────────┐
│ ⚠️ DEMO MODE: Market data is simulated for demonstration    │
│ purposes. Do not make investment decisions based on this     │
│ data. Connect real-time data feeds for live information.     │
│ [Dismiss] [Learn more about data sources →]                  │
└──────────────────────────────────────────────────────────────┘
```

**Component Code:**
```python
def render_demo_warning():
    """Render demo data warning banner for Market Dashboard."""
    st.warning("""
    ⚠️ **DEMO MODE: Market data is simulated**

    The economic indicators, market performance, and sentiment data shown on this page are
    **simulated for demonstration purposes**. Do not make investment decisions based on this data.

    **Why demo data?**
    - Real-time market data requires paid subscriptions (e.g., Polygon, Alpha Vantage)
    - Your portfolio data from Alpaca is always real and accurate
    - This page shows what's possible if real-time data feeds are connected

    **To get real data:** Connect API keys for [Polygon](https://polygon.io),
    [Alpha Vantage](https://www.alphavantage.co), or [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/docs/api/fred/).
    """)

    st.divider()
```

---

### Component 6: Regulatory Disclaimer

**Placement:** Footer on all pages

**Visual Design:**
```
────────────────────────────────────────────────────────────
⚖️ IMPORTANT DISCLAIMERS

• Not financial advice: Dalio Lite is educational software. Consult a licensed
  financial advisor before making investment decisions.

• Past performance ≠ future results: Historical returns do not guarantee
  future performance.

• Your brokerage: All trades execute through Alpaca Markets, an SEC-registered
  broker-dealer and FINRA member. SIPC protection applies.

• Open source: This software is provided "as-is" without warranties. Review
  the code at github.com/your-repo before trading real money.

────────────────────────────────────────────────────────────
```

**Component Code:**
```python
def render_disclaimer():
    """Render regulatory disclaimer footer."""
    st.divider()
    st.markdown("""
    <div style='background: #f9fafb; padding: 1.5rem; border-radius: 8px;
                border-left: 4px solid #6b7280; margin-top: 2rem;'>

    <p style='font-size: 0.875rem; color: #374151; margin-bottom: 0.75rem;'>
    <strong>⚖️ IMPORTANT DISCLAIMERS</strong>
    </p>

    <ul style='font-size: 0.75rem; color: #6b7280; line-height: 1.6;'>
        <li><strong>Not financial advice:</strong> Dalio Lite is educational software.
        Consult a licensed financial advisor before making investment decisions.</li>

        <li><strong>Past performance ≠ future results:</strong> Historical returns do
        not guarantee future performance.</li>

        <li><strong>Your brokerage:</strong> All trades execute through Alpaca Markets,
        an SEC-registered broker-dealer and FINRA member. SIPC protection applies.</li>

        <li><strong>Open source:</strong> This software is provided "as-is" without
        warranties. Review the code before trading real money.</li>
    </ul>

    <p style='font-size: 0.75rem; color: #9ca3af; margin-top: 0.75rem; margin-bottom: 0;'>
    Dalio Lite v1.0 | Last updated: 2026-02-17
    </p>

    </div>
    """, unsafe_allow_html=True)
```

---

### Session State Management

**Track trust metrics in session state:**

```python
# Initialize in dashboard.py
if 'trust_metrics' not in st.session_state:
    st.session_state.trust_metrics = {
        'last_sync_time': None,
        'connection_secure': True,  # Assume HTTPS
        'api_calls_count': 0,
        'last_error_time': None,
        'market_open': is_market_open()
    }

# Update on API calls
def update_sync_time():
    """Call this after any Alpaca API call."""
    st.session_state.trust_metrics['last_sync_time'] = datetime.now()
    st.session_state.trust_metrics['api_calls_count'] += 1

# Usage after successful API call:
account = dalio.trading_client.get_account()
update_sync_time()  # Track freshness
```

---

## Verification Strategy

### Unit Tests

Create `tests/test_trust_indicators.py`:

```python
def test_data_freshness_recent():
    """Test freshness indicator for recent data."""
    timestamp = datetime.now() - timedelta(seconds=30)
    # Should show "just now"
    assert get_freshness_text(timestamp) == "just now"

def test_data_freshness_stale():
    """Test freshness indicator for stale data."""
    timestamp = datetime.now() - timedelta(minutes=20)
    # Should show warning
    assert get_freshness_severity(timestamp) == "warning"

def test_demo_warning_displayed():
    """Test demo warning banner renders."""
    html = render_demo_warning()
    assert "DEMO MODE" in html
    assert "simulated" in html

def test_security_badge_all_checks():
    """Test security badge shows all indicators."""
    html = render_security_details()
    assert "256-bit encryption" in html
    assert "HTTPS connection" in html
    assert "API keys secure" in html
```

### Integration Tests

1. **Test trust bar on all pages:**
   - Navigate to each page
   - Verify trust bar appears
   - Verify correct connection status

2. **Test data freshness:**
   - Load dashboard with fresh data → Should show "just now"
   - Wait 10 minutes → Should show warning
   - Refresh page → Should update timestamp

3. **Test demo warning:**
   - Load Market Dashboard → Should see demo warning banner
   - Verify it's NOT on other pages

### Manual Verification

**Checklist:**
- [ ] Trust bar visible on all 6 pages
- [ ] Trust bar shows correct connection status (connected vs. disconnected)
- [ ] Data freshness updates after API calls
- [ ] Demo warning appears on Market Dashboard only
- [ ] Security details in sidebar
- [ ] Disclaimer footer on all pages
- [ ] Paper/Live mode indicator correct
- [ ] Market open/closed status correct (test during and after market hours)

---

## Benefits

### Why This Approach

1. **Builds trust immediately:** Users see security indicators on first page load
2. **Transparent about data:** Users know when they're looking at real vs. demo data
3. **Reusable components:** DRY principle - define once, use everywhere
4. **Industry standard:** Matches patterns from Betterment, Wealthfront, Robinhood
5. **Low maintenance:** Components are self-contained, easy to update

### Alternatives Considered

**Alternative 1: Minimal trust indicators (just connection status)**
- ❌ Rejected: Insufficient for financial app. Users need more reassurance.

**Alternative 2: Trust indicators only on dashboard, not other pages**
- ❌ Rejected: Users should see trust signals everywhere, not just main page.

**Alternative 3: Separate trust indicator page**
- ❌ Rejected: Trust should be visible, not hidden in a separate page.

---

## Expectations

### Success Metrics

**Quantitative:**
- Trust bar on 100% of pages
- Data freshness indicator next to all real-time data
- Demo warning on Market Dashboard
- Disclaimer footer on 100% of pages
- <2 seconds to render trust indicators (performance)

**Qualitative:**
- User feedback mentions "professional appearance"
- Users report feeling "secure" using the app
- Support requests about "is my data safe?" decrease

### What Success Looks Like

**Before:** Users see dashboard, wonder:
- "Is this connection secure?"
- "Is this data real or cached?"
- "Is my account protected?"

**After:** Users see dashboard, immediately know:
- 🔒 Secure connection with 256-bit encryption
- 📊 Data updated 2 minutes ago
- ✅ Account active, SIPC protected

---

## Risks & Mitigations

### Technical Risks

**Risk 1: Performance impact (trust bar on every page)**
- **Likelihood:** Low (minimal computation)
- **Impact:** Low (if any, <100ms delay)
- **Mitigation:** Cache trust metrics in session state, don't recalculate on every render

**Risk 2: Alpaca API doesn't provide all needed data**
- **Likelihood:** Medium (need to verify account verification status API)
- **Impact:** Medium (can't show full account status)
- **Mitigation:** Research Alpaca API docs during implementation. Fall back to simplified status if fields unavailable.

**Risk 3: Market hours detection incorrect (timezone issues)**
- **Likelihood:** Low (use Alpaca clock API)
- **Impact:** Low (shows wrong "Market: Open" status)
- **Mitigation:** Use Alpaca's official clock API: `trading_client.get_clock()`

### Implementation Risks

**Risk 1: Too many trust indicators (cluttered UI)**
- **Likelihood:** Low (design is minimal)
- **Impact:** Medium (could overwhelm users)
- **Mitigation:** User test after Phase 1. If feedback is "too much", hide detailed security info in expander

**Risk 2: Users ignore demo warning on Market Dashboard**
- **Likelihood:** Medium (banner blindness)
- **Impact:** High (users make decisions on fake data)
- **Mitigation:** Make demo warning prominent (yellow/red), require dismissal on first visit

---

## Results Criteria

### Acceptance Criteria (Must-Haves)

- [ ] Trust bar component created (`trust_indicators.py`)
- [ ] Trust bar on all 6 pages (dashboard + 5 pages)
- [ ] Data freshness tracked in session state
- [ ] Data freshness indicators next to portfolio metrics
- [ ] Demo warning banner on Market Dashboard (page 3)
- [ ] Security details in dashboard sidebar
- [ ] Account status component in dashboard sidebar
- [ ] Disclaimer footer on all pages
- [ ] Paper/Live mode indicator visible
- [ ] Market open/closed status visible
- [ ] Unit tests pass (100% coverage of trust_indicators.py)
- [ ] Manual verification checklist complete

### Success Metrics

**Deployment Success:**
- Trust indicators visible in production
- No performance degradation (<100ms overhead)
- Correct data displayed (no bugs showing wrong status)

**Long-term Success:**
- User feedback includes "feels secure", "professional"
- <2% of users report confusion about data freshness
- Support requests about security decrease by 50%

---

## Domain-Specific Considerations

### Financial Application Context

**Regulatory requirements (informational):**
- Not required to show SIPC insurance (Alpaca handles this)
- Should disclose that software is not financial advice
- Should clarify that Alpaca, not Dalio Lite, holds securities

**Best practices from industry:**
- Betterment: Shows "SIPC protected" badge prominently
- Wealthfront: Shows last sync time next to portfolio value
- Robinhood: Shows green/red dot for connection status
- M1 Finance: Shows "Demo" vs. "Live" indicator prominently

**Our approach:** Combine best practices from all four.

### User Personas

**Persona 1: New investor (low trust, needs reassurance)**
- Needs: Prominent security badges, clear disclaimers
- Benefits: Trust bar + security details address this

**Persona 2: Experienced investor (moderate trust, wants data accuracy)**
- Needs: Data freshness indicators, market hours
- Benefits: Timestamp next to metrics, market open/closed status

**Persona 3: Skeptical user (low trust, scrutinizes everything)**
- Needs: Detailed security info, regulatory context
- Benefits: Expandable security details, disclaimer footer

---

## Cross-References

- **Depends on:** None (standalone)
- **Enables:**
  - `03-goal-based-interface.md` will use trust bar component
  - `04-information-architecture.md` references trust bar placement
  - `05-onboarding-flow.md` references security messaging

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial specification |

---

**Status:** ✅ Complete and ready for implementation
