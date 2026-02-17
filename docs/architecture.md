# Architecture Documentation

**Last Updated:** 2026-02-16T21:15:00Z
**AI-Parseable:** Yes
**System:** Dalio Lite - Automated All Weather Portfolio System

---

## 🤖 AI Architecture Summary

**Architecture Style:** Monolithic Python application with external API integration
**Deployment Model:** Single-user, local execution (cron/manual)
**Scale:** Small (single user, $10K-50K portfolio)
**Components:** 4 main components (CLI, Core Logic, Broker API, Storage)
**External Dependencies:** 1 critical (Alpaca API)
**Data Flow:** Synchronous, request-response
**Bottlenecks:** None detected (appropriate for scale)
**Scaling Readiness:** 2/10 (designed for single-user, not multi-user)

---

## System Overview

**Purpose:** Automate Ray Dalio's "All Weather" portfolio strategy for small accounts

**High-Level Flow:**
1. User/cron invokes `dalio_lite.py` daily
2. System checks current portfolio allocation via Alpaca API
3. Calculates drift from target allocation (40% VTI, 30% TLT, 20% GLD, 10% DBC)
4. If drift >10%, executes rebalancing orders
5. Logs all actions and updates state files

**Design Philosophy:**
- Simple > Complex
- Config-driven (zero hardcoded values)
- Safety-first (paper trading default, circuit breakers)
- Educational (learning tool, not production trading system)

---

## Component Architecture

### 1. CLI / User Interface [SCALE: Low, BOTTLENECK: None]
- **Technology:** Python command-line script
- **Entry Point:** `dalio_lite.py:main()`
- **Commands:**
  - `python dalio_lite.py` - Daily check
  - `python dalio_lite.py --dry-run` - Calculate only
  - `python dalio_lite.py --report` - Generate performance report
- **Invocation:** Manual or cron job (scheduled daily)
- **Bottleneck:** None (human/cron rate-limited)
- **AI Tags:** `#cli`, `#user-interface`

---

### 2. Core Logic / DalioLite Class [SCALE: Medium, BOTTLENECK: None]
- **Technology:** Python class (object-oriented)
- **Location:** `dalio_lite.py:36-430`
- **Responsibilities:**
  - **Configuration Management:** Load and validate `config.yaml`
  - **Broker Connection:** Initialize Alpaca API client
  - **State Management:** Track last rebalance timestamp
  - **Portfolio Analysis:** Calculate current positions and drift
  - **Decision Logic:** Determine if rebalancing needed
  - **Risk Management:** Check circuit breakers
  - **Order Execution:** Place buy/sell orders
  - **Logging:** Comprehensive action logging

**Sub-components:**
- **Config Loader:** Parses YAML, validates allocation sums to 100%
- **Broker Client:** Alpaca SDK wrapper with paper/live mode toggle
- **Drift Calculator:** Math engine comparing current vs target allocation
- **Rebalance Engine:** Order sequencing (sells first, then buys)
- **Circuit Breakers:** Safety checks (5% daily loss, 30% drawdown)

**Complexity:** 🟡 Medium (8/10 average cyclomatic complexity)
**Bottleneck:** None (executes in <5 seconds typically)
**AI Tags:** `#core-logic`, `#portfolio-management`

---

### 3. External Services [DEPENDENCIES: 3rd party]

#### Alpaca Trading API [CRITICAL DEPENDENCY]
- **Purpose:** Trading execution + market data + account management
- **Endpoints Used:**
  - `GET /v2/account` - Account balance and equity
  - `GET /v2/positions` - Current portfolio positions
  - `GET /v2/stocks/quotes/latest` - Real-time quote data
  - `POST /v2/orders` - Submit buy/sell orders
- **Authentication:** API Key + Secret (stored in `.env`)
- **Rate Limits:**
  - 🟢 **Paper Trading:** 200 requests/minute
  - 🟡 **Live Trading:** 200 requests/minute (shared across account)
- **SLA:** 99.9% uptime
- **Response Time:** Typical <100ms
- **Circuit Breaker:** ❌ Not implemented (relies on Alpaca SDK)
- **Retry Logic:** ❌ Not explicit (Alpaca SDK handles internally)
- **Fallback:** ❌ None (system fails if Alpaca down)
- **Status:** 🟢 Healthy (well-maintained API, stable)
- **AI Tags:** `#external-api`, `#alpaca`, `#broker`, `#critical`

---

### 4. Storage Layer [SCALE: Low, BOTTLENECK: None]

