# Implementation Guide

**Document:** 06-implementation-guide.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document provides the complete implementation roadmap for the Dalio Lite UI redesign. It synthesizes all specification documents (01-05) into a phased, testable, deployable plan with specific file:line edit locations, testing strategies, and rollback procedures.

**Why this exists:** Specification documents define WHAT to build. This implementation guide defines HOW and WHEN to build it, in what order, with what level of risk, and how to verify success at each phase.

**Scope:** All files identified in audit1 (`dashboard.py` + 5 `pages/*.py` files) plus new files from specifications.

---

## Implementation Strategy

### Approach: Phased Rollout (Incremental Deployment)

**Why phased?**
- Reduces risk (deploy small changes, verify, then proceed)
- Allows testing in production (measure impact of each phase)
- Enables quick rollback (only one phase at risk at a time)
- Builds confidence (early wins before big changes)

**Alternative rejected:** Big Bang deployment (all changes at once)
- ❌ Too risky for 6-file, 2-3 day project
- ❌ Hard to identify which change caused issues
- ❌ All-or-nothing rollback (lose all progress)

---

## Phase Overview

| Phase | Focus | Complexity | Duration | Risk | Deploy When |
|-------|-------|------------|----------|------|-------------|
| **Phase 1** | Error handling + Trust indicators | Low | 4-5 hours | Low | Week 1 |
| **Phase 2** | Goal UI + Dashboard redesign | High | 6-7 hours | Medium | Week 2 |
| **Phase 3** | Onboarding improvements | Medium | 2 hours | Low | Week 3 |

**Total:** 12-14 hours implementation + 8-10 hours specification writing = **20-24 hours**

---

## Phase 1: Error Handling & Trust Indicators

**Goal:** Fix critical UX issues (raw exceptions, missing trust signals)

**Deliverables:**
- User-friendly error messages (no more stack traces)
- Trust bar on all pages
- Security details in sidebar
- Demo data warning on Market Dashboard

