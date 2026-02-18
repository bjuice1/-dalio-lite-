"""
Goals Page - Set and Track Your Financial Goals
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from goal_tracker import GoalTracker, GoalType
from trust_indicators import render_trust_bar
from error_handler import translate_exception, handle_error_display

st.set_page_config(
    page_title="Goals - Dalio Lite",
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
    .goal-card {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .goal-card.primary {
        border-color: #667eea;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
        border-width: 3px;
    }
    .progress-bar {
        height: 8px;
        background: #e2e8f0;
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.3s ease;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .status-on-track { background: #c6f6d5; color: #22543d; }
    .status-close { background: #bee3f8; color: #2c5282; }
    .status-progressing { background: #feebc8; color: #7c2d12; }
    .status-behind { background: #fed7d7; color: #742a2a; }
</style>
""", unsafe_allow_html=True)

# Trust indicators
render_trust_bar()

# Header
st.title("🎯 Your Financial Goals")
st.markdown("### Track your progress and stay motivated")
st.markdown("---")

# Initialize goal tracker
try:
    tracker = GoalTracker()
except Exception as e:
    message, severity = translate_exception(e, context="Initializing goal tracker")
    handle_error_display(message, severity)
    st.stop()

# Get current portfolio value if connected
current_portfolio_value = 0
if 'connected' in st.session_state and st.session_state.connected:
    try:
        dalio = st.session_state.dalio
        account = dalio.api.get_account()
        current_portfolio_value = float(account.portfolio_value)
    except Exception as e:
        # Don't show error here, just default to 0
        pass

# Check if goal exists
all_goals = tracker.get_all_goals()
has_primary_goal = all_goals["primary_goal"] is not None

# Tab navigation
tab1, tab2, tab3 = st.tabs(["📊 Goal Dashboard", "➕ Set Goal", "⚙️ Assumptions"])

