# MVP Stock Scanner - Implementation Guide

**Status:** Ready to Build
**Timeline:** 2 weeks
**Confidence:** High

---

## 🚀 GETTING STARTED (Day 1)

### Step 1: Extract Infrastructure from Dalio Lite

```bash
# Create new project
mkdir scanner_mvp
cd scanner_mvp

# Extract reusable modules
cp ../dalio-lite/error_handler.py ./infrastructure/
cp ../dalio-lite/send_notification.py ./infrastructure/
cp ../dalio-lite/monitoring.py ./infrastructure/
cp ../dalio-lite/trust_indicators.py ./infrastructure/

# Create project structure
mkdir -p scanner tests strategies config data logs
touch scanner_main.py
```

---

### Step 2: Install Dependencies

```bash
# requirements.txt
cat > requirements.txt <<EOF
# New dependencies for scanner
yfinance>=0.2.0          # Stock market data
pandas>=2.0.0            # Data manipulation
pandas-ta>=0.3.14b       # Technical analysis
numpy>=1.24.0            # Numerical operations

# Reused from Dalio Lite
python-dotenv>=1.0.0     # Environment variables
PyYAML>=6.0              # Config files
EOF

# Install
pip install -r requirements.txt
```

---

### Step 3: Create Configuration

```yaml
# config/config.yaml
scanner:
  # Stock universe (start with 100 for testing, scale to 500)
  ticker_source: "sp500"  # or "file:config/tickers.txt"
  max_stocks: 100

  # Data fetching
  cache_ttl_hours: 24
  batch_size: 50  # Fetch 50 stocks at a time

  # Indicators
  technical:
    rsi_period: 14
    macd_fast: 12
    macd_slow: 26
    macd_signal: 9
    ma_periods: [50, 200]

  # Screening
  strategies:
    - name: "RSI Oversold Bounce"
      enabled: true
      conditions:
        rsi_max: 30
        price_above_ma: 200
        volume_surge_min: 1.5
        pe_max: 30
        market_cap_min: 1000000000

    - name: "MACD Golden Cross"
      enabled: false  # Enable in Week 2

  # Signal generation
  max_signals_per_strategy: 5
  min_signal_score: 60  # 0-100 scale

  # Notification
  email:
    enabled: true
    recipients: ["your-email@example.com"]
    send_time: "00:00"  # Midnight
    subject_template: "🎯 {count} Stock Signals for {date}"

# Scheduler
schedule:
  run_time: "23:00"  # 11 PM
  timezone: "America/New_York"
```

---

## 📝 IMPLEMENTATION CHECKLIST

### Week 1: Core Engine

#### Day 1-2: Setup ✅
- [x] Extract infrastructure modules
- [ ] Install dependencies
- [ ] Create project structure
- [ ] Set up configuration
- [ ] Initialize git repo
- [ ] Create .gitignore (exclude cache.db, .env, logs/)

