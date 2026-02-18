# Goal-Based Interface Specification

**Document:** 03-goal-based-interface.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document defines the goal-setting and goal-tracking interface for Dalio Lite. Currently, the dashboard shows raw metrics (portfolio value, cash, equity) without context about whether users are "on track" to meet their financial goals. Modern robo-advisors (Betterment, Wealthfront) frame everything around goals: "You're projected to have $847K at age 65 (Above your $750K goal)."

**Why this exists:** Financial metrics without context are meaningless. "$50,000 in your portfolio" could be great or terrible depending on your goals, age, and timeline. Goal-based framing provides emotional connection and motivation—users aren't just watching numbers change, they're tracking progress toward life milestones (retirement, house down payment, financial independence).

**Scope:** New goal-setting page + goal progress display on dashboard hero section (integrated per Doc 04).

---

## Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────┐
│                 User Interface Layer                     │
│  • Goal Setting Page (new page)                         │
│  • Goal Progress Display (dashboard hero section)       │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ read/write goals
                     ↓
┌──────────────────────────────────────────────────────────┐
│              Goal State Management                       │
│  • state/goals.json (file-based, like other state)     │
│  • Goal schema: target, current, timeline, etc.         │
└────────────────────┬─────────────────────────────────────┘
                     │
                     │ project future value
                     ↓
┌──────────────────────────────────────────────────────────┐
│            Projection Engine (NEW)                       │
│  • Calculate: "At current rate, reach goal by X"        │
│  • Use portfolio value + growth rate + timeline         │
│  • Simple compound interest formula                      │
└──────────────────────────────────────────────────────────┘
```

### Dependencies

**Input:**
- Current portfolio value (from Alpaca API)
- Historical growth rate (calculated from rebalance history)
- User-defined goal (target amount, target year, goal type)

**Output:**
- Goal progress percentage (0-100%)
- Projected completion date
- "On track" vs. "Behind" vs. "Ahead" status
- Visual progress bar

### Data Flow

1. **User sets goal** on Goal Setting page → Saved to `state/goals.json`
2. **Dashboard loads** → Reads `state/goals.json` + current portfolio value
3. **Projection engine** → Calculates: "At X% growth rate, will reach $Y by date Z"
4. **Hero section** → Displays progress bar + "On track" message
5. **Daily updates** → Recalculate projection on each portfolio update

---

## Specification

### Goal Data Schema

**File:** `state/goals.json`

```json
{
  "version": "1.0",
  "primary_goal": {
    "goal_type": "retirement",
    "target_amount": 1000000,
    "target_year": 2050,
    "current_amount": 50000,
    "created_at": "2026-02-17T10:00:00Z",
    "last_updated": "2026-02-17T14:30:00Z",
    "risk_tolerance": "moderate",
    "notes": "Retire at 65 with comfortable lifestyle"
  },
  "projections": {
    "expected_final_amount": 1050000,
    "expected_completion_year": 2049,
    "on_track": true,
    "required_monthly_contribution": 0,
    "assumed_annual_return": 0.085,
    "confidence_level": "medium"
  },
  "history": [
    {
      "date": "2026-02-17",
      "portfolio_value": 50000,
      "progress_pct": 5.0,
      "on_track": true
    }
  ]
}
```

**Schema Validation:**
- `goal_type`: One of ["retirement", "house", "education", "wealth", "other"]
- `target_amount`: Positive number, >1000
- `target_year`: Future year, >current_year, <current_year+50
- `risk_tolerance`: One of ["conservative", "moderate", "aggressive"]

---

### Component 1: Goal Setting Page (NEW PAGE)

**File:** `pages/6_🎯_Goals.py`

**Page Structure:**
```
┌────────────────────────────────────────────────────────────┐
│                   🎯 Set Your Financial Goal              │
│                                                            │
│   Tell us what you're saving for, and we'll track your    │
│   progress and provide personalized guidance.              │
└────────────────────────────────────────────────────────────┘

┌─ STEP 1: WHAT'S YOUR GOAL? ───────────────────────────────┐
│ ○ Retirement                                               │
│ ○ House Down Payment                                       │
│ ○ Education (College/Children)                             │
│ ○ Build Wealth                                             │
│ ○ Other                                                    │
└────────────────────────────────────────────────────────────┘

┌─ STEP 2: HOW MUCH DO YOU NEED? ───────────────────────────┐
│ Target Amount: [$_________] (e.g., $1,000,000)            │
│ Current Portfolio: $50,245  (Auto-filled)                 │
│                                                            │
│ You need to grow by: $949,755                              │
└────────────────────────────────────────────────────────────┘

