"""
Dalio Lite - Premium Web Dashboard
Beautiful, modern interface for your All Weather portfolio
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
import json

# Import new error handling and trust indicators
from error_handler import translate_exception, handle_error_display, safe_execute
from trust_indicators import render_trust_bar, render_paper_trading_warning, render_live_trading_warning
from goal_tracker import GoalTracker

# Page config
st.set_page_config(
    page_title="Dalio Lite - Portfolio Manager",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium custom CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styles */
    * {
        font-family: 'Inter', sans-serif !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Main content area */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Content container */
    .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
        background: white;
        border-radius: 20px;
        margin: 2rem auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    }

    /* Headers */
    h1 {
        font-size: 3rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        margin-top: 2rem !important;
    }

    h3 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #4a5568 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }

    /* Secondary button */
    .stButton > button:not([kind="primary"]) {
        background: white !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #2d3748 !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        color: #718096 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    [data-testid="stMetricDelta"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }

    /* Success box */
    .stSuccess {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
        color: white !important;
    }

    /* Info box */
    .stInfo {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        color: white !important;
    }

    /* Warning box */
    .stWarning {
        background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%) !important;
        color: white !important;
    }

    /* Error box */
    .stError {
        background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%) !important;
        color: white !important;
    }

    /* Dataframe */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Text area */
    .stTextArea textarea {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        font-family: 'Monaco', monospace !important;
        font-size: 0.875rem !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-radius: 12px;
        font-weight: 600;
    }

    /* Custom cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }

    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-success {
        background: #c6f6d5;
        color: #22543d;
    }

    .status-warning {
        background: #feebc8;
        color: #7c2d12;
    }

    .status-error {
        background: #fed7d7;
        color: #742a2a;
    }

    .status-info {
        background: #bee3f8;
        color: #2c5282;
    }

    /* Pulse animation for live status */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    .pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }

    /* Separator */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'dalio' not in st.session_state:
    st.session_state.dalio = None
if 'last_check' not in st.session_state:
    st.session_state.last_check = None
if 'execution_count' not in st.session_state:
    st.session_state.execution_count = 0

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ SETTINGS")
    st.markdown("---")

    # Connection status
    env_file = Path(".env")
    if env_file.exists():
        st.markdown("<div class='status-badge status-success'>✅ ENV FILE FOUND</div>", unsafe_allow_html=True)
        st.markdown("")

        # Connect button
        if not st.session_state.connected:
            if st.button("🔌 CONNECT TO ALPACA", type="primary"):
                try:
                    from dalio_lite import DalioLite
                    with st.spinner("Connecting..."):
                        st.session_state.dalio = DalioLite()
                        st.session_state.connected = True
                    st.rerun()
                except Exception as e:
                    message, severity = translate_exception(e, context="Connecting to Alpaca")
                    handle_error_display(message, severity)
        else:
            st.markdown("<div class='status-badge status-success pulse'>🟢 CONNECTED</div>", unsafe_allow_html=True)

            # Disconnect button
            if st.button("🔌 DISCONNECT"):
                st.session_state.connected = False
                st.session_state.dalio = None
                st.rerun()

    else:
        st.markdown("<div class='status-badge status-error'>❌ ENV FILE MISSING</div>", unsafe_allow_html=True)
        st.warning("Create .env file with Alpaca API keys")

    st.markdown("---")

    # Mode indicator
    if st.session_state.connected and st.session_state.dalio:
        mode = st.session_state.dalio.config['mode']['paper_trading']
        if mode:
            st.markdown("<div class='status-badge status-info'>📄 PAPER TRADING</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-badge status-error'>🚨 LIVE TRADING</div>", unsafe_allow_html=True)

    st.markdown("---")

    # AutoPilot status
    st.markdown("### 🤖 AUTO-PILOT")
    autopilot_status_file = Path("state/autopilot_status.json")
    if autopilot_status_file.exists():
        try:
            with open(autopilot_status_file, 'r') as f:
                autopilot_status = json.load(f)

            if autopilot_status.get('enabled'):
                st.markdown("<div class='status-badge status-success pulse'>🟢 ENABLED</div>", unsafe_allow_html=True)
                st.markdown(f"**Schedule:** Daily at {autopilot_status.get('schedule', 'N/A')}")
                if autopilot_status.get('notifications'):
                    st.markdown(f"📧 {autopilot_status.get('email', 'Email enabled')}")

                st.info("✨ System runs automatically. You'll receive email notifications.")
            else:
                st.markdown("<div class='status-badge status-warning'>⏸️ DISABLED</div>", unsafe_allow_html=True)
        except:
            st.markdown("<div class='status-badge status-warning'>⏸️ NOT CONFIGURED</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-badge status-warning'>⏸️ NOT CONFIGURED</div>", unsafe_allow_html=True)
        st.warning("Enable Auto-Pilot for hands-free portfolio management")

        if st.button("🚀 ENABLE AUTO-PILOT", type="primary", use_container_width=True):
            st.info("""
            **To enable Auto-Pilot:**

            1. Open Terminal
            2. Navigate to: `dalio-lite` folder
            3. Run: `./setup_autopilot.sh`
            4. Follow the prompts

            This will schedule daily checks and email notifications.
            """)

    st.markdown("---")

    # Quick stats
    st.markdown("### 📊 SESSION STATS")
    if st.session_state.last_check:
        st.metric("Last Check", st.session_state.last_check.strftime("%H:%M:%S"))
    st.metric("Actions", st.session_state.execution_count)

    st.markdown("---")
    st.markdown("### 🎯 TARGET ALLOCATION")
    st.markdown("""
    - 📈 **VTI** - 40%
    - 📊 **TLT** - 30%
    - 🥇 **GLD** - 20%
    - 🌾 **DBC** - 10%
    """)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("💰 Dalio Lite")
    st.markdown("### Automated All Weather Portfolio Manager")

with col2:
    if st.session_state.connected:
        st.markdown("<div style='text-align: right; margin-top: 2rem;'><div class='status-badge status-success pulse'>● LIVE</div></div>", unsafe_allow_html=True)

st.markdown("---")

# Trust indicators and trading mode warnings
if st.session_state.connected:
    render_trust_bar()
    render_paper_trading_warning()
    render_live_trading_warning()

# Main content
if not st.session_state.connected:
    # Hero section for non-connected state
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <div style='font-size: 4rem; margin-bottom: 1rem;'>🚀</div>
        <h2 style='font-size: 2rem; margin-bottom: 1rem;'>Get Started in 3 Easy Steps</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 2.5rem; text-align: center; margin-bottom: 1rem;'>1️⃣</div>
            <h3 style='text-align: center; margin-bottom: 1rem;'>Setup API Keys</h3>
            <p style='text-align: center; color: #718096;'>Add your Alpaca API keys to the .env file</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 2.5rem; text-align: center; margin-bottom: 1rem;'>2️⃣</div>
            <h3 style='text-align: center; margin-bottom: 1rem;'>Connect</h3>
            <p style='text-align: center; color: #718096;'>Click "Connect to Alpaca" in the sidebar</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div style='font-size: 2.5rem; text-align: center; margin-bottom: 1rem;'>3️⃣</div>
            <h3 style='text-align: center; margin-bottom: 1rem;'>Run & Relax</h3>
            <p style='text-align: center; color: #718096;'>Let the system manage your portfolio automatically</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # What is Dalio Lite section
    st.markdown("---")
    st.markdown("## 📖 What is Dalio Lite?")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **Dalio Lite** implements Ray Dalio's legendary "All Weather" portfolio strategy -
        a balanced approach designed to perform well in any economic environment.

        ### Why All Weather?
        - ✅ **Diversified across asset classes** - Stocks, bonds, gold, commodities
        - ✅ **Weather any storm** - Designed for inflation, deflation, growth, recession
        - ✅ **Proven track record** - 30+ years of stable returns
        - ✅ **Automated rebalancing** - Set it and forget it

        ### How it works:
        The system automatically monitors your portfolio daily and rebalances when
        your allocation drifts more than 10% from the target, ensuring you stay on strategy.
        """)

    with col2:
        # Simple allocation chart
        fig = go.Figure(data=[go.Pie(
            labels=['VTI<br>40%', 'TLT<br>30%', 'GLD<br>20%', 'DBC<br>10%'],
            values=[40, 30, 20, 10],
            hole=0.4,
            marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
            textfont=dict(size=16, color='white', family='Inter')
        )])
        fig.update_layout(
            title="Target Allocation",
            height=300,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, width='stretch')

