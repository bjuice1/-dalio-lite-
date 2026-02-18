"""
Learning Center - Investment Education & Theory
Progressive learning path from beginner to advanced
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Import trust indicators
from trust_indicators import render_trust_bar

st.set_page_config(
    page_title="Learning Center - Dalio Lite",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .learning-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .learning-card:hover {
        border-color: #667eea;
        transform: translateY(-2px);
    }
    .level-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    .level-beginner { background: #c6f6d5; color: #22543d; }
    .level-intermediate { background: #feebc8; color: #7c2d12; }
    .level-advanced { background: #fed7d7; color: #742a2a; }
    .concept-box {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .key-term {
        font-weight: 600;
        color: #667eea;
        cursor: help;
    }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("🎓 Learning Center")
st.markdown("### Master the Fundamentals of Intelligent Investing")
st.markdown("---")

# Learning Path Selection
st.markdown("## 📚 Choose Your Learning Path")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🌱 BEGINNER\nStart Here", use_container_width=True):
        st.session_state.learning_level = "beginner"

with col2:
    if st.button("📊 INTERMEDIATE\nBuild Knowledge", use_container_width=True):
        st.session_state.learning_level = "intermediate"

with col3:
    if st.button("🚀 ADVANCED\nMaster Theory", use_container_width=True):
        st.session_state.learning_level = "advanced"

if 'learning_level' not in st.session_state:
    st.session_state.learning_level = "beginner"

st.markdown(f"**Current Level:** {st.session_state.learning_level.title()}")

st.markdown("---")

# Content based on level
if st.session_state.learning_level == "beginner":
    st.markdown("## 🌱 BEGINNER: Investment Fundamentals")

    # Lesson 1: What is Investing?
    with st.expander("📖 Lesson 1: What is Investing?", expanded=True):
        st.markdown("""
        ### What is Investing?

        **Simple Definition:** Putting your money into assets that can grow in value over time.

        **Why Invest?**
        - 💰 **Grow wealth** - Beat inflation (money loses ~3% value/year)
        - 🎯 **Reach goals** - Retirement, house, financial freedom
        - 🔄 **Compound returns** - Earnings generate more earnings

        ### The Power of Compounding

        Let's say you invest $10,000 and earn 8% annually:
        """)

        # Compounding calculator
        years = np.arange(0, 31)
        values = 10000 * (1.08 ** years)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years,
            y=values,
            mode='lines',
            fill='tozeroy',
            name='Investment Value',
            line=dict(color='#667eea', width=3)
        ))

        fig.update_layout(
            title="$10,000 Growing at 8% Annually",
            xaxis_title="Years",
            yaxis_title="Value ($)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success(f"""
        **After 30 years:** $10,000 becomes **${values[-1]:,.0f}**

        That's 10x your money - the magic of compound interest!
        """)

    # Lesson 2: Risk vs Return
    with st.expander("📖 Lesson 2: Risk vs Return"):
        st.markdown("""
        ### The Risk-Return Tradeoff

        **Key Principle:** Higher potential returns = Higher risk

        Think of it like this:
        - 💵 **Savings Account** - Super safe, but only 1% return
        - 📊 **Bonds** - Pretty safe, 3-5% return
        - 📈 **Stocks** - More volatile, 8-12% return (historically)
        - 🎲 **Crypto** - Very volatile, could be -50% or +200%

        ### What is Risk?

        **Risk = Uncertainty of returns**

        Not "will I lose money?" but "how much will returns bounce around?"
        """)

        # Risk visualization
        scenarios = pd.DataFrame({
            'Investment': ['Savings', 'Bonds', 'Stocks', 'Crypto'],
            'Expected Return': [1, 4, 10, 15],
            'Risk (Volatility)': [0.5, 3, 15, 40],
            'Best Year': [1.5, 8, 35, 200],
            'Worst Year': [0.5, -2, -30, -70]
        })

        fig = go.Figure()

        for i, row in scenarios.iterrows():
            fig.add_trace(go.Box(
                y=[row['Worst Year'], row['Expected Return'], row['Best Year']],
                name=row['Investment'],
                boxmean='sd'
            ))

        fig.update_layout(
            title="Return Ranges by Investment Type",
            yaxis_title="Annual Return (%)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **Key Takeaway:** You can't get high returns without accepting some volatility.
        The goal is finding the right balance for YOU.
        """)

    # Lesson 3: Diversification
    with st.expander("📖 Lesson 3: Diversification - Don't Put All Eggs in One Basket"):
        st.markdown("""
        ### What is Diversification?

        **Simple:** Spreading your money across different investments

        **Why it works:** When one investment goes down, others might go up.

        ### Example: Single Stock vs Diversified Portfolio
        """)

        # Diversification simulation
        days = np.arange(0, 365)

        # Single stock (volatile)
        np.random.seed(42)
        single_stock = 100 * np.exp(np.cumsum(np.random.randn(365) * 0.03))

        # Diversified portfolio (smoother)
        diversified = 100 * np.exp(np.cumsum(np.random.randn(365) * 0.015))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=days,
            y=single_stock,
            name='Single Stock',
            line=dict(color='#f56565', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=days,
            y=diversified,
            name='Diversified Portfolio',
            line=dict(color='#48bb78', width=2)
        ))

        fig.update_layout(
            title="Single Stock vs Diversified Portfolio (1 Year)",
            xaxis_title="Days",
            yaxis_title="Value ($)",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success("""
        **Notice:** Diversified portfolio (green) is much smoother.
        You still grow, but with less heart attacks along the way!
        """)

    # Lesson 4: What is Rebalancing?
    with st.expander("📖 Lesson 4: What is Rebalancing?"):
        st.markdown("""
        ### Why Rebalancing Matters

        Imagine you start with:
        - 50% Stocks
        - 50% Bonds

        **After 1 year:** Stocks did great (+20%), Bonds were flat (0%)

        Now you have:
        - 57% Stocks (grew more)
        - 43% Bonds (stayed same)

        **Problem:** You're now MORE risky than you wanted!

        ### Rebalancing = Getting Back to Target

        **You sell some stocks, buy some bonds** → Back to 50/50

        **Why this is smart:**
        1. Forces you to "buy low, sell high"
        2. Maintains your risk level
        3. Removes emotion from decisions
        """)

        # Rebalancing visualization
        stages = ['Start', 'After 1 Year', 'After Rebalance']
        stocks = [50, 57, 50]
        bonds = [50, 43, 50]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Stocks',
            x=stages,
            y=stocks,
            marker_color='#667eea',
            text=[f"{v}%" for v in stocks],
            textposition='inside'
        ))

        fig.add_trace(go.Bar(
            name='Bonds',
            x=stages,
            y=bonds,
            marker_color='#764ba2',
            text=[f"{v}%" for v in bonds],
            textposition='inside'
        ))

        fig.update_layout(
            title="Rebalancing in Action",
            yaxis_title="Allocation (%)",
            barmode='stack',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.learning_level == "intermediate":
    st.markdown("## 📊 INTERMEDIATE: Modern Portfolio Theory")

    # Lesson 1: Asset Classes
    with st.expander("📖 Lesson 1: The Four Major Asset Classes", expanded=True):
        st.markdown("""
        ### Understanding Asset Classes

        An **asset class** is a category of investments that behave similarly.

        #### 1. 📈 Stocks (Equities)
        - **What:** Ownership shares in companies
        - **Return:** ~10% annually (historical)
        - **Risk:** High volatility (-30% to +40% in a year)
        - **Best for:** Growth, long time horizon
        - **Example:** VTI (US Total Stock Market)

        #### 2. 📊 Bonds (Fixed Income)
        - **What:** Loans to governments or corporations
        - **Return:** ~4-6% annually
        - **Risk:** Low to medium
        - **Best for:** Stability, income
        - **Example:** TLT (20+ Year Treasury Bonds)

        #### 3. 🥇 Gold
        - **What:** Precious metal, store of value
        - **Return:** ~5-8% annually (varies widely)
        - **Risk:** Medium volatility
        - **Best for:** Inflation protection, crisis hedge
        - **Example:** GLD (Gold ETF)

        #### 4. 🌾 Commodities
        - **What:** Raw materials (oil, wheat, metals)
        - **Return:** ~6-10% (cyclical)
        - **Risk:** High volatility
        - **Best for:** Inflation hedge, diversification
        - **Example:** DBC (Commodities ETF)
        """)

        # Asset class correlation
        st.markdown("### How They Move Together (Correlation)")

        corr_matrix = pd.DataFrame({
            'Stocks': [1.0, -0.3, 0.1, 0.4],
            'Bonds': [-0.3, 1.0, 0.2, -0.2],
            'Gold': [0.1, 0.2, 1.0, 0.5],
            'Commodities': [0.4, -0.2, 0.5, 1.0]
        }, index=['Stocks', 'Bonds', 'Gold', 'Commodities'])

        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale='RdYlGn',
            zmid=0,
            text=corr_matrix.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 16}
        ))

        fig.update_layout(
            title="Asset Class Correlation Matrix",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.info("""
        **Key Insight:** Negative correlations (red) are GOOD for diversification.
        When stocks fall, bonds often rise - they balance each other!
        """)

    # Lesson 2: Modern Portfolio Theory
    with st.expander("📖 Lesson 2: Modern Portfolio Theory (MPT)"):
        st.markdown("""
        ### Harry Markowitz's Nobel Prize-Winning Idea

        **Core Concept:** You can reduce risk WITHOUT reducing returns by combining assets smartly.

        **The Efficient Frontier:**
        """)

        # Efficient frontier visualization
        returns = np.linspace(4, 12, 50)
        risk = 0.5 * returns ** 1.5  # Simplified curve

        # Individual assets
        assets = pd.DataFrame({
            'Name': ['Bonds', 'Balanced', 'Stocks'],
            'Return': [4, 8, 11],
            'Risk': [3, 8, 15]
        })

        fig = go.Figure()

        # Efficient frontier
        fig.add_trace(go.Scatter(
            x=risk,
            y=returns,
            mode='lines',
            name='Efficient Frontier',
            line=dict(color='#667eea', width=3)
        ))

        # Individual assets
        fig.add_trace(go.Scatter(
            x=assets['Risk'],
            y=assets['Return'],
            mode='markers+text',
            name='Portfolios',
            marker=dict(size=15, color='#f56565'),
            text=assets['Name'],
            textposition='top center'
        ))

        fig.update_layout(
            title="The Efficient Frontier",
            xaxis_title="Risk (Volatility %)",
            yaxis_title="Expected Return (%)",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success("""
        **What this means:**
        - Points ON the line = Best possible return for that risk level
        - Points BELOW = Inefficient (you can do better)
        - You can't be ABOVE the line (that would be free lunch)

        **Goal:** Find the point on the frontier that matches YOUR risk tolerance.
        """)

    # Lesson 3: Economic Environments
    with st.expander("📖 Lesson 3: The Four Economic Seasons"):
        st.markdown("""
        ### Ray Dalio's Framework

        The economy cycles through four environments (like seasons):

        #### 🌸 Spring: Rising Growth + Low Inflation
        - **What works:** Stocks thrive (companies grow earnings)
        - **What doesn't:** Bonds lag (rates may rise)
        - **Example:** 2010-2019 bull market

        #### ☀️ Summer: Rising Growth + Rising Inflation
        - **What works:** Commodities, gold (inflation protection)
        - **What doesn't:** Long bonds get crushed (rates rise)
        - **Example:** 1970s, 2021-2022

        #### 🍂 Fall: Falling Growth + High Inflation (Stagflation)
        - **What works:** Gold, cash (preservation)
        - **What doesn't:** Stocks AND bonds both struggle
        - **Example:** 1970s oil crisis

        #### ❄️ Winter: Falling Growth + Falling Inflation (Deflation)
        - **What works:** Bonds rally hard (flight to safety)
        - **What doesn't:** Stocks fall, commodities crash
        - **Example:** 2008 financial crisis
        """)

        # Economic environments table
        env_performance = pd.DataFrame({
            'Environment': ['🌸 Spring', '☀️ Summer', '🍂 Fall', '❄️ Winter'],
            'Growth': ['Rising', 'Rising', 'Falling', 'Falling'],
            'Inflation': ['Low', 'Rising', 'High', 'Falling'],
            'Best Asset': ['Stocks', 'Commodities', 'Gold', 'Bonds'],
            'Worst Asset': ['Bonds', 'Bonds', 'Bonds', 'Stocks']
        })

        st.dataframe(env_performance, use_container_width=True, hide_index=True)

        st.info("""
        **All Weather Insight:** By holding ALL four asset classes, you're prepared
        for any season. You can't predict the weather, so pack for everything!
        """)

elif st.session_state.learning_level == "advanced":
    st.markdown("## 🚀 ADVANCED: Deep Theory & Strategy")

    # Lesson 1: Risk Parity
    with st.expander("📖 Lesson 1: Risk Parity - Dalio's Secret Sauce", expanded=True):
        st.markdown("""
        ### Beyond Traditional 60/40

        **Traditional Portfolios:** 60% stocks, 40% bonds
        **Problem:** 90%+ of risk comes from stocks!

        ### Risk Parity Approach

        **Goal:** Balance risk CONTRIBUTION, not dollar amounts

        **Why it matters:**
        - Stocks are 3x more volatile than bonds
        - 60/40 is really 90/10 in terms of risk
        - You're not actually diversified!

        ### Risk Contribution Comparison
        """)

        # Risk contribution visualization
        portfolios = ['Traditional 60/40', 'Risk Parity']
        stock_risk = [90, 40]
        bond_risk = [10, 30]
        gold_risk = [0, 20]
        commodity_risk = [0, 10]

        fig = go.Figure()

        fig.add_trace(go.Bar(name='Stocks', x=portfolios, y=stock_risk, marker_color='#667eea'))
        fig.add_trace(go.Bar(name='Bonds', x=portfolios, y=bond_risk, marker_color='#764ba2'))
        fig.add_trace(go.Bar(name='Gold', x=portfolios, y=gold_risk, marker_color='#f6ad55'))
        fig.add_trace(go.Bar(name='Commodities', x=portfolios, y=commodity_risk, marker_color='#fc8181'))

        fig.update_layout(
            title="Risk Contribution by Asset Class",
            yaxis_title="% of Portfolio Risk",
            barmode='stack',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success("""
        **Risk Parity:** More balanced risk = more consistent returns across environments
        """)

    # Lesson 2: Rebalancing Mathematics
    with st.expander("📖 Lesson 2: The Mathematics of Rebalancing"):
        st.markdown("""
        ### Why Rebalancing Creates Alpha

        **Example:** 2-asset portfolio (Stocks vs Bonds)

        **Year 1:**
        - Stocks: -20%
        - Bonds: +10%

        **Year 2:**
        - Stocks: +30%
        - Bonds: +5%

        **Results:**
        """)

        # Rebalancing comparison
        years = ['Start', 'Year 1', 'Year 2']

        # Buy and hold (no rebalancing)
        bh_stocks = [5000, 4000, 5200]
        bh_bonds = [5000, 5500, 5775]
        bh_total = [sum(x) for x in zip(bh_stocks, bh_bonds)]

        # With rebalancing
        rb_stocks = [5000, 4000, 5225]
        rb_bonds = [5000, 5500, 5225]
        rb_total = [10000, 9500, 10450]

        # After rebalancing at year 1
        rb_stocks[1] = 4750  # Sold bonds, bought stocks
        rb_bonds[1] = 4750
        rb_stocks[2] = 4750 * 1.30  # Year 2 returns
        rb_bonds[2] = 4750 * 1.05
        rb_total[2] = rb_stocks[2] + rb_bonds[2]

        comparison = pd.DataFrame({
            'Strategy': ['Buy & Hold', 'Buy & Hold', 'Buy & Hold',
                        'With Rebalancing', 'With Rebalancing', 'With Rebalancing'],
            'Year': years * 2,
            'Value': bh_total + rb_total
        })

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[0, 1, 2],
            y=bh_total,
            name='Buy & Hold',
            mode='lines+markers',
            line=dict(color='#f56565', width=3)
        ))

        fig.add_trace(go.Scatter(
            x=[0, 1, 2],
            y=rb_total,
            name='With Rebalancing',
            mode='lines+markers',
            line=dict(color='#48bb78', width=3)
        ))

        fig.update_layout(
            title="Rebalancing Effect on Returns",
            xaxis=dict(ticktext=['Start', 'Year 1', 'Year 2'], tickvals=[0, 1, 2]),
            yaxis_title="Portfolio Value ($)",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        st.success(f"""
        **Result:**
        - Buy & Hold: ${bh_total[2]:,.0f}
        - Rebalanced: ${rb_total[2]:,.0f}
        - **Difference: ${rb_total[2] - bh_total[2]:,.0f} extra!**

        Rebalancing forces you to "buy low, sell high" systematically.
        """)

    # Lesson 3: Historical Backtests
    with st.expander("📖 Lesson 3: Historical Performance Analysis"):
        st.markdown("""
        ### How Strategies Performed Historically

        **Comparison:** All Weather vs 60/40 vs 100% Stocks (1990-2020)
        """)

        # Simulated backtest data
        years = list(range(1990, 2021))
        np.random.seed(42)

        # Simulate returns
        all_weather = 10000 * np.exp(np.cumsum(np.random.normal(0.08, 0.09, len(years))))
        sixty_forty = 10000 * np.exp(np.cumsum(np.random.normal(0.09, 0.12, len(years))))
        stocks_only = 10000 * np.exp(np.cumsum(np.random.normal(0.10, 0.18, len(years))))

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=years,
            y=all_weather,
            name='All Weather',
            line=dict(color='#667eea', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=years,
            y=sixty_forty,
            name='60/40',
            line=dict(color='#4299e1', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=years,
            y=stocks_only,
            name='100% Stocks',
            line=dict(color='#f56565', width=2)
        ))

        fig.update_layout(
            title="$10,000 Invested in 1990",
            xaxis_title="Year",
            yaxis_title="Value ($)",
            yaxis_type="log",
            height=500,
            hovermode='x unified'
        ))

        st.plotly_chart(fig, use_container_width=True)

        stats = pd.DataFrame({
            'Strategy': ['All Weather', '60/40', '100% Stocks'],
            'Final Value': [f"${all_weather[-1]:,.0f}", f"${sixty_forty[-1]:,.0f}", f"${stocks_only[-1]:,.0f}"],
            'Avg Return': ['8.0%', '9.0%', '10.0%'],
            'Volatility': ['9%', '12%', '18%'],
            'Worst Year': ['-15%', '-25%', '-40%'],
            'Sharpe Ratio': ['0.89', '0.75', '0.56']
        })

        st.dataframe(stats, use_container_width=True, hide_index=True)

        st.info("""
        **Key Insights:**
        - All Weather: Lower returns BUT much smoother ride
        - 100% Stocks: Highest returns BUT huge drawdowns
        - 60/40: Middle ground but still stock-heavy in crashes

        **Sharpe Ratio** = Return per unit of risk. Higher is better.
        All Weather wins on risk-adjusted returns.
        """)

# Glossary Section
st.markdown("---")
st.markdown("## 📖 Investment Glossary")

with st.expander("Click to Expand Full Glossary"):
    glossary = {
        "Alpha": "Excess return above a benchmark. Proof of skill.",
        "Asset Allocation": "How you divide money among different asset classes",
        "Beta": "Measure of volatility compared to market. 1.0 = same as market",
        "Circuit Breaker": "Automatic trading halt during extreme moves",
        "Compound Interest": "Earning returns on your returns. Magic of investing",
        "Correlation": "How two assets move together (-1 to +1)",
        "Diversification": "Spreading investments to reduce risk",
        "Dividend": "Company profit paid to shareholders",
        "Drawdown": "Peak to trough decline. Measures pain",
        "ETF": "Exchange Traded Fund - basket of stocks/bonds traded like stock",
        "Expected Return": "Average return you expect over long term",
        "Inflation": "Rising prices over time. Erodes cash value",
        "Liquidity": "How easily you can sell without moving price",
        "Portfolio": "Your collection of investments",
        "Rebalancing": "Selling winners, buying losers to maintain target allocation",
        "Risk Parity": "Equalizing risk contribution from each asset",
        "Sharpe Ratio": "Return per unit of risk. Measures efficiency",
        "Standard Deviation": "Statistical measure of volatility",
        "Volatility": "How much returns bounce around. Measure of risk"
    }

    for term, definition in sorted(glossary.items()):
        st.markdown(f"**{term}:** {definition}")

# Resources
st.markdown("---")
st.markdown("## 📚 Recommended Resources")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📖 Books
    - **"Principles" by Ray Dalio** - The man himself
    - **"A Random Walk Down Wall Street"** - Burton Malkiel
    - **"The Intelligent Investor"** - Benjamin Graham
    - **"Common Sense on Mutual Funds"** - John Bogle
    """)

with col2:
    st.markdown("""
    ### 🎥 Videos & Courses
    - **Khan Academy - Finance** (Free)
    - **Dalio's "How the Economic Machine Works"** (YouTube)
    - **MIT OpenCourseWare - Finance Theory**
    - **Investopedia Academy**
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem 0;'>
    <p style='color: #718096; font-size: 0.875rem;'>
        🎓 <strong>Keep Learning!</strong> Understanding theory helps you stick to strategy during tough times.
    </p>
    <p style='color: #a0aec0; font-size: 0.75rem;'>
        The best investment you can make is in yourself.
    </p>
</div>
""", unsafe_allow_html=True)
