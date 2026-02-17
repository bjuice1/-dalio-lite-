# BUILD MANIFEST: Dalio Lite Production Hardening

**Project:** Dalio Lite - Automated Ray Dalio All Weather Portfolio Manager
**Date:** 2026-02-17
**Complexity:** HIGH
**Status:** Specifications Complete - Ready for Implementation

---

## Executive Summary

This build manifest defines the complete production hardening plan for Dalio Lite, transforming it from an educational paper trading system into a production-ready automated investment platform suitable for live trading.

**Current State:**
- 3,353 lines of functional code
- Works well for paper trading and learning
- Zero test coverage
- No concurrency protection
- Missing production observability

**Target State:**
- Production-grade reliability (99%+ uptime)
- Comprehensive test coverage (80%+)
- Race condition prevention
- Full observability and monitoring
- Disaster recovery capability

**Estimated Implementation Time:** 5 days (40 hours)
**Confidence Level:** HIGH

---

## Document Index

1. **[01-testing-infrastructure.md](01-testing-infrastructure.md)** — Complete test suite architecture
   - Purpose: Add zero-to-hero testing (unit + integration tests)
   - Scope: pytest framework, mock Alpaca API, 80%+ coverage target
   - Estimated: 8 hours

2. **[02-concurrency-control.md](02-concurrency-control.md)** — File locking and state synchronization
   - Purpose: Prevent AutoPilot + Dashboard race conditions
   - Scope: StateLockManager, filelock library, atomic state writes
   - Estimated: 4 hours

3. **[03-error-handling-recovery.md](03-error-handling-recovery.md)** — Rollback patterns and retry logic
   - Purpose: Detect and recover from partial rebalance failures
   - Scope: Enhanced order execution, retry with backoff, transaction logging
   - Estimated: 6 hours

4. **[04-observability-monitoring.md](04-observability-monitoring.md)** — Metrics and health checks
   - Purpose: Make system operations visible (no more flying blind)
   - Scope: MetricsCollector, health checks, monitoring dashboard page
   - Estimated: 6 hours

5. **[05-backup-disaster-recovery.md](05-backup-disaster-recovery.md)** — State file backup and recovery
   - Purpose: Prevent data loss from state file corruption
   - Scope: BackupManager, local backups with checksums, cloud backup (optional)
   - Estimated: 4 hours

6. **[06-migration-rollout.md](06-migration-rollout.md)** — Phased deployment strategy
   - Purpose: Safe migration path from current to production state
   - Scope: 4-phase rollout, validation gates, 30-day paper trading
   - Estimated: 3 hours (documentation, not code)

7. **[07-production-checklist.md](07-production-checklist.md)** — Pre-live-trading validation
   - Purpose: Gate-keeper for enabling live trading
   - Scope: 80-item checklist, go/no-go decision framework
   - Estimated: 1 hour (documentation, validation process)

---

## Execution Order

### Phase 1: Foundational Infrastructure (Week 1)

**Parallel Track A (Day 1-2):**
1. Implement 01-testing-infrastructure.md (8 hours)
   - Install pytest framework
   - Write unit tests for core logic
   - Write integration tests with mocked Alpaca API
   - Achieve 80%+ coverage

**Parallel Track B (Day 1-2):**
2. Implement 02-concurrency-control.md (4 hours)
   - Create StateLockManager class
   - Integrate with DalioLite
   - Test concurrent execution scenarios

**Day 3:**
3. Implement 03-error-handling-recovery.md (6 hours)
   - Enhance order execution with OrderResult
   - Add retry logic with backoff
   - Implement transaction logging

**Day 4:**
4. Implement 04-observability-monitoring.md (6 hours)
   - Create MetricsCollector
   - Instrument all operations
   - Build monitoring dashboard page

**Day 5:**
5. Implement 05-backup-disaster-recovery.md (4 hours)
   - Create BackupManager
   - Integrate automatic backups
   - Test restore procedure