┌─ STEP 3: WHEN DO YOU NEED IT? ────────────────────────────┐
│ Target Year: [____] (e.g., 2050)                          │
│ Time Horizon: 24 years from now                           │
│                                                            │
│ Recommended: At least 5 years for market volatility       │
└────────────────────────────────────────────────────────────┘

┌─ STEP 4: PROJECTION ───────────────────────────────────────┐
│ 📊 Based on your All Weather strategy (8.5% annual        │
│    return), you're projected to reach:                     │
│                                                            │
│    $1,050,000 by 2049  ✅ On Track!                        │
│                                                            │
│ Need to adjust? You can:                                   │
│ • Increase monthly contributions                           │
│ • Extend your timeline                                     │
│ • Switch to a more aggressive strategy                     │
└────────────────────────────────────────────────────────────┘

                   [💾 Save Goal & Return to Dashboard]
```

**Code Implementation:**

```python
"""Goal Setting Page - Set and track your financial goals."""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Set Your Goals", page_icon="🎯", layout="wide")

# Initialize
if 'goal_draft' not in st.session_state:
    st.session_state.goal_draft = {}

# Header
st.title("🎯 Set Your Financial Goal")
st.markdown("""
Tell us what you're saving for, and we'll track your progress and provide
personalized guidance. You can always update your goal later.
""")
st.divider()

# STEP 1: Goal Type
st.markdown("## Step 1: What's Your Goal?")

goal_types = {
    "retirement": {
        "label": "🏖️ Retirement",
        "description": "Build a nest egg to retire comfortably",
        "typical_amount": "$500K - $2M",
        "typical_timeline": "20-40 years"
    },
    "house": {
        "label": "🏠 House Down Payment",
        "description": "Save for a down payment on a home",
        "typical_amount": "$50K - $200K",
        "typical_timeline": "3-10 years"
    },
    "education": {
        "label": "🎓 Education Fund",
        "description": "Save for college or children's education",
        "typical_amount": "$50K - $300K",
        "typical_timeline": "5-18 years"
    },
    "wealth": {
        "label": "💰 Build Wealth",
        "description": "Grow your wealth for financial independence",
        "typical_amount": "$500K - $5M",
        "typical_timeline": "10-30 years"
    },
    "other": {
        "label": "🎯 Other Goal",
        "description": "Custom financial goal",
        "typical_amount": "Any amount",
        "typical_timeline": "Any timeline"
    }
}

cols = st.columns(len(goal_types))
for i, (goal_key, goal_info) in enumerate(goal_types.items()):
    with cols[i]:
        if st.button(
            goal_info["label"],
            use_container_width=True,
            type="primary" if st.session_state.goal_draft.get('type') == goal_key else "secondary"
        ):
            st.session_state.goal_draft['type'] = goal_key

        st.caption(goal_info["description"])
        st.caption(f"**Typical:** {goal_info['typical_amount']}")
        st.caption(f"**Timeline:** {goal_info['typical_timeline']}")

if not st.session_state.goal_draft.get('type'):
    st.info("👆 Select a goal type to continue")
    st.stop()

st.divider()

# STEP 2: Target Amount
st.markdown("## Step 2: How Much Do You Need?")

col1, col2 = st.columns(2)

with col1:
    target_amount = st.number_input(
        "Target Amount ($)",
        min_value=1000,
        max_value=100000000,
        value=st.session_state.goal_draft.get('target_amount', 1000000),
        step=10000,
        help="How much money do you need to reach your goal?"
    )
    st.session_state.goal_draft['target_amount'] = target_amount

with col2:
    # Get current portfolio value
    current_value = get_portfolio_value() if st.session_state.connected else 0

    st.metric(
        label="Current Portfolio",
        value=f"${current_value:,.2f}",
        help="Your current portfolio value from Alpaca"
    )

# Calculate gap
gap = target_amount - current_value
progress_pct = (current_value / target_amount * 100) if target_amount > 0 else 0

st.markdown(f"""
**You need to grow by:** ${gap:,.2f} ({100-progress_pct:.1f}% remaining)
""")

st.divider()

# STEP 3: Timeline
st.markdown("## Step 3: When Do You Need It?")

current_year = datetime.now().year
target_year = st.slider(
    "Target Year",
    min_value=current_year + 1,
    max_value=current_year + 50,
    value=st.session_state.goal_draft.get('target_year', current_year + 20),
    help="When do you need to reach your goal?"
)
st.session_state.goal_draft['target_year'] = target_year

