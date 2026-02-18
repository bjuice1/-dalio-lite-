"""
Strategy Selector - Choose or Customize Your Investment Strategy
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yaml
from pathlib import Path

# Import trust indicators
from trust_indicators import render_trust_bar

st.set_page_config(
    page_title="Strategy Selector - Dalio Lite",
    page_icon="🎯",
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
    .strategy-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .strategy-card:hover {
        border-color: #667eea;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        transform: translateY(-2px);
    }
    .strategy-card.selected {
        border-color: #667eea;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
        border-width: 3px;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .risk-low { background: #c6f6d5; color: #22543d; }
    .risk-medium { background: #feebc8; color: #7c2d12; }
    .risk-high { background: #fed7d7; color: #742a2a; }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("🎯 Strategy Selector")
st.markdown("### Choose Your Investment Track")
st.markdown("---")

# Load current config
config_file = Path("config.yaml")
if config_file.exists():
    with open(config_file, 'r') as f:
        current_config = yaml.safe_load(f)
    current_allocation = current_config['allocation']
else:
    current_allocation = None

# Define preset strategies
strategies = {
    "All Weather (Dalio)": {
        "allocation": {"VTI": 0.40, "TLT": 0.30, "GLD": 0.20, "DBC": 0.10},
        "risk": "Low-Medium",
        "volatility": "~8-10%",
        "expected_return": "7-10%",
        "description": "Balanced for all economic environments. Designed to weather storms.",
        "best_for": "Long-term investors seeking stability",
        "rebalance_frequency": "Monthly when drift >10%"
    },
    "60/40 Classic": {
        "allocation": {"VTI": 0.60, "TLT": 0.40, "GLD": 0.00, "DBC": 0.00},
        "risk": "Medium",
        "volatility": "~10-12%",
        "expected_return": "8-12%",
        "description": "Traditional balanced portfolio. 60% stocks, 40% bonds.",
        "best_for": "Moderate risk tolerance, pre-retirees",
        "rebalance_frequency": "Quarterly when drift >10%"
    },
    "Aggressive Growth": {
        "allocation": {"VTI": 0.80, "TLT": 0.10, "GLD": 0.05, "DBC": 0.05},
        "risk": "High",
        "volatility": "~15-18%",
        "expected_return": "10-15%",
        "description": "Heavy stocks for maximum growth. Higher risk, higher potential reward.",
        "best_for": "Young investors with long time horizon",
        "rebalance_frequency": "Monthly when drift >15%"
    },
    "Conservative Income": {
        "allocation": {"VTI": 0.20, "TLT": 0.50, "GLD": 0.20, "DBC": 0.10},
        "risk": "Low",
        "volatility": "~5-7%",
        "expected_return": "5-8%",
        "description": "Focus on preservation and income. Heavy bonds for stability.",
        "best_for": "Retirees, capital preservation",
        "rebalance_frequency": "Quarterly when drift >10%"
    },
    "Inflation Fighter": {
        "allocation": {"VTI": 0.25, "TLT": 0.15, "GLD": 0.35, "DBC": 0.25},
        "risk": "Medium",
        "volatility": "~12-14%",
        "expected_return": "8-12%",
        "description": "Heavily weighted to inflation-resistant assets (gold & commodities).",
        "best_for": "High inflation environments",
        "rebalance_frequency": "Monthly when drift >10%"
    }
}

# Strategy comparison
st.markdown("## 📊 Compare Strategies")

# Create comparison table
comparison_data = []
for name, data in strategies.items():
    comparison_data.append({
        'Strategy': name,
        'Risk Level': data['risk'],
        'Expected Return': data['expected_return'],
        'Volatility': data['volatility'],
        'VTI %': f"{data['allocation']['VTI']:.0%}",
        'TLT %': f"{data['allocation']['TLT']:.0%}",
        'GLD %': f"{data['allocation']['GLD']:.0%}",
        'DBC %': f"{data['allocation']['DBC']:.0%}"
    })

df_comparison = pd.DataFrame(comparison_data)
st.dataframe(df_comparison, width='stretch', hide_index=True)

st.markdown("---")

# Strategy selection
st.markdown("## 🎨 Choose or Customize Your Strategy")

selected_strategy = st.selectbox(
    "Select a preset strategy:",
    options=list(strategies.keys()) + ["Custom Allocation"],
    help="Choose a preset or create your own"
)

if selected_strategy == "Custom Allocation":
    st.markdown("### 🛠️ Custom Allocation Builder")

    st.info("💡 **Tip:** Allocations must sum to 100%")

    col1, col2 = st.columns(2)

    with col1:
        vti_pct = st.slider("🇺🇸 VTI (US Stocks)", 0, 100, 40, 5,
                           help="US Total Stock Market - Growth engine")
        tlt_pct = st.slider("📈 TLT (Long Bonds)", 0, 100, 30, 5,
                           help="20+ Year Treasury Bonds - Deflation hedge")

    with col2:
        gld_pct = st.slider("🥇 GLD (Gold)", 0, 100, 20, 5,
                           help="Gold ETF - Inflation hedge")
        dbc_pct = st.slider("🌾 DBC (Commodities)", 0, 100, 10, 5,
                           help="Commodities ETF - Inflation hedge")

    total = vti_pct + tlt_pct + gld_pct + dbc_pct

    if total == 100:
        st.success(f"✅ Total: {total}% - Ready to apply!")
    else:
        st.error(f"❌ Total: {total}% - Must equal 100%")

    custom_allocation = {
        "VTI": vti_pct / 100,
        "TLT": tlt_pct / 100,
        "GLD": gld_pct / 100,
        "DBC": dbc_pct / 100
    }

    # Show custom strategy preview
    fig = go.Figure(data=[go.Pie(
        labels=[f"VTI<br>{vti_pct}%", f"TLT<br>{tlt_pct}%",
                f"GLD<br>{gld_pct}%", f"DBC<br>{dbc_pct}%"],
        values=[vti_pct, tlt_pct, gld_pct, dbc_pct],
        hole=0.4,
        marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
        textfont=dict(size=16, color='white', family='Inter')
    )])
    fig.update_layout(title="Your Custom Allocation", height=400)
    st.plotly_chart(fig, width='stretch')

    if total == 100:
        if st.button("💾 Save Custom Strategy", type="primary"):
            # Update config file
            current_config['allocation'] = custom_allocation
            with open(config_file, 'w') as f:
                yaml.dump(current_config, f, default_flow_style=False)
            st.success("✅ Custom strategy saved! Restart dashboard to apply.")
            st.balloons()

else:
    # Show selected preset strategy
    strategy = strategies[selected_strategy]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"### {selected_strategy}")
        st.markdown(f"**Description:** {strategy['description']}")
        st.markdown(f"**Best for:** {strategy['best_for']}")
        st.markdown(f"**Rebalancing:** {strategy['rebalance_frequency']}")

        # Metrics
        st.markdown("**Key Metrics:**")
        risk_class = f"risk-{strategy['risk'].lower().replace('-', '').replace(' ', '')}"
        st.markdown(f"""
        <div>
            <span class='metric-badge {risk_class}'>Risk: {strategy['risk']}</span>
            <span class='metric-badge' style='background: #bee3f8; color: #2c5282;'>
                Expected Return: {strategy['expected_return']}
            </span>
            <span class='metric-badge' style='background: #e2e8f0; color: #2d3748;'>
                Volatility: {strategy['volatility']}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Allocation breakdown
        st.markdown("**Allocation:**")
        alloc_df = pd.DataFrame([
            {"Asset": "🇺🇸 VTI", "Percentage": f"{strategy['allocation']['VTI']:.0%}",
             "Dollar (on $100K)": f"${strategy['allocation']['VTI'] * 100000:,.0f}"},
            {"Asset": "📈 TLT", "Percentage": f"{strategy['allocation']['TLT']:.0%}",
             "Dollar (on $100K)": f"${strategy['allocation']['TLT'] * 100000:,.0f}"},
            {"Asset": "🥇 GLD", "Percentage": f"{strategy['allocation']['GLD']:.0%}",
             "Dollar (on $100K)": f"${strategy['allocation']['GLD'] * 100000:,.0f}"},
            {"Asset": "🌾 DBC", "Percentage": f"{strategy['allocation']['DBC']:.0%}",
             "Dollar (on $100K)": f"${strategy['allocation']['DBC'] * 100000:,.0f}"}
        ])
        st.dataframe(alloc_df, width='stretch', hide_index=True)

    with col2:
        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[f"VTI<br>{strategy['allocation']['VTI']:.0%}",
                   f"TLT<br>{strategy['allocation']['TLT']:.0%}",
                   f"GLD<br>{strategy['allocation']['GLD']:.0%}",
                   f"DBC<br>{strategy['allocation']['DBC']:.0%}"],
            values=list(strategy['allocation'].values()),
            hole=0.4,
            marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
            textfont=dict(size=16, color='white', family='Inter')
        )])
        fig.update_layout(title=selected_strategy, height=400, showlegend=False)
        st.plotly_chart(fig, width='stretch')

    # Apply button
    if st.button(f"✅ Apply {selected_strategy}", type="primary", use_container_width=True):
        # Update config file
        current_config['allocation'] = strategy['allocation']
        with open(config_file, 'w') as f:
            yaml.dump(current_config, f, default_flow_style=False)
        st.success(f"✅ {selected_strategy} applied! Restart dashboard to use new allocation.")
        st.balloons()