#### Day 3-4: Data Layer
```python
# scanner/data_fetcher.py
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from infrastructure.error_handler import safe_execute

class DataFetcher:
    def __init__(self, cache_db_path="data/cache.db"):
        self.cache_db = cache_db_path
        self._init_cache()

    def _init_cache(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.cache_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                ticker TEXT,
                date DATE,
                data TEXT,
                PRIMARY KEY (ticker, date)
            )
        """)
        conn.close()

    @safe_execute(context="Fetching stock data")
    def fetch_stocks(self, tickers: list) -> pd.DataFrame:
        """
        Fetch stock data with caching

        Returns DataFrame with columns:
        - ticker, price, volume, pe_ratio, market_cap,
        - close_30d (30 days of historical closes for indicators)
        """
        results = []

        for ticker in tickers:
            # Check cache first
            cached = self._get_from_cache(ticker)
            if cached:
                results.append(cached)
                continue

            # Fetch from yfinance
            try:
                stock = yf.Ticker(ticker)

                # Current data
                info = stock.info
                hist = stock.history(period="30d")

                data = {
                    'ticker': ticker,
                    'price': info.get('currentPrice', hist['Close'].iloc[-1]),
                    'volume': info.get('volume', hist['Volume'].iloc[-1]),
                    'pe_ratio': info.get('trailingPE', None),
                    'market_cap': info.get('marketCap', None),
                    'close_30d': hist['Close'].tolist(),
                    'volume_30d': hist['Volume'].tolist(),
                }

                # Cache it
                self._save_to_cache(ticker, data)
                results.append(data)

            except Exception as e:
                print(f"Failed to fetch {ticker}: {e}")
                continue

        return pd.DataFrame(results)

    def _get_from_cache(self, ticker):
        """Retrieve from cache if < 24h old"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.execute(
            "SELECT data FROM stock_cache WHERE ticker = ? AND date = date('now')",
            (ticker,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            import json
            return json.loads(row[0])
        return None

    def _save_to_cache(self, ticker, data):
        """Save to cache"""
        import json
        conn = sqlite3.connect(self.cache_db)
        conn.execute(
            "INSERT OR REPLACE INTO stock_cache (ticker, date, data) VALUES (?, date('now'), ?)",
            (ticker, json.dumps(data))
        )
        conn.commit()
        conn.close()
```

**Test it:**
```python
# test_data_fetcher.py
fetcher = DataFetcher()
df = fetcher.fetch_stocks(['AAPL', 'MSFT', 'GOOGL'])
print(df)
```

#### Day 5-7: Screening Engine
```python
# scanner/technical_indicators.py
import pandas as pd
import pandas_ta as ta

class TechnicalAnalyzer:
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to DataFrame

        Expects 'close_30d' column with list of prices
        Adds: rsi, macd, ma_50, ma_200, volume_ratio
        """
        df = df.copy()

        for idx, row in df.iterrows():
            closes = pd.Series(row['close_30d'])
            volumes = pd.Series(row['volume_30d'])

            # RSI
            rsi = ta.rsi(closes, length=14)
            df.at[idx, 'rsi'] = rsi.iloc[-1] if len(rsi) > 0 else None

            # MACD
            macd = ta.macd(closes)
            if macd is not None and len(macd) > 0:
                df.at[idx, 'macd'] = macd['MACD_12_26_9'].iloc[-1]
                df.at[idx, 'macd_signal'] = macd['MACDs_12_26_9'].iloc[-1]

            # Moving averages
            ma_50 = ta.sma(closes, length=50)
            ma_200 = ta.sma(closes, length=200)
            df.at[idx, 'ma_50'] = ma_50.iloc[-1] if len(ma_50) > 0 else None
            df.at[idx, 'ma_200'] = ma_200.iloc[-1] if len(ma_200) > 0 else None

            # Volume ratio
            vol_avg = volumes.rolling(20).mean().iloc[-1]
            df.at[idx, 'volume_ratio'] = row['volume'] / vol_avg if vol_avg > 0 else 1.0

        return df
```

```python
# scanner/screening_engine.py
class Strategy:
    def __init__(self, name, conditions):
        self.name = name
        self.conditions = conditions

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply strategy conditions, return matches"""
        matches = df.copy()

        # Technical conditions
        if 'rsi_max' in self.conditions:
            matches = matches[matches['rsi'] < self.conditions['rsi_max']]

        if 'price_above_ma' in self.conditions:
            ma_col = f"ma_{self.conditions['price_above_ma']}"
            matches = matches[matches['price'] > matches[ma_col]]

        if 'volume_surge_min' in self.conditions:
            matches = matches[matches['volume_ratio'] > self.conditions['volume_surge_min']]

        # Fundamental conditions
        if 'pe_max' in self.conditions:
            matches = matches[matches['pe_ratio'] < self.conditions['pe_max']]

        if 'market_cap_min' in self.conditions:
            matches = matches[matches['market_cap'] > self.conditions['market_cap_min']]

        return matches

class ScreeningEngine:
    def __init__(self, strategies):
        self.strategies = strategies

    def screen(self, df: pd.DataFrame) -> dict:
        """Run all strategies, return matches"""
        results = {}
        for strategy in self.strategies:
            matches = strategy.apply(df)
            results[strategy.name] = matches
        return results
```

