# Information Architecture Specification

**Document:** 04-information-architecture.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document defines the redesigned information architecture for Dalio Lite's dashboard. Currently, the dashboard suffers from information overload: 7 sidebar indicators + 4 top metrics + 2 pie charts + allocation table + quick actions + system status + activity log—all given equal visual weight. Modern robo-advisors use progressive disclosure: show hero metrics first, details on request.

**Why this exists:** Cognitive load is the enemy of good decision-making. When users see too much information at once, they either freeze (decision paralysis) or leave. Financial dashboards should answer "What matters most?" at a glance, then allow drilling down for details.

**Scope:** Redesign `dashboard.py` layout and component hierarchy. Does not change functionality, only presentation.

---

## Architecture

### Current vs. New Information Hierarchy

**Current (Flat hierarchy - everything is equal weight):**
```
┌─ SIDEBAR ───────────────────┬─ MAIN AREA ─────────────────────┐
│ • Connection status         │ • 4 top metrics (equal weight)   │
│ • ENV file status           │ • 2 pie charts side by side      │
│ • Mode indicator            │ • Allocation table (detailed)    │
│ • AutoPilot status          │ • Quick actions panel            │
│ • Session stats             │ • System status                  │
│ • Target allocation         │ • Activity log                   │
│ • (7 different things)      │ • (6 different sections)         │
└─────────────────────────────┴──────────────────────────────────┘
```

**New (Hierarchical - progressive disclosure):**
```
┌─ SIDEBAR ───────────────────┬─ MAIN AREA ─────────────────────┐
│ 🔒 Security & Status        │ 🎯 HERO SECTION                  │
│ • Trust bar (from Doc 02)   │   "Your Portfolio" (LARGE)       │
│ • Connection: Connected     │   Goal Progress (from Doc 03)    │
│ • Mode: Paper               │                                  │
│ • [Details ▼]               │ 📊 KEY METRICS (3 only)          │
│                             │   Today's Change | Cash | On Track│
│ 🤖 AutoPilot                │                                  │
│ • Status: Enabled           │ ⚡ QUICK ACTIONS                 │
│ • Next run: Tomorrow        │   [Run Check] [View Details ▼]   │
│ • [Configure ▼]             │                                  │
│                             │ 📋 DETAILS (Collapsed by default)│
│ 🎯 Strategy                 │   ▼ Current Allocation           │
│ • All Weather               │   ▼ Rebalance History            │
│ • 40/30/20/10               │   ▼ Activity Log                 │
│ • [Change ▼]                │   (User expands what they want)  │
└─────────────────────────────┴──────────────────────────────────┘
```

---

## Specification

### Design Principles

1. **Hierarchy over Flatness:** Most important info at top/large, details below/small
2. **Progressive Disclosure:** Show summary by default, details in expanders
3. **Single Focus:** One hero element per page (portfolio value + goal progress)
4. **Action-Oriented:** Primary actions prominent, advanced actions hidden
5. **Scannable:** User should understand page in 3 seconds

---

### Dashboard Layout Specification

#### Section 1: Hero Section (Top, ~30% of viewport)

**Purpose:** Answer "How am I doing?" at a glance

**Content:**
```
┌────────────────────────────────────────────────────────────┐
│                      Your Portfolio                        │
│                       $50,245.32                          │
│                    ▲ +$1,234.56 (2.5%)                    │
│                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━ 67% to goal         │
│  On track to reach $75,000 by 2030                        │
│                                                            │
│  [Set Your Goals →]  (if not set)                         │
└────────────────────────────────────────────────────────────┘
```

