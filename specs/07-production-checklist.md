# Production Readiness Checklist

**Document:** 07-production-checklist.md
**Project:** Dalio Lite Production Hardening
**Date:** 2026-02-17
**Status:** Final
**Dependencies:** All previous documents (synthesizes requirements)
**Purpose:** Gate-keeper for live trading enablement

---

## Overview

This checklist must be 100% complete before enabling live trading (`paper_trading: false`).

**Purpose:**
- Prevent premature live trading
- Ensure all hardening complete
- Document due diligence
- Provide audit trail

---

## Pre-Live Trading Checklist

### 🧪 Testing Infrastructure (Doc 01)

- [ ] **Test suite installed:** pytest, pytest-cov, pytest-mock, responses
- [ ] **Unit tests written:** All critical functions have tests
  - [ ] Drift calculation tested (4+ test cases)
  - [ ] Rebalancing logic tested (3+ test cases)
  - [ ] Order calculation tested (3+ test cases)
  - [ ] Circuit breakers tested (3+ test cases)
  - [ ] State management tested (3+ test cases)
- [ ] **Integration tests written:** API mocking, end-to-end rebalance
  - [ ] Alpaca integration tested (5+ scenarios)
  - [ ] End-to-end rebalance tested (1+ scenario)
- [ ] **Test coverage:** ≥80% on core logic (`pytest --cov`)
- [ ] **All tests passing:** `pytest` runs green
- [ ] **CI/CD configured:** GitHub Actions (or equivalent) running tests
- [ ] **Pre-commit hook:** Tests run before every commit

**Validation:** Run `pytest --cov` → 80%+ coverage, 0 failures

---

### 🔒 Concurrency Control (Doc 02)

- [ ] **StateLockManager implemented:** File locking working
- [ ] **DalioLite integrated:** All state operations acquire lock
- [ ] **Lock timeout configured:** 30s timeout in config.yaml
- [ ] **Lock file created:** `state/dalio_lite.lock` exists
- [ ] **Atomic state writes:** Write-rename pattern implemented
- [ ] **Manual test passed:** Dashboard + AutoPilot concurrent execution → no double rebalance
- [ ] **Crash test passed:** Kill process mid-rebalance → lock released automatically
- [ ] **Logs show lock operations:** "State lock acquired/released" messages present

**Validation:** Concurrent execution test, kill-9 test

---

### ⚠️ Error Handling & Recovery (Doc 03)

- [ ] **Enhanced order execution:** Returns OrderResult with status
- [ ] **Retry logic implemented:** 3 retries with exponential backoff
- [ ] **Retryable errors detected:** 500, 429, timeout errors retry
- [ ] **Non-retryable errors skipped:** 401, 404 errors don't retry
- [ ] **Transaction logging implemented:** All rebalances logged
- [ ] **Transaction logs created:** `state/transactions/*.json` files exist
- [ ] **Partial failure handling:** System detects and logs partial failures
- [ ] **Reconciliation implemented:** Target vs actual orders compared
- [ ] **User notifications:** Email sent on failures (tested)
- [ ] **Error test passed:** Inject API failure → retry logic works

**Validation:** Test transaction log after rebalance, inject failure and verify retry

---

### 📊 Observability & Monitoring (Doc 04)

- [ ] **MetricsCollector implemented:** Singleton metrics collection
- [ ] **All operations instrumented:** Rebalance, orders, API calls tracked
- [ ] **Metrics file created:** `monitoring/metrics.json` exists
- [ ] **Metrics dashboard page:** `pages/5_📊_Monitoring.py` created
- [ ] **Health checks implemented:** HealthChecker class working
- [ ] **Health dashboard:** Health status visible in dashboard
- [ ] **Alert thresholds defined:** Rebalance success rate, AutoPilot, API errors
- [ ] **Metrics visible:** Dashboard shows metrics after 1 rebalance
- [ ] **Historical tracking:** Metrics accumulate over time

**Validation:** Run 1 rebalance, verify metrics.json created, dashboard shows data

---

### 💾 Backup & Disaster Recovery (Doc 05)

- [ ] **BackupManager implemented:** Backup system working
- [ ] **Automatic backups:** State backed up after every change
- [ ] **Backups directory created:** `backups/` contains backup files
- [ ] **Checksums generated:** `.sha256` files created for each backup
- [ ] **Retention policy:** Old backups deleted (>30 days)
- [ ] **Recovery tested:** Can restore from backup successfully
- [ ] **Cloud backup (optional):** S3 configured if desired
- [ ] **Recovery procedure documented:** README includes restore steps

**Validation:** Trigger rebalance, verify backup in backups/, test restore

---

### 🚀 Migration & Rollout (Doc 06)

- [ ] **Phase 1 complete:** Infrastructure deployed, no behavior changes
- [ ] **Phase 2 complete:** Safety improvements deployed, tested 7 days
- [ ] **Phase 3 complete:** 30 days paper trading validation passed
  - [ ] Zero double rebalancing incidents
  - [ ] Zero undetected partial failures
  - [ ] All test scenarios passed
  - [ ] Health checks green 95%+ of time