# ========================================
# TAB 1: GOAL DASHBOARD
# ========================================
with tab1:
    if not has_primary_goal:
        # No goal set - show getting started
        st.markdown("""
        <div style='text-align: center; padding: 3rem 0;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>🎯</div>
            <h2 style='font-size: 2rem; margin-bottom: 1rem;'>Set Your First Financial Goal</h2>
            <p style='font-size: 1.2rem; color: #718096;'>
                Goals give your investing a clear purpose. Whether you're saving for retirement,
                a house, or financial independence, tracking your progress keeps you motivated.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class='goal-card'>
                <div style='font-size: 2rem; text-align: center; margin-bottom: 1rem;'>🏖️</div>
                <h3 style='text-align: center; margin-bottom: 0.5rem;'>Retirement</h3>
                <p style='text-align: center; color: #718096;'>Build wealth for your golden years</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class='goal-card'>
                <div style='font-size: 2rem; text-align: center; margin-bottom: 1rem;'>🏠</div>
                <h3 style='text-align: center; margin-bottom: 0.5rem;'>Home</h3>
                <p style='text-align: center; color: #718096;'>Save for your dream house</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class='goal-card'>
                <div style='font-size: 2rem; text-align: center; margin-bottom: 1rem;'>🎓</div>
                <h3 style='text-align: center; margin-bottom: 0.5rem;'>Education</h3>
                <p style='text-align: center; color: #718096;'>Fund education for you or family</p>
            </div>
            """, unsafe_allow_html=True)

        st.info("💡 **Get started:** Switch to the 'Set Goal' tab to create your first goal.", icon="ℹ️")

    else:
        # Goal exists - show progress dashboard
        try:
            progress = tracker.get_goal_progress(current_portfolio_value)

            # Hero section - Goal progress
            st.markdown(f"## {progress['goal_name']}")

            # Progress percentage
            progress_pct = progress['progress_percentage']
            status = progress['status']

            # Status badge
            badge_class = {
                "on_track": "status-on-track",
                "close": "status-close",
                "progressing": "status-progressing",
                "behind": "status-behind"
            }.get(status, "status-progressing")

            st.markdown(
                f"<span class='status-badge {badge_class}'>{progress['status_message']}</span>",
                unsafe_allow_html=True
            )

            # Progress bar
            st.markdown(
                f"""
                <div class='progress-bar'>
                    <div class='progress-fill' style='width: {min(100, progress_pct):.1f}%'></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    label="Current Value",
                    value=f"${progress['current_amount']:,.0f}",
                    delta=None
                )

            with col2:
                st.metric(
                    label="Target Amount",
                    value=f"${progress['target_amount']:,.0f}",
                    delta=None
                )

            with col3:
                st.metric(
                    label="Progress",
                    value=f"{progress_pct:.1f}%",
                    delta=None
                )

            with col4:
                st.metric(
                    label="Years Remaining",
                    value=f"{progress['years_remaining']} years",
                    delta=None
                )

            st.markdown("---")

            # Projection details
            st.markdown("## 📈 Projection Analysis")

            projection = progress['projection']

            col_left, col_right = st.columns([2, 1])

            with col_left:
                # Projection chart
                current_year = datetime.now().year
                target_year = progress['target_year']
                years_range = list(range(current_year, target_year + 1))

                # Calculate year-by-year projection
                annual_return = projection['annual_return_assumed']
                monthly_contrib = projection['monthly_contribution']
                current_amount = progress['current_amount']

                projected_values = []
                for i, year in enumerate(years_range):
                    years_elapsed = i
                    # Growth from current amount
                    fv_current = current_amount * ((1 + annual_return) ** years_elapsed)
                    # Growth from contributions
                    if monthly_contrib > 0:
                        months_elapsed = years_elapsed * 12
                        monthly_rate = annual_return / 12
                        fv_contrib = monthly_contrib * (
                            ((1 + monthly_rate) ** months_elapsed - 1) / monthly_rate
                        ) if monthly_rate > 0 else monthly_contrib * months_elapsed
                    else:
                        fv_contrib = 0
                    projected_values.append(fv_current + fv_contrib)

                # Create projection chart
                fig = go.Figure()

                # Projected growth line
                fig.add_trace(go.Scatter(
                    x=years_range,
                    y=projected_values,
                    mode='lines+markers',
                    name='Projected Value',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(102, 126, 234, 0.1)'
                ))

                # Target line
                fig.add_trace(go.Scatter(
                    x=[current_year, target_year],
                    y=[progress['target_amount'], progress['target_amount']],
                    mode='lines',
                    name='Target',
                    line=dict(color='#48bb78', width=2, dash='dash')
                ))

                fig.update_layout(
                    title="Growth Projection",
                    xaxis_title="Year",
                    yaxis_title="Portfolio Value ($)",
                    height=400,
                    hovermode='x unified',
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                # Projection breakdown
                st.markdown("### Breakdown")

                st.markdown(f"""
                **Projected Final Value:**
                ${projection['projected_amount']:,.0f}

                **Growth from Current Amount:**
                ${projection['growth_from_current']:,.0f}

                **Growth from Contributions:**
                ${projection['growth_from_contributions']:,.0f}

                **Assumed Annual Return:**
                {projection['annual_return_assumed']:.1%}

                **Monthly Contribution:**
                ${projection['monthly_contribution']:,.0f}
                """)

                if projection['on_track']:
                    st.success(f"🎉 **Surplus:** ${projection['surplus']:,.0f} above target")
                else:
                    st.warning(f"⚠️ **Shortfall:** ${projection['shortfall']:,.0f} below target")

                # Recommendation
                if projection['required_monthly_contribution'] > projection['monthly_contribution']:
                    required = projection['required_monthly_contribution']
                    st.info(
                        f"💡 **To reach your goal:**  \n"
                        f"Contribute ${required:,.0f}/month\n\n"
                        f"*(Currently: ${projection['monthly_contribution']:,.0f}/month)*"
                    )

        except Exception as e:
            message, severity = translate_exception(e, context="Loading goal progress")
            handle_error_display(message, severity)

# ========================================
# TAB 2: SET GOAL
# ========================================
with tab2:
    st.markdown("## Set Your Financial Goal")

    if has_primary_goal:
        st.warning("⚠️ You already have a primary goal set. Setting a new goal will replace the existing one.")

        if st.button("🗑️ Clear Existing Goal"):
            tracker.clear_primary_goal()
            st.success("Goal cleared! You can now set a new goal.")
            st.rerun()

    st.markdown("---")

    # Goal type selection
    goal_type = st.selectbox(
        "What are you saving for?",
        options=[
            ("retirement", "🏖️ Retirement"),
            ("house", "🏠 Home Down Payment"),
            ("education", "🎓 Education Fund"),
            ("financial_independence", "💰 Financial Independence"),
            ("wealth_building", "📈 Wealth Building"),
            ("custom", "✏️ Custom Goal")
        ],
        format_func=lambda x: x[1],
        index=0
    )

    goal_type_value = goal_type[0]

    # Custom goal name (if custom selected)
    goal_name = None
    if goal_type_value == "custom":
        goal_name = st.text_input("Goal Name", placeholder="e.g., 'Start a Business'")

    # Target amount
    target_amount = st.number_input(
        "Target Amount ($)",
        min_value=1000,
        max_value=100000000,
        value=1000000,
        step=10000,
        help="How much money do you want to accumulate?"
    )

    # Target year
    current_year = datetime.now().year
    target_year = st.number_input(
        "Target Year",
        min_value=current_year + 1,
        max_value=current_year + 50,
        value=current_year + 25,
        step=1,
        help="When do you want to reach this goal?"
    )

    # Current amount (pre-filled if connected)
    st.markdown("**Current Portfolio Value**")
    if current_portfolio_value > 0:
        st.info(f"Your current portfolio value: **${current_portfolio_value:,.0f}**")
        current_amount_input = current_portfolio_value
    else:
        current_amount_input = st.number_input(
            "Starting Amount ($)",
            min_value=0,
            max_value=100000000,
            value=0,
            step=1000,
            help="Your current portfolio value (if any)"
        )

    st.markdown("---")

    # Set goal button
    if st.button("🎯 SET GOAL", type="primary", use_container_width=True):
        if goal_type_value == "custom" and not goal_name:
            st.error("Please provide a name for your custom goal.")
        else:
            try:
                tracker.set_primary_goal(
                    goal_type=goal_type_value,
                    target_amount=target_amount,
                    target_year=target_year,
                    current_amount=current_amount_input,
                    goal_name=goal_name
                )

                st.success("🎉 Goal set successfully!")
                st.balloons()
                st.info("Switch to the 'Goal Dashboard' tab to see your progress.")

                # Optionally rerun to refresh
                # st.rerun()

            except ValueError as e:
                st.error(f"Invalid goal parameters: {str(e)}")
            except Exception as e:
                message, severity = translate_exception(e, context="Setting goal")
                handle_error_display(message, severity)

# ========================================
# TAB 3: ASSUMPTIONS
# ========================================
with tab3:
    st.markdown("## Projection Assumptions")

    st.markdown("""
    These assumptions are used to project your portfolio's future growth.
    Adjust them based on your personal situation and expectations.
    """)

    st.markdown("---")

    assumptions = tracker.get_assumptions()

    # Annual return rate
    annual_return = st.slider(
        "Expected Annual Return (%)",
        min_value=0.0,
        max_value=20.0,
        value=assumptions["annual_return_rate"] * 100,
        step=0.5,
        help="All Weather portfolio historical average is ~8.5%"
    )

    st.caption("""
    **Note:** The All Weather portfolio has historically returned around 8.5% annually.
    Conservative: 6-7% | Moderate: 8-9% | Aggressive: 10%+
    """)

    # Monthly contribution
    monthly_contrib = st.number_input(
        "Monthly Contribution ($)",
        min_value=0,
        max_value=100000,
        value=int(assumptions["monthly_contribution"]),
        step=100,
        help="How much will you add to your portfolio each month?"
    )

    st.caption("💡 Regular contributions significantly accelerate your progress toward your goal.")

    # Inflation rate
    inflation = st.slider(
        "Expected Inflation Rate (%)",
        min_value=0.0,
        max_value=10.0,
        value=assumptions["inflation_rate"] * 100,
        step=0.5,
        help="Used for inflation-adjusted projections (future feature)"
    )

    st.markdown("---")

    # Update assumptions button
    if st.button("💾 UPDATE ASSUMPTIONS", type="primary", use_container_width=True):
        try:
            tracker.update_assumptions(
                annual_return_rate=annual_return / 100,
                monthly_contribution=monthly_contrib,
                inflation_rate=inflation / 100
            )

            st.success("✅ Assumptions updated!")

            # If goal exists, recalculate projection
            if has_primary_goal:
                st.info("Your goal projections have been updated with the new assumptions. Switch to 'Goal Dashboard' to see the changes.")

        except Exception as e:
            message, severity = translate_exception(e, context="Updating assumptions")
            handle_error_display(message, severity)

    # Reset to defaults
    if st.button("🔄 Reset to Defaults"):
        tracker.update_assumptions(
            annual_return_rate=0.085,
            monthly_contribution=0,
            inflation_rate=0.03
        )
        st.success("Reset to default assumptions.")
        st.rerun()
