# Onboarding Flow Specification

**Document:** 05-onboarding-flow.md
**Version:** 1.0
**Date:** 2026-02-17
**Status:** Final
**Owner:** Dalio Lite UI Redesign Project

---

## Overview

This document defines the improved onboarding experience for Dalio Lite. Currently, the non-connected state shows vague instructions ("Add your Alpaca API keys to the .env file") without explaining HOW to get keys, WHERE the .env file is, or WHAT the file should look like. Modern fintech apps provide step-by-step guided onboarding with clear CTAs and visual feedback.

**Why this exists:** First impressions matter. If users can't get started within 5 minutes, they abandon the product. The current onboarding has high cognitive load—users must:
1. Figure out what Alpaca is
2. Sign up for Alpaca
3. Navigate Alpaca's dashboard to find API keys
4. Understand what a .env file is
5. Create/edit .env file with correct format
6. Restart the dashboard

**This specification reduces friction by providing clear, step-by-step guidance with no assumed technical knowledge.**

**Scope:** Onboarding flow on `dashboard.py` (non-connected state) + new Setup Guide page (`pages/7_📝_Setup.py`).

---

## Architecture

### Onboarding Journey Map

```
┌─────────────────────────────────────────────────────────┐
│  User arrives at dashboard (not connected)              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  CHECKPOINT 1: Welcome Screen                           │
│  • 3-step progress indicator                            │
│  • Clear CTAs for each step                             │
│  • Link to detailed Setup Guide                         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ Click "Go to Alpaca" or "Setup Guide"
┌─────────────────────────────────────────────────────────┐
│  CHECKPOINT 2: Setup Guide Page (NEW)                   │
│  • Detailed instructions with screenshots               │
│  • Copy-paste .env template                             │
│  • Troubleshooting section                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ User creates Alpaca account, gets keys
┌─────────────────────────────────────────────────────────┐
│  CHECKPOINT 3: Connect Button                           │
│  • User returns to dashboard                            │
│  • Clicks "Connect to Alpaca"                           │
│  • System validates connection                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓ Connection succeeds
┌─────────────────────────────────────────────────────────┐
│  CHECKPOINT 4: First Run Guidance                       │
│  • Congratulations message                              │
│  • Prompt to run first daily check                      │
│  • Optional: Set your goals                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────┐
│  SUCCESS: User is onboarded, dashboard fully functional │
└─────────────────────────────────────────────────────────┘
```

---

## Specification

### Component 1: Welcome Screen (Dashboard Non-Connected State)

**Location:** `dashboard.py` (when `st.session_state.connected == False`)

**Visual Design (Updated from Doc 04):**

```
┌────────────────────────────────────────────────────────────┐
│              🚀 Welcome to Dalio Lite!                     │
│          Automated All Weather Portfolio Management        │
│                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                            │
│  Get started in 3 steps:                                   │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ STEP 1: Create Alpaca Account                    │    │
│  │ ✅ Done  or  [Go to Alpaca →]                   │    │
│  │                                                  │    │
│  │ Alpaca is your brokerage. They execute trades.  │    │
│  │ • Free account (no fees to start)               │    │
│  │ • Start with Paper Trading (simulated money)    │    │
│  │ • Takes 5 minutes to sign up                    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ STEP 2: Get Your API Keys                        │    │
│  │ ⏳ In Progress  or  [View Setup Guide →]        │    │
│  │                                                  │    │
│  │ API keys let Dalio Lite access your account.    │    │
│  │ • Find them in Alpaca Dashboard → Your API Keys │    │
│  │ • Copy both the API Key and Secret Key          │    │
│  │ • Keep them private (never share!)              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ STEP 3: Connect to Dalio Lite                    │    │
│  │ ⬜ Not Started  or  [Connect →]                 │    │
│  │                                                  │    │
│  │ Once you have API keys, connect here.            │    │
│  │ • Creates secure connection to Alpaca           │    │
│  │ • Validates your credentials                    │    │
│  │ • Loads your portfolio data                     │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                            │
│  Need help? [📖 View Detailed Setup Guide]                │
│                                                            │
│  Questions? Check the [❓ FAQ]                             │
└────────────────────────────────────────────────────────────┘
```

**Code Implementation:**

