"""
Market Dashboard - Real-Time Economic Indicators & Key Metrics
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import random  # For demo data - replace with real API calls

# Import trust indicators
from trust_indicators import render_trust_bar, render_demo_data_warning

st.set_page_config(
    page_title="Market Dashboard - Dalio Lite",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .block-container {
        padding: 2rem 3rem !important;
        background: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    h1 {
        font-size: 3rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .env-indicator {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        border: 2px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .env-good { border-color: #48bb78; background: rgba(72, 187, 120, 0.05); }
    .env-neutral { border-color: #4299e1; background: rgba(66, 153, 225, 0.05); }
    .env-warning { border-color: #ed8936; background: rgba(237, 137, 54, 0.05); }
    .env-bad { border-color: #f56565; background: rgba(245, 101, 101, 0.05); }

    .signal-strong { color: #48bb78; font-weight: 700; }
    .signal-weak { color: #f56565; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("📊 Market Dashboard")
st.markdown("### Real-Time Economic Indicators & Asset Performance")

# Last updated
st.markdown(f"<div style='text-align: right; color: #718096; font-size: 0.875rem;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("---")

# Demo data warning
render_demo_data_warning()

# Current Economic Environment Assessment
st.markdown("## 🌍 Current Economic Environment")

col1, col2 = st.columns(2)

# DEMO DATA - In production, fetch from APIs (FRED, Yahoo Finance, etc.)
growth_signal = 0.65  # 0-1 scale (low to high growth)
inflation_signal = 0.45  # 0-1 scale (low to high inflation)

with col1:
    # Growth indicator
    st.markdown("""
    <div class='env-indicator env-good'>
        <h3>📈 Economic Growth</h3>
        <p style='font-size: 2rem; font-weight: 700; margin: 0.5rem 0;'>
            <span class='signal-strong'>STRONG</span>
        </p>
        <p style='color: #718096;'>GDP growth positive, low unemployment, strong consumer spending</p>
    </div>
    """, unsafe_allow_html=True)

    # Growth gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=growth_signal * 100,
        title={'text': "Growth Signal"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 33], 'color': "#fed7d7"},
                {'range': [33, 66], 'color': "#feebc8"},
                {'range': [66, 100], 'color': "#c6f6d5"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    fig.update_layout(height=250, font=dict(family='Inter'))
    st.plotly_chart(fig, width='stretch')

with col2:
    # Inflation indicator
    st.markdown("""
    <div class='env-indicator env-neutral'>
        <h3>💰 Inflation Pressure</h3>
        <p style='font-size: 2rem; font-weight: 700; margin: 0.5rem 0;'>
            MODERATE
        </p>
        <p style='color: #718096;'>CPI around target, Fed watching closely, commodity prices stable</p>
    </div>
    """, unsafe_allow_html=True)

    # Inflation gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=inflation_signal * 100,
        title={'text': "Inflation Signal"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#ed8936"},
            'steps': [
                {'range': [0, 33], 'color': "#c6f6d5"},
                {'range': [33, 66], 'color': "#feebc8"},
                {'range': [66, 100], 'color': "#fed7d7"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    fig.update_layout(height=250, font=dict(family='Inter'))
    st.plotly_chart(fig, width='stretch')

# Environment matrix
st.markdown("### 🎯 Current Environment: **Goldilocks** (High Growth + Moderate Inflation)")

env_text = """
**What this means for your portfolio:**
- ✅ **Stocks (VTI)** should perform well - companies grow earnings
- ✅ **Commodities (DBC)** moderate gains - inflation support without panic
- 🟡 **Bonds (TLT)** may underperform - Fed could raise rates
- 🟡 **Gold (GLD)** neutral - not needed for inflation protection yet