years_to_goal = target_year - current_year
st.info(f"⏱️ **Time Horizon:** {years_to_goal} years from now")

if years_to_goal < 5:
    st.warning("⚠️ **Short timeline:** With less than 5 years, market volatility is a risk. Consider a more conservative strategy.")

st.divider()

# STEP 4: Projection
st.markdown("## Step 4: Projection")

# Calculate projection
assumed_return = 0.085  # All Weather historical return
projected_value = calculate_future_value(current_value, assumed_return, years_to_goal)
on_track = projected_value >= target_amount

# Display projection
if on_track:
    st.success(f"""
    📊 **Based on your All Weather strategy ({assumed_return*100:.1f}% annual return),
    you're projected to reach:**

    **${projected_value:,.0f} by {target_year}** ✅ **On Track!**

    You'll exceed your goal by ${projected_value - target_amount:,.0f}.
    """)
else:
    shortfall = target_amount - projected_value
    st.warning(f"""
    📊 **Based on your All Weather strategy ({assumed_return*100:.1f}% annual return),
    you're projected to reach:**

    **${projected_value:,.0f} by {target_year}** ⚠️ **Below target**

    You'll be short by ${shortfall:,.0f}.
    """)

    st.markdown("**Need to adjust? You can:**")
    st.markdown("""
    • **Increase monthly contributions** (deposit more each month)
    • **Extend your timeline** (choose a later target year)
    • **Switch to a more aggressive strategy** (higher risk, higher potential return)
    """)

# Projection chart
st.markdown("### 📈 Growth Projection")
render_projection_chart(current_value, target_amount, years_to_goal, assumed_return)

st.divider()

# Save button
st.markdown("## Save Your Goal")

notes = st.text_area(
    "Notes (Optional)",
    value=st.session_state.goal_draft.get('notes', ''),
    placeholder="E.g., Retire at 65 with comfortable lifestyle, travel budget of $50K/year",
    help="Add any notes about your goal for future reference"
)
st.session_state.goal_draft['notes'] = notes

if st.button("💾 Save Goal & Return to Dashboard", type="primary", use_container_width=True):
    # Save goal to state file
    goal_data = {
        "version": "1.0",
        "primary_goal": {
            "goal_type": st.session_state.goal_draft['type'],
            "target_amount": target_amount,
            "target_year": target_year,
            "current_amount": current_value,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "risk_tolerance": "moderate",  # Default, can be edited later
            "notes": notes
        },
        "projections": {
            "expected_final_amount": projected_value,
            "expected_completion_year": target_year if on_track else target_year + 5,
            "on_track": on_track,
            "required_monthly_contribution": 0,  # Calculated separately
            "assumed_annual_return": assumed_return,
            "confidence_level": "medium"
        },
        "history": [
            {
                "date": datetime.now().date().isoformat(),
                "portfolio_value": current_value,
                "progress_pct": progress_pct,
                "on_track": on_track
            }
        ]
    }

    # Write to file
    goals_file = Path("state/goals.json")
    goals_file.parent.mkdir(exist_ok=True)
    with open(goals_file, 'w') as f:
        json.dump(goal_data, f, indent=2)

    st.success("✅ Goal saved! Redirecting to dashboard...")
    st.balloons()
    st.switch_page("dashboard.py")
```

**Helper Functions:**

```python
def calculate_future_value(present_value, annual_return, years):
    """Calculate future value using compound interest."""
    return present_value * ((1 + annual_return) ** years)

def render_projection_chart(current, target, years, return_rate):
    """Render projection chart showing growth path."""
    years_array = list(range(years + 1))
    projected_values = [current * ((1 + return_rate) ** y) for y in years_array]
    target_line = [target] * len(years_array)

    fig = go.Figure()

    # Projected growth line
    fig.add_trace(go.Scatter(
        x=years_array,
        y=projected_values,
        mode='lines',
        name='Projected Portfolio',
        line=dict(color='#667eea', width=3),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.1)'
    ))

    # Target line
    fig.add_trace(go.Scatter(
        x=years_array,
        y=target_line,
        mode='lines',
        name='Target Goal',
        line=dict(color='#10b981', width=2, dash='dash')
    ))

    fig.update_layout(
        title=f"Portfolio Growth Projection ({return_rate*100:.1f}% annual return)",
        xaxis_title="Years from Now",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)