```python
def render_onboarding_welcome():
    """Render welcome screen for non-connected users."""
    # Center the welcome message
    _, col, _ = st.columns([1, 3, 1])

    with col:
        # Header
        st.markdown("""
        <div style='text-align: center; padding: 2rem 0 1rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>🚀 Welcome to Dalio Lite!</h1>
            <p style='font-size: 1.25rem; color: #6b7280;'>
                Automated All Weather Portfolio Management
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown("### Get started in 3 steps:")
        st.markdown("")

        # STEP 1: Create Alpaca Account
        with st.container():
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px;
                        border: 2px solid #e2e8f0; margin-bottom: 1.5rem;'>
                <h3>STEP 1: Create Alpaca Account</h3>
            </div>
            """, unsafe_allow_html=True)

            # Check if user has marked this step complete
            step1_complete = st.session_state.get('onboarding_step1_complete', False)

            if step1_complete:
                st.success("✅ Alpaca account created")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown("""
                    **Alpaca is your brokerage.** They execute trades on your behalf.

                    • Free account (no fees to start)
                    • Start with **Paper Trading** (simulated $100K)
                    • Takes 5 minutes to sign up
                    """)
                with col2:
                    if st.button("Go to Alpaca →", type="primary", use_container_width=True):
                        st.link_button("Open Alpaca", "https://app.alpaca.markets/signup")

                if st.checkbox("I've created my Alpaca account"):
                    st.session_state.onboarding_step1_complete = True
                    st.rerun()

        st.markdown("")

        # STEP 2: Get API Keys
        with st.container():
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px;
                        border: 2px solid #e2e8f0; margin-bottom: 1.5rem;'>
                <h3>STEP 2: Get Your API Keys</h3>
            </div>
            """, unsafe_allow_html=True)

            # Check if .env file exists (indicates keys entered)
            env_file = Path(".env")
            step2_complete = env_file.exists()

            if step2_complete:
                st.success("✅ API keys configured")
            else:
                step1_complete = st.session_state.get('onboarding_step1_complete', False)

                if not step1_complete:
                    st.info("⏳ Complete Step 1 first")
                else:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("""
                        **API keys** let Dalio Lite access your Alpaca account.

                        • Find them: Alpaca Dashboard → **Your API Keys**
                        • Copy both the **API Key** and **Secret Key**
                        • Keep them private (never share!)
                        """)
                    with col2:
                        if st.button("Setup Guide →", use_container_width=True):
                            st.switch_page("pages/7_📝_Setup.py")

        st.markdown("")

        # STEP 3: Connect
        with st.container():
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px;
                        border: 2px solid #e2e8f0; margin-bottom: 1.5rem;'>
                <h3>STEP 3: Connect to Dalio Lite</h3>
            </div>
            """, unsafe_allow_html=True)

            env_file = Path(".env")
            step2_complete = env_file.exists()

            if not step2_complete:
                st.info("⏳ Complete Step 2 first")
            else:
                st.markdown("""
                **Ready to connect!** Your API keys are configured.

                • Creates secure connection to Alpaca
                • Validates your credentials
                • Loads your portfolio data
                """)

                if st.button("🔌 Connect to Alpaca", type="primary", use_container_width=True):
                    with st.spinner("Connecting to Alpaca..."):
                        try:
                            from dalio_lite import DalioLite
                            st.session_state.dalio = DalioLite()
                            st.session_state.connected = True
                            st.success("✅ Connected successfully!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            from error_handler import display_error
                            display_error(e, context="connecting_to_alpaca")

        st.divider()

        # Help links
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 View Detailed Setup Guide", use_container_width=True):
                st.switch_page("pages/7_📝_Setup.py")
        with col2:
            if st.button("❓ FAQ", use_container_width=True):
                st.info("FAQ coming soon! For now, check the How It Works page.")
```

---

### Component 2: Setup Guide Page (NEW PAGE)

**File:** `pages/7_📝_Setup.py`

**Page Structure:**