**Total: Week 1 (40 hours)**

---

### Phase 2: Validation & Testing (Week 2)

**Day 6-7:**
- Run complete test suite
- Fix any failing tests
- Manual validation of all features
- Document any deviations from specs

**Day 8-12:**
- Deploy to paper trading environment
- Monitor for issues
- Fix any bugs found

---

### Phase 3: Extended Paper Trading (Weeks 3-7)

**Duration:** 30 consecutive days
**Activity:** Run system in paper trading with full monitoring
**Gate:** Zero critical errors, all health checks green

---

### Phase 4: Live Trading Rollout (Weeks 8-12+)

**Week 8:** $1K live account
**Weeks 9-11:** $5K live account
**Month 3+:** Full account ($10-50K)

---

## Critical Path

**Longest Sequential Dependency Chain:**

```
01-testing-infrastructure (8h)
  ↓
03-error-handling-recovery (6h)
  ↓
04-observability-monitoring (6h)
  ↓
06-migration-rollout (3h)
  ↓
07-production-checklist (1h)

Total Critical Path: 24 hours (3 days)
```

**Parallel work saves 2 days:**
- 02-concurrency (4h) runs parallel with 01-testing
- 05-backup (4h) runs parallel with 03-error-handling
- **Net time: 3 days with parallelization**

---

## Tech Stack

### Core Technologies (No Changes)
- **Language:** Python 3.11+
- **Framework:** Streamlit (dashboard)
- **Broker:** Alpaca Trading API (alpaca-py SDK)
- **State:** File-based JSON

### New Dependencies (Production Hardening)
- **Testing:** pytest, pytest-cov, pytest-mock, responses
- **Concurrency:** filelock (cross-platform file locking)
- **Cloud Backup (Optional):** boto3 (AWS S3)
- **Observability:** No new dependencies (file-based metrics)

### Rationale
- Minimal new dependencies (only filelock is critical)
- All dependencies are mature, well-maintained libraries
- No architectural changes (still file-based, single-machine)
- Backward compatible (existing users not disrupted)

---

## Validation Checklist

Before starting implementation, validate:

- [x] audit1 findings documented and understood
- [x] audit2 plan reviewed and approved
- [x] All 7 specification documents complete
- [x] Dependency chain mapped
- [x] Parallel work identified
- [ ] Development environment ready (Python 3.11+, virtualenv)
- [ ] Alpaca paper trading account active
- [ ] Git repository initialized
- [ ] Baseline commit tagged (rollback point)

**Before proceeding, confirm all boxes checked.**

---

## Risk Register

| Risk | Probability | Impact | Mitigation | Status |
|------|-------------|--------|------------|--------|
| Tests reveal bugs in existing code | High | Medium | Fix bugs as found, don't skip testing | Accepted |
| filelock incompatible on Windows | Low | Low | Dalio Lite is macOS/Linux only | Accepted |
| API rate limits hit during testing | Medium | Low | Use mock API for most tests | Mitigated |
| 30-day validation too long | Low | Low | Can reduce to 14 days if no errors | Acceptable |
| User impatient for live trading | Medium | Medium | Clear communication, show progress | Manageable |

---

## Open Questions

**None remaining.** All design decisions documented in specifications with default choices.

If questions arise during implementation:
1. Check relevant specification document first
2. If not covered, make pragmatic decision and document
3. Update specification for future reference

---

## Rollback Criteria

Abandon implementation and return to audit1 if:

1. **Core assumption invalidated:**
   - filelock doesn't work on target platform
   - Alpaca API fundamentally incompatible with testing approach
   - Performance degradation >50ms per operation

2. **Implementation time exceeds 2x estimate:**
   - 5 days estimated → abort if not complete by day 10
   - Indicates misunderstanding of complexity

3. **Tests reveal critical design flaw:**
   - Race condition unfixable with file locks
   - State corruption unavoidable
   - Requires architectural redesign (database instead of files)