#### Configuration Storage
- **Technology:** YAML file (`config.yaml`)
- **Purpose:** All system settings (allocation, thresholds, risk limits)
- **Location:** `/config.yaml` (64 lines)
- **Mutability:** User-editable (manual changes)
- **Validation:** Checked on startup (allocation sums to 100%)
- **AI Tags:** `#config`, `#yaml`

#### State Storage
- **Technology:** JSON files
- **Purpose:** Track last rebalance timestamp
- **Location:** `/state/last_rebalance.json`
- **Format:** `{"timestamp": "2026-02-16T10:30:00"}`
- **Persistence:** Written after each rebalance
- **Mutability:** System-managed (never manually edited)
- **Bottleneck:** None (tiny files, filesystem I/O <1ms)
- **AI Tags:** `#state`, `#json`, `#persistence`

#### Logging Storage
- **Technology:** Text log files
- **Purpose:** Audit trail of all system actions
- **Location:** `/logs/dalio_lite.log`
- **Format:** `YYYY-MM-DD HH:MM:SS | LEVEL | Message`
- **Rotation:** Manual (not auto-rotated)
- **Size:** Grows ~1KB per day (low volume)
- **Bottleneck:** None (asynchronous file I/O)
- **AI Tags:** `#logging`, `#audit-trail`

#### Reporting Storage
- **Technology:** JSON files
- **Purpose:** Daily performance snapshots
- **Location:** `/reports/report_YYYYMMDD.json`
- **Format:** Portfolio value, positions, benchmark data
- **Retention:** Manual cleanup (no auto-deletion)
- **AI Tags:** `#reporting`, `#performance`

---

## Data Flow

### Daily Workflow (Typical Execution)

```
1. [USER/CRON] → [CLI] → [dalio_lite.py:main()]
2. [Core Logic] → Load config.yaml
3. [Core Logic] → Load state/last_rebalance.json
4. [Core Logic] → Connect to Alpaca API
5. [Core Logic] ← [Alpaca API] Fetch account balance
6. [Core Logic] ← [Alpaca API] Fetch current positions
7. [Core Logic] → Calculate drift (current % vs target %)
8. [Core Logic] → Check: Drift >10%? AND Days since last rebalance >30?
9a. IF NO → Log "No rebalancing needed" → END
9b. IF YES → Continue to step 10
10. [Core Logic] → Check circuit breakers (daily loss <5%, total drawdown <30%)
11a. IF BREAKER TRIGGERED → Log warning, halt → END
11b. IF BREAKERS CLEAR → Continue to step 12
12. [Core Logic] → Calculate order amounts ($ to buy/sell each ETF)
13. [Core Logic] → [Alpaca API] Fetch latest quotes for pricing
14. [Core Logic] → [Alpaca API] Submit SELL orders (to free up cash)
15. [Core Logic] ← [Alpaca API] Order confirmations
16. [Core Logic] → [Alpaca API] Submit BUY orders
17. [Core Logic] ← [Alpaca API] Order confirmations
18. [Core Logic] → Update state/last_rebalance.json with timestamp
19. [Core Logic] → Write to logs/dalio_lite.log
20. [Core Logic] → END
```

**Estimated Total Time:** 3-8 seconds
- Config load: <10ms
- API calls: 2-5 seconds (network latency)
- Logic/math: <100ms
- File I/O: <10ms

**AI Tags:** `#data-flow`, `#workflow`, `#synchronous`

---

## Integration Points

### Alpaca Trading API Integration
- **Protocol:** HTTPS REST API
- **SDK:** alpaca-py (official Python SDK)
- **Authentication:** API Key + Secret (passed via headers)
- **Base URL:**
  - Paper: `https://paper-api.alpaca.markets`
  - Live: `https://api.alpaca.markets`
- **Data Format:** JSON request/response
- **Error Handling:** Try/except with logging
- **Timeout:** Not explicitly set (relies on SDK defaults ~30s)
- **Connection Pooling:** Managed by SDK
- **AI Tags:** `#integration`, `#rest-api`, `#alpaca`

---

## Failure Modes & Mitigation

### 1. Alpaca API Down [Impact: High]
- **Symptom:** Connection timeout or HTTP 500 errors
- **Current Mitigation:** ❌ None (system fails loudly, logs error)
- **Impact:** Cannot rebalance that day
- **Recovery:** Retry next day (manual restart)
- **Recommended Enhancement:** Add circuit breaker + exponential backoff retry
- **AI Tags:** `#failure-mode`, `#api-downtime`

### 2. Invalid API Keys [Impact: High]
- **Symptom:** HTTP 401 Unauthorized
- **Current Mitigation:** Error message on startup, system exits
- **Impact:** Cannot run at all
- **Recovery:** User must fix `.env` file
- **Prevention:** Clear error message with troubleshooting steps
- **AI Tags:** `#failure-mode`, `#auth-failure`

