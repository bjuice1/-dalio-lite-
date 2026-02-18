"""
How It Works - Visual Explainer Page
Interactive diagrams showing how Dalio Lite operates
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

# Import trust indicators
from trust_indicators import render_trust_bar

st.set_page_config(
    page_title="How It Works - Dalio Lite",
    page_icon="📖",
    layout="wide"
)

# Custom CSS (matching main dashboard)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif !important; }
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .block-container {
        padding: 2rem 3rem;
        background: white;
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }
    h1 {
        font-size: 3rem !important;
        font-weight: 700 !important;
        color: #5a67d8 !important;
    }
    p, div, span {
        color: #2d3748 !important;
    }
    .info-box {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .step-box {
        background: white;
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("📖 How It Works")
st.markdown("### Visual Guide to Dalio Lite's Automated Portfolio Management")
st.markdown("---")

# Table of contents
st.markdown("""
**Jump to:**
- [The All Weather Strategy](#the-all-weather-strategy)
- [How Rebalancing Works](#how-rebalancing-works)
- [Data Flow](#data-flow)
- [Daily Check Process](#daily-check-process)
- [Risk Management](#risk-management)
""")

st.markdown("---")

# Section 1: All Weather Strategy
st.markdown("## 🌤️ The All Weather Strategy")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    Ray Dalio's "All Weather" portfolio is designed to perform well in **any economic environment**:

    ### The Four Economic Seasons:
    - 📈 **Rising Growth** → Stocks thrive
    - 📉 **Falling Growth** → Bonds rally
    - 💰 **Rising Inflation** → Gold & commodities protect
    - 🧊 **Falling Inflation** → Long bonds shine

    By holding all four asset types, your portfolio is "weatherproof" - it doesn't rely on predicting
    which environment is coming. Something in your portfolio will always be working.
    """)

with col2:
    # Asset allocation pie
    fig = go.Figure(data=[go.Pie(
        labels=['🇺🇸 VTI<br>US Stocks', '📈 TLT<br>Long Bonds', '🥇 GLD<br>Gold', '🌾 DBC<br>Commodities'],
        values=[40, 30, 20, 10],
        hole=0.5,
        marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
        textfont=dict(size=14, color='#2d3748', family='Inter'),
        hovertemplate='<b>%{label}</b><br>%{value}%<extra></extra>'
    )])
    fig.update_layout(
        title="Target Allocation",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig, width='stretch')

# Economic environments table
st.markdown("### 📊 Performance by Economic Environment")

env_data = pd.DataFrame({
    'Environment': ['📈 High Growth', '📉 Low Growth', '💰 High Inflation', '🧊 Low Inflation'],
    'Stocks (VTI)': ['🟢 Strong', '🔴 Weak', '🟡 Mixed', '🟢 Strong'],
    'Bonds (TLT)': ['🔴 Weak', '🟢 Strong', '🔴 Weak', '🟢 Strong'],
    'Gold (GLD)': ['🟡 Mixed', '🟢 Strong', '🟢 Strong', '🔴 Weak'],
    'Commodities (DBC)': ['🟢 Strong', '🔴 Weak', '🟢 Strong', '🔴 Weak']
})

st.dataframe(env_data, width='stretch', hide_index=True)

st.markdown("---")

# Section 2: Rebalancing Process
st.markdown("## 🔄 How Rebalancing Works")

st.markdown("""
Rebalancing is the key to maintaining your target allocation. Here's what happens:
""")

# Rebalancing flowchart using Sankey
fig = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 15,
      thickness = 20,
      line = dict(color = "black", width = 0.5),
      label = [
          "Your Portfolio<br>$100,000",  # 0
          "Daily Check",  # 1
          "Calculate Drift",  # 2
          "Drift < 10%",  # 3
          "Drift > 10%",  # 4
          "✅ No Action",  # 5
          "Execute Rebalance",  # 6
          "SELL Overweight",  # 7
          "BUY Underweight",  # 8
          "✅ Balanced"  # 9
      ],
      color = ['#667eea', '#4299e1', '#f6ad55', '#48bb78', '#f56565',
               '#48bb78', '#ed8936', '#e53e3e', '#48bb78', '#48bb78']
    ),
    link = dict(
      source = [0, 1, 2, 2, 4, 6, 6, 7, 8],
      target = [1, 2, 3, 4, 6, 7, 8, 9, 9],
      value = [100, 100, 30, 70, 70, 35, 35, 35, 35],
      color = ['rgba(102, 126, 234, 0.3)'] * 9
  )
)])

fig.update_layout(
    title="Rebalancing Decision Flow",
    height=500,
    font=dict(size=12, family='Inter')
)

st.plotly_chart(fig, width='stretch')