```

---

### Component 2: Goal Progress Display (Dashboard Hero Section)

**Integration:** Per Doc 04, this appears in the dashboard hero section

**Visual Design:**
```
┌────────────────────────────────────────────────────────────┐
│                      Your Portfolio                        │
│                       $50,245.32                          │
│                    ▲ +$1,234.56 (2.5%)                    │
│                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━●━━━━━━ 5% to goal ($1M)   │
│  🎯 Retirement Goal: On track to reach by 2049            │
│                                                            │
│  [View Goal Details →]                                    │
└────────────────────────────────────────────────────────────┘
```

**Code Implementation:**

```python
def render_goal_progress():
    """Render goal progress in dashboard hero section."""
    # Load goal from state file
    goals_file = Path("state/goals.json")

    if not goals_file.exists():
        st.info("🎯 **Set your financial goals** to track progress and stay motivated.")
        if st.button("Set Your Goals →", type="primary", use_container_width=True):
            st.switch_page("pages/6_🎯_Goals.py")
        return

    with open(goals_file, 'r') as f:
        goal_data = json.load(f)

    primary_goal = goal_data['primary_goal']
    projections = goal_data['projections']

    # Calculate current progress
    current_value = get_portfolio_value()
    target_amount = primary_goal['target_amount']
    progress_pct = (current_value / target_amount * 100) if target_amount > 0 else 0

    # Progress bar
    st.markdown(f"""
    <div style='margin: 2rem 0;'>
        <div style='width: 100%; height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;'>
            <div style='width: {min(progress_pct, 100):.1f}%; height: 100%;
                        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                        transition: width 0.3s ease;'></div>
        </div>
        <p style='text-align: center; color: #6b7280; font-size: 1rem; margin-top: 0.5rem;'>
            {progress_pct:.1f}% to goal (${target_amount:,.0f})
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Goal status message
    goal_type_emoji = {
        "retirement": "🏖️",
        "house": "🏠",
        "education": "🎓",
        "wealth": "💰",
        "other": "🎯"
    }
    emoji = goal_type_emoji.get(primary_goal['goal_type'], "🎯")

    if projections['on_track']:
        status_icon = "✅"
        status_text = "On track"
        status_color = "#10b981"
    else:
        status_icon = "⚠️"
        status_text = "Behind schedule"
        status_color = "#f59e0b"

    target_year = primary_goal['target_year']
    expected_year = projections['expected_completion_year']

    st.markdown(f"""
    <div style='text-align: center; color: #6b7280; font-size: 1rem;'>
        {emoji} <strong>{primary_goal['goal_type'].title()} Goal:</strong>
        <span style='color: {status_color}; font-weight: 600;'>{status_icon} {status_text}</span>
        to reach by {expected_year}
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("View Goal Details →", use_container_width=True):
            st.switch_page("pages/6_🎯_Goals.py")
```

---

### Component 3: Goal Update & Tracking

**Automatic Updates:** Track progress automatically on each portfolio update

**Code:**

```python
def update_goal_progress():
    """Update goal progress history (call after portfolio updates)."""
    goals_file = Path("state/goals.json")
    if not goals_file.exists():
        return

    with open(goals_file, 'r') as f:
        goal_data = json.load(f)

    current_value = get_portfolio_value()
    target_amount = goal_data['primary_goal']['target_amount']
    progress_pct = (current_value / target_amount * 100) if target_amount > 0 else 0

    # Recalculate projection
    target_year = goal_data['primary_goal']['target_year']
    years_remaining = target_year - datetime.now().year
    assumed_return = goal_data['projections']['assumed_annual_return']
    projected_value = calculate_future_value(current_value, assumed_return, years_remaining)
    on_track = projected_value >= target_amount

    # Update projections
    goal_data['projections']['expected_final_amount'] = projected_value
    goal_data['projections']['on_track'] = on_track
    goal_data['primary_goal']['last_updated'] = datetime.now().isoformat()

    # Add history entry (daily)
    today = datetime.now().date().isoformat()
    if not goal_data['history'] or goal_data['history'][-1]['date'] != today:
        goal_data['history'].append({
            "date": today,
            "portfolio_value": current_value,
            "progress_pct": progress_pct,
            "on_track": on_track
        })

    # Write back
    with open(goals_file, 'w') as f:
        json.dump(goal_data, f, indent=2)

# Call in dashboard after portfolio data loads
if st.session_state.connected:
    update_goal_progress()
```

---

## Verification Strategy

### Unit Tests

Create `tests/test_goal_projection.py`:

```python
def test_future_value_calculation():
    """Test compound interest calculation."""
    pv = 10000
    rate = 0.08
    years = 10
    fv = calculate_future_value(pv, rate, years)
    expected = 10000 * (1.08 ** 10)  # ~21,589
    assert abs(fv - expected) < 1.0

def test_progress_percentage():
    """Test progress calculation."""
    current = 50000
    target = 1000000
    progress = (current / target) * 100
    assert progress == 5.0

def test_on_track_logic():
    """Test on-track determination."""
    current = 50000
    target = 1000000
    years = 24
    rate = 0.085
    projected = calculate_future_value(current, rate, years)
    on_track = projected >= target
    assert on_track == True  # Should be on track with 8.5% over 24 years
```

### Integration Tests

1. **Test goal setting flow:**
   - Navigate to Goals page
   - Set goal type: Retirement
   - Enter target: $1,000,000
   - Enter year: 2050
   - Save goal
   - Verify `state/goals.json` created
   - Return to dashboard → Goal progress appears

2. **Test goal progress tracking:**
   - Set goal
   - Simulate portfolio growth (mock portfolio value increase)
   - Verify progress bar updates
   - Verify "on track" status updates

3. **Test edge cases:**
   - Very short timeline (<5 years) → Shows warning
   - Target amount < current value → Shows "Goal achieved!"
   - No portfolio value (new user) → Shows "Connect account to track progress"

### Manual Verification

**Checklist:**
- [ ] Goals page accessible from dashboard
- [ ] All goal types selectable
- [ ] Target amount input validation (min $1K)
- [ ] Target year input validation (future year only)
- [ ] Projection calculation correct (verify with calculator)
- [ ] Projection chart renders
- [ ] Goal saves to `state/goals.json`
- [ ] Dashboard hero section shows goal progress
- [ ] Progress bar animates smoothly
- [ ] "On track" vs. "Behind" status correct
- [ ] Goal updates daily (history array grows)
- [ ] "View Goal Details" button returns to Goals page

---

## Benefits

### Why This Approach

1. **Emotional connection:** Users care about goals (retirement), not metrics (portfolio value)
2. **Motivation:** Progress bar + "on track" message provides positive reinforcement
3. **Simple math:** Compound interest calculation is straightforward, no complex ML needed
4. **File-based state:** Consistent with existing state management (no database needed)
5. **Industry standard:** Betterment, Wealthfront, Personal Capital all use goal-based framing

### Alternatives Considered

**Alternative 1: Multiple goals (retirement + house + education)**
- ❌ Rejected for MVP: Too complex for target users ($10K-50K accounts)
- ✅ Future enhancement: Add multiple goals in v2.0

**Alternative 2: Goal-based portfolio allocation (change strategy based on goal)**
- ❌ Rejected: Adds complexity. All Weather strategy works for most goals.
- ✅ Future enhancement: Suggest strategy changes if goal timeline is very short

**Alternative 3: Monte Carlo simulation for projections**
- ❌ Rejected: Overkill for MVP. Simple compound interest is sufficient.
- ✅ Future enhancement: Add confidence intervals in advanced view

---

## Expectations

### Success Metrics

**Quantitative:**
- 80%+ of connected users set a goal (high adoption)
- Goal progress visible on dashboard for all users with goals
- Projection accuracy: ±10% of actual outcome (measure after 1 year)
- <5% of users report confusion about goal setting

**Qualitative:**
- User feedback includes "motivating", "helpful", "clear"
- Users report feeling "on track" or understanding their financial progress
- Support requests asking "am I on track?" decrease by 70%

### What Success Looks Like

**Before:** User sees dashboard:
- "Portfolio value: $50,245"
- Thinks: "Is that good? Am I where I should be?"
- Feels uncertain, no context

**After:** User sees dashboard:
- "Portfolio value: $50,245"
- "🎯 Retirement Goal: ✅ On track to reach $1M by 2049"
- "━━━━●━━━━━━ 5% complete"
- Thinks: "I'm on track! Keep going."
- Feels confident, motivated

---

## Risks & Mitigations

### Technical Risks

**Risk 1: Projection accuracy depends on market returns**
- **Likelihood:** High (markets are unpredictable)
- **Impact:** Medium (users might reach goal earlier/later than projected)
- **Mitigation:** Include disclaimer: "Projections based on historical 8.5% return. Actual results may vary." Add confidence levels (low/medium/high confidence).

**Risk 2: File-based state could be corrupted**
- **Likelihood:** Low (JSON is resilient)
- **Impact:** Medium (users lose goal data)
- **Mitigation:** Validate JSON on load, backup goals file on each save, allow re-creating goal

**Risk 3: Goal updates slow dashboard load**
- **Likelihood:** Low (simple calculation)
- **Impact:** Low (<100ms if any)
- **Mitigation:** Cache projection calculation in session state, only recalculate daily

### UX Risks

**Risk 1: Users set unrealistic goals**
- **Likelihood:** Medium (e.g., $10M in 5 years on $50K)
- **Impact:** High (users become discouraged when "behind schedule")
- **Mitigation:** Show warning if goal is unrealistic: "⚠️ This goal requires 45% annual return—consider adjusting timeline or amount."

**Risk 2: Users don't understand compound interest**
- **Likelihood:** Medium (financial literacy varies)
- **Impact:** Medium (confusion about projections)
- **Mitigation:** Show projection chart visually, add tooltip: "How projections work →" linking to Learning Center

**Risk 3: "Behind schedule" message discourages users**
- **Likelihood:** Low (most users on track with 24+ year timeline)
- **Impact:** Medium (users might abandon system)
- **Mitigation:** Soften language: Instead of "Behind schedule", say "Trending slightly below target—small adjustments can help."

---

## Results Criteria

### Acceptance Criteria (Must-Haves)

**Goal Setting Page (`pages/6_🎯_Goals.py`):**
- [ ] Goal type selection (5 types)
- [ ] Target amount input (validation: >$1K)
- [ ] Target year input (validation: future year)
- [ ] Current portfolio value auto-filled
- [ ] Projection calculation (compound interest)
- [ ] Projection chart (growth over time)
- [ ] "On track" vs. "Behind" determination
- [ ] Save goal to `state/goals.json`
- [ ] Return to dashboard after save

**Dashboard Integration:**
- [ ] Hero section shows goal progress bar
- [ ] Progress percentage displayed
- [ ] "On track" status displayed
- [ ] "View Goal Details" button
- [ ] Placeholder if no goal set ("Set Your Goals →")

**State Management:**
- [ ] `state/goals.json` created on first goal save
- [ ] Goal data schema validated
- [ ] Goal progress updated daily (history tracking)
- [ ] File handles concurrent access safely

**Performance:**
- [ ] Goal projection calculates in <100ms
- [ ] Progress bar animates smoothly (<16ms frame time)
- [ ] Goals page loads in <2 seconds

### Success Metrics

**Deployment Success:**
- Goal setting page accessible
- Goal progress appears on dashboard for users with goals
- No errors in goal calculation
- User feedback collected

**Long-term Success:**
- 60%+ of users set goals within first week
- Users with goals check dashboard 2x more frequently than users without
- "Am I on track?" support requests decrease by 70%
- User retention increases (users with goals stay engaged longer)

---

## Domain-Specific Considerations

### Financial Planning Context

**Disclaimer requirements:**
- Projections are estimates, not guarantees
- Past performance doesn't predict future results
- Users should consult financial advisors for personalized advice

**Best practices from industry:**
- Betterment: Shows confidence intervals (10th-90th percentile outcomes)
- Wealthfront: Adjusts projections based on deposits/withdrawals
- Personal Capital: Offers multiple goal tracking simultaneously
- Vanguard: Shows required savings rate to reach goal

**Our approach for MVP:** Simple single-goal tracking with compound interest projection. Can add advanced features (confidence intervals, multiple goals) in v2.0.

### User Personas

**Persona 1: Young professional (25-35 years old)**
- Goal: Retirement in 30-40 years
- Needs: Long-term projection, motivation to stay invested
- Benefits: Progress bar + "on track" messaging provides motivation

**Persona 2: Mid-career saver (35-50 years old)**
- Goal: Retirement in 15-30 years, or house down payment
- Needs: Realistic timeline, adjust strategy if needed
- Benefits: Projection shows if timeline is achievable, suggests adjustments

**Persona 3: Pre-retiree (50-65 years old)**
- Goal: Retirement in <15 years
- Needs: Conservative estimate, risk awareness
- Benefits: Short timeline triggers warning about volatility, suggests conservative strategy

---

## Cross-References

- **Depends on:**
  - `04-information-architecture.md` (defines where goal progress appears - hero section)
- **Referenced by:**
  - `06-implementation-guide.md` (Phase 2 implementation)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial specification |

---

**Status:** ✅ Complete and ready for implementation
