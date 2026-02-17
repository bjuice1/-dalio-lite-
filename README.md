# Dalio Lite 💼

**A simplified, educational implementation of Ray Dalio's All Weather portfolio for small accounts ($10K-50K).**

Built for learning, not for beating the market. If it works after 6 months of paper trading, you've learned discipline. If it doesn't, you've learned why simplicity matters.

---

## 🎯 What This Does

- **4-ETF portfolio:** VTI (stocks), TLT (bonds), GLD (gold), DBC (commodities)
- **Auto-rebalancing:** Only when drift exceeds 10% (not calendar-based = lower costs)
- **Risk management:** Circuit breakers halt trading if losses exceed thresholds
- **Paper trading first:** Test with fake money for 6 months before risking real capital
- **Educational:** Every line is commented; learn by reading the code

---

## 📊 The Strategy

**Target Allocation:**
- 40% VTI (US Total Stock Market) - Growth engine
- 30% TLT (20+ Year Treasuries) - Deflation hedge
- 20% GLD (Gold) - Inflation hedge, safe haven
- 10% DBC (Commodities) - Inflation hedge, diversifier

**Why this works (in theory):**
- Balanced across economic regimes (growth, recession, inflation, deflation)
- Lower volatility than 100% stocks
- Lower correlation than 60/40 stocks/bonds
- Historically ~7-9% annual returns with smaller drawdowns

**Why this might NOT work:**
- Past performance ≠ future results
- Bonds struggled 2022-2024 (rates rising)
- Commodities are volatile and decay over time
- Small portfolios pay higher transaction costs

---

## 🚀 Quick Start (30 Minutes)

### 1. Get Alpaca Paper Trading Account (5 min)

1. Go to https://alpaca.markets
2. Sign up (free, no credit card)
3. Navigate to "Paper Trading" section
4. Copy your API Key and Secret Key

### 2. Install Dependencies (2 min)

```bash
cd dalio-lite
pip install -r requirements.txt
```

### 3. Set Environment Variables (2 min)

```bash
# Copy example env file
cp .env.example .env

# Edit .env and paste your Alpaca keys
nano .env
```

Your `.env` should look like:
```
ALPACA_API_KEY=PK...your_paper_key
ALPACA_SECRET_KEY=...your_paper_secret
```

### 4. Fund Your Paper Account (5 min)

1. Log into Alpaca web dashboard
2. Go to Paper Trading
3. "Reset" paper account to $17,000 (match your real portfolio size)

### 5. Run Your First Check (1 min)

```bash
python dalio_lite.py --dry-run
```

You should see:
```
DALIO LITE INITIALIZED
Mode: PAPER TRADING
Connected to Alpaca: $17000.00 cash

DAILY CHECK
Current Allocation:
  VTI:   0.0% (target: 40.0%, drift: -40.0%)
  TLT:   0.0% (target: 30.0%, drift: -30.0%)
  GLD:   0.0% (target: 20.0%, drift: -20.0%)
  DBC:   0.0% (target: 10.0%, drift: -10.0%)

Rebalance Check: Drift 40.0% exceeds threshold 10.0%
🔄 Rebalancing required
DRY RUN - No orders executed
```

### 6. Execute Your First Rebalance (2 min)

```bash
# Remove --dry-run to actually place orders
python dalio_lite.py
```

This will buy:
- ~$6,800 of VTI
- ~$5,100 of TLT
- ~$3,400 of GLD
- ~$1,700 of DBC

✅ **You now have an automated Dalio portfolio!**

---

## 📅 Daily Usage

### Set Up Daily Automation

**Option A: Cron Job (Mac/Linux)**

```bash
# Open crontab
crontab -e

# Add this line (runs every day at 10:30am ET, after market open)
30 10 * * 1-5 cd /path/to/dalio-lite && python dalio_lite.py >> logs/cron.log 2>&1
```

**Option B: Manual (Recommended for First Month)**

```bash
# Run this once a day after market opens
python dalio_lite.py
```

**What it does:**
1. ✓ Checks if any position drifted >10% from target
2. ✓ If yes, rebalances back to target allocation
3. ✓ If no, does nothing (saves transaction costs)
4. ✓ Logs everything to `logs/dalio_lite.log`

---

## 📈 Monitoring & Reports

### Daily: Check the Logs

```bash
tail -f logs/dalio_lite.log
```

### Weekly: Generate Performance Report

```bash
python dalio_lite.py --report
```

Output:
```json
{
  "timestamp": "2026-02-16T10:30:00",
  "portfolio_value": 17234.56,
  "cash": 123.45,
  "positions": {
    "VTI": 0.398,
    "TLT": 0.305,
    "GLD": 0.201,
    "DBC": 0.096
  }
}
```

### Monthly: Compare to Benchmarks

```bash
python scripts/compare_benchmarks.py
```

Shows your return vs:
- SPY (S&P 500)
- AGG (Total Bond Market)
- 60/40 portfolio

---

## 🛡️ Safety Features

### 1. **Paper Trading Lock**

In `config.yaml`:
```yaml
mode:
  paper_trading: true  # Cannot be changed without manual edit
```

**Rule:** Do NOT set to `false` until you've successfully run paper trading for 6 months.

### 2. **Circuit Breakers**

System automatically halts rebalancing if:
- Portfolio loses >5% in a single day (data error or market crash)
- Portfolio loses >30% total (requires manual review)

### 3. **Minimum Trade Size**

Won't execute orders <$100 (avoids bad pricing on tiny orders).

### 4. **Minimum Days Between Rebalances**

Default: 30 days minimum (prevents overtrading on volatile days).

---

## 🎓 Learning Path (First 6 Months)

