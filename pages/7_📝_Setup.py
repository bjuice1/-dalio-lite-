"""
Setup Guide - Step-by-step onboarding instructions for Dalio Lite
"""

import streamlit as st
from pathlib import Path

# Import trust indicators
from trust_indicators import render_trust_bar

st.set_page_config(
    page_title="Setup Guide - Dalio Lite",
    page_icon="📝",
    layout="wide"
)

# Custom CSS (matching other pages)
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
    .step-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .step-card.complete {
        border-color: #48bb78;
        background: rgba(72, 187, 120, 0.05);
    }
    .code-block {
        background: #2d3748;
        color: #e2e8f0;
        padding: 1rem;
        border-radius: 8px;
        font-family: 'Courier New', monospace;
        font-size: 0.875rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("📝 Setup Guide")
st.markdown("### Get started with Dalio Lite in 3 simple steps")
st.markdown("---")

# Introduction
st.markdown("""
Welcome to Dalio Lite! This guide will help you get set up and running in under 5 minutes.

**What you'll need:**
- An Alpaca account (free to sign up)
- 5 minutes to follow these steps
- Basic familiarity with text files
""")

st.markdown("---")

# Progress indicator
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class='step-card'>
        <div style='font-size: 2rem; text-align: center; margin-bottom: 0.5rem;'>1️⃣</div>
        <h3 style='text-align: center; margin-bottom: 0.5rem;'>Create Account</h3>
        <p style='text-align: center; color: #718096; font-size: 0.875rem;'>Sign up for Alpaca</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class='step-card'>
        <div style='font-size: 2rem; text-align: center; margin-bottom: 0.5rem;'>2️⃣</div>
        <h3 style='text-align: center; margin-bottom: 0.5rem;'>Get API Keys</h3>
        <p style='text-align: center; color: #718096; font-size: 0.875rem;'>Find your credentials</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class='step-card'>
        <div style='font-size: 2rem; text-align: center; margin-bottom: 0.5rem;'>3️⃣</div>
        <h3 style='text-align: center; margin-bottom: 0.5rem;'>Configure</h3>
        <p style='text-align: center; color: #718096; font-size: 0.875rem;'>Create .env file</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Step 1: Create Alpaca Account
st.markdown("## Step 1: Create Your Alpaca Account")

st.markdown("""
**Alpaca** is a commission-free trading platform that provides the API Dalio Lite uses to manage your portfolio.

**Why Alpaca?**
- 🆓 Commission-free trading
- 📝 Free paper trading (practice with simulated money)
- 🔒 SEC-registered broker-dealer
- 🛡️ SIPC-insured up to $500,000
""")

st.info("""
💡 **Tip:** Start with **paper trading** mode to practice risk-free with simulated money before using real funds.
""", icon="💡")

st.markdown("""
### Create your account:

1. **Visit Alpaca:** [https://alpaca.markets/](https://alpaca.markets/)
2. **Click "Sign Up"** in the top right
3. **Choose account type:**
   - **Paper Trading Only:** Practice with simulated money (recommended for beginners)
   - **Live Trading:** Requires identity verification and funding (for experienced investors)
4. **Complete registration:** Follow the on-screen prompts

**⏱️ Time required:** 2-3 minutes for paper trading, 10-15 minutes for live trading
""")

st.markdown("---")

# Step 2: Get API Keys
st.markdown("## Step 2: Get Your API Keys")

st.markdown("""
API keys allow Dalio Lite to securely connect to your Alpaca account without storing your password.

### Find your API keys:

1. **Log into Alpaca** at [https://app.alpaca.markets/](https://app.alpaca.markets/)
2. **Navigate to API Keys:**
   - Click your username in the top right
   - Select "**API Keys**" from the dropdown menu
3. **Generate new keys:**
   - Click "**Generate New Key**"
   - **Important:** Copy both the **API Key** and **Secret Key** immediately
   - Secret keys are only shown once — if you lose them, you'll need to generate new ones
4. **Choose the right keys:**
   - **Paper Trading:** Use keys from the "Paper Trading" section
   - **Live Trading:** Use keys from the "Live Trading" section
""")

st.warning("""
⚠️ **Security reminder:** Your Secret Key is like a password. Never share it publicly or commit it to version control.
""", icon="⚠️")

st.markdown("---")

# Step 3: Configure .env File
st.markdown("## Step 3: Configure Your .env File")

st.markdown("""
The `.env` file stores your API credentials securely on your local machine.

### Create the .env file:

**Location:** Place this file in the **root directory** of Dalio Lite (same folder as `dashboard.py`)

**Filename:** Exactly `.env` (including the dot at the start, no file extension)
""")

# .env template with copy button
env_template = """# Alpaca API Configuration
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_PAPER=true  # Set to 'false' for live trading

# Optional: Notifications (uncomment to enable)
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id
"""

st.markdown("### .env File Template")
st.markdown("**Copy this template and replace the placeholder values with your actual API keys:**")

st.code(env_template, language="bash")

st.markdown("""
### Fill in your keys:

1. **Replace `your_api_key_here`** with your Alpaca API Key
2. **Replace `your_secret_key_here`** with your Alpaca Secret Key
3. **Keep `ALPACA_PAPER=true`** for paper trading, or change to `false` for live trading
4. **Save the file** as `.env` in the Dalio Lite root directory

**Example (with fake keys):**
""")

st.code("""# Alpaca API Configuration
ALPACA_API_KEY=PKABCDEF123456789
ALPACA_SECRET_KEY=7xYzAbCdEf123456789GhIjKlMnOpQrStUvWxYz
ALPACA_PAPER=true
""", language="bash")

st.markdown("---")

# Step 4: Connect and Verify
st.markdown("## Step 4: Connect and Verify")

st.markdown("""
### Test your connection:

1. **Return to the Dashboard** (click "💰 Dalio Lite" in the sidebar)
2. **Look for the connection status** in the sidebar under "Settings"
3. **Click "🔌 CONNECT TO ALPACA"**
4. **Verify successful connection:**
   - You should see "🟢 CONNECTED" status
   - Your portfolio value and metrics will appear
   - Paper/Live trading mode indicator will show

**If connection succeeds:**
🎉 Congratulations! You're all set up. Your portfolio is now being managed automatically.

**If connection fails:**
❌ See the troubleshooting section below for common issues and solutions.
""")

st.markdown("---")

# Troubleshooting
st.markdown("## 🛠️ Troubleshooting")

with st.expander("**❌ 'Invalid API credentials' error**"):
    st.markdown("""
    **Problem:** API keys are incorrect or expired.

    **Solutions:**
    1. **Double-check your keys** in the Alpaca dashboard
    2. **Regenerate new keys** if old ones were deleted or expired
    3. **Verify no extra spaces** when copying keys (trim whitespace)
    4. **Check paper vs. live keys** — make sure you're using keys from the right mode
    5. **Ensure .env file is saved** in the correct location (root directory)
    """)

with st.expander("**❌ '.env file not found' error**"):
    st.markdown("""
    **Problem:** Dalio Lite can't find your .env file.

    **Solutions:**
    1. **Check file location** — .env must be in the **root directory** (same folder as `dashboard.py`)
    2. **Check filename** — Must be exactly `.env` (with leading dot, no extension)
    3. **Check hidden files** — .env files are hidden by default on macOS/Linux
       - macOS: Press `Cmd+Shift+.` in Finder to show hidden files
       - Linux: Press `Ctrl+H` in file manager
    4. **File permissions** — Ensure the file is readable:
       ```bash
       chmod 644 .env
       ```
    """)

with st.expander("**❌ 'Rate limit reached' error**"):
    st.markdown("""
    **Problem:** Too many API requests in a short time.

    **Solutions:**
    1. **Wait 60 seconds** and try again
    2. **Avoid rapid clicking** of Connect/Refresh buttons
    3. **This is temporary** — rate limits reset automatically
    4. **Paper trading:** 200 requests/minute
    5. **Live trading:** Higher limits (depends on your account tier)
    """)

with st.expander("**❌ 'Market is currently closed' error**"):
    st.markdown("""
    **Problem:** You're trying to execute trades when the market is closed.

    **Solutions:**
    1. **Check market hours:**
       - Monday-Friday: 9:30 AM - 4:00 PM ET
       - Closed on weekends and U.S. market holidays
    2. **Use paper trading** for testing outside market hours
    3. **Dry run mode** works anytime (simulates trades without executing)
    4. **Portfolio viewing** works 24/7 (you can always see your positions)
    """)

with st.expander("**❌ Connection succeeds but no data appears**"):
    st.markdown("""
    **Problem:** Connected but portfolio shows zero or no data.

    **Solutions:**
    1. **Fresh account:** If your Alpaca account is brand new, you may have no positions yet
       - Run your **first rebalance** to establish positions
       - Click "🔄 RUN DAILY CHECK" on the dashboard
    2. **Paper trading reset:** Paper accounts reset occasionally
       - Check your paper account balance in Alpaca dashboard
       - Reset available at Alpaca website if needed
    3. **Refresh the page** after the first rebalance completes
    """)

st.markdown("---")

# FAQ
st.markdown("## ❓ Frequently Asked Questions")

with st.expander("**Is my money safe with Alpaca?**"):
    st.markdown("""
    **Yes.** Alpaca is a FINRA-registered broker-dealer and SEC-registered investment advisor.
    Securities in your account are protected up to $500,000 by SIPC (Securities Investor Protection Corporation),
    including $250,000 for cash.

    **Learn more:** [Alpaca Security](https://alpaca.markets/learn/alpaca-security/)
    """)

with st.expander("**What's the difference between paper and live trading?**"):
    st.markdown("""
    **Paper Trading:**
    - ✅ Practice with **simulated money** (usually $100,000 virtual cash)
    - ✅ No risk — your real money is never at stake
    - ✅ Perfect for learning and testing strategies
    - ✅ No account verification or funding required
    - ❌ Results may differ slightly from live trading (order fills, slippage)

    **Live Trading:**
    - 💵 Uses **real money** from your brokerage account
    - 📊 Actual market execution with real prices
    - ⚠️ Subject to market risk — you can lose money
    - 🔐 Requires identity verification and account funding
    - ✅ Real returns on your investments

    **Recommendation:** Start with paper trading until you're comfortable, then switch to live trading.
    """)

with st.expander("**How much does Dalio Lite cost?**"):
    st.markdown("""
    **Dalio Lite:** Free and open-source

    **Alpaca Trading:**
    - ✅ **Commission-free** stock trading
    - ✅ **No monthly fees** for basic accounts
    - ✅ **Free paper trading** forever

    **Costs you may encounter:**
    - Standard market spreads (difference between buy/sell prices)
    - SEC fees (small regulatory fees on stock sales)
    - Margin interest if using borrowed funds (only applies if you enable margin)
    """)

with st.expander("**Can I use this with other brokers besides Alpaca?**"):
    st.markdown("""
    **Currently:** Dalio Lite only supports Alpaca Markets.

    **Why Alpaca?**
    - Modern API designed for algorithmic trading
    - Commission-free trading
    - Excellent paper trading for risk-free testing
    - Reliable uptime and support

    **Future:** Support for other brokers may be added in future releases.
    """)

with st.expander("**What is the All Weather portfolio strategy?**"):
    st.markdown("""
    The **All Weather** portfolio is a strategic asset allocation approach developed by Ray Dalio
    (founder of Bridgewater Associates). It's designed to perform well across different economic environments.

    **Default allocation:**
    - 40% VTI (Total U.S. Stock Market)
    - 30% TLT (Long-term Treasury Bonds)
    - 20% GLD (Gold)
    - 10% DBC (Commodities)

    **Philosophy:** Balance risk across different asset classes so no single economic environment
    (growth, inflation, deflation, recession) can sink your portfolio.

    **Learn more:** Visit the "How It Works" page in the sidebar for detailed explanations.
    """)

st.markdown("---")

# Next Steps
st.markdown("## 🚀 Next Steps")

st.success("""
**Ready to get started?**

1. **Return to the Dashboard** → Click "💰 Dalio Lite" in the sidebar
2. **Connect your account** → Click "🔌 CONNECT TO ALPACA"
3. **Run your first check** → Click "🔄 RUN DAILY CHECK" to establish positions
4. **Set your goals** → Visit the "🎯 Goals" page to track progress toward financial milestones
5. **Monitor your portfolio** → Check back daily or let AutoPilot handle it automatically

**Need help?** Check the troubleshooting section above or revisit this guide anytime from the sidebar.
""", icon="✅")

st.markdown("---")

# Footer
st.caption("""
💡 **Tip:** Bookmark this page for quick reference. You can return to this Setup Guide anytime from the sidebar.
""")