- [ ] **Rollback tested:** Can rollback to previous version in <15 min
- [ ] **User trained:** Understands dashboard, knows how to check health

**Validation:** 30 consecutive days paper trading, zero critical errors

---

### 📋 Documentation & Configuration

- [ ] **README updated:** Installation, setup, running tests documented
- [ ] **Configuration reviewed:** `config.yaml` settings appropriate for live trading
  - [ ] Allocation sums to 1.0
  - [ ] Drift threshold reasonable (10%)
  - [ ] Risk limits set (5% daily loss, 30% drawdown)
- [ ] **API keys verified:** Live trading keys (not paper keys) in `.env`
- [ ] **Email notifications configured:** User email in `.notification_config`
- [ ] **AutoPilot scheduled:** Cron/launchd running daily at appropriate time
- [ ] **.gitignore includes .env:** Secrets not committed to git
- [ ] **Transaction logs readable:** User understands how to review logs

**Validation:** Review config.yaml, verify live API keys, test email notification

---

### 🎯 Final Validation Tests

**Run these tests immediately before enabling live trading:**

1. **Dry Run Rebalance:**
   ```bash
   python dalio_lite.py --dry-run
   ```
   - [ ] Completes without errors
   - [ ] Shows rebalance plan
   - [ ] Logs to file
   - [ ] Metrics collected

2. **Health Check:**
   ```bash
   python -c "from health_check import health; print(health.check_all())"
   ```
   - [ ] Returns "healthy" status
   - [ ] All checks passing

3. **Backup Restore:**
   ```bash
   # Create backup, delete state, restore
   python -c "from backup_manager import BackupManager; bm = BackupManager(); bm.restore_from_backup('state/last_rebalance.json'); print('OK')"
   ```
   - [ ] Restore succeeds
   - [ ] State file restored correctly

4. **Lock Test:**
   ```bash
   # Start process holding lock, try to acquire in another terminal
   python -c "from state_lock import StateLockManager; lock = StateLockManager(); lock.acquire(); import time; time.sleep(60)"
   # In another terminal: try to acquire lock
   ```
   - [ ] Second process waits (or times out)
   - [ ] First process exit releases lock

5. **Full System Test (Paper Trading):**
   - [ ] Run AutoPilot: `python dalio_lite.py`
   - [ ] Open Dashboard: `streamlit run dashboard.py`
   - [ ] Trigger manual rebalance from dashboard
   - [ ] All operations complete successfully
   - [ ] Metrics updated
   - [ ] Transaction logged
   - [ ] Backup created

---

## FINAL GO/NO-GO DECISION

**Count the checkboxes:**

- **Total items:** ~80
- **Required for live trading:** 100% (all items checked)
- **Partial completion:** Return to paper trading, complete remaining items

**Decision Matrix:**

| Completion | Decision | Action |
|------------|----------|--------|
| 100% (80/80) | ✅ GO | Enable live trading with $1K account (Phase 4 Tier 1) |
| 95-99% (76-79/80) | ⚠️ REVIEW | Assess missing items, decide if acceptable risk |
| <95% (<76/80) | 🛑 NO-GO | Complete remaining items, re-validate |

---

## Post-Live Trading Monitoring

**After enabling live trading, monitor for 7 days:**

- [ ] **Day 1:** Check every 4 hours
  - [ ] Portfolio value as expected
  - [ ] No unauthorized trades
  - [ ] Logs look normal
  - [ ] Health checks green

- [ ] **Days 2-7:** Check daily
  - [ ] Rebalancing working (if triggered)
  - [ ] No errors in logs
  - [ ] Metrics stable
  - [ ] User satisfied

- [ ] **Week 2+:** Check weekly
  - [ ] Performance tracking vs benchmarks
  - [ ] Cost analysis (transaction fees)
  - [ ] System reliability (uptime)

---

## Emergency Contacts & Procedures

**If something goes wrong after enabling live trading:**

1. **Disable live trading immediately:**
   ```bash
   # Edit config.yaml: paper_trading: true
   # Restart system
   ```

2. **Stop AutoPilot:**
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.daliolite.autopilot.plist  # macOS
   ```

3. **Review transaction logs:**
   ```bash
   ls -lh state/transactions/
   # Open most recent transaction log
   ```

4. **Check Alpaca dashboard:**
   - Log in to https://alpaca.markets
   - Review recent orders
   - Cancel any pending orders if needed

5. **Notify user via email**

---

## Sign-Off

**Before enabling live trading, complete this sign-off:**

**Date:** _______________

**System Tested By:** _______________

**Checklist Completion:** _______ / 80 items (must be 80/80)

**Paper Trading Duration:** _______ days (must be ≥30)

**Critical Errors in Paper Trading:** _______ (must be 0)

**Decision:** ☐ GO  ☐ NO-GO

**Approved By:** _______________

**Live Trading Enabled:** ☐ Yes  ☐ No

**Notes:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

**Status:** Ready to use as production gate
**Usage:** Complete this checklist before setting `paper_trading: false`