### Month 1: Setup & First Rebalance
- [x] Set up paper trading
- [x] Execute first rebalance
- [ ] Read through `dalio_lite.py` line by line
- [ ] Understand what each function does

### Month 2: Monitor Daily
- [ ] Check logs every day
- [ ] Track how often rebalancing triggers
- [ ] Note: Does drift threshold (10%) trigger too often or too rarely?

### Month 3: Compare Performance
- [ ] Run weekly performance reports
- [ ] Compare your return to SPY (stocks) and AGG (bonds)
- [ ] Ask: Is All Weather beating 60/40? Why or why not?

### Month 4: Stress Test
- [ ] What happens during a volatile week? (Watch for overtrading)
- [ ] Check: Are circuit breakers working?
- [ ] Simulate: What if one ETF delisted? How would you handle it?

### Month 5: Optimization Experiments
- [ ] Try adjusting drift threshold (5% vs 10% vs 15%)
- [ ] Track transaction costs
- [ ] Calculate: Is frequent rebalancing worth the cost?

### Month 6: Go/No-Go Decision
- [ ] Total return vs benchmarks?
- [ ] Did you stick with it through volatility?
- [ ] Do you understand WHY it worked (or didn't)?

**If all 3 are YES → Consider going live with 50% of capital**
**If any are NO → Keep paper trading or buy RPAR ETF instead**

---

## 🔧 Advanced: Customization

### Change Allocation

Edit `config.yaml`:
```yaml
allocation:
  VTI: 0.50  # Increase stocks if you want more growth
  TLT: 0.20  # Decrease bonds
  GLD: 0.20
  DBC: 0.10
```

### Change Rebalance Trigger

```yaml
rebalancing:
  drift_threshold: 0.15  # 15% = less frequent (lower costs)
  # OR
  drift_threshold: 0.05  # 5% = more frequent (tighter discipline)
```

### Add Notifications (Telegram)

1. Create Telegram bot: https://core.telegram.org/bots#how-do-i-create-a-bot
2. Get your chat_id: Message @userinfobot
3. Edit `config.yaml`:
```yaml
notifications:
  enabled: true
  method: telegram
```
4. Add to `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## ❓ FAQ

### Q: Why only 4 ETFs instead of 11?
**A:** At $17K portfolio, 11 ETFs means ~$1,500 per position. Small orders get worse pricing (wider bid-ask spreads). 4 ETFs = $4K+ per position = better pricing, lower costs.

### Q: Why drift-based rebalancing instead of quarterly?
**A:** Calendar rebalancing = you might trade when not needed (costs money) or miss when you should trade (drift gets extreme). Drift-based = only trade when necessary.

### Q: What if I want to add my current Robinhood holdings?
**A:** Two options:
1. **Liquidate Robinhood, transfer cash to Alpaca, start fresh** (cleanest)
2. **Keep Robinhood separate, run Dalio Lite with new $5K only** (easier but divided focus)

Do NOT try to merge the two systems—too complex for V1.

### Q: When can I go live?
**A:** After 6 months of successful paper trading AND you can answer "yes" to:
- Did I check it daily without panic?
- Did I resist the urge to override it?
- Do I understand why it worked (or didn't)?

### Q: What about taxes?
**A:** If taxable account: every rebalance = taxable event. Recommend:
- Use IRA/Roth if possible (tax-free rebalancing)
- If taxable: run annually not quarterly, add tax-loss harvesting

---

## 🚨 What Could Go Wrong

### 1. **You Override During a Crash**
**Symptom:** Gold/stocks both crash 20%, you panic and sell everything
**Fix:** Paper trade until you can watch -20% without touching it

### 2. **Transaction Costs Eat Returns**
**Symptom:** Rebalancing every week, paying spreads/fees constantly
**Fix:** Increase drift threshold to 15%, check monthly not daily

### 3. **API Downtime**
**Symptom:** Alpaca API down, system can't rebalance
**Fix:** System logs error and skips day—just run manually when API is back

### 4. **Forgetting It's Paper Trading**
**Symptom:** After 6 months, thinking "I made 15%!" but it was fake money
**Fix:** Remember: Paper trading = learning, not returns. Goal is process, not profit.

---

## 📚 Learn More

**Ray Dalio's Actual Writings:**
- *Principles* (book) - Philosophy of systems thinking
- *The Changing World Order* (book) - Big cycle framework
- LinkedIn posts: https://www.linkedin.com/in/raydalio/

**Risk Parity Explained:**
- https://www.bridgewater.com/research-and-insights/all-weather-strategy

**Why This Approach (Simplified for Small Accounts):**
- Real risk parity uses leverage + derivatives (not accessible to retail)
- ETF version is "risk parity lite" - captures philosophy, not exact implementation
- At <$100K, simplicity > optimization

---

## 🤝 Contributing

Found a bug? Have an idea?

1. This is YOUR learning project—modify freely
2. Share learnings (not financial advice) with friends
3. If you improve it, consider open sourcing on GitHub

**Legal note:** If friends ask you to manage THEIR money with this → say NO (requires SEC registration). Share the CODE, not advice.

---

## 📄 License

MIT License - Do whatever you want with this code.

**Disclaimer:** This is educational software. Not financial advice. You will lose money. The question is: will you learn from it?

---

## 🎯 Success Criteria

After 6 months, you should be able to answer:

1. **Did the system work technically?** (No crashes, rebalancing executed)
2. **Did YOU work emotionally?** (Didn't override, followed the process)
3. **What did you learn?** (About markets, systems, yourself)

If 3/3 = Success (regardless of returns)
If 2/3 = Partial success (refine and retry)
If 1/3 = Buy RPAR ETF instead (no shame in that)

---

**Ready to start? Run: `python dalio_lite.py --dry-run`**