**Test it:**
```python
# Test screening
fetcher = DataFetcher()
df = fetcher.fetch_stocks(['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'])

analyzer = TechnicalAnalyzer()
df = analyzer.add_indicators(df)

strategy = Strategy(
    name="RSI Oversold",
    conditions={'rsi_max': 30, 'price_above_ma': 200, 'volume_surge_min': 1.5}
)

engine = ScreeningEngine([strategy])
results = engine.screen(df)

print(f"Found {len(results['RSI Oversold'])} signals")
print(results['RSI Oversold'][['ticker', 'price', 'rsi', 'volume_ratio']])
```

---

### Week 2: Signal Generation & Testing

#### Day 8-9: Signal Generation
```python
# scanner/signal_generator.py
from dataclasses import dataclass

@dataclass
class Signal:
    ticker: str
    strategy_name: str
    score: float
    entry_price: float
    technical_reason: str
    fundamental_reason: str
    action: str = "BUY"

class SignalGenerator:
    def generate(self, strategy_results: dict, max_per_strategy=5) -> list:
        """
        Rank and score signals from screening results
        """
        all_signals = []

        for strategy_name, matches in strategy_results.items():
            for _, row in matches.iterrows():
                # Calculate score (0-100)
                score = self._calculate_score(row, strategy_name)

                # Generate reasoning
                tech_reason = self._technical_reason(row)
                fund_reason = self._fundamental_reason(row)

                signal = Signal(
                    ticker=row['ticker'],
                    strategy_name=strategy_name,
                    score=score,
                    entry_price=row['price'],
                    technical_reason=tech_reason,
                    fundamental_reason=fund_reason
                )
                all_signals.append(signal)

            # Sort by score, take top N
            all_signals = sorted(all_signals, key=lambda s: s.score, reverse=True)
            all_signals = all_signals[:max_per_strategy]

        return all_signals

    def _calculate_score(self, row, strategy_name):
        """Score 0-100 based on signal strength"""
        score = 50  # Base score

        # RSI: Lower = better for oversold
        if strategy_name == "RSI Oversold":
            rsi = row.get('rsi', 50)
            score += (30 - rsi) * 2  # +40 if RSI=10, +0 if RSI=30

        # Volume surge
        vol_ratio = row.get('volume_ratio', 1.0)
        score += min((vol_ratio - 1.0) * 10, 30)  # +30 max for 4x volume

        return min(max(score, 0), 100)

    def _technical_reason(self, row):
        rsi = row.get('rsi', 'N/A')
        ma_200 = row.get('ma_200', 'N/A')
        vol_ratio = row.get('volume_ratio', 'N/A')
        return f"RSI {rsi:.0f}, Price ${row['price']:.2f} above 200-MA ${ma_200:.2f}, Volume {vol_ratio:.1f}x average"

    def _fundamental_reason(self, row):
        pe = row.get('pe_ratio', 'N/A')
        mcap = row.get('market_cap', 0) / 1e9  # Billions
        return f"P/E {pe:.1f}, Market Cap ${mcap:.1f}B"
```