st.markdown("---")

# Risk comparison chart
st.markdown("## 📈 Risk vs. Return Comparison")

risk_return_data = pd.DataFrame({
    'Strategy': list(strategies.keys()),
    'Expected Return': [8.5, 10, 12.5, 6.5, 10],
    'Risk (Volatility)': [9, 11, 16.5, 6, 13],
    'Size': [100, 100, 100, 100, 100]
})

fig = go.Figure()

for i, row in risk_return_data.iterrows():
    fig.add_trace(go.Scatter(
        x=[row['Risk (Volatility)']],
        y=[row['Expected Return']],
        mode='markers+text',
        marker=dict(size=20, color=['#667eea', '#4299e1', '#f56565', '#48bb78', '#ed8936'][i]),
        text=row['Strategy'],
        textposition='top center',
        name=row['Strategy'],
        hovertemplate=f"<b>{row['Strategy']}</b><br>Return: {row['Expected Return']}%<br>Risk: {row['Risk (Volatility)']}%<extra></extra>"
    ))

fig.update_layout(
    title="Risk vs. Expected Return by Strategy",
    xaxis_title="Risk (Volatility %)",
    yaxis_title="Expected Annual Return %",
    height=500,
    font=dict(family='Inter'),
    showlegend=False
)

st.plotly_chart(fig, width='stretch')

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <p style='color: #718096;'>
        💡 <strong>Pro Tip:</strong> Test strategies in paper trading mode for 6 months before going live.
    </p>
    <p style='color: #a0aec0; font-size: 0.875rem;'>
        Past performance doesn't guarantee future results. Adjust based on your risk tolerance.
    </p>
</div>
""", unsafe_allow_html=True)
