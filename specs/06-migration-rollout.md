# Migration & Rollout Strategy

**Document:** 06-migration-rollout.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** 01-testing, 04-observability (gates require tests + monitoring)
**Enables:** 07-production-checklist.md (defines validation criteria)

---

## Overview

Defines phased deployment strategy for production hardening, ensuring safe migration from current (untested, unmonitored) state to production-ready system.

**Why This Exists:**
- Can't deploy all changes at once (too risky)
- Need validation gates between phases
- Users currently in paper trading (must not disrupt)
- Live trading requires extra validation

**What This Covers:**
- 4-phase rollout plan
- Validation gates between phases
- Rollback procedures
- Timeline and milestones

---

## Rollout Phases

### Phase 1: Infrastructure (No Behavior Changes)

**Duration:** 1 week
**Goal:** Add testing, monitoring, backup without changing trading logic

**What Gets Deployed:**
- ✅ Test suite (01-testing-infrastructure)
- ✅ Metrics collection (04-observability-monitoring)
- ✅ Backup system (05-backup-disaster-recovery)
- ✅ Transaction logging (03-error-handling-recovery - logging only)

**What Does NOT Change:**
- ❌ Rebalancing logic (unchanged)
- ❌ Order execution (unchanged)
- ❌ State management (unchanged)

**Validation Gate:**
- [ ] All tests pass (pytest)
- [ ] Metrics collected after 1 rebalance
- [ ] Backups created automatically
- [ ] Transaction logs written
- [ ] Zero production errors

**Rollback:** Delete new files (tests/, monitoring/, backups/), no production impact

---

### Phase 2: Safety Improvements (Low-Risk Changes)

**Duration:** 3 days
**Goal:** Add concurrency control and error handling

**What Gets Deployed:**
- ✅ Concurrency control (02-concurrency-control)
- ✅ Enhanced error handling (03-error-handling-recovery)
- ✅ Retry logic with backoff
- ✅ Health checks (04-observability-monitoring)

**What Changes:**
- Order execution now returns detailed results (not just bool)
- State writes are atomic (write-rename pattern)
- Rebalancing acquires lock before execution

**Validation Gate:**
- [ ] All tests pass
- [ ] Manual test: Dashboard + AutoPilot concurrent execution → no double rebalance
- [ ] Manual test: Kill process mid-rebalance → lock released
- [ ] Error handling tested (inject API failure, verify retry)
- [ ] 7 days in paper trading with zero incidents

**Rollback:** Revert to Phase 1 code (30-min rollback)

---

### Phase 3: Extended Paper Trading Validation

**Duration:** 30 days
**Goal:** Run full system in paper trading, monitor for issues

**Activities:**
- Run AutoPilot daily
- Use Dashboard for manual checks
- Monitor all metrics
- Test failure scenarios deliberately

**Test Scenarios:**
1. **Concurrent execution:** Trigger AutoPilot + Dashboard simultaneously
2. **API failure:** Block Alpaca API with firewall, verify error handling
3. **State corruption:** Truncate state file, verify recovery
4. **Process crash:** Kill process mid-rebalance, verify lock release
5. **Rate limit:** Rapid API calls, verify backoff logic

**Validation Gate:**
- [ ] Zero double rebalancing incidents
- [ ] Zero undetected partial failures
- [ ] All test scenarios handled gracefully
- [ ] Health checks green 95%+ of time
- [ ] User confidence high (no complaints)

**Success Criteria:**
- 30 consecutive days without critical errors
- <5% API error rate
- <2% order failure rate
- Monitoring dashboard shows stable metrics

---

### Phase 4: Live Trading (Graduated Rollout)

**Duration:** 2 months
**Goal:** Gradually increase financial exposure

**Tier 1: $1K Account (Week 1)**
- Create new brokerage account with $1K
- Enable live trading (`paper_trading: false`)
- Monitor daily
- Validate: Zero errors, expected behavior

**Tier 2: $5K Account (Weeks 2-4)**
- Increase to $5K
- Continue daily monitoring
- Validate: Performance tracking vs benchmarks

**Tier 3: Full Account $10-50K (Month 2+)**
- Scale to full account size
- Weekly monitoring (not daily)
- System proven in production

**Validation Gate (Before Each Tier):**
- [ ] Previous tier ran 7+ days error-free
- [ ] All health checks green
- [ ] Production checklist (Doc 07) complete
- [ ] User approves tier increase

**Rollback:** Disable live trading, return to paper trading

---

## Rollback Procedures

### Quick Rollback (Production Hotfix)

```bash
# Stop AutoPilot
launchctl unload ~/Library/LaunchAgents/com.daliolite.autopilot.plist  # macOS
# or: crontab -e and comment out dalio line  # Linux

# Revert code to last stable version
git checkout <last-stable-tag>
pip install -r requirements.txt

# Restart dashboard
streamlit run dashboard.py

# Time to rollback: ~5 minutes
```

### Full Rollback (Return to Phase 1)

```bash
# Disable all new features
git checkout phase-1-baseline

# Remove new directories (optional)
rm -rf tests/ monitoring/ backups/ specs/

# Restart system
# Time to rollback: ~15 minutes
```

---

## Timeline

```
Week 1:     Phase 1 (Infrastructure)
Week 2:     Phase 2 (Safety Improvements)
Weeks 3-7:  Phase 3 (Paper Trading Validation)
Week 8:     Phase 4 Tier 1 ($1K live)
Weeks 9-11: Phase 4 Tier 2 ($5K live)
Month 3+:   Phase 4 Tier 3 (Full account live)

Total: ~3 months to full production
```

---

## Success Criteria

**Phase 1 Success:**
- Tests pass, metrics collected, backups working

**Phase 2 Success:**
- No race conditions, error handling works, 7 days stable

**Phase 3 Success:**
- 30 days paper trading, zero critical errors, user confident

**Phase 4 Success:**
- Live trading working, performance meets expectations, user satisfied

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Phase 2 breaks trading | 7-day paper validation before declaring success |
| Test failure in production | CI/CD blocks deployment if tests fail |
| Monitoring overhead | Metrics flush async, <10ms overhead |
| User loses confidence | Transparent communication, rollback always available |

---

**Status:** Ready for execution
**Next Document:** 07-production-checklist.md