**Rollback Action:**
- Tag current state: `git tag failed-implementation-attempt`
- Return to audit1 with new findings
- Redesign approach

**Likelihood:** LOW (all assumptions pre-validated)

---

## Scope Estimate

### By Component:

| Component | Estimated Time | Confidence |
|-----------|---------------|------------|
| 01 Testing Infrastructure | 8 hours | High |
| 02 Concurrency Control | 4 hours | High |
| 03 Error Handling | 6 hours | Medium (Alpaca API quirks) |
| 04 Observability | 6 hours | High |
| 05 Backup/Recovery | 4 hours | High |
| 06 Migration Docs | 3 hours | High |
| 07 Checklist | 1 hour | High |
| **Total Implementation** | **32 hours** | **High** |
| Testing & Debugging | +8 hours | Medium |
| **Total with Buffer** | **40 hours (5 days)** | **High** |

### Confidence Breakdown:
- **High confidence (80%):** Well-understood Python patterns, clear specs
- **Medium confidence (20%):** Alpaca API behavior under error conditions
- **Buffer included:** 25% time buffer for unknowns

---

## Success Metrics

### Immediate (After Implementation)
- ✅ All 80 items in production checklist complete
- ✅ Test coverage ≥80%
- ✅ Zero test failures
- ✅ All specifications implemented

### Short-term (30 Days Paper Trading)
- ✅ Zero double rebalancing incidents
- ✅ Zero undetected partial failures
- ✅ Health checks green 95%+ of time
- ✅ User confidence high

### Long-term (3 Months Live Trading)
- ✅ System running reliably with live money
- ✅ Rebalance success rate >95%
- ✅ Order execution success rate >98%
- ✅ Zero critical bugs in production
- ✅ User satisfaction (portfolio performing as expected)

---

## Next Steps

### Immediate Actions:
1. ✅ Review and approve this BUILD MANIFEST
2. ✅ Ensure development environment ready
3. ✅ Tag baseline commit: `git tag pre-hardening-baseline`
4. ✅ Create feature branch: `git checkout -b production-hardening`
5. Begin implementation following execution order

### Implementation Strategy:
- **Incremental:** Implement one specification at a time
- **Test-driven:** Write tests before implementation (where applicable)
- **Commit frequently:** Small, logical commits for easy rollback
- **Document deviations:** If specs change during implementation, update docs

### Daily Standup Questions:
1. What did I implement yesterday?
2. What am I implementing today?
3. Any blockers or spec ambiguities?
4. Any deviations from plan?

---

## Source of Truth

**This BUILD MANIFEST is the master reference for:**
- Implementation order
- Time estimates
- Success criteria
- Risk mitigation

**If conflict arises:**
1. BUILD MANIFEST overrides individual specifications
2. Specifications override audit2 plan
3. audit2 plan overrides audit1 findings
4. audit1 findings are immutable (historical record)

---

## Final Checklist Before Starting

- [ ] BUILD MANIFEST reviewed and understood
- [ ] All 7 specifications read
- [ ] Development environment ready
- [ ] Baseline commit tagged
- [ ] Feature branch created
- [ ] Time allocated (5 consecutive days preferred)
- [ ] User informed of timeline
- [ ] Rollback plan understood

**Status: ✅ READY TO BUILD**

---

**Document Count:** 8 (7 specifications + 1 manifest)
**Total Pages:** ~150 pages of specifications
**Total Estimated Scope:** 40 hours (5 days)
**Next Step:** Begin implementation with Document 01 (testing infrastructure)

**For questions or clarifications, reference:**
- Technical details → Individual specification documents
- Timeline/ordering → This BUILD MANIFEST
- Original findings → audit1 report in conversation history
- Architecture decisions → audit2 plan in conversation history

---

**🎯 The system is fully specified and ready to build.**

Use these documents as your source of truth for implementation.