**Visual Specifications:**
- **Portfolio Value:**
  - Font size: 48px (3rem)
  - Font weight: 700 (bold)
  - Color: Gradient (#667eea to #764ba2)

- **Today's Change:**
  - Font size: 24px (1.5rem)
  - Color: Green if positive, red if negative
  - Include % and $ amount

- **Goal Progress Bar:**
  - Height: 8px
  - Background: #e2e8f0
  - Progress: Gradient (#667eea to #764ba2)
  - Show percentage as text next to bar

- **Goal Text:**
  - Font size: 16px (1rem)
  - Color: #6b7280
  - If no goal set: Show "Set Your Goals →" button (purple)

**Code Pattern:**
```python
def render_hero_section():
    """Render hero section with portfolio value and goal progress."""
    # Center the hero content
    _, col, _ = st.columns([1, 2, 1])

    with col:
        # Portfolio value (large)
        portfolio_value = get_portfolio_value()
        daily_change = get_daily_change()
        daily_pct = (daily_change / portfolio_value) * 100 if portfolio_value > 0 else 0

        st.markdown(f"""
        <div style='text-align: center; padding: 3rem 0;'>
            <p style='font-size: 1.25rem; color: #6b7280; margin-bottom: 0.5rem;'>
                Your Portfolio
            </p>
            <h1 style='font-size: 3rem; font-weight: 700; margin: 0;
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
                ${portfolio_value:,.2f}
            </h1>
            <p style='font-size: 1.5rem; font-weight: 600; margin-top: 0.5rem;
                     color: {"#10b981" if daily_change >= 0 else "#ef4444"};'>
                {"▲" if daily_change >= 0 else "▼"} ${abs(daily_change):,.2f} ({daily_pct:+.2f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Goal progress (if goal set)
        if has_goal_set():
            render_goal_progress()  # From Doc 03
        else:
            st.info("🎯 **Set your financial goals** to track progress and stay motivated.")
            if st.button("Set Your Goals →", type="primary", use_container_width=True):
                st.switch_page("pages/6_🎯_Goals.py")  # New page from Doc 03
```

---

#### Section 2: Key Metrics (Below hero, ~15% of viewport)

**Purpose:** Show 3 most important metrics (not 4+)

**Content:**
```
┌──────────────────┬──────────────────┬──────────────────┐
│   💵 Cash       │   📊 Allocated   │   ✅ Status      │
│   $5,234        │   95% invested   │   On Target      │
│   Available     │   5% cash        │   Last check: 1h │
└──────────────────┴──────────────────┴──────────────────┘
```

**Why only 3 metrics?**
- Research shows humans process 3-4 chunks optimally
- Reduces cognitive load vs. current 4 metrics
- Chosen metrics answer: "Can I trade?" + "Am I invested?" + "Is system working?"

**Visual Specifications:**
- Use Streamlit's native `st.metric()` - clean, professional
- Equal width columns (1:1:1 ratio)
- Small icons (emoji) for quick visual scanning
- Help tooltips on each metric

**Code Pattern:**
```python
def render_key_metrics():
    """Render 3 key metrics below hero section."""
    col1, col2, col3 = st.columns(3)

    with col1:
        cash = get_available_cash()
        st.metric(
            label="💵 Cash Available",
            value=f"${cash:,.0f}",
            help="Available cash for trading"
        )

    with col2:
        invested_pct = get_invested_percentage()
        cash_pct = 100 - invested_pct
        st.metric(
            label="📊 Invested",
            value=f"{invested_pct:.0f}%",
            delta=f"{cash_pct:.0f}% cash",
            help="Percentage of portfolio invested in securities"
        )

    with col3:
        status, last_check = get_system_status()
        st.metric(
            label="✅ System Status",
            value=status,  # "On Target" or "Rebalance Needed"
            delta=f"Checked {last_check}",
            help="Current portfolio status and last check time"
        )

    st.divider()
```

---

#### Section 3: Primary Action (Below metrics, ~10% of viewport)

**Purpose:** Make primary action (Run Daily Check) prominent, hide advanced actions

**Content:**
```
┌────────────────────────────────────────────────────────────┐
│                 [🔄 RUN DAILY CHECK]                       │
│                                                            │
│         ⚙️ Advanced Actions ▼  (Collapsed)                │
└────────────────────────────────────────────────────────────┘
```

**When expanded:**
```
┌────────────────────────────────────────────────────────────┐
│                 [🔄 RUN DAILY CHECK]                       │
│                                                            │
│         ⚙️ Advanced Actions ▲  (Expanded)                 │
│         ├─ [🧪 Dry Run]                                    │
│         ├─ [📊 Generate Report]                            │
│         └─ [⚡ Force Rebalance]  (Danger)                  │
└────────────────────────────────────────────────────────────┘
```

**Code Pattern:**
```python
def render_primary_action():
    """Render primary action button and advanced actions."""
    # Primary action (always visible, prominent)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if st.button("🔄 RUN DAILY CHECK", type="primary", use_container_width=True):
            run_daily_check()

    st.markdown("<br>", unsafe_allow_html=True)

    # Advanced actions (collapsed by default)
    with st.expander("⚙️ Advanced Actions", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🧪 Dry Run", use_container_width=True):
                run_dry_run()

            if st.button("📊 Generate Report", use_container_width=True):
                generate_report()

        with col2:
            if st.button("⚡ Force Rebalance", use_container_width=True):
                st.warning("⚠️ This bypasses safety checks. Use with caution.")
                if st.button("Confirm Force Rebalance", type="primary"):
                    force_rebalance()

    st.divider()
```

---

#### Section 4: Details (Bottom, ~45% of viewport - ALL COLLAPSED BY DEFAULT)

**Purpose:** Provide detailed information for users who want to drill down

**Content:**
```
┌────────────────────────────────────────────────────────────┐
│  📊 Current Allocation ▼  (Collapsed)                      │
│                                                            │
│  🎯 Target vs. Actual ▼  (Collapsed)                      │
│                                                            │
│  📈 Performance ▼  (Collapsed)                             │
│                                                            │
│  🔄 Rebalance History ▼  (Collapsed)                      │
│                                                            │
│  📜 Activity Log ▼  (Collapsed)                            │
└────────────────────────────────────────────────────────────┘
```

**When user expands "Current Allocation":**
```
┌────────────────────────────────────────────────────────────┐
│  📊 Current Allocation ▲  (Expanded)                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Pie Chart        │   Allocation Table              │ │
│  │  (Interactive)    │   Ticker | %  | $  | Drift     │ │
│  │                   │   VTI    | 42 | $X | +2% 🟢    │ │
│  │                   │   TLT    | 28 | $X | -2% 🟢    │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Code Pattern:**
```python
def render_details_section():
    """Render details section with collapsible expanders."""

    # Current Allocation
    with st.expander("📊 Current Allocation", expanded=False):
        col1, col2 = st.columns([1, 2])

        with col1:
            # Pie chart (keep one, not two)
            render_allocation_pie_chart()

        with col2:
            # Allocation table (more useful than chart)
            render_allocation_table()

    # Target vs. Actual Comparison
    with st.expander("🎯 Target vs. Actual", expanded=False):
        render_drift_analysis()

    # Performance (remove separate report button, integrate here)
    with st.expander("📈 Performance", expanded=False):
        render_performance_summary()

    # Rebalance History
    with st.expander("🔄 Rebalance History", expanded=False):
        render_rebalance_history()

    # Activity Log
    with st.expander("📜 Activity Log", expanded=False):
        render_activity_log()
```

---

### Sidebar Redesign

**Current Problem:** 7 different status indicators competing for attention

**New Approach:** Group related information, use expanders

```
┌─ SIDEBAR ──────────────────────┐
│ 🔒 SECURITY & CONNECTION       │
│ • Trust bar (from Doc 02)      │
│ • Connected | Paper Mode       │
│ • [Details ▼]                  │
│                                │
│ 🤖 AUTO-PILOT                  │
│ • Status: ● Enabled            │
│ • Next run: Tomorrow 9 AM      │
│ • [Configure ▼]                │
│                                │
│ 🎯 STRATEGY                    │
│ • All Weather Portfolio        │
│ • 40% VTI | 30% TLT           │
│ • 20% GLD | 10% DBC           │
│ • [Change Strategy →]          │
│                                │
│ 📚 LEARN & HELP                │
│ • [How It Works]               │
│ • [Investment Guide]           │
│ • [FAQ]                        │
└────────────────────────────────┘
```

**Code Pattern:**
```python
def render_sidebar():
    """Render redesigned sidebar with grouped information."""
    with st.sidebar:
        st.markdown("## ⚙️ Dashboard")
        st.divider()

        # Security & Connection (always visible summary)
        st.markdown("### 🔒 Security & Status")
        render_trust_bar()  # From Doc 02

        connection_status = "🟢 Connected" if st.session_state.connected else "🔴 Disconnected"
        mode = "📄 Paper Mode" if is_paper_mode() else "🚨 Live Mode"

        st.markdown(f"{connection_status} | {mode}")

        with st.expander("Connection Details", expanded=False):
            render_security_details()  # From Doc 02
            render_account_status()    # From Doc 02

        st.divider()

        # AutoPilot Status
        st.markdown("### 🤖 Auto-Pilot")
        autopilot_enabled = get_autopilot_status()

        if autopilot_enabled:
            st.success("● **Enabled**")
            next_run = get_next_autopilot_run()
            st.caption(f"Next run: {next_run}")
        else:
            st.warning("○ **Disabled**")
            st.caption("Enable for hands-free management")

        with st.expander("Configure Auto-Pilot", expanded=False):
            st.info("Auto-Pilot runs daily checks and rebalances when needed.")
            st.button("Enable Auto-Pilot →")

        st.divider()

        # Strategy Summary
        st.markdown("### 🎯 Strategy")
        strategy = get_current_strategy()
        st.info(f"**{strategy['name']}**")

        allocation = strategy['allocation']
        for ticker, pct in allocation.items():
            st.caption(f"• {ticker}: {pct:.0%}")

        st.button("Change Strategy →", help="Visit Strategy Selector page")

        st.divider()

        # Learn & Help
        st.markdown("### 📚 Learn & Help")
        st.page_link("pages/1_📖_How_It_Works.py", label="How It Works")
        st.page_link("pages/4_🎓_Learning_Center.py", label="Investment Guide")
        st.button("FAQ", help="Frequently asked questions")
```

---

### Non-Connected State (Onboarding)

**Current:** Shows 3-step cards with vague instructions

**New:** Progressive onboarding with clear CTAs (see Doc 05 for full flow)

**Key change:** Move detailed instructions to Doc 05, keep dashboard clean

```
┌────────────────────────────────────────────────────────────┐
│                    Welcome to Dalio Lite!                  │
│               Automated All Weather Portfolio              │
│                                                            │
│  Get started in 3 minutes:                                 │
│                                                            │
│  ✅ 1. Create Alpaca Account  [Go to Alpaca →]            │
│  ⏳ 2. Connect Your Account   [Connect →]                 │
│  ⬜ 3. Run First Check        (Available after connecting)│
│                                                            │
│  [View Setup Guide →]  (Links to Doc 05 onboarding)       │
└────────────────────────────────────────────────────────────┘
```

**Code Pattern:**
```python
def render_onboarding():
    """Render onboarding flow for non-connected users."""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1>Welcome to Dalio Lite!</h1>
            <p style='font-size: 1.25rem; color: #6b7280;'>
                Automated All Weather Portfolio Management
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Get started in 3 minutes:")

        # Step 1: Create Alpaca Account
        if not has_alpaca_account():
            st.info("✅ **Step 1:** Create Alpaca Account")
            st.markdown("""
            Dalio Lite connects to Alpaca Markets (your brokerage) to execute trades.

            **What you'll need:**
            • Email address
            • Social Security Number (for identity verification)
            • Bank account (to fund your account)

            **Note:** Start with Paper Trading (simulated money) to test the system.
            """)
            st.link_button("Go to Alpaca →", "https://app.alpaca.markets/signup", type="primary")
        else:
            st.success("✅ **Step 1:** Alpaca account created")

        # Step 2: Connect
        if not st.session_state.connected:
            st.warning("⏳ **Step 2:** Connect Your Account")
            st.markdown("""
            Once you have Alpaca API keys (from Alpaca dashboard), connect here.

            **Need help?** [View Setup Guide →](link-to-onboarding-page)
            """)
            if st.button("Connect Now →", type="primary", use_container_width=True):
                st.switch_page("pages/7_Setup.py")  # From Doc 05
        else:
            st.success("✅ **Step 2:** Account connected")

        # Step 3: Run First Check
        if not st.session_state.connected:
            st.caption("⬜ **Step 3:** Run First Check (Available after connecting)")
        else:
            st.info("⚡ **Step 3:** Run your first daily check!")
            if st.button("Run Daily Check →", type="primary", use_container_width=True):
                run_first_check()
```

---

## Verification Strategy

### A/B Testing (If Possible)

**Ideal scenario:** Show old layout to 50% of users, new layout to 50%

**Metrics to track:**
- Time to first action (lower is better)
- Bounce rate (lower is better)
- Feature discovery (% of users who expand details)
- User satisfaction survey (post-usage)

### Qualitative Testing

**Test with 5 users (different experience levels):**

1. **Task 1:** "Look at the dashboard and tell me what you see" (test scanability)
   - Success: User can summarize portfolio status in <10 seconds

2. **Task 2:** "How would you run a portfolio check?" (test action discovery)
   - Success: User clicks "Run Daily Check" without confusion

3. **Task 3:** "Find your current allocation breakdown" (test progressive disclosure)
   - Success: User expands "Current Allocation" expander

4. **Task 4:** "How do you feel about the amount of information shown?" (test cognitive load)
   - Success: User says "manageable" or "clear", not "overwhelming"

### Manual Verification

**Checklist:**
- [ ] Hero section shows portfolio value prominently
- [ ] Goal progress bar appears (when goal set)
- [ ] Only 3 key metrics shown (not 4+)
- [ ] Primary action (Run Daily Check) is prominent
- [ ] Advanced actions hidden in expander
- [ ] All details collapsed by default
- [ ] User can expand any detail section
- [ ] Sidebar shows grouped information (not flat list)
- [ ] Onboarding flow clear for non-connected state
- [ ] Trust bar integrated at top (from Doc 02)
- [ ] Page loads in <2 seconds (performance)

---

## Benefits

### Why This Approach

1. **Reduces cognitive load:** From 13 competing elements to 1 hero + 3 metrics + 1 action
2. **Guides attention:** Visual hierarchy directs eyes to most important info first
3. **Empowers exploration:** Advanced users can still access all details via expanders
4. **Mobile-friendly:** Vertical layout works better on small screens
5. **Industry standard:** Matches patterns from Betterment, Wealthfront (tested UX)

### Alternatives Considered

**Alternative 1: Tabs for organization (Overview | Details | History | Settings)**
- ❌ Rejected: Hides information, requires navigation to see anything
- ❌ Rejected: Users don't know which tab to check

**Alternative 2: Dashboard builder (user customizes what to show)**
- ❌ Rejected: Too complex for target users ($10K-50K accounts)
- ❌ Rejected: Requires decisions before users understand the system

**Alternative 3: Minimal dashboard (just portfolio value, everything else hidden)**
- ❌ Rejected: Too minimal - users need some context beyond just value
- ❌ Rejected: Doesn't show "am I on track?" at a glance

---

## Expectations

### Success Metrics

**Quantitative:**
- User can identify portfolio status in <5 seconds (eye tracking or task timing)
- 80%+ users find primary action without help
- <10% users report "too much information" in survey
- Page load time <2 seconds (performance maintained)

**Qualitative:**
- User feedback includes "clear", "organized", "easy to understand"
- Support requests asking "where is X?" decrease by 50%
- Users naturally discover detail sections (expand expanders)

### What Success Looks Like

**Before:** User opens dashboard, sees:
- 4 metrics + 2 charts + table + actions + status + log
- Scans for 20+ seconds trying to understand
- Feels overwhelmed, closes app

**After:** User opens dashboard, sees:
- Portfolio value (large) + goal progress
- 3 key metrics (small)
- "Run Daily Check" button
- Understands status in 5 seconds
- Knows what to do next

---

## Risks & Mitigations

### Technical Risks

**Risk 1: Expanders slow page load**
- **Likelihood:** Low (Streamlit handles this efficiently)
- **Impact:** Low (<500ms if any)
- **Mitigation:** Use Streamlit's native expanders, don't load data until expanded

**Risk 2: Goal progress requires state not yet implemented**
- **Likelihood:** High (Doc 03 defines this)
- **Impact:** Medium (can't show progress bar)
- **Mitigation:** Show placeholder until Doc 03 implemented: "Set your goals to track progress"

### UX Risks

**Risk 1: Users don't discover detail sections (everything collapsed)**
- **Likelihood:** Medium (users might not know to expand)
- **Impact:** Medium (users think information is missing)
- **Mitigation:** Add hint on first load: "💡 Tip: Expand sections below for detailed information"

**Risk 2: Power users frustrated by collapsed details**
- **Likelihood:** Low (advanced users understand expanders)
- **Impact:** Low (can still access everything)
- **Mitigation:** Save user preferences (if they expand, keep expanded in session)

**Risk 3: Hero section too large on small screens**
- **Likelihood:** Medium (mobile users)
- **Impact:** Medium (pushes content below fold)
- **Mitigation:** Responsive CSS - reduce hero size on mobile (<768px width)

### Implementation Risks

**Risk 1: Refactoring breaks existing functionality**
- **Likelihood:** Medium (lots of code movement)
- **Impact:** High (dashboard stops working)
- **Mitigation:** Test thoroughly, keep backup of old dashboard.py, phased rollout

---

## Results Criteria

### Acceptance Criteria (Must-Haves)

**Dashboard Page:**
- [ ] Hero section with portfolio value (large, prominent)
- [ ] Goal progress bar (when goal set) - placeholder until Doc 03
- [ ] 3 key metrics (not 4+)
- [ ] Primary action button (Run Daily Check) prominent
- [ ] Advanced actions in expander (collapsed by default)
- [ ] 5 detail sections in expanders (all collapsed by default):
  - [ ] Current Allocation
  - [ ] Target vs. Actual
  - [ ] Performance
  - [ ] Rebalance History
  - [ ] Activity Log
- [ ] Trust bar at top (from Doc 02)

**Sidebar:**
- [ ] Grouped information (not flat list)
- [ ] Security & Status section with expander
- [ ] AutoPilot section with expander
- [ ] Strategy summary with action button
- [ ] Learn & Help links

**Onboarding (non-connected state):**
- [ ] 3-step progress indicator
- [ ] Clear CTAs for each step
- [ ] Link to detailed setup guide (Doc 05)

**Performance:**
- [ ] Page loads in <2 seconds
- [ ] Expanders open instantly (<100ms)
- [ ] No janky animations or delays

### Success Metrics

**Deployment Success:**
- New layout visible in production
- No functionality broken (all actions still work)
- User feedback collected via in-app survey

**Long-term Success:**
- User task completion time decreases by 30%
- "Dashboard is confusing" support tickets decrease by 50%
- Users naturally discover detail sections (analytics on expander usage)

---

## Domain-Specific Considerations

### Financial Dashboard Best Practices

**From industry leaders:**
- **Betterment:** Hero section shows "Your Balance" + goal progress
- **Wealthfront:** Single large number + today's change + path forecast
- **M1 Finance:** Portfolio pie chart (visual) + key metrics below
- **Robinhood:** Portfolio graph (visual) + buying power + watchlist

**Our approach:** Combine Betterment's goal focus + Wealthfront's clarity + M1's detail expanders

### Mobile Considerations

**Responsive breakpoints:**
- Desktop (>1024px): Full layout as specified
- Tablet (768-1024px): Reduce hero size, stack metrics vertically if needed
- Mobile (<768px): Single column layout, hero reduced to 32px font, hide sidebar by default

**Code pattern:**
```css
@media (max-width: 768px) {
    h1 { font-size: 2rem !important; }  /* Reduce from 3rem */
    .hero-section { padding: 1rem 0 !important; }  /* Reduce padding */
}
```

---

## Cross-References

- **Depends on:**
  - `02-trust-security-indicators.md` (trust bar component)
- **Enables:**
  - `03-goal-based-interface.md` (needs to know where goal progress appears - hero section)
  - `05-onboarding-flow.md` (references non-connected state design)
- **Referenced by:**
  - `06-implementation-guide.md` (Phase 2 implementation)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial specification |

---

**Status:** ✅ Complete and ready for implementation