# Step-by-step explanation
st.markdown("### Step-by-Step Rebalancing")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class='step-box'>
        <h3>1️⃣ Check Drift</h3>
        <p>System calculates how far each asset is from its target:</p>
        <ul>
            <li>VTI should be 40%</li>
            <li>Currently 45%</li>
            <li><strong>Drift: +5%</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='step-box'>
        <h3>2️⃣ Decide Action</h3>
        <p>If <strong>any</strong> asset drifts >10%:</p>
        <ul>
            <li>✅ >30 days since last rebalance</li>
            <li>✅ No circuit breakers triggered</li>
            <li>→ <strong>Rebalance!</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='step-box'>
        <h3>3️⃣ Execute Trades</h3>
        <p>Two-phase execution:</p>
        <ul>
            <li><strong>Phase 1:</strong> Sell overweight assets</li>
            <li><strong>Phase 2:</strong> Buy underweight assets</li>
            <li>→ <strong>Back to target!</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Section 3: Drift Visualization
st.markdown("## 📏 Understanding Drift")

st.markdown("""
**Drift** is how far your actual allocation moves away from your target. Markets move daily,
causing your percentages to shift. Here's what 10% drift looks like:
""")

# Drift comparison
drift_scenarios = pd.DataFrame({
    'Ticker': ['VTI', 'TLT', 'GLD', 'DBC'],
    'Target': [40, 30, 20, 10],
    'Scenario 1: No Drift': [40, 30, 20, 10],
    'Scenario 2: 5% Drift': [42, 29, 20, 9],
    'Scenario 3: 15% Drift (TRIGGER)': [46, 28, 18, 8]
})

fig = go.Figure()

# Add bars for each scenario
fig.add_trace(go.Bar(
    name='Target',
    x=drift_scenarios['Ticker'],
    y=drift_scenarios['Target'],
    marker_color='#667eea',
    text=drift_scenarios['Target'],
    textposition='outside',
    texttemplate='%{text}%'
))

fig.add_trace(go.Bar(
    name='5% Drift (OK)',
    x=drift_scenarios['Ticker'],
    y=drift_scenarios['Scenario 2: 5% Drift'],
    marker_color='#48bb78',
    text=drift_scenarios['Scenario 2: 5% Drift'],
    textposition='outside',
    texttemplate='%{text}%'
))

fig.add_trace(go.Bar(
    name='15% Drift (REBALANCE!)',
    x=drift_scenarios['Ticker'],
    y=drift_scenarios['Scenario 3: 15% Drift (TRIGGER)'],
    marker_color='#f56565',
    text=drift_scenarios['Scenario 3: 15% Drift (TRIGGER)'],
    textposition='outside',
    texttemplate='%{text}%'
))

fig.update_layout(
    title="Drift Scenarios - When to Rebalance",
    barmode='group',
    height=400,
    yaxis_title="Allocation %",
    xaxis_title="Asset",
    font=dict(family='Inter'),
    hovermode='x unified'
)

st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Section 4: Data Flow
st.markdown("## 🔄 Data Flow")

st.markdown("""
Here's how data moves through the system when you click "Run Daily Check":
""")

# Data flow Sankey
fig = go.Figure(data=[go.Sankey(
    node = dict(
      pad = 20,
      thickness = 30,
      line = dict(color = "black", width = 0.5),
      label = [
          "🖱️ You Click<br>'Run Check'",  # 0
          "💻 Dalio Lite<br>System",  # 1
          "🏦 Alpaca API",  # 2
          "📊 Get Account<br>Data",  # 3
          "💼 Get Current<br>Positions",  # 4
          "💰 Get Real-Time<br>Prices",  # 5
          "🧮 Calculate<br>Drift",  # 6
          "✅ Decision:<br>Rebalance?",  # 7
          "📤 Submit<br>Orders",  # 8
          "📝 Write Logs",  # 9
          "📊 Update<br>Dashboard",  # 10
          "👁️ You See<br>Results"  # 11
      ],
      color = ['#667eea', '#4299e1', '#48bb78', '#48bb78', '#48bb78',
               '#48bb78', '#f6ad55', '#ed8936', '#f56565', '#718096',
               '#4299e1', '#667eea']
    ),
    link = dict(
      source = [0, 1, 1, 2, 2, 2, 3, 4, 5, 6, 7, 7, 8, 9, 10],
      target = [1, 2, 6, 3, 4, 5, 6, 6, 6, 7, 8, 9, 9, 10, 11],
      value = [1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 0.7, 0.3, 0.7, 1, 1],
      color = ['rgba(102, 126, 234, 0.4)'] * 15
  )
)])

fig.update_layout(
    title="Data Flow: From Click to Result",
    height=600,
    font=dict(size=11, family='Inter')
)

st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Section 5: Daily Check Timeline
st.markdown("## ⏱️ Daily Check Process (Timeline)")

st.markdown("""
This is what happens in those 3-8 seconds when you run a daily check:
""")