```python
# scanner/email_formatter.py
def format_email(signals: list, date: str) -> str:
    """Generate HTML email from signals"""

    buy_signals = [s for s in signals if s.action == "BUY"]

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #667eea; }}
            .signal {{ background: #f7fafc; border-left: 4px solid #48bb78; padding: 15px; margin: 15px 0; }}
            .ticker {{ font-size: 1.5rem; font-weight: bold; color: #2d3748; }}
            .score {{ color: #48bb78; font-weight: bold; }}
            .technical {{ color: #4a5568; margin: 5px 0; }}
            .fundamental {{ color: #718096; margin: 5px 0; }}
        </style>
    </head>
    <body>
        <h1>🎯 {len(buy_signals)} Stock Signals for {date}</h1>
        <p>Good morning! Here are today's top opportunities:</p>

        <h2>🟢 BUY Signals ({len(buy_signals)})</h2>
    """

    for i, signal in enumerate(buy_signals, 1):
        html += f"""
        <div class="signal">
            <div class="ticker">{i}. {signal.ticker} - ${signal.entry_price:.2f} <span class="score">(Score: {signal.score:.0f}/100)</span></div>
            <div><strong>Setup:</strong> {signal.strategy_name}</div>
            <div class="technical"><strong>Technical:</strong> {signal.technical_reason}</div>
            <div class="fundamental"><strong>Fundamental:</strong> {signal.fundamental_reason}</div>
        </div>
        """

    html += """
        <hr/>
        <p style="color: #718096; font-size: 0.875rem;">
            Generated by Stock Scanner MVP<br/>
            Data as of: {date} 23:59 EST
        </p>
    </body>
    </html>
    """

    return html
```

#### Day 10-11: Main Integration
```python
# scanner_main.py
import yaml
from scanner.data_fetcher import DataFetcher
from scanner.technical_indicators import TechnicalAnalyzer
from scanner.screening_engine import Strategy, ScreeningEngine
from scanner.signal_generator import SignalGenerator
from scanner.email_formatter import format_email
from infrastructure.send_notification import send_email
from infrastructure.error_handler import safe_execute
from datetime import datetime

@safe_execute(context="Running stock scanner")
def run_scanner():
    print(f"🚀 Starting scanner at {datetime.now()}")

    # Load config
    with open('config/config.yaml') as f:
        config = yaml.safe_load(f)

    # Load tickers (S&P 500 or custom list)
    tickers = _load_tickers(config)
    print(f"📊 Scanning {len(tickers)} stocks...")

    # Step 1: Fetch data
    print("1️⃣ Fetching stock data...")
    fetcher = DataFetcher()
    df = fetcher.fetch_stocks(tickers)
    print(f"   Fetched {len(df)} stocks")

    # Step 2: Calculate indicators
    print("2️⃣ Calculating technical indicators...")
    analyzer = TechnicalAnalyzer()
    df = analyzer.add_indicators(df)

    # Step 3: Screen for signals
    print("3️⃣ Screening for signals...")
    strategies = _load_strategies(config)
    engine = ScreeningEngine(strategies)
    results = engine.screen(df)

    total_matches = sum(len(matches) for matches in results.values())
    print(f"   Found {total_matches} total matches")

    # Step 4: Generate signals
    print("4️⃣ Generating top signals...")
    generator = SignalGenerator()
    signals = generator.generate(results, max_per_strategy=config['scanner']['max_signals_per_strategy'])
    print(f"   Generated {len(signals)} signals")

    # Step 5: Send email
    if len(signals) > 0:
        print("5️⃣ Sending email...")
        html = format_email(signals, datetime.now().strftime("%Y-%m-%d"))
        subject = f"🎯 {len(signals)} Stock Signals for {datetime.now().strftime('%Y-%m-%d')}"

        for recipient in config['scanner']['email']['recipients']:
            send_email(subject, html, recipient)
            print(f"   ✅ Sent to {recipient}")
    else:
        print("⚠️ No signals generated today")

    print(f"✅ Scanner complete at {datetime.now()}")

def _load_tickers(config):
    """Load ticker list (S&P 500 or custom file)"""
    if config['scanner']['ticker_source'] == 'sp500':
        # Use a hardcoded list or fetch from Wikipedia
        import pandas as pd
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        return sp500['Symbol'].tolist()[:config['scanner']['max_stocks']]
    else:
        with open(config['scanner']['ticker_source'].replace('file:', '')) as f:
            return [line.strip() for line in f if line.strip()]

def _load_strategies(config):
    """Load strategies from config"""
    strategies = []
    for strat_config in config['scanner']['strategies']:
        if strat_config.get('enabled', False):
            strategy = Strategy(
                name=strat_config['name'],
                conditions=strat_config['conditions']
            )
            strategies.append(strategy)
    return strategies

if __name__ == "__main__":
    run_scanner()
```

