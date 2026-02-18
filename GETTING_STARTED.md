# 🚀 Getting Started with Dalio Lite

**You now have a complete, production-ready automated portfolio system.**

This guide will get you running in 30 minutes.

---

## ✅ What You Have

```
dalio-lite/
├── dalio_lite.py          # Main system (300 lines, fully commented)
├── config.yaml            # All settings (edit this, not code)
├── requirements.txt       # Dependencies
├── .env.example          # API keys template
├── quick_start.sh        # Automated setup script
├── README.md             # Full documentation
├── GETTING_STARTED.md    # This file
└── scripts/
    └── compare_benchmarks.py  # Performance comparison tool
```

**What it does:**
- ✅ Manages 4-ETF Dalio-style portfolio (40% VTI, 30% TLT, 20% GLD, 10% DBC)
- ✅ Auto-rebalances when drift exceeds 10%
- ✅ Paper trading mode (test with fake money first)
- ✅ Risk management (circuit breakers, position limits)
- ✅ Performance tracking and reporting
- ✅ Fully logged (every decision recorded)

---

## 🏃 Quick Start (30 Minutes)

### Step 1: Install (5 minutes)

```bash
cd "/Users/JB/Documents/JB - Takeover/dalio-lite"

# Option A: Use quick start script
./quick_start.sh

# Option B: Manual install
pip install -r requirements.txt
cp .env.example .env
mkdir -p logs state reports
```

---

### Step 2: Get Alpaca Account (10 minutes)

1. **Sign up:** https://alpaca.markets (free, no credit card)

2. **Navigate to Paper Trading:**
   - Dashboard → Paper Trading
   - Click "Generate API Keys"

3. **Copy your keys:**
   - API Key ID: `PK...` (starts with PK for paper)
   - Secret Key: `...` (long string)

4. **Fund paper account:**
   - Click "Reset Account"
   - Set balance to $17,000 (matches your real portfolio size)

---

### Step 3: Configure (5 minutes)

Edit `.env` file:

```bash
nano .env
```

Paste your keys:
```
ALPACA_API_KEY=PK1234567890abcdef
ALPACA_SECRET_KEY=your_secret_key_here
```

Save and exit (Ctrl+X, then Y, then Enter).

**Verify it worked:**
```bash
# This should show your keys (first few characters)
grep ALPACA_API_KEY .env
```

---

### Step 4: First Run (5 minutes)