```
┌────────────────────────────────────────────────────────────┐
│                📝 Dalio Lite Setup Guide                   │
│        Complete instructions to get up and running         │
└────────────────────────────────────────────────────────────┘

TABLE OF CONTENTS
  • Step 1: Sign Up for Alpaca
  • Step 2: Get Your API Keys
  • Step 3: Configure Dalio Lite
  • Step 4: Connect and Verify
  • Troubleshooting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: SIGN UP FOR ALPACA

Alpaca Markets is your brokerage. They hold your money and execute trades.
Dalio Lite connects to Alpaca to manage your portfolio automatically.

1. Go to: https://app.alpaca.markets/signup

2. Choose account type:
   • Start with "Paper Trading" (simulated $100K) ✅ Recommended
   • Live Trading requires identity verification + funding

3. Complete signup:
   • Email address
   • Password
   • Accept terms

4. Verify your email (check inbox)

✅ Once complete, you'll land on the Alpaca Dashboard.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: GET YOUR API KEYS

API keys let Dalio Lite access your Alpaca account securely.

1. In Alpaca Dashboard, click your profile icon (top right)

2. Select "Your API Keys" from dropdown

3. You'll see:
   ┌──────────────────────────────────────────┐
   │ Paper Trading API Keys                   │
   │                                          │
   │ API Key:    PK...ABC123                  │
   │ Secret Key: ••••••••••  [Reveal]         │
   │                                          │
   │ [Generate New Keys]                      │
   └──────────────────────────────────────────┘

4. Click [Reveal] next to Secret Key

5. Copy BOTH keys:
   • API Key (starts with "PK")
   • Secret Key (starts with "SK" or similar)

⚠️ IMPORTANT: Keep your Secret Key private! Never commit it to git,
share it publicly, or show it in screenshots.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3: CONFIGURE DALIO LITE

Now we'll tell Dalio Lite how to connect to your Alpaca account.

Option A: Railway Deployment (Recommended)
  1. Go to your Railway project dashboard
  2. Click "Variables" tab
  3. Add these environment variables:
     • ALPACA_API_KEY = [Your API Key]
     • ALPACA_SECRET_KEY = [Your Secret Key]
  4. Click "Deploy" to restart with new variables

Option B: Local Setup (.env file)
  1. In the `dalio-lite` folder, create a file named `.env`

  2. Open `.env` in a text editor

  3. Copy this template:

     ┌────────────────────────────────────────┐
     │ # Alpaca Trading API Credentials       │
     │ ALPACA_API_KEY=your_api_key_here       │
     │ ALPACA_SECRET_KEY=your_secret_key_here │
     │                                        │
     │ # Optional: Notification Services      │
     │ # SLACK_WEBHOOK_URL=your_webhook_url   │
     │ # PUSHOVER_USER_KEY=your_user_key      │
     │                                        │
     │ # Port (Railway sets this)             │
     │ PORT=8501                              │
     └────────────────────────────────────────┘

  4. Replace `your_api_key_here` with your actual API Key (from Step 2)

  5. Replace `your_secret_key_here` with your actual Secret Key

  6. Save the file

  7. If dashboard is already running, restart it:
     • Stop: Press Ctrl+C in terminal
     • Start: Run `streamlit run dashboard.py`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4: CONNECT AND VERIFY

Return to the dashboard and click "Connect to Alpaca".

If successful, you'll see:
  ✅ Connected successfully!
  🟢 CONNECTED in sidebar
  Your portfolio data will load

If it fails, see Troubleshooting below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING

Problem: "Invalid API credentials" error

Solution:
  • Double-check API keys in .env file (no typos)
  • Make sure you copied BOTH keys (API Key + Secret Key)
  • Verify you're using Paper Trading keys (not Live keys)
  • Try regenerating keys in Alpaca Dashboard

---

Problem: "Connection failed" error

Solution:
  • Check your internet connection
  • Verify Alpaca is online: https://status.alpaca.markets
  • Try again in 1 minute (temporary API issue)
  • Disable VPN if using corporate network

---

Problem: ".env file not found" error

Solution:
  • Make sure .env file is in the `dalio-lite` folder (same level as dashboard.py)
  • Check file name is exactly `.env` (not `env.txt` or `.env.txt`)
  • On Windows, enable "Show file extensions" to verify

---

Problem: "Market is closed" message

Solution:
  • This is normal! US stock market is open 9:30 AM - 4:00 PM ET, Monday-Friday
  • You can still connect and view your portfolio
  • Rebalancing will execute when market opens
  • Use "Dry Run" to test without executing trades

---

Still having issues?

  • Check the Activity Log on the dashboard for detailed error messages
  • Visit "How It Works" page for system overview
  • Report issues at: https://github.com/[your-repo]/issues

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ SETUP COMPLETE!

Once connected, you can:
  • Run your first daily check
  • Set your financial goals
  • Explore the dashboard

[← Back to Dashboard]
```