**Strategy Recommendation:** Stick to All Weather allocation. This is a favorable environment.
"""

st.info(env_text)

st.markdown("---")

# Asset Class Performance
st.markdown("## 📈 Asset Class Performance")

# Demo data - replace with real market data
asset_performance = pd.DataFrame({
    'Asset': ['VTI (US Stocks)', 'TLT (Long Bonds)', 'GLD (Gold)', 'DBC (Commodities)'],
    '1D': [0.8, -0.3, 0.1, 0.5],
    '1W': [2.3, -0.8, 0.4, 1.2],
    '1M': [5.1, -1.5, 2.1, 3.8],
    'YTD': [8.5, -3.2, 4.5, 7.2],
    '1Y': [18.3, -5.6, 12.1, 15.4],
    'Trend': ['🚀', '📉', '📊', '📈']
})

st.dataframe(asset_performance, width='stretch', hide_index=True)

# Performance chart
fig = go.Figure()

timeframes = ['1D', '1W', '1M', 'YTD', '1Y']
colors = ['#667eea', '#764ba2', '#f6ad55', '#fc8181']

for i, asset in enumerate(['VTI (US Stocks)', 'TLT (Long Bonds)', 'GLD (Gold)', 'DBC (Commodities)']):
    values = asset_performance[asset_performance['Asset'] == asset][timeframes].values[0]
    fig.add_trace(go.Bar(
        name=asset,
        x=timeframes,
        y=values,
        marker_color=colors[i],
        text=[f"{v:+.1f}%" for v in values],
        textposition='outside'
    ))

fig.update_layout(
    title="Returns by Timeframe",
    barmode='group',
    height=400,
    yaxis_title="Return %",
    font=dict(family='Inter'),
    hovermode='x unified'
)

st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Key Economic Indicators
st.markdown("## 📊 Key Economic Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📈 S&P 500",
        "5,248",
        "+0.8% today",
        delta_color="normal",
        help="US Stock Market Index"
    )

with col2:
    st.metric(
        "📊 10Y Treasury Yield",
        "4.25%",
        "+0.05%",
        delta_color="inverse",
        help="Long-term interest rate benchmark"
    )

with col3:
    st.metric(
        "💰 Gold Price",
        "$2,045/oz",
        "+$12",
        delta_color="normal",
        help="Gold spot price"
    )

with col4:
    st.metric(
        "📉 VIX (Fear Index)",
        "14.5",
        "-1.2",
        delta_color="inverse",
        help="Market volatility - lower is calmer"
    )

st.markdown("---")

# Market Sentiment Indicators
st.markdown("## 🎭 Market Sentiment & Risk Indicators")

col1, col2 = st.columns(2)

with col1:
    # Fear & Greed Index (demo)
    fear_greed = 62  # 0-100 scale

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=fear_greed,
        title={'text': "Fear & Greed Index"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#667eea"},
            'steps': [
                {'range': [0, 25], 'color': "#fed7d7", 'name': 'Extreme Fear'},
                {'range': [25, 45], 'color': "#feebc8", 'name': 'Fear'},
                {'range': [45, 55], 'color': "#e2e8f0", 'name': 'Neutral'},
                {'range': [55, 75], 'color': '#c6f6d5', 'name': 'Greed'},
                {'range': [75, 100], 'color': '#48bb78', 'name': 'Extreme Greed'}
            ],
            'threshold': {
                'line': {'color': "#667eea", 'width': 4},
                'thickness': 0.75,
                'value': fear_greed
            }
        }
    ))
    fig.update_layout(height=350, font=dict(family='Inter'))
    fig.add_annotation(
        text="GREED",
        x=0.5, y=0.15,
        showarrow=False,
        font=dict(size=20, color='#48bb78', family='Inter')
    )
    st.plotly_chart(fig, width='stretch')

with col2:
    # Risk-On vs Risk-Off indicator
    st.markdown("### 🎲 Risk Appetite")

    risk_indicators = pd.DataFrame({
        'Indicator': ['Stock Momentum', 'Volatility', 'Credit Spreads', 'Commodity Strength', 'Dollar Weakness'],
        'Signal': ['Risk On', 'Risk On', 'Risk Off', 'Risk On', 'Risk On'],
        'Strength': [8, 7, 3, 6, 7]
    })

    fig = go.Figure()

    colors_risk = ['#48bb78' if s == 'Risk On' else '#f56565' for s in risk_indicators['Signal']]

    fig.add_trace(go.Bar(
        y=risk_indicators['Indicator'],
        x=risk_indicators['Strength'],
        orientation='h',
        marker_color=colors_risk,
        text=risk_indicators['Signal'],
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Strength: %{x}/10<extra></extra>'
    ))

    fig.update_layout(
        title="Risk Appetite Signals",
        height=350,
        xaxis=dict(range=[0, 10], title="Signal Strength"),
        font=dict(family='Inter'),
        showlegend=False
    )

    st.plotly_chart(fig, width='stretch')

# Overall assessment
risk_score = risk_indicators[risk_indicators['Signal'] == 'Risk On']['Strength'].sum() / len(risk_indicators)

if risk_score > 6:
    st.success("✅ **Overall:** Strong RISK-ON environment. Markets favor growth assets (stocks, commodities).")
elif risk_score > 4:
    st.info("🟡 **Overall:** Mixed signals. Stay balanced.")
else:
    st.warning("⚠️ **Overall:** RISK-OFF environment. Flight to safety (bonds, gold).")

st.markdown("---")

# What's Moving Today
st.markdown("## 🔥 What's Moving Markets Today")

st.markdown("""
<div class='env-indicator env-good'>
    <h3>📰 Top Market Drivers</h3>
    <ul>
        <li><strong>Fed Minutes:</strong> No surprises, rates on hold - positive for stocks ✅</li>
        <li><strong>Tech Earnings:</strong> Strong results from mega-caps - VTI benefits 📈</li>
        <li><strong>Oil Prices:</strong> Stable at $78/barrel - neutral for DBC 🟡</li>
        <li><strong>Dollar Index:</strong> Weakening - good for gold and commodities 💰</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Upcoming Events Calendar
