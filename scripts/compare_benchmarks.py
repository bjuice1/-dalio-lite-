"""
Compare Dalio Lite performance to common benchmarks

Benchmarks:
- SPY: S&P 500 (100% stocks)
- AGG: Total Bond Market (100% bonds)
- 60/40: 60% SPY, 40% AGG (classic balanced)
- Your Dalio Lite portfolio
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import sys

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("❌ Missing dependencies. Install: pip install yfinance pandas")
    sys.exit(1)


def load_reports():
    """Load all performance reports"""
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("❌ No reports found. Run the system first to generate data.")
        return []

    reports = []
    for report_file in sorted(reports_dir.glob("report_*.json")):
        with open(report_file) as f:
            reports.append(json.load(f))

    return reports


def get_benchmark_returns(start_date, end_date):
    """Fetch benchmark returns"""
    tickers = ['SPY', 'AGG']

    print(f"Fetching benchmark data from {start_date} to {end_date}...")
    data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Adj Close']

    # Calculate returns
    returns = {
        'SPY': (data['SPY'].iloc[-1] / data['SPY'].iloc[0] - 1) * 100,
        'AGG': (data['AGG'].iloc[-1] / data['AGG'].iloc[0] - 1) * 100,
    }

    # Calculate 60/40
    returns['60/40'] = 0.6 * returns['SPY'] + 0.4 * returns['AGG']

    return returns


def calculate_dalio_return(reports):
    """Calculate Dalio Lite return from reports"""
    if len(reports) < 2:
        return None

    first = reports[0]
    last = reports[-1]

    start_value = first['portfolio_value']
    end_value = last['portfolio_value']

    return (end_value / start_value - 1) * 100


def main():
    print("\n" + "="*60)
    print("DALIO LITE PERFORMANCE COMPARISON")
    print("="*60 + "\n")

    # Load reports
    reports = load_reports()

    if len(reports) < 2:
        print("❌ Need at least 2 reports to compare performance")
        print("   Run the system for a few weeks first")
        return

    # Get date range
    start_date = datetime.fromisoformat(reports[0]['timestamp']).strftime('%Y-%m-%d')
    end_date = datetime.fromisoformat(reports[-1]['timestamp']).strftime('%Y-%m-%d')

    days = (datetime.fromisoformat(reports[-1]['timestamp']) -
            datetime.fromisoformat(reports[0]['timestamp'])).days

    print(f"Period: {start_date} to {end_date} ({days} days)\n")

    # Calculate returns
    dalio_return = calculate_dalio_return(reports)
    benchmark_returns = get_benchmark_returns(start_date, end_date)

    # Display results
    print("📊 TOTAL RETURNS:\n")
    print(f"  Dalio Lite:  {dalio_return:+6.2f}%")
    print(f"  SPY (100% stocks):  {benchmark_returns['SPY']:+6.2f}%")
    print(f"  AGG (100% bonds):   {benchmark_returns['AGG']:+6.2f}%")
    print(f"  60/40 Balanced:     {benchmark_returns['60/40']:+6.2f}%")

    print("\n" + "="*60)
    print("📈 RELATIVE PERFORMANCE:\n")

    outperformance = {
        'vs SPY': dalio_return - benchmark_returns['SPY'],
        'vs AGG': dalio_return - benchmark_returns['AGG'],
        'vs 60/40': dalio_return - benchmark_returns['60/40'],
    }

    for benchmark, diff in outperformance.items():
        symbol = "📈" if diff > 0 else "📉"
        print(f"  {symbol} {benchmark:12s}: {diff:+6.2f}%")

    print("\n" + "="*60)
    print("💡 INTERPRETATION:\n")

    # Give context
    if days < 30:
        print("⚠️  Very short time period - results not meaningful yet")
        print("   Wait at least 3 months for valid comparison")
    elif days < 90:
        print("⚠️  Still early - need 6+ months for statistical significance")
    else:
        if abs(outperformance['vs 60/40']) < 2:
            print("✓ Performing in line with 60/40 (expected for All Weather)")
        elif outperformance['vs 60/40'] > 5:
            print("📈 Outperforming 60/40 significantly")
            print("   → Check if recent market favored gold/commodities")
        else:
            print("📉 Underperforming 60/40")
            print("   → Check transaction costs or if rebalancing too frequently")

    print("\n" + "="*60)
    print("📝 NOTES:\n")
    print("- All Weather portfolio is designed for stability, not maximum returns")
    print("- Expect to underperform in strong bull markets")
    print("- Expect to outperform (lose less) in bear markets")
    print("- True test is full market cycle (5-10 years)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