### 3. Configuration Error [Impact: High]
- **Symptom:** Allocation doesn't sum to 100%
- **Current Mitigation:** ✅ Validation on startup, ValueError raised
- **Impact:** System exits before trading
- **Recovery:** User must fix `config.yaml`
- **Prevention:** Excellent (validates before any trading)
- **AI Tags:** `#failure-mode`, `#config-error`

### 4. State File Corrupted [Impact: Low]
- **Symptom:** JSON parse error
- **Current Mitigation:** ❌ None (system crashes)
- **Impact:** Cannot determine last rebalance date
- **Recovery:** Delete `state/last_rebalance.json`, system treats as first run
- **Recommended Enhancement:** Try/except with fallback to "no previous rebalance"
- **AI Tags:** `#failure-mode`, `#state-corruption`

### 5. Insufficient Buying Power [Impact: Medium]
- **Symptom:** Alpaca rejects order (insufficient funds)
- **Current Mitigation:** ❌ Order fails, logged, continues to next order
- **Impact:** Partial rebalancing (some orders succeed, others fail)
- **Recovery:** Manual review, may need to adjust allocations
- **Recommended Enhancement:** Pre-check cash balance before submitting orders
- **AI Tags:** `#failure-mode`, `#insufficient-funds`

### 6. Circuit Breaker Triggered [Impact: Low - By Design]
- **Symptom:** Portfolio down >5% in one day or >30% total
- **Current Mitigation:** ✅ System halts rebalancing, logs warning
- **Impact:** No rebalancing until manual review
- **Recovery:** User reviews situation, manually resets if appropriate
- **Prevention:** This IS the safety feature (working as intended)
- **AI Tags:** `#failure-mode`, `#circuit-breaker`, `#safety`

---

## 🤖 AI Architecture Analysis

### Component Complexity Scores
- **CLI:** 1/10 (Minimal - just argument parsing)
- **Core Logic:** 5/10 (Medium - rebalancing logic, state management)
- **Alpaca Integration:** 3/10 (Low - SDK abstracts complexity)
- **Storage:** 1/10 (Trivial - filesystem read/write)

**Overall System Complexity:** 3/10 (Low - intentionally simple)

---

### Bottleneck Indicators

**No critical bottlenecks detected.**

Current scale (single user, daily execution) is far below any component limits:
- 🟢 **CLI:** Human-triggered, no scale concerns
- 🟢 **Core Logic:** Executes in <1 second, no CPU/memory issues
- 🟢 **Alpaca API:** 200 req/min limit, system makes ~5-10 req/day
- 🟢 **Storage:** Filesystem I/O <10ms, negligible

**Headroom Analysis:**
- API Rate Limit Headroom: 99.5% unused (5 calls/day vs 200/min capacity)
- Execution Time Headroom: 99.9% unused (<5s execution vs daily cadence)
- Storage Headroom: Unlimited (text files grow ~1KB/day)

**AI Tags:** `#bottleneck`, `#performance`, `#headroom`

---

### Scale Readiness Score: 2/10 (Not Designed for Scale)

**Current Design Is Correct for Intended Use.**

**Why Low Score:**
- Single-user design (no multi-tenancy)
- File-based state (not concurrent-safe)
- No rate limiting (assumes single instance)
- Synchronous execution (blocking)

**If Scaling to Multi-User Would Need:**
1. Database for state/config (PostgreSQL/MongoDB)
2. Job queue for rebalancing (Celery/RabbitMQ)
3. User authentication & authorization
4. API rate limiting per user
5. Horizontal scaling (multiple workers)
6. Observability (metrics, tracing)

**Estimated Effort to Scale:** 4-6 weeks

**Recommendation:** ❌ Do NOT scale. Current design is perfect for intended single-user, educational use case.

**AI Tags:** `#scale`, `#single-user`, `#not-for-scale`

---

### Concerns & Recommendations

#### 🟡 MEDIUM PRIORITY

**1. No Circuit Breaker for Alpaca API**
- **Problem:** If Alpaca API is degraded (slow responses, intermittent failures), system keeps retrying
- **Impact:** Wasted time, potential duplicate orders
- **Solution:** Implement circuit breaker pattern (e.g., tenacity library)
- **Effort:** 4 hours
- **AI Tags:** `#circuit-breaker`, `#reliability`

**2. No Retry Logic for Transient Failures**
- **Problem:** Single network blip = failed rebalance
- **Impact:** Missed rebalancing opportunities
- **Solution:** Exponential backoff retry (3 attempts with 2^n delays)
- **Effort:** 2 hours
- **AI Tags:** `#retry`, `#reliability`