**Code Implementation:**

```python
"""Setup Guide - Complete onboarding instructions."""
import streamlit as st

st.set_page_config(page_title="Setup Guide", page_icon="📝", layout="wide")

st.title("📝 Dalio Lite Setup Guide")
st.markdown("Complete instructions to get up and running")
st.divider()

# Table of Contents
st.markdown("### 📑 Table of Contents")
st.markdown("""
- [Step 1: Sign Up for Alpaca](#step-1-sign-up-for-alpaca)
- [Step 2: Get Your API Keys](#step-2-get-your-api-keys)
- [Step 3: Configure Dalio Lite](#step-3-configure-dalio-lite)
- [Step 4: Connect and Verify](#step-4-connect-and-verify)
- [Troubleshooting](#troubleshooting)
""")

st.divider()

# STEP 1
st.markdown("## Step 1: Sign Up for Alpaca")
st.markdown("""
**Alpaca Markets** is your brokerage. They hold your money and execute trades.
Dalio Lite connects to Alpaca to manage your portfolio automatically.

1. **Go to:** https://app.alpaca.markets/signup

2. **Choose account type:**
   - ✅ Start with **"Paper Trading"** (simulated $100K) — Recommended
   - Live Trading requires identity verification + funding

3. **Complete signup:**
   - Email address
   - Password
   - Accept terms

4. **Verify your email** (check inbox)

✅ Once complete, you'll land on the Alpaca Dashboard.
""")

st.link_button("Go to Alpaca Signup →", "https://app.alpaca.markets/signup", type="primary")

st.divider()

# STEP 2
st.markdown("## Step 2: Get Your API Keys")
st.markdown("""
**API keys** let Dalio Lite access your Alpaca account securely.

1. In **Alpaca Dashboard**, click your **profile icon** (top right)

2. Select **"Your API Keys"** from dropdown

3. You'll see:
""")

st.info("""
**Paper Trading API Keys**

• API Key: `PK...ABC123`
• Secret Key: `••••••••••` [Reveal]

[Generate New Keys]
""")

st.markdown("""
4. Click **[Reveal]** next to Secret Key

5. **Copy BOTH keys:**
   - API Key (starts with "PK")
   - Secret Key (starts with a different prefix)

⚠️ **IMPORTANT:** Keep your Secret Key private! Never commit it to git,
share it publicly, or show it in screenshots.
""")

st.divider()

# STEP 3
st.markdown("## Step 3: Configure Dalio Lite")
st.markdown("""
Now we'll tell Dalio Lite how to connect to your Alpaca account.
""")

tab1, tab2 = st.tabs(["Railway Deployment (Recommended)", "Local Setup (.env file)"])

with tab1:
    st.markdown("""
    **For Railway deployment:**

    1. Go to your **Railway project dashboard**
    2. Click **"Variables"** tab
    3. Add these environment variables:
       - `ALPACA_API_KEY` = [Your API Key]
       - `ALPACA_SECRET_KEY` = [Your Secret Key]
    4. Click **"Deploy"** to restart with new variables

    ✅ That's it! Railway will automatically use these variables.
    """)

with tab2:
    st.markdown("""
    **For local development:**

    1. In the `dalio-lite` folder, create a file named `.env`

    2. Open `.env` in a text editor (Notepad, VS Code, etc.)

    3. Copy this template:
    """)

    st.code("""
# Alpaca Trading API Credentials (REQUIRED)
ALPACA_API_KEY=your_paper_trading_api_key_here
ALPACA_SECRET_KEY=your_paper_trading_secret_key_here

# Optional: Notification Services
# SLACK_WEBHOOK_URL=your_slack_webhook_url
# PUSHOVER_USER_KEY=your_pushover_user_key
# PUSHOVER_APP_TOKEN=your_pushover_app_token

# Railway sets this automatically
PORT=8501
""", language="bash")

    st.markdown("""
    4. Replace `your_paper_trading_api_key_here` with your actual API Key (from Step 2)

    5. Replace `your_paper_trading_secret_key_here` with your actual Secret Key

    6. **Save the file**

    7. If dashboard is already running, **restart it:**
       - Stop: Press `Ctrl+C` in terminal
       - Start: Run `streamlit run dashboard.py`
    """)

st.divider()

# STEP 4
st.markdown("## Step 4: Connect and Verify")
st.markdown("""
**Return to the dashboard** and click **"Connect to Alpaca"**.

If successful, you'll see:
- ✅ Connected successfully!
- 🟢 CONNECTED in sidebar
- Your portfolio data will load

If it fails, see Troubleshooting below.
""")

if st.button("← Back to Dashboard", type="primary"):
    st.switch_page("dashboard.py")

st.divider()

# Troubleshooting
st.markdown("## Troubleshooting")

with st.expander("❌ \"Invalid API credentials\" error"):
    st.markdown("""
    **Solution:**
    - Double-check API keys in .env file (no typos)
    - Make sure you copied BOTH keys (API Key + Secret Key)
    - Verify you're using **Paper Trading keys** (not Live keys)
    - Try regenerating keys in Alpaca Dashboard
    """)

with st.expander("🔌 \"Connection failed\" error"):
    st.markdown("""
    **Solution:**
    - Check your internet connection
    - Verify Alpaca is online: https://status.alpaca.markets
    - Try again in 1 minute (temporary API issue)
    - Disable VPN if using corporate network
    """)

with st.expander("📁 \".env file not found\" error"):
    st.markdown("""
    **Solution:**
    - Make sure `.env` file is in the `dalio-lite` folder (same level as `dashboard.py`)
    - Check file name is exactly `.env` (not `env.txt` or `.env.txt`)
    - On Windows, enable "Show file extensions" to verify
    """)

with st.expander("🕐 \"Market is closed\" message"):
    st.markdown("""
    **This is normal!**
    - US stock market is open 9:30 AM - 4:00 PM ET, Monday-Friday
    - You can still connect and view your portfolio
    - Rebalancing will execute when market opens
    - Use "Dry Run" to test without executing trades
    """)

with st.expander("🆘 Still having issues?"):
    st.markdown("""
    - Check the **Activity Log** on the dashboard for detailed error messages
    - Visit **"How It Works"** page for system overview
    - Report issues at: https://github.com/[your-repo]/issues
    """)

st.divider()

# Success message
st.success("""
✅ **SETUP COMPLETE!**

Once connected, you can:
• Run your first daily check
• Set your financial goals
• Explore the dashboard
""")

if st.button("← Back to Dashboard"):
    st.switch_page("dashboard.py")
```