st.markdown("## 📅 Upcoming Economic Events")

events = pd.DataFrame({
    'Date': ['2026-02-20', '2026-02-22', '2026-02-25', '2026-02-28'],
    'Event': ['Fed Chair Speech', 'CPI Report', 'GDP Report', 'PCE Inflation Data'],
    'Impact': ['🟡 Medium', '🔴 High', '🔴 High', '🟡 Medium'],
    'Expected': ['Hawkish tone', 'CPI: 3.2%', 'GDP: 2.5%', 'PCE: 2.8%'],
    'Watch For': ['Rate hints', 'Core inflation', 'Growth momentum', 'Fed target metric']
})

st.dataframe(events, width='stretch', hide_index=True)

st.info("💡 **Pro Tip:** High-impact events can cause increased volatility. System may trigger circuit breakers if markets move >5% in a day.")

st.markdown("---")

# Asset Correlation Matrix
st.markdown("## 🔗 Asset Correlation Analysis")

st.markdown("""
Understanding how assets move together helps explain diversification benefits.
**Negative correlation** means assets move opposite - good for risk reduction!
""")

# Demo correlation data
corr_data = pd.DataFrame({
    'Asset': ['VTI', 'TLT', 'GLD', 'DBC'],
    'VTI': [1.0, -0.3, 0.1, 0.4],
    'TLT': [-0.3, 1.0, 0.2, -0.2],
    'GLD': [0.1, 0.2, 1.0, 0.5],
    'DBC': [0.4, -0.2, 0.5, 1.0]
})

fig = go.Figure(data=go.Heatmap(
    z=corr_data[['VTI', 'TLT', 'GLD', 'DBC']].values,
    x=['VTI', 'TLT', 'GLD', 'DBC'],
    y=['VTI', 'TLT', 'GLD', 'DBC'],
    colorscale=[
        [0, '#f56565'],    # Negative (red)
        [0.5, '#e2e8f0'],  # Zero (gray)
        [1, '#48bb78']     # Positive (green)
    ],
    zmid=0,
    text=corr_data[['VTI', 'TLT', 'GLD', 'DBC']].values,
    texttemplate='%{text:.2f}',
    textfont={"size": 16},
    hovertemplate='Correlation: %{z:.2f}<extra></extra>'
))

fig.update_layout(
    title="30-Day Rolling Correlation",
    height=400,
    font=dict(family='Inter')
)

st.plotly_chart(fig, width='stretch')

st.markdown("""
**Key Insights:**
- 🔴 **VTI vs TLT: -0.3** → Stocks and bonds move opposite (good diversification!)
- 🟢 **GLD vs DBC: +0.5** → Gold and commodities move together (both inflation hedges)
- 🟡 **VTI vs GLD: +0.1** → Nearly uncorrelated (excellent diversification)
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <p style='color: #718096;'>
        📊 <strong>Data Sources:</strong> Demo mode - In production, connect to: Federal Reserve (FRED), Yahoo Finance, Alpha Vantage
    </p>
    <p style='color: #a0aec0; font-size: 0.875rem;'>
        Refresh page to update market data | Updates every 15 minutes during market hours
    </p>
</div>
""", unsafe_allow_html=True)