#### 🟢 LOW PRIORITY (Nice-to-Have)

**3. No Monitoring/Alerting**
- **Problem:** User must manually check logs for issues
- **Impact:** Delayed awareness of problems
- **Solution:** Add Telegram/email notifications for failures
- **Effort:** 2 hours (Telegram bot integration)
- **AI Tags:** `#monitoring`, `#alerts`

**4. State File Not Transactional**
- **Problem:** If system crashes while writing state file, could corrupt
- **Impact:** Very low probability, easy recovery (delete file)
- **Solution:** Atomic write (write to temp file, then rename)
- **Effort:** 1 hour
- **AI Tags:** `#atomicity`, `#reliability`

---

## Deployment Architecture

### Current Deployment Model

```
┌─────────────────────────────────────────┐
│   User's Local Machine (macOS/Linux)   │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Python 3.11+ Runtime Environment │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │   dalio_lite.py             │ │ │
│  │  │   (Main Application)        │ │ │
│  │  └─────────────────────────────┘ │ │
│  │                                   │ │
│  │  ┌─────────────────────────────┐ │ │
│  │  │   File System Storage       │ │ │
│  │  │   - config.yaml             │ │ │
│  │  │   - state/                  │ │ │
│  │  │   - logs/                   │ │ │
│  │  │   - reports/                │ │ │
│  │  └─────────────────────────────┘ │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   Cron Job (Optional)             │ │
│  │   Daily: 10:30 AM ET              │ │
│  │   Command: python dalio_lite.py   │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
                    │
                    │ HTTPS
                    ↓
        ┌─────────────────────────┐
        │   Alpaca API (Cloud)    │
        │   - paper-api (default) │
        │   - api.alpaca.markets  │
        └─────────────────────────┘
```

**Deployment Characteristics:**
- **Environment:** Local laptop/desktop
- **Runtime:** Python 3.11+ (user's install)
- **Execution:** Manual or cron-scheduled
- **Networking:** Outbound HTTPS only (no inbound connections)
- **Security:** API keys in `.env` file (not in code/git)
- **Backups:** Manual (user should backup config.yaml periodically)
- **Updates:** Manual (git pull or download new version)

**AI Tags:** `#deployment`, `#local`, `#cron`

---

## Security Architecture

### Secrets Management
- **API Keys:** Stored in `.env` file (git-ignored)
- **Environment Variables:** Loaded via Python `os.getenv()`
- **Never Logged:** API keys NEVER appear in logs
- **Rotation:** Manual (user must update `.env` and restart)
- **Access Control:** File system permissions (user's account only)

### Attack Surface
- **Minimal:** No server, no open ports, no web interface
- **Local Only:** All code runs locally on user's machine
- **Outbound Only:** Only makes HTTPS requests to Alpaca API
- **No User Input:** Config is YAML (no injection risk if user controls files)

### Risks
- 🟢 **Low Risk:** User's machine compromised → attacker could access `.env` keys
- 🟢 **Low Risk:** Malicious config.yaml → would fail validation or cause errors
- 🟢 **Low Risk:** API key leaked → user must rotate via Alpaca dashboard

**Overall Security Posture:** 🟢 Good (appropriate for single-user, local system)

**AI Tags:** `#security`, `#secrets`, `#attack-surface`

---

## 🤖 Metadata for AI Agents

```json
{
  "architecture": {
    "style": "monolithic",
    "deployment": "local-single-user",
    "scale": "small",
    "complexity": 3
  },
  "components": {
    "count": 4,
    "cli": {"complexity": 1, "bottleneck": false},
    "core_logic": {"complexity": 5, "bottleneck": false},
    "external_apis": {"count": 1, "critical": true},
    "storage": {"type": "filesystem", "bottleneck": false}
  },
  "bottlenecks": {
    "detected": 0,
    "critical": 0,
    "warnings": 0
  },
  "scale_readiness": {
    "score": 2,
    "designed_for_multi_user": false,
    "horizontal_scalability": "not-applicable"
  },
  "dependencies": {
    "external_apis": 1,
    "critical_services": ["alpaca"],
    "fallback_options": 0
  },
  "failure_modes": {
    "high_impact": 2,
    "medium_impact": 1,
    "low_impact": 3,
    "mitigations_in_place": 2
  }
}
```

---

**🎯 Architecture Summary:** Simple, monolithic Python application with external API integration. Appropriate complexity for single-user, educational portfolio automation. No scaling concerns for intended use case.