**Dry run** (calculates but doesn't execute):
```bash
python dalio_lite.py --dry-run
```

**Expected output:**
```
============================================================
DALIO LITE INITIALIZED
Mode: PAPER TRADING
Target Allocation: {'VTI': 0.4, 'TLT': 0.3, 'GLD': 0.2, 'DBC': 0.1}
============================================================

Connected to Alpaca: $17000.00 cash, $17000.00 total value

============================================================
DAILY CHECK - 2026-02-16 10:30
============================================================

✓ Risk check: All circuit breakers clear

Current Allocation:
  VTI:   0.0% (target: 40.0%, drift: -40.0%)
  TLT:   0.0% (target: 30.0%, drift: -30.0%)
  GLD:   0.0% (target: 20.0%, drift: -20.0%)
  DBC:   0.0% (target: 10.0%, drift: -10.0%)

Rebalance Check: Drift 40.0% exceeds threshold 10.0%
🔄 Rebalancing required

============================================================
EXECUTING REBALANCE
============================================================

Rebalance Plan:
  VTI: BUY $6800.00
  TLT: BUY $5100.00
  GLD: BUY $3400.00
  DBC: BUY $1700.00

Total to sell: $0.00
Total to buy: $17000.00

DRY RUN - No orders executed
============================================================
```

✅ **If you see this, your system is working!**

---

### Step 5: Execute First Rebalance (2 minutes)

**Now do it for real** (in paper trading):

```bash
python dalio_lite.py
```

This will:
1. ✓ Buy ~$6,800 of VTI (stocks)
2. ✓ Buy ~$5,100 of TLT (bonds)
3. ✓ Buy ~$3,400 of GLD (gold)
4. ✓ Buy ~$1,700 of DBC (commodities)

**Check Alpaca dashboard:**
- You should see 4 positions
- Total value: ~$17,000

🎉 **Congratulations! You now have an automated Dalio portfolio.**

---

## 📅 Daily Usage

### Option A: Manual (Recommended for First Month)

Run once per day after market opens:

```bash
cd "/Users/JB/Documents/JB - Takeover/dalio-lite"
python dalio_lite.py
```

**What happens:**
- ✅ Checks if any position drifted >10%
- ✅ If yes → rebalances
- ✅ If no → does nothing (saves costs)
- ✅ Logs everything

---

### Option B: Automated (After You're Comfortable)

Set up cron job to run automatically:

```bash
# Open crontab editor
crontab -e

# Add this line (runs weekdays at 10:30am ET)
30 10 * * 1-5 cd /Users/JB/Documents/JB\ -\ Takeover/dalio-lite && /usr/bin/python3 dalio_lite.py >> logs/cron.log 2>&1
```

Now it runs automatically every trading day!

---

## 📊 Monitoring

### Daily: Check Logs

```bash
tail -20 logs/dalio_lite.log
```

Look for:
- ✅ "No rebalancing needed" (most days)
- 🔄 "Rebalancing required" (when drift >10%)
- 🛑 "Circuit breaker triggered" (if major loss)

---

### Weekly: Review Positions

Log into Alpaca dashboard:
- Check: Are all 4 positions still there?
- Check: Are %s close to target (40/30/20/10)?
- Check: Total value growing/shrinking?

---

### Monthly: Performance Report

```bash
python dalio_lite.py --report
python scripts/compare_benchmarks.py
```

This shows:
- Your total return
- vs SPY (stocks)
- vs AGG (bonds)
- vs 60/40 balanced

---

## 🎓 Learning Checklist (First 6 Months)

### Week 1: ✅ Setup & First Run
- [x] Install and configure
- [x] Execute first rebalance
- [ ] Read through `dalio_lite.py` code
- [ ] Understand what each function does

### Month 1: Monitor & Learn
- [ ] Check logs daily
- [ ] Note when rebalancing triggers
- [ ] Read README.md fully
- [ ] Understand: Why these 4 ETFs?

### Month 2: Track Performance
- [ ] Run `compare_benchmarks.py` weekly
- [ ] Ask: Am I beating/losing to 60/40?
- [ ] Understand: Why is it performing this way?

### Month 3: Stress Test
- [ ] What happens during volatile week?
- [ ] Did circuit breakers work?
- [ ] Did I feel urge to override?

### Month 4-5: Experimentation
- [ ] Try adjusting drift threshold (5% vs 15%)
- [ ] Compare transaction costs
- [ ] Test: What if I checked monthly instead of daily?

### Month 6: Go/No-Go Decision

**Ask yourself:**
1. Did it work technically? (No crashes, executed as designed)
2. Did I work emotionally? (Didn't override, stuck to process)
3. What did I learn? (About markets, coding, discipline)

**If 3/3 YES:**
- Consider going live with 50% of real capital
- Keep other 50% in paper trading 6 more months

**If 2/3 YES:**
- Continue paper trading, work on weak area

**If 1/3 or 0/3:**
- Honest assessment: Buy RPAR ETF instead (no shame!)

---

## 🔧 Customization

### Change Allocation

Edit `config.yaml`:
```yaml
allocation:
  VTI: 0.50  # More growth
  TLT: 0.20  # Less bonds
  GLD: 0.20
  DBC: 0.10
```

System will auto-adjust on next rebalance.

---

### Change Sensitivity

```yaml
rebalancing:
  drift_threshold: 0.15  # 15% = less frequent (lower costs)
  # OR
  drift_threshold: 0.05  # 5% = more frequent (tighter discipline)
```

**Recommendation:** Start with 10%, adjust after 3 months based on:
- If rebalancing >2x/month → increase to 15%
- If positions drift to 45/25/15/5 → decrease to 7%

---

## 🚨 Troubleshooting

### "Failed to connect to Alpaca"

**Fix:**
```bash
# Check if keys are set
grep ALPACA .env

# Verify keys work
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ALPACA_API_KEY'))"
```

---

### "Order failed: insufficient buying power"

**Cause:** Paper account has <$17K

**Fix:** Log into Alpaca → Paper Trading → Reset Account → $17,000

---

### Positions drifting too much

**Symptom:** Rebalancing every week

**Cause:** Either markets are very volatile, or threshold is too low

**Fix:** Increase `drift_threshold` to 0.15 in config.yaml

---

### Not rebalancing when I expect it to

**Symptom:** Allocation is 42/28/19/11 but no rebalance

**Cause:** Drift <10% on ALL positions (biggest is 2%)

**Fact:** This is correct behavior! Small drift = don't trade (saves costs)

---

## 📚 Next Steps

1. **Run it:** `python dalio_lite.py`

2. **Read the code:** Open `dalio_lite.py`, read line by line

3. **Track for 6 months:** Don't change anything, just observe

4. **Learn continuously:**
   - Why did it rebalance this week?
   - How did gold perform vs stocks?
   - What would I have done emotionally (panic sell, FOMO buy)?

5. **After 6 months:** Decide if ready for live trading

---

## 🎯 Your Mission (If You Choose to Accept)

**Goal:** Survive 6 months of paper trading without:
- ❌ Overriding the system emotionally
- ❌ Changing allocation every week
- ❌ Abandoning after one bad month

**If you succeed:**
- ✅ You've learned discipline (worth more than 10% returns)
- ✅ You've learned to build systems (career skill)
- ✅ You've learned about markets (costly education, you got it free)

**The real win:** 6 months from now, you'll know if automation works *for you*, regardless of returns.

---

## 🤝 Need Help?

**Common issues:** Check README.md FAQ section

**Want to modify:** Code is heavily commented, start reading in `dalio_lite.py`

**Want to share:** Open source it! Help others learn. (Just don't manage their money)

---

## ✨ Final Thought

You're not trying to beat Ray Dalio or Bridgewater.

You're trying to beat **emotional you** - the version that panic-sells at bottoms or FOMO-buys at tops.

If this system helps you do that, it's worth 10x any return it generates.

**Now go run it: `python dalio_lite.py`**

Good luck! 🚀