**Test it:**
```bash
# Run manually first
python scanner_main.py

# Check email inbox for results
```

#### Day 12-14: Deploy & Validate

**Deploy to Cloud:**
```bash
# DigitalOcean Droplet ($6/month)
ssh root@your-droplet-ip

# Clone repo
git clone https://github.com/yourusername/scanner_mvp.git
cd scanner_mvp

# Install dependencies
pip3 install -r requirements.txt

# Set up .env
nano .env
# Add email credentials

# Set up cron
crontab -e
# Add: 0 23 * * * cd /root/scanner_mvp && /usr/bin/python3 scanner_main.py >> logs/scanner.log 2>&1
```

**Invite Test Users:**
```
Subject: Beta Test Invite - Stock Scanner MVP

Hey [Name],

I'm testing a new tool that scans the stock market every night and emails you 5-10 high-quality trade signals by 6am.

Current strategies:
- RSI Oversold Bounce (find oversold stocks in uptrends)
- MACD Golden Cross (momentum breakouts)

Want to try it for 3 days? Just reply with your email and I'll add you.

No cost, just need your feedback on:
1. Are the signals useful?
2. Would you pay $20/month for this?

Thanks!
```

**Collect Feedback:**
- Day 1: Did they open the email?
- Day 2: Any questions or confusion?
- Day 3: Follow-up survey:
  1. How useful were the signals? (1-10)
  2. Did you execute any trades based on them?
  3. Would you pay for this service?
  4. What would make it better?

---

## ✅ VALIDATION CRITERIA

### Decision Matrix

| Users Who Would Pay | Decision |
|---------------------|----------|
| 0/5 | ❌ Pivot - concept doesn't resonate |
| 1-2/5 | 🤔 Iterate - refine strategies, try different signals |
| 3+/5 | ✅ Proceed - build full product |

### Success Signals
- ✅ Users open emails 3+ days in a row
- ✅ Users ask questions or engage with content
- ✅ Users report taking action (even if no trade)
- ✅ Users proactively suggest improvements
- ❌ Users ignore emails after day 1
- ❌ Users say "this is just like [existing tool]"
- ❌ Users question accuracy or quality

---

## 🚀 IF MVP SUCCEEDS - NEXT STEPS

### Phase 2: Full Product (Month 2-3)
1. Add 8-10 more strategies
2. Build web dashboard (signal history, performance tracking)
3. Add user accounts & authentication
4. Custom watchlists & alerts
5. Backtesting engine
6. Premium tier ($20-50/month)

### Phase 3: Scale (Month 4-6)
1. Expand to 5000+ stocks
2. Real-time intraday alerts
3. Mobile app
4. Community features (see what others are watching)
5. Performance attribution
6. Integration with brokers (TradingView, Interactive Brokers)

---

## 📚 RESOURCES

### Learning
- yfinance docs: https://pypi.org/project/yfinance/
- pandas-ta docs: https://github.com/twopirllc/pandas-ta
- Technical analysis tutorial: https://www.investopedia.com/terms/t/technicalanalysis.asp

### Competitors (Study These)
- Finviz: Stock screener (free + $40/month pro)
- TradingView: Charting + alerts ($15-60/month)
- Benzinga Pro: News + signals ($99-250/month)
- StockRover: Fundamental screening ($8-28/month)

### Your Advantage
- ✅ Simple: No configuration, just signals
- ✅ Actionable: Top 5-10 only (not 100+ results)
- ✅ Educational: Explains WHY each signal triggered
- ✅ Affordable: $20/month vs. $50-250

---

**Last Updated:** 2026-02-18T21:15:00Z
**Status:** Ready to implement
**Estimated LOC:** ~800 lines (new code) + 200 (reused infrastructure)