# Timeline
timeline_data = pd.DataFrame({
    'Step': ['Connect to Alpaca', 'Fetch Account Data', 'Fetch Positions', 'Calculate Drift',
             'Check Circuit Breakers', 'Decide: Rebalance?', 'Get Real-Time Prices',
             'Execute SELL Orders', 'Execute BUY Orders', 'Update State File', 'Write Logs', 'Done!'],
    'Duration (ms)': [500, 200, 300, 10, 50, 5, 400, 800, 800, 50, 100, 0],
    'Color': ['#667eea', '#4299e1', '#4299e1', '#f6ad55', '#f56565', '#ed8936',
              '#48bb78', '#e53e3e', '#48bb78', '#718096', '#718096', '#48bb78']
})

timeline_data['Cumulative'] = timeline_data['Duration (ms)'].cumsum()

fig = go.Figure()

for i, row in timeline_data.iterrows():
    fig.add_trace(go.Scatter(
        x=[row['Cumulative'], row['Cumulative']],
        y=[0, 1],
        mode='lines+markers+text',
        line=dict(color=row['Color'], width=8),
        marker=dict(size=15, color=row['Color']),
        text=[f"{row['Step']}<br>{row['Duration (ms)']}ms", ""],
        textposition="top center",
        name=row['Step'],
        showlegend=False,
        hovertemplate=f"<b>{row['Step']}</b><br>Duration: {row['Duration (ms)']}ms<br>At: {row['Cumulative']}ms<extra></extra>"
    ))

fig.update_layout(
    title="Timeline of a Typical Rebalance (Total: ~3 seconds)",
    height=300,
    xaxis=dict(title="Time (milliseconds)", range=[0, timeline_data['Cumulative'].max() + 200]),
    yaxis=dict(visible=False),
    font=dict(family='Inter'),
    hovermode='closest'
)

st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Section 6: Risk Management
st.markdown("## 🛡️ Risk Management (Circuit Breakers)")

st.markdown("""
The system has built-in safety features to protect your portfolio from disasters:
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class='info-box'>
        <h3>🔴 Circuit Breaker #1: Daily Loss</h3>
        <p><strong>Trigger:</strong> Portfolio drops >5% in one day</p>
        <p><strong>Action:</strong> Halt all rebalancing, send alert</p>
        <p><strong>Why:</strong> Prevents trading during market crashes when prices are distorted</p>
        <p><strong>Recovery:</strong> Waits 24 hours, then checks again</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='info-box'>
        <h3>🔴 Circuit Breaker #2: Drawdown</h3>
        <p><strong>Trigger:</strong> Portfolio drops >30% from peak</p>
        <p><strong>Action:</strong> Halt all rebalancing, require manual review</p>
        <p><strong>Why:</strong> Protects against catastrophic losses, forces human oversight</p>
        <p><strong>Recovery:</strong> Manual reset after investigation</p>
    </div>
    """, unsafe_allow_html=True)

# Circuit breaker visualization
cb_scenarios = pd.DataFrame({
    'Scenario': ['Normal Day', 'Volatile Day', 'Circuit Breaker #1', 'Circuit Breaker #2'],
    'Daily Change': [0.5, -3, -6, -15],
    'Status': ['🟢 OK', '🟢 OK', '🔴 HALT', '🔴 HALT'],
    'Action': ['Rebalance if needed', 'Rebalance if needed', 'Wait 24h', 'Manual review required']
})

fig = go.Figure()

fig.add_trace(go.Bar(
    x=cb_scenarios['Scenario'],
    y=cb_scenarios['Daily Change'],
    marker_color=['#48bb78', '#4299e1', '#f56565', '#e53e3e'],
    text=cb_scenarios['Status'],
    textposition='outside',
    hovertemplate='<b>%{x}</b><br>Change: %{y}%<br>Action: %{text}<extra></extra>'
))

# Add circuit breaker threshold lines
fig.add_hline(y=-5, line_dash="dash", line_color="orange",
              annotation_text="Circuit Breaker #1: -5%",
              annotation_position="right")

fig.add_hline(y=-30, line_dash="dash", line_color="red",
              annotation_text="Circuit Breaker #2: -30%",
              annotation_position="right")

fig.update_layout(
    title="Circuit Breaker Triggers",
    height=400,
    yaxis_title="Daily Change %",
    font=dict(family='Inter'),
    showlegend=False
)

st.plotly_chart(fig, width='stretch')

st.markdown("---")

# Footer
st.markdown("""
## 🎓 Want to Learn More?

- 📖 [Ray Dalio's All Weather Strategy](https://www.bridgewater.com/research-and-insights/all-weather-strategy)
- 📊 [Modern Portfolio Theory](https://www.investopedia.com/terms/m/modernportfoliotheory.asp)
- 🔄 [Understanding Rebalancing](https://www.investopedia.com/terms/r/rebalancing.asp)
- 🛡️ [Risk Management in Investing](https://www.investopedia.com/terms/r/riskmanagement.asp)

---

<div style='text-align: center; padding: 2rem 0;'>
    <p style='color: #718096;'><strong>Ready to see it in action?</strong></p>
    <p style='color: #a0aec0;'>Go back to the main dashboard and click "Run Daily Check"!</p>
</div>
""", unsafe_allow_html=True)