else:
    # Connected state - Full dashboard with progressive disclosure
    dalio = st.session_state.dalio

    # Fetch account data
    try:
        account = dalio.trading_client.get_account()
        portfolio_value = float(account.portfolio_value)
        cash = float(account.cash)
        equity = float(account.equity)
        daily_pl = float(account.equity) - float(account.last_equity)
        daily_pl_pct = (daily_pl / float(account.last_equity) * 100) if float(account.last_equity) > 0 else 0

    except Exception as e:
        message, severity = translate_exception(e, context="Fetching account data")
        handle_error_display(message, severity)
        portfolio_value = 0
        cash = 0
        equity = 0
        daily_pl = 0
        daily_pl_pct = 0

    # ========================================
    # HERO SECTION - Portfolio Value + Goal Progress
    # ========================================

    # Large portfolio value display
    st.markdown(f"""
    <div style='text-align: center; padding: 2rem 0 1rem 0;'>
        <div style='font-size: 1rem; color: #718096; margin-bottom: 0.5rem;'>Total Portfolio Value</div>
        <div style='font-size: 4rem; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            ${portfolio_value:,.0f}
        </div>
        <div style='font-size: 1.2rem; color: {'#48bb78' if daily_pl >= 0 else '#f56565'}; margin-top: 0.5rem;'>
            {'+' if daily_pl >= 0 else ''}{daily_pl:,.2f} ({daily_pl_pct:+.2f}%) today
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Goal progress (if goal exists)
    try:
        tracker = GoalTracker()
        progress = tracker.get_goal_progress(portfolio_value)

        if progress.get("has_goal"):
            # Goal progress bar
            progress_pct = progress['progress_percentage']
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); padding: 1rem; border-radius: 12px; margin: 1rem 0;'>
                <div style='font-size: 0.875rem; color: #4a5568; margin-bottom: 0.5rem;'>
                    🎯 Goal: {progress['goal_name']} • Target: ${progress['target_amount']:,.0f} by {progress['target_year']}
                </div>
                <div style='background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;'>
                    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {min(100, progress_pct):.1f}%;'></div>
                </div>
                <div style='font-size: 0.875rem; color: #718096; margin-top: 0.5rem;'>
                    {progress_pct:.1f}% complete • {progress['years_remaining']} years remaining
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # No goal - show CTA
            st.info("🎯 **Set a financial goal** to see your progress here. Visit the Goals page to get started.", icon="💡")

    except Exception:
        # Silently fail if goal tracking isn't available
        pass

    st.markdown("---")

    # ========================================
    # KEY METRICS - Reduced to 3 most important
    # ========================================

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "💵 Cash Available",
            f"${cash:,.2f}",
            help="Available cash for trading"
        )

    with col2:
        st.metric(
            "📊 Total Equity",
            f"${equity:,.2f}",
            help="Current equity value"
        )

    with col3:
        # Show last check time if available
        if 'last_check' in st.session_state and st.session_state.last_check:
            last_check_time = st.session_state.last_check.strftime("%I:%M %p")
            st.metric(
                "🕐 Last Check",
                last_check_time,
                help="When the system last ran a rebalance check"
            )
        else:
            st.metric(
                "🕐 Last Check",
                "Never",
                help="Run your first daily check to start automated management"
            )

    st.markdown("---")

    # ========================================
    # PRIMARY ACTION - Prominent CTA
    # ========================================

    st.markdown("## ⚡ What do you want to do?")

    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:
        if st.button("🔄 RUN DAILY CHECK", type="primary", use_container_width=True, help="Check if rebalancing is needed and execute if necessary"):
            with st.spinner("🔄 Running daily check..."):
                try:
                    dalio.run_daily_check(dry_run=False)
                    st.session_state.last_check = datetime.now()
                    st.session_state.execution_count += 1
                    st.success("✅ Daily check complete!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    message, severity = translate_exception(e, context="Running daily check")
                    handle_error_display(message, severity)

    with action_col2:
        if st.button("🧪 DRY RUN", use_container_width=True, help="Preview what would happen without executing trades"):
            with st.spinner("🧪 Running dry run..."):
                try:
                    dalio.run_daily_check(dry_run=True)
                    st.session_state.last_check = datetime.now()
                    st.session_state.execution_count += 1
                    st.success("✅ Dry run complete!")
                    st.rerun()
                except Exception as e:
                    message, severity = translate_exception(e, context="Running dry run")
                    handle_error_display(message, severity)

    with action_col3:
        if st.button("📊 GENERATE REPORT", use_container_width=True, help="Create a performance summary"):
            with st.spinner("📊 Generating report..."):
                try:
                    report = dalio.generate_performance_report()
                    st.success("✅ Report generated!")
                    st.json(report)
                except Exception as e:
                    message, severity = translate_exception(e, context="Generating report")
                    handle_error_display(message, severity)

    st.markdown("---")

    # ========================================
    # DETAILED SECTIONS - All in Expanders (Progressive Disclosure)
    # ========================================

    # Portfolio Allocation Details (Collapsed by default)
    with st.expander("📊 **Portfolio Allocation** - See current vs. target breakdown", expanded=False):
        try:
            current_positions = dalio.get_current_positions()
            target_allocation = dalio.config['allocation']

            # Two-column layout for charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                # Current allocation pie chart
                if sum(current_positions.values()) > 0:
                    fig = go.Figure(data=[go.Pie(
                        labels=[f"{k}<br>{v:.1%}" for k, v in current_positions.items()],
                        values=list(current_positions.values()),
                        hole=0.4,
                        marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
                        textfont=dict(size=14, color='white', family='Inter')
                    )])
                    fig.update_layout(
                        title="Current Allocation",
                        height=350,
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
                    )
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("📭 No positions yet - run your first rebalance!")

            with chart_col2:
                # Target allocation pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=[f"{k}<br>{v:.1%}" for k, v in target_allocation.items()],
                    values=list(target_allocation.values()),
                    hole=0.4,
                    marker=dict(colors=['#667eea', '#764ba2', '#f6ad55', '#fc8181']),
                    textfont=dict(size=14, color='white', family='Inter')
                )])
                fig.update_layout(
                    title="Target Allocation",
                    height=350,
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1)
                )
                st.plotly_chart(fig, width='stretch')

            # Allocation comparison table
            st.markdown("### Allocation Details")

            allocation_data = []
            for ticker in target_allocation.keys():
                current_pct = current_positions.get(ticker, 0.0)
                target_pct = target_allocation[ticker]
                drift = current_pct - target_pct
                drift_pct = (drift / target_pct * 100) if target_pct > 0 else 0

                # Calculate dollar values
                current_value = portfolio_value * current_pct
                target_value = portfolio_value * target_pct

                allocation_data.append({
                    'Ticker': ticker,
                    'Current $': f"${current_value:,.0f}",
                    'Current %': f"{current_pct:.1%}",
                    'Target %': f"{target_pct:.1%}",
                    'Drift': f"{drift:+.1%}",
                    'Status': '🔴' if abs(drift) > 0.10 else '🟢'
                })

            df = pd.DataFrame(allocation_data)
            st.dataframe(df, width='stretch', hide_index=True)

        except Exception as e:
            message, severity = translate_exception(e, context="Loading portfolio data")
            handle_error_display(message, severity)

    # System Status (Collapsed by default)
    with st.expander("📏 **System Status** - Check rebalance needs", expanded=False):
        try:
            needs_rebal, reason = dalio.needs_rebalancing()

            if needs_rebal:
                st.markdown("<div class='status-badge status-error'>🔴 REBALANCE NEEDED</div>", unsafe_allow_html=True)
                st.info(reason)
            else:
                st.markdown("<div class='status-badge status-success'>🟢 ON TARGET</div>", unsafe_allow_html=True)
                st.info(reason)

            # Circuit breakers
            triggered, cb_reason = dalio.check_circuit_breakers()
            st.markdown("**Circuit Breakers:**")
            if triggered:
                st.markdown("<div class='status-badge status-error'>🛑 TRIGGERED</div>", unsafe_allow_html=True)
                st.warning(cb_reason)
            else:
                st.markdown("<div class='status-badge status-success'>✅ ALL CLEAR</div>", unsafe_allow_html=True)

        except Exception as e:
            message, severity = translate_exception(e, context="Checking system status")
            handle_error_display(message, severity)

    # Advanced Actions (Collapsed by default)
    with st.expander("⚙️ **Advanced Actions** - Force rebalance and manual controls", expanded=False):
        st.warning("**⚠️ Warning:** Force Rebalance bypasses all safety checks and circuit breakers")

        if st.button("⚡ FORCE REBALANCE", use_container_width=True):
            with st.spinner("⚡ Executing rebalance..."):
                try:
                    dalio.execute_rebalance(dry_run=False)
                    st.session_state.execution_count += 1
                    st.success("✅ Rebalance complete!")
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    message, severity = translate_exception(e, context="Executing force rebalance")
                    handle_error_display(message, severity)

    # Recent Activity Log (Collapsed by default)
    with st.expander("📜 **Recent Activity** - View system logs", expanded=False):
        log_file = Path("logs/dalio_lite.log")
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-30:]

                log_text = "".join(recent_lines)
                st.text_area("Log Output", log_text, height=250, help="Last 30 lines from system log", label_visibility="collapsed")

            except Exception as e:
                message, severity = translate_exception(e, context="Reading log file")
                handle_error_display(message, severity)
        else:
            st.info("📭 No activity yet - run your first check to see logs!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <p style='color: #718096; font-size: 0.875rem;'>
        <strong>Dalio Lite v1.0</strong> | Paper Trading Mode | Built with ❤️ using Streamlit
    </p>
    <p style='color: #a0aec0; font-size: 0.75rem;'>
        ⚠️ Not financial advice. Past performance doesn't guarantee future results.
    </p>
</div>
""", unsafe_allow_html=True)