---

### Component 3: First-Run Experience

**Trigger:** After successful first connection

**Visual Design:**

```
┌────────────────────────────────────────────────────────────┐
│                   🎉 Welcome to Dalio Lite!                │
│               You're successfully connected!               │
│                                                            │
│  Here's what to do next:                                   │
│                                                            │
│  1. 🔄 Run your first daily check                         │
│     See if your portfolio needs rebalancing                │
│     [Run Daily Check →]                                    │
│                                                            │
│  2. 🎯 Set your financial goals (Optional)                │
│     Track progress toward retirement, house, etc.          │
│     [Set Goals →]                                          │
│                                                            │
│  3. 📖 Learn how it works (Recommended)                   │
│     Understand the All Weather strategy                    │
│     [How It Works →]                                       │
│                                                            │
│  [Skip Tour - Take Me to Dashboard]                        │
└────────────────────────────────────────────────────────────┘
```

**Code:**

```python
def show_first_run_welcome():
    """Show welcome message after first successful connection."""
    if st.session_state.get('first_run_complete', False):
        return  # Only show once

    st.info("""
    🎉 **Welcome to Dalio Lite! You're successfully connected.**

    Here's what to do next:

    **1. 🔄 Run your first daily check**
    See if your portfolio needs rebalancing.

    **2. 🎯 Set your financial goals** (Optional)
    Track progress toward retirement, house, etc.

    **3. 📖 Learn how it works** (Recommended)
    Understand the All Weather strategy.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Run Daily Check →", use_container_width=True):
            st.session_state.first_run_complete = True
            # Trigger daily check
    with col2:
        if st.button("Set Goals →", use_container_width=True):
            st.session_state.first_run_complete = True
            st.switch_page("pages/6_🎯_Goals.py")
    with col3:
        if st.button("How It Works →", use_container_width=True):
            st.session_state.first_run_complete = True
            st.switch_page("pages/1_📖_How_It_Works.py")

    if st.button("Skip Tour - Take Me to Dashboard", use_container_width=True):
        st.session_state.first_run_complete = True
        st.rerun()

    st.divider()

# Call after successful connection
if st.session_state.connected and not st.session_state.get('first_run_complete'):
    show_first_run_welcome()
```