**Why Phase 1?**
- Highest user impact (fixes "tacky" error messages)
- Low risk (only improves existing, doesn't break functionality)
- Quick wins (builds confidence for later phases)

### Files Created

1. **`error_handler.py`** (NEW - ~200 lines)
   - Error translation layer
   - Maps exceptions to user-friendly messages
   - Logging for technical details

2. **`trust_indicators.py`** (NEW - ~150 lines)
   - Reusable trust UI components
   - `render_trust_bar()` function
   - `render_security_details()` function
   - `render_disclaimer()` function

### Files Modified

#### `dashboard.py`

**Edit 1: Import error handler** (Line 1-13 area)
```python
# Add after existing imports
from error_handler import display_error
from trust_indicators import render_trust_bar, render_security_details, render_disclaimer
```

**Edit 2: Add trust bar after title** (Line 380-382 area)
```python
st.markdown("---")
# NEW: Add trust bar
render_trust_bar()
st.divider()
```

**Edit 3: Replace error on line 292**
```python
# OLD:
except Exception as e:
    st.error(f"Connection failed: {str(e)}")

# NEW:
except Exception as e:
    display_error(e, context="connecting_to_alpaca")
```

**Edit 4-11: Replace 8 more error messages** (Lines 508, 589, 605, 617, 627, 654, 671, 689)
- Pattern: Replace `st.error(f"...{str(e)}")` with `display_error(e, context="...")`
- Contexts: `"fetching_account"`, `"loading_portfolio"`, `"running_check"`, `"dry_run"`, `"generating_report"`, `"checking_status"`, `"force_rebalance"`, `"reading_log"`

**Edit 12: Add security details in sidebar** (Line 353 area, after AutoPilot section)
```python
st.divider()
render_security_details()
```

**Edit 13: Add disclaimer footer** (Line 704, replace existing footer)
```python
# Replace static footer with:
render_disclaimer()
```

#### `pages/5_📊_Monitoring.py`

**Edit 1: Import error handler** (Top of file)
```python
from error_handler import display_error
from trust_indicators import render_trust_bar
```

**Edit 2: Add trust bar** (After line 16)
```python
render_trust_bar()
st.divider()
```

**Edit 3-5: Replace 3 error messages** (Lines 57, 233, 304, 307)
- Replace `st.error(f"...{e}")` with `display_error(e, context="...")`

#### `pages/3_📊_Market_Dashboard.py`

**Edit 1: Import trust indicators** (Top of file)
```python
from trust_indicators import render_trust_bar, render_demo_warning
```

**Edit 2: Add demo warning** (After line 64, before main content)
```python
# CRITICAL: Demo data warning
render_demo_warning()
st.divider()
```

**Edit 3: Add trust bar** (After title)
```python
render_trust_bar()
st.divider()
```

#### `pages/1_📖_How_It_Works.py`, `pages/2_🎯_Strategy_Selector.py`, `pages/4_🎓_Learning_Center.py`

**Same pattern for all 3:**
- Import `render_trust_bar` at top
- Add `render_trust_bar()` + `st.divider()` after title

### Testing Strategy (Phase 1)

**Unit Tests:**
```bash
# Create tests/test_error_handler.py (from Doc 01)
pytest tests/test_error_handler.py

# Expected: 100% pass
```

**Integration Tests:**
- Intentionally trigger each error type (invalid keys, timeout, etc.)
- Verify friendly message appears (not stack trace)
- Verify technical details logged to `logs/dalio_lite.log`

**Manual Verification:**
- [ ] Disconnect internet → Try connect → See friendly connection error
- [ ] Use invalid API keys → See auth error (not stack trace)
- [ ] Trust bar visible on all 6 pages
- [ ] Demo warning on Market Dashboard only
- [ ] Security details in sidebar
- [ ] Disclaimer footer on all pages

**Performance Test:**
- Page load time should not increase by >100ms
- Measure: Open dashboard 10 times, average load time

**Success Criteria:**
- ✅ Zero raw exceptions visible in any scenario
- ✅ Trust bar on 6/6 pages
- ✅ Demo warning prominently displayed
- ✅ <100ms performance overhead

### Deployment (Phase 1)

**Steps:**
1. Create new branch: `git checkout -b ui-redesign-phase1`
2. Implement all Phase 1 changes
3. Run tests: `pytest tests/` (should pass)
4. Commit: `git commit -m "Phase 1: Error handling + trust indicators"`
5. Push: `git push origin ui-redesign-phase1`
6. Deploy to staging (if available) OR Railway production
7. Test in production for 24 hours
8. If successful, merge to main

**Rollback Plan:**
- If issues found: `git revert [commit-hash]` and redeploy
- Estimated rollback time: 5 minutes
- Rollback trigger: User reports of broken functionality OR errors in logs

---

## Phase 2: Goal UI & Dashboard Redesign

**Goal:** Transform dashboard from metrics-centric to goal-centric, reduce cognitive load

**Deliverables:**
- Goal setting page (new)
- Goal progress in hero section
- Dashboard layout with progressive disclosure
- Simplified sidebar

**Why Phase 2?**
- Highest value-add (addresses "20x better" user feedback)
- Medium risk (significant layout changes but no backend logic changes)
- Builds on Phase 1 trust indicators

### Files Created

1. **`pages/6_🎯_Goals.py`** (NEW - ~300 lines)
   - Goal setting interface
   - Projection calculator
   - Goal progress chart

2. **`state/goals.json`** (Created by goals page)
   - Goal data schema (from Doc 03)

### Files Modified

#### `dashboard.py` (MAJOR REFACTOR)

**Warning:** This is the most complex phase. Recommend creating `dashboard_backup.py` before starting.

**Approach:** Rather than line-by-line edits, restructure entire file:

**New Structure:**
```python
# Imports (add goal helpers)
from goal_tracker import (
    load_goal,
    calculate_projection,
    render_goal_progress,
    update_goal_progress
)

# ... existing imports ...

# Page config (unchanged)

# Custom CSS (unchanged)

# Session state (unchanged)

# Sidebar (REDESIGNED - from Doc 04)
with st.sidebar:
    render_sidebar()  # New function from sidebar_components.py

# Main content
if not st.session_state.connected:
    # Onboarding (keep Phase 1 version for now, Phase 3 will replace)
    render_onboarding_welcome()  # Keep existing
else:
    # HERO SECTION (NEW - from Doc 04)
    render_hero_section()  # Includes portfolio value + goal progress

    # KEY METRICS (REDESIGNED - from Doc 04)
    render_key_metrics()  # 3 metrics instead of 4

    # PRIMARY ACTION (REDESIGNED - from Doc 04)
    render_primary_action()  # Prominent daily check button

    # DETAILS SECTION (NEW - from Doc 04)
    render_details_section()  # All in expanders

# Footer (unchanged from Phase 1)
render_disclaimer()
```

**Implementation Strategy:**
1. Extract current connected state code into functions
2. Create new functions per Doc 04 spec
3. Replace main content section
4. Test thoroughly before deployment

**File: `sidebar_components.py` (NEW - ~150 lines)**
- Extracted sidebar rendering from Doc 04
- Grouped information display
- Easier to maintain than inline code

**File: `goal_tracker.py` (NEW - ~200 lines)**
- Goal loading/saving functions
- Projection calculation
- Progress rendering
- Automatic daily updates

### Testing Strategy (Phase 2)

**Unit Tests:**
```bash
# Create tests/test_goal_projection.py (from Doc 03)
pytest tests/test_goal_projection.py

# Create tests/test_dashboard_layout.py
# Test that all sections render
pytest tests/test_dashboard_layout.py
```

**Integration Tests:**
- Set goal → Return to dashboard → Verify progress bar appears
- Expand each detail section → Verify content loads
- Test with no goal set → Verify "Set Your Goals" prompt

**Manual Verification:**
- [ ] Hero section shows portfolio value (large)
- [ ] Goal progress bar appears (if goal set)
- [ ] 3 key metrics visible (not 4)
- [ ] Primary action button prominent
- [ ] Detail sections collapsed by default
- [ ] All detail sections expandable
- [ ] Sidebar shows grouped information
- [ ] Trust bar still present (from Phase 1)

**User Testing:**
- Show new layout to 3-5 users
- Ask: "What's the most important thing on this page?"
- Success: 80%+ say "portfolio value" or "goal progress"

**Performance Test:**
- Dashboard load time <2 seconds
- Expanders open instantly (<100ms)

**Success Criteria:**
- ✅ Hero section renders correctly
- ✅ Goal progress functional (if goal set)
- ✅ Layout hierarchy clear (users focus on hero)
- ✅ No broken functionality (all actions still work)
- ✅ Performance maintained (<2s load)

### Deployment (Phase 2)

**Steps:**
1. Create branch: `git checkout -b ui-redesign-phase2`
2. **IMPORTANT:** Copy `dashboard.py` to `dashboard_backup_phase1.py`
3. Implement dashboard refactor
4. Test extensively (this is high-risk phase)
5. Commit: `git commit -m "Phase 2: Goal UI + dashboard redesign"`
6. Push and deploy to staging FIRST (if available)
7. Test in staging for 2-3 days
8. Deploy to production
9. Monitor closely for 48 hours

**Rollback Plan:**
- If critical issues: Copy `dashboard_backup_phase1.py` back to `dashboard.py`, redeploy
- Estimated rollback time: 10 minutes
- Rollback triggers:
  - Dashboard won't load
  - Actions (Run Check, etc.) don't work
  - Errors in logs
  - >20% performance degradation

---

## Phase 3: Onboarding Improvements

**Goal:** Reduce onboarding friction, increase completion rate

**Deliverables:**
- Improved welcome screen (3-step progress)
- Setup Guide page (detailed instructions)
- First-run welcome experience

**Why Phase 3?**
- Lower priority (only affects new users)
- Low risk (doesn't touch core functionality)
- Can be done last (builds on Phases 1-2)

### Files Created

1. **`pages/7_📝_Setup.py`** (NEW - ~250 lines)
   - Complete setup instructions
   - Troubleshooting guide
   - .env template with copy button

### Files Modified

#### `dashboard.py` (Non-Connected State)

**Replace onboarding section** (Lines 383-462 area)
- Replace 3-card layout with progressive 3-step flow (from Doc 05)
- Add step completion tracking
- Add CTAs for each step

**Add first-run welcome** (After successful connection, line 464 area)
```python
# After connection succeeds, show welcome
if st.session_state.connected:
    show_first_run_welcome()  # From onboarding_helpers.py
```

**File: `onboarding_helpers.py` (NEW - ~100 lines)**
- `render_onboarding_welcome()` function
- `show_first_run_welcome()` function
- Step tracking logic

### Testing Strategy (Phase 3)

**User Testing (Critical for Phase 3):**
- Recruit 5 users who've never seen Dalio Lite
- Give task: "Get the app connected to Alpaca"
- Observe: Where do they get stuck? How long does it take?
- Success: 4/5 complete without asking for help, <10 minutes

**Integration Tests:**
- Fresh install → Follow onboarding → Verify connection succeeds
- Click "Setup Guide" → Verify page loads with all sections
- Mark Step 1 complete → Verify step 2 unlocks

**Manual Verification:**
- [ ] Welcome screen shows 3 steps
- [ ] Steps unlock sequentially
- [ ] Setup Guide accessible from welcome
- [ ] Setup Guide has all sections (4 steps + troubleshooting)
- [ ] .env template copy-pasteable
- [ ] First-run welcome appears after connection
- [ ] First-run welcome dismisses after interaction

**Metrics to Track (A/B test if possible):**
- Onboarding completion rate (before vs. after)
- Time to first connection
- Drop-off rate at each step

**Success Criteria:**
- ✅ 70%+ onboarding completion rate (up from est. 40%)
- ✅ <10 minutes average connection time
- ✅ 50% reduction in "how do I start?" support requests

### Deployment (Phase 3)

**Steps:**
1. Create branch: `git checkout -b ui-redesign-phase3`
2. Implement onboarding changes
3. Test with fresh .env (simulate new user)
4. Commit: `git commit -m "Phase 3: Onboarding improvements"`
5. Push and deploy
6. Monitor onboarding completion metrics

**Rollback Plan:**
- If issues: Revert to Phase 2 onboarding (still functional)
- Estimated rollback time: 5 minutes
- Rollback trigger: Onboarding completion rate drops below pre-Phase 3 baseline

---

## Testing Matrix

### Test Coverage by Phase

| Test Type | Phase 1 | Phase 2 | Phase 3 | Total |
|-----------|---------|---------|---------|-------|
| Unit Tests | 10 tests | 8 tests | 3 tests | 21 tests |
| Integration | 5 tests | 6 tests | 4 tests | 15 tests |
| Manual Checks | 8 items | 12 items | 7 items | 27 items |
| User Testing | - | 1 session | 1 session | 2 sessions |

**Total Testing Time:** ~6 hours (across all phases)

### Regression Testing (After Each Phase)

Run this checklist after deploying each phase to ensure no breakage:

- [ ] Dashboard loads without errors
- [ ] Can connect to Alpaca (if not already connected)
- [ ] Can run daily check (mock if market closed)
- [ ] Can run dry run
- [ ] Can generate report
- [ ] Can view all pages (navigation works)
- [ ] Can change strategy (on Strategy Selector page)
- [ ] Sidebar shows correct status
- [ ] Trust bar visible (Phase 1+)
- [ ] Goal progress visible (Phase 2+, if goal set)
- [ ] Onboarding works for new users (Phase 3+)

**Estimated time per regression:** 15 minutes

---

## Risk Register

| Risk | Phase | Likelihood | Impact | Mitigation | Status |
|------|-------|------------|--------|------------|--------|
| Raw exception slips through error handler | 1 | Low | Medium | Code review, test all error paths | Not Started |
| Trust bar breaks page layout | 1 | Low | Low | CSS testing across pages | Not Started |
| Dashboard refactor breaks core functionality | 2 | Medium | High | Backup file, extensive testing, staged rollout | Not Started |
| Goal projection calculation wrong | 2 | Low | Medium | Unit tests, verify with calculator | Not Started |
| Onboarding confuses users more | 3 | Low | Medium | User testing before deployment | Not Started |
| Performance degrades (>2s dashboard load) | All | Low | Medium | Performance testing after each phase | Not Started |

### Rollback Triggers (Stop and Revert)

**Automatic rollback if:**
- Dashboard won't load (HTTP 500)
- >10% error rate in logs
- Core actions broken (can't run daily check)
- >50% performance degradation (>4s load time)

**Manual rollback if:**
- User feedback is overwhelmingly negative
- Onboarding completion rate drops below baseline
- Critical bug discovered that can't be hot-fixed quickly

---

## Success Metrics

### Phase 1 Success Metrics

**Quantitative:**
- Zero raw exceptions visible in production (100% coverage)
- Trust bar on 6/6 pages (100% coverage)
- Demo warning on Market Dashboard (100% visibility)
- <100ms performance overhead (maintain baseline)

**Qualitative:**
- User feedback: "errors are clear now"
- Support tickets: 30% reduction in "what does this error mean?"

### Phase 2 Success Metrics

**Quantitative:**
- 60%+ users set goals within first week
- Users with goals check dashboard 2x more frequently
- Dashboard load time <2 seconds (maintain baseline)
- 80%+ users focus on hero section first (eye tracking or user survey)

**Qualitative:**
- User feedback: "I know if I'm on track now"
- Support tickets: 70% reduction in "am I doing well?"

### Phase 3 Success Metrics

**Quantitative:**
- 70%+ onboarding completion rate (up from est. 40%)
- <10 minutes average time to connection
- 50% reduction in onboarding support requests
- 80%+ new users complete first check within 24 hours

**Qualitative:**
- User feedback: "setup was easy"
- Support tickets: 50% reduction in "how do I start?"

### Overall Project Success Metrics

**Measured 30 days after Phase 3 deployment:**
- User retention: 20%+ increase (users return more often)
- User satisfaction: Net Promoter Score (NPS) improvement
- Support load: 50%+ reduction in UI/UX related tickets
- User feedback: Shift from "tacky" to "professional"

---

## Post-Deployment Monitoring

### Week 1 (Phase 1)

**Monitor:**
- Error logs: Verify no raw exceptions appear
- Performance: Dashboard load time
- User feedback: In-app survey or support tickets

**Action if issues:**
- Hot-fix if minor (typo, CSS issue)
- Rollback if major (broken functionality)

### Week 2 (Phase 2)

**Monitor:**
- Dashboard load time (most critical)
- Goal setting adoption rate
- Error logs for dashboard-related errors
- User feedback on new layout

**Action if issues:**
- Rollback to Phase 1 if critical
- Hot-fix if non-blocking issue

### Week 3 (Phase 3)

**Monitor:**
- Onboarding completion rate
- Time to first connection
- Setup Guide page views
- User feedback on onboarding

**Action if issues:**
- Rollback to Phase 2 if onboarding broken
- Iterate on Setup Guide content if confusion persists

### Ongoing (Post-Launch)

**Monthly review:**
- All success metrics
- User feedback trends
- Support ticket analysis
- Performance trends

**Quarterly:**
- User satisfaction survey
- A/B test potential improvements
- Plan v2.0 enhancements (multiple goals, advanced features)

---

## Future Enhancements (Post-MVP)

**Not in scope for current project, but consider for v2.0:**

1. **Multiple goals** (retirement + house + education)
   - Complexity: High
   - Value: Medium (most users have 1 primary goal)

2. **In-app API key input** (vs. .env file)
   - Complexity: High (requires secure backend)
   - Value: High (better onboarding UX)

3. **Monte Carlo simulation** for goal projections
   - Complexity: Medium
   - Value: Medium (adds confidence intervals)

4. **Mobile app** (React Native or PWA)
   - Complexity: Extreme
   - Value: High (users want mobile access)

5. **Real-time market data** (replace demo data)
   - Complexity: Medium (API integration + cost)
   - Value: Medium (educational value, not critical for strategy)

6. **Advanced charts** (portfolio performance over time)
   - Complexity: Medium
   - Value: Medium (nice-to-have, not must-have)

---

## Appendix: File Inventory

### Files Modified (Existing)

1. `dashboard.py` - ~705 lines, heavily modified in Phases 1-3
2. `pages/1_📖_How_It_Works.py` - ~462 lines, minor edits (trust bar)
3. `pages/2_🎯_Strategy_Selector.py` - ~332 lines, minor edits (trust bar)
4. `pages/3_📊_Market_Dashboard.py` - ~431 lines, moderate edits (demo warning + trust bar)
5. `pages/4_🎓_Learning_Center.py` - ~769 lines, minor edits (trust bar)
6. `pages/5_📊_Monitoring.py` - ~322 lines, moderate edits (errors + trust bar)

**Total lines modified:** ~3,021 lines across 6 files

### Files Created (New)

1. `error_handler.py` - ~200 lines (Phase 1)
2. `trust_indicators.py` - ~150 lines (Phase 1)
3. `pages/6_🎯_Goals.py` - ~300 lines (Phase 2)
4. `goal_tracker.py` - ~200 lines (Phase 2)
5. `sidebar_components.py` - ~150 lines (Phase 2)
6. `pages/7_📝_Setup.py` - ~250 lines (Phase 3)
7. `onboarding_helpers.py` - ~100 lines (Phase 3)

**Total new lines:** ~1,350 lines across 7 files

### Test Files Created

1. `tests/test_error_handler.py` - ~100 lines
2. `tests/test_trust_indicators.py` - ~80 lines
3. `tests/test_goal_projection.py` - ~120 lines
4. `tests/test_dashboard_layout.py` - ~150 lines
5. `tests/test_onboarding.py` - ~80 lines

**Total test lines:** ~530 lines across 5 files

### Total Project Size

- Existing code: 3,021 lines modified
- New code: 1,350 lines created
- Tests: 530 lines created
- **Grand total:** ~4,900 lines of code

---

## Implementation Checklist

### Pre-Implementation

- [ ] All specification documents reviewed (Docs 01-05)
- [ ] Implementation guide reviewed (this document)
- [ ] Git branch strategy agreed upon
- [ ] Backup strategy confirmed
- [ ] Testing environment ready (local + staging if available)

### Phase 1 Implementation

- [ ] Create `error_handler.py`
- [ ] Create `trust_indicators.py`
- [ ] Modify `dashboard.py` (10 edits)
- [ ] Modify `pages/5_📊_Monitoring.py` (5 edits)
- [ ] Modify `pages/3_📊_Market_Dashboard.py` (3 edits)
- [ ] Modify `pages/1_📖_How_It_Works.py` (2 edits)
- [ ] Modify `pages/2_🎯_Strategy_Selector.py` (2 edits)
- [ ] Modify `pages/4_🎓_Learning_Center.py` (2 edits)
- [ ] Create test files (2 files)
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Manual verification checklist
- [ ] Commit and deploy
- [ ] Monitor for 24 hours

### Phase 2 Implementation

- [ ] Create `goal_tracker.py`
- [ ] Create `sidebar_components.py`
- [ ] Create `pages/6_🎯_Goals.py`
- [ ] Backup `dashboard.py` to `dashboard_backup_phase1.py`
- [ ] Refactor `dashboard.py` (major changes)
- [ ] Create test files (2 files)
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] User testing (3-5 users)
- [ ] Manual verification checklist
- [ ] Performance testing
- [ ] Commit and deploy to staging
- [ ] Test in staging for 2-3 days
- [ ] Deploy to production
- [ ] Monitor for 48 hours

### Phase 3 Implementation

- [ ] Create `onboarding_helpers.py`
- [ ] Create `pages/7_📝_Setup.py`
- [ ] Modify `dashboard.py` (onboarding section)
- [ ] Create test files (1 file)
- [ ] Run integration tests
- [ ] User testing with fresh installs (5 users)
- [ ] Manual verification checklist
- [ ] Commit and deploy
- [ ] Monitor onboarding metrics

### Post-Implementation

- [ ] All phases deployed successfully
- [ ] Success metrics baseline captured
- [ ] User feedback survey sent
- [ ] Support ticket trends analyzed
- [ ] Performance metrics stable
- [ ] Documentation updated (README, etc.)
- [ ] Team retrospective completed

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial implementation guide |

---

**Status:** ✅ Complete and ready for execution

**Next Step:** Begin Phase 1 implementation following this guide
