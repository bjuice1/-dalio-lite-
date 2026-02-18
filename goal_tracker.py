"""
Goal Tracker Module for Dalio Lite

Manages user financial goals, projections, and progress tracking.
Calculates compound interest projections and provides goal-based portfolio context.

Usage:
    from goal_tracker import GoalTracker

    tracker = GoalTracker()
    tracker.set_primary_goal(
        goal_type="retirement",
        target_amount=1000000,
        target_year=2050,
        current_amount=50000
    )

    progress = tracker.get_goal_progress(current_portfolio_value=75000)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum


class GoalType(Enum):
    """Supported financial goal types"""
    RETIREMENT = "retirement"
    HOUSE = "house"
    EDUCATION = "education"
    FINANCIAL_INDEPENDENCE = "financial_independence"
    WEALTH_BUILDING = "wealth_building"
    CUSTOM = "custom"


class GoalTracker:
    """
    Manages user financial goals and projections.

    Uses compound interest projections with configurable assumptions
    to help users understand if they're on track.
    """

    def __init__(self, state_file: str = "state/goals.json"):
        """
        Initialize goal tracker.

        Args:
            state_file: Path to JSON file storing goal state
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.goals = self._load_goals()

    def _load_goals(self) -> Dict:
        """Load goals from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, return empty state
                return self._empty_state()
        else:
            return self._empty_state()

    def _empty_state(self) -> Dict:
        """Return empty goal state structure."""
        return {
            "primary_goal": None,
            "secondary_goals": [],
            "assumptions": {
                "annual_return_rate": 0.085,  # 8.5% (All Weather historical average)
                "monthly_contribution": 0,
                "inflation_rate": 0.03
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _save_goals(self) -> None:
        """Save goals to state file."""
        self.goals["updated_at"] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.goals, f, indent=2)

    def set_primary_goal(
        self,
        goal_type: str,
        target_amount: float,
        target_year: int,
        current_amount: float = 0,
        goal_name: Optional[str] = None
    ) -> Dict:
        """
        Set the primary financial goal.

        Args:
            goal_type: Type of goal (retirement, house, education, etc.)
            target_amount: Target dollar amount to reach
            target_year: Year to reach the goal
            current_amount: Current portfolio value (optional)
            goal_name: Custom name for the goal (optional)

        Returns:
            Dictionary with goal details and initial projections
        """
        # Validate goal type
        try:
            GoalType(goal_type)
        except ValueError:
            goal_type = GoalType.CUSTOM.value

        # Calculate years until goal
        current_year = datetime.now().year
        years_to_goal = target_year - current_year

        if years_to_goal <= 0:
            raise ValueError(f"Target year {target_year} must be in the future")

        # Build goal object
        goal = {
            "goal_type": goal_type,
            "goal_name": goal_name or self._default_goal_name(goal_type),
            "target_amount": target_amount,
            "target_year": target_year,
            "years_to_goal": years_to_goal,
            "current_amount": current_amount,
            "created_at": datetime.now().isoformat()
        }

        # Calculate initial projection
        projection = self.calculate_projection(
            current_amount=current_amount,
            years=years_to_goal,
            target_amount=target_amount
        )

        goal["initial_projection"] = projection

        # Save as primary goal
        self.goals["primary_goal"] = goal
        self._save_goals()

        return goal

    def _default_goal_name(self, goal_type: str) -> str:
        """Generate default name for goal type."""
        names = {
            "retirement": "Retirement Fund",
            "house": "Home Down Payment",
            "education": "Education Fund",
            "financial_independence": "Financial Independence",
            "wealth_building": "Wealth Building",
            "custom": "Financial Goal"
        }
        return names.get(goal_type, "Financial Goal")

    def calculate_projection(
        self,
        current_amount: float,
        years: int,
        target_amount: float,
        monthly_contribution: Optional[float] = None
    ) -> Dict:
        """
        Calculate compound interest projection for a goal.

        Formula:
        - Without contributions: FV = PV × (1 + r)^n
        - With contributions: FV = PV × (1 + r)^n + PMT × [((1 + r)^n - 1) / r]

        Args:
            current_amount: Starting portfolio value
            years: Years until goal
            target_amount: Target dollar amount
            monthly_contribution: Optional monthly contribution

        Returns:
            Dictionary with projection details
        """
        if monthly_contribution is None:
            monthly_contribution = self.goals["assumptions"]["monthly_contribution"]

        annual_return = self.goals["assumptions"]["annual_return_rate"]
        monthly_return = annual_return / 12
        months = years * 12

        # Calculate future value without contributions
        fv_no_contributions = current_amount * ((1 + annual_return) ** years)

        # Calculate future value of contributions
        if monthly_contribution > 0 and monthly_return > 0:
            fv_contributions = monthly_contribution * (
                ((1 + monthly_return) ** months - 1) / monthly_return
            )
        else:
            fv_contributions = monthly_contribution * months

        # Total future value
        total_fv = fv_no_contributions + fv_contributions

        # Calculate if on track
        on_track = total_fv >= target_amount
        shortfall = max(0, target_amount - total_fv)
        surplus = max(0, total_fv - target_amount)

        # Calculate required monthly contribution to reach goal
        if current_amount * ((1 + annual_return) ** years) < target_amount:
            # Need contributions to reach goal
            remaining_needed = target_amount - (current_amount * ((1 + annual_return) ** years))
            if monthly_return > 0:
                required_monthly = remaining_needed / (
                    ((1 + monthly_return) ** months - 1) / monthly_return
                )
            else:
                required_monthly = remaining_needed / months
        else:
            # Already on track without contributions
            required_monthly = 0

        return {
            "target_amount": target_amount,
            "projected_amount": total_fv,
            "growth_from_current": fv_no_contributions - current_amount,
            "growth_from_contributions": fv_contributions,
            "on_track": on_track,
            "shortfall": shortfall,
            "surplus": surplus,
            "required_monthly_contribution": max(0, required_monthly),
            "years_to_goal": years,
            "annual_return_assumed": annual_return,
            "monthly_contribution": monthly_contribution
        }

    def get_goal_progress(self, current_portfolio_value: float) -> Dict:
        """
        Get current progress toward primary goal.

        Args:
            current_portfolio_value: Current total portfolio value

        Returns:
            Dictionary with progress metrics
        """
        if not self.goals.get("primary_goal"):
            return {
                "has_goal": False,
                "message": "No goal set. Visit the Goals page to set your first goal."
            }

        goal = self.goals["primary_goal"]
        target_amount = goal["target_amount"]
        target_year = goal["target_year"]
        years_remaining = target_year - datetime.now().year

        # Calculate current progress percentage
        progress_pct = (current_portfolio_value / target_amount) * 100

        # Recalculate projection with current value
        projection = self.calculate_projection(
            current_amount=current_portfolio_value,
            years=max(1, years_remaining),  # At least 1 year
            target_amount=target_amount
        )

        # Determine status
        if projection["on_track"]:
            status = "on_track"
            status_message = f"🎯 On track to reach {goal['goal_name']} by {target_year}"
        elif progress_pct >= 80:
            status = "close"
            status_message = f"⚡ Close to {goal['goal_name']} - almost there!"
        elif progress_pct >= 50:
            status = "progressing"
            status_message = f"📈 Making progress toward {goal['goal_name']}"
        else:
            status = "behind"
            status_message = f"⚠️ Behind on {goal['goal_name']} - consider increasing contributions"

        return {
            "has_goal": True,
            "goal_name": goal["goal_name"],
            "goal_type": goal["goal_type"],
            "target_amount": target_amount,
            "current_amount": current_portfolio_value,
            "target_year": target_year,
            "years_remaining": years_remaining,
            "progress_percentage": min(100, progress_pct),
            "status": status,
            "status_message": status_message,
            "projection": projection
        }

    def add_secondary_goal(
        self,
        goal_type: str,
        target_amount: float,
        target_year: int,
        goal_name: Optional[str] = None
    ) -> Dict:
        """
        Add a secondary goal (in addition to primary goal).

        Args:
            goal_type: Type of goal
            target_amount: Target dollar amount
            target_year: Year to reach goal
            goal_name: Custom name for goal

        Returns:
            Dictionary with goal details
        """
        goal = {
            "goal_type": goal_type,
            "goal_name": goal_name or self._default_goal_name(goal_type),
            "target_amount": target_amount,
            "target_year": target_year,
            "years_to_goal": target_year - datetime.now().year,
            "created_at": datetime.now().isoformat()
        }

        if "secondary_goals" not in self.goals:
            self.goals["secondary_goals"] = []

        self.goals["secondary_goals"].append(goal)
        self._save_goals()

        return goal

    def update_assumptions(
        self,
        annual_return_rate: Optional[float] = None,
        monthly_contribution: Optional[float] = None,
        inflation_rate: Optional[float] = None
    ) -> Dict:
        """
        Update projection assumptions.

        Args:
            annual_return_rate: Expected annual return (e.g., 0.085 for 8.5%)
            monthly_contribution: Monthly contribution amount
            inflation_rate: Expected inflation rate

        Returns:
            Updated assumptions dictionary
        """
        if annual_return_rate is not None:
            self.goals["assumptions"]["annual_return_rate"] = annual_return_rate

        if monthly_contribution is not None:
            self.goals["assumptions"]["monthly_contribution"] = monthly_contribution

        if inflation_rate is not None:
            self.goals["assumptions"]["inflation_rate"] = inflation_rate

        self._save_goals()

        return self.goals["assumptions"]

    def get_assumptions(self) -> Dict:
        """Get current projection assumptions."""
        return self.goals["assumptions"]

    def clear_primary_goal(self) -> None:
        """Remove primary goal."""
        self.goals["primary_goal"] = None
        self._save_goals()

    def get_all_goals(self) -> Dict:
        """Get all goals (primary + secondary)."""
        return {
            "primary_goal": self.goals.get("primary_goal"),
            "secondary_goals": self.goals.get("secondary_goals", []),
            "assumptions": self.goals["assumptions"]
        }