---

## Verification Strategy

### User Testing (Qualitative)

**Test with 5 users (non-technical):**

**Task:** "Get Dalio Lite connected to Alpaca" (start from fresh install)

**Observe:**
- Do they understand what Alpaca is?
- Can they find API keys without help?
- Do they know where to put .env file?
- How long does onboarding take?

**Success criteria:**
- 4 out of 5 users complete onboarding without asking for help
- Average time to connection: <10 minutes

### A/B Testing (Quantitative)

**Metrics to track:**
- Onboarding completion rate (% of users who connect successfully)
- Time to first connection
- Drop-off point (which step do users abandon?)
- Support requests during onboarding

**Target:**
- 70%+ completion rate (up from est. 40% current)
- <10 minutes average time to connection
- 50% reduction in "how do I get started?" support requests

### Manual Verification

**Checklist:**
- [ ] Welcome screen shows 3-step progress
- [ ] Each step has clear description + CTA
- [ ] Step 1 marked complete when user checks box
- [ ] Step 2 marked complete when .env exists
- [ ] Step 3 (Connect) only enabled after Step 2
- [ ] Setup Guide page accessible from welcome screen
- [ ] Setup Guide has all 4 steps + troubleshooting
- [ ] .env template code is copy-pasteable
- [ ] External links (Alpaca signup) open in new tab
- [ ] First-run welcome appears after connection
- [ ] First-run welcome dismisses after interaction

---

## Benefits

### Why This Approach

1. **Progressive disclosure:** Show overview first, details on request
2. **Visual feedback:** Progress indicators show completion status
3. **Contextual help:** Help available when/where needed
4. **Error prevention:** Steps unlock sequentially (can't skip ahead)
5. **Tested pattern:** Matches onboarding flows from Stripe, Plaid, other dev tools

### Alternatives Considered

**Alternative 1: Single-page onboarding wizard**
- ❌ Rejected: Forces linear flow, users can't skip around
- ❌ Rejected: Can't return to dashboard mid-setup

**Alternative 2: Video tutorial**
- ❌ Rejected: Video becomes outdated quickly (Alpaca UI changes)
- ❌ Rejected: Users can't copy-paste from video

**Alternative 3: In-app API key input (vs. .env file)**
- ❌ Rejected for MVP: Requires secure backend storage
- ✅ Future enhancement: Consider for v2.0 (better UX, more complex implementation)

---

## Expectations

### Success Metrics

**Quantitative:**
- Onboarding completion rate: 70%+ (up from est. 40%)
- Time to first connection: <10 minutes average
- Setup Guide page views: 60%+ of new users
- First-run welcome dismissal: 80%+ interact (don't just close)

**Qualitative:**
- User feedback: "easy to set up", "clear instructions"
- Support requests: 50% reduction in onboarding questions
- User confidence: Users report feeling "ready" after onboarding

### What Success Looks Like

**Before:** User arrives at dashboard:
- Sees "Add your Alpaca API keys to the .env file"
- Thinks: "What's Alpaca? What's a .env file? Where is it?"
- Gives up, abandons product

**After:** User arrives at dashboard:
- Sees 3-step progress: Create Account → Get Keys → Connect
- Clicks "Go to Alpaca", signs up in 5 minutes
- Clicks "Setup Guide", follows step-by-step instructions
- Copies .env template, pastes keys, connects
- Sees "Welcome! Run your first check"
- Feels confident, continues using product

---

## Risks & Mitigations

### Technical Risks

**Risk 1: .env file approach is technical**
- **Likelihood:** Medium (some users uncomfortable with files)
- **Impact:** High (blocks onboarding)
- **Mitigation:** Provide extremely detailed instructions + screenshots. Future: Add in-app key input.

**Risk 2: Railway deployment hides .env file**
- **Likelihood:** High (Railway users don't have file system access)
- **Impact:** High (onboarding won't work)
- **Mitigation:** Provide separate instructions for Railway (environment variables via UI)

### UX Risks

**Risk 1: Users skip Setup Guide**
- **Likelihood:** Medium (users want quick start)
- **Impact:** High (get stuck, can't connect)
- **Mitigation:** Make Setup Guide link prominent. Show inline instructions on dashboard (not just link).

**Risk 2: Alpaca UI changes, instructions become outdated**
- **Likelihood:** Medium (Alpaca updates their dashboard)
- **Impact:** Medium (users can't find API keys)
- **Mitigation:** Keep instructions high-level ("find 'Your API Keys' in menu"). Add last-updated date to Setup Guide.

**Risk 3: Users expose Secret Keys (screenshot, git commit)**
- **Likelihood:** Low (most users understand "private")
- **Impact:** High (account compromise)
- **Mitigation:** Multiple warnings in Setup Guide. Add .gitignore protection (already exists). Show warning if .env committed to git.

---

## Results Criteria

### Acceptance Criteria (Must-Haves)

**Welcome Screen (dashboard.py non-connected):**
- [ ] 3-step progress indicator
- [ ] Step 1: Alpaca signup CTA + description
- [ ] Step 2: API keys guidance + Setup Guide link
- [ ] Step 3: Connect button (enabled when .env exists)
- [ ] Progress updates (steps marked complete)

**Setup Guide Page (`pages/7_📝_Setup.py`):**
- [ ] Step 1: Alpaca signup instructions
- [ ] Step 2: API keys retrieval instructions
- [ ] Step 3: .env file configuration (with template)
- [ ] Step 4: Connection verification
- [ ] Troubleshooting section (5+ common issues)
- [ ] Railway-specific instructions (environment variables)
- [ ] External links open in new tab

**First-Run Welcome:**
- [ ] Appears after first successful connection
- [ ] Suggests next actions (Run Check, Set Goals, Learn)
- [ ] Dismisses after interaction
- [ ] Doesn't reappear on subsequent logins

### Success Metrics

**Deployment Success:**
- Onboarding flow visible on dashboard
- Setup Guide page accessible
- No functionality broken
- User feedback collected

**Long-term Success:**
- 70%+ onboarding completion rate (vs. est. 40% baseline)
- <10 minutes average time to connection
- 50% reduction in "how do I start?" support requests
- 80%+ of users complete first daily check within 24 hours of connecting

---

## Domain-Specific Considerations

### Fintech Onboarding Best Practices

**From industry leaders:**
- **Robinhood:** 3-minute signup, in-app identity verification, instant funding
- **Betterment:** Goal-first onboarding ("What are you saving for?"), then account setup
- **Wealthfront:** Progressive disclosure, can skip optional steps
- **Plaid (API tool):** Sandbox mode first, production keys later

**Our approach:** Combine Plaid's developer-friendly setup + Betterment's goal focus + Robinhood's simplicity

### Security Considerations

**Best practices:**
- Never ask users to paste API keys in support tickets
- Never log API keys (even encrypted)
- Warn about .env file security (don't commit to git)
- Suggest key rotation if exposed

**Our implementation:**
- .gitignore includes .env (already in place)
- Multiple warnings in Setup Guide about key privacy
- Use python-dotenv for secure key loading
- Never display Secret Key in UI after initial setup

---

## Cross-References

- **Depends on:**
  - `01-error-handling-specification.md` (uses error patterns for connection failures)
  - `04-information-architecture.md` (references dashboard layout for non-connected state)
- **Referenced by:**
  - `06-implementation-guide.md` (Phase 3 implementation)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Dalio Lite Team | Initial specification |

---

**Status:** ✅ Complete and ready for implementation
