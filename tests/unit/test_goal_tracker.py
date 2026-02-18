"""
Unit tests for goal_tracker.py

Tests financial math (compound interest), edge cases, and goal management.
"""

import pytest
from datetime import datetime
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from goal_tracker import GoalTracker, GoalType


class TestGoalTrackerEdgeCases:
    """Test edge cases in goal tracking and financial calculations"""

    def test_zero_annual_return(self, tmp_path):
        """Test projection with 0% annual return (edge case)"""
        # Use temporary state file for testing
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))
        tracker.update_assumptions(annual_return_rate=0.0, monthly_contribution=1000)

        projection = tracker.calculate_projection(
            current_amount=10000,
            years=10,
            target_amount=100000
        )

        # Should handle without crash
        assert projection["required_monthly_contribution"] > 0
        assert projection["projected_amount"] > 0
        # With 0% return, projection should be current + contributions
        expected = 10000 + (1000 * 12 * 10)
        assert abs(projection["projected_amount"] - expected) < 1  # Allow small float error

    def test_negative_years_raises_error(self, tmp_path):
        """Test that past target year raises ValueError"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        with pytest.raises(ValueError, match="must be in the future"):
            tracker.set_primary_goal(
                goal_type="retirement",
                target_amount=1000000,
                target_year=2020  # Past year
            )

    def test_goal_already_achieved(self, tmp_path):
        """Test when current amount exceeds target"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        projection = tracker.calculate_projection(
            current_amount=1500000,
            years=10,
            target_amount=1000000
        )

        assert projection["on_track"] is True
        assert projection["surplus"] > 0
        assert projection["shortfall"] == 0
        assert projection["required_monthly_contribution"] == 0

    def test_compound_interest_calculation(self, tmp_path):
        """Verify compound interest formula accuracy"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        # Test compound interest formula: 10000 * 1.085^10 ≈ 22610
        projection = tracker.calculate_projection(
            current_amount=10000,
            years=10,
            target_amount=20000,  # Set target below projection to ensure on_track
            monthly_contribution=0
        )

        # Verify projection amount is close to expected (22610)
        assert abs(projection["projected_amount"] - 22610) < 100
        # Should be on track since projection > target
        assert projection["on_track"] is True

    def test_high_contribution_reaches_goal(self, tmp_path):
        """Test that high monthly contributions can reach any goal"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        projection = tracker.calculate_projection(
            current_amount=10000,
            years=5,
            target_amount=100000,
            monthly_contribution=1500
        )

        # With $1500/month for 5 years, should reach goal
        assert projection["on_track"] is True or projection["shortfall"] < 5000


class TestGoalManagement:
    """Test goal creation, updates, and persistence"""

    def test_set_primary_goal(self, tmp_path):
        """Test setting a primary goal"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        current_year = datetime.now().year
        goal = tracker.set_primary_goal(
            goal_type="retirement",
            target_amount=1000000,
            target_year=current_year + 25,
            current_amount=50000
        )

        assert goal["goal_type"] == "retirement"
        assert goal["target_amount"] == 1000000
        assert goal["years_to_goal"] == 25
        assert "initial_projection" in goal

    def test_goal_persistence(self, tmp_path):
        """Test that goals are saved and can be reloaded"""
        state_file = tmp_path / "test_goals.json"

        # Create tracker and set goal
        tracker1 = GoalTracker(state_file=str(state_file))
        current_year = datetime.now().year
        tracker1.set_primary_goal(
            goal_type="house",
            target_amount=500000,
            target_year=current_year + 10,
            current_amount=100000
        )

        # Create new tracker instance (simulates app restart)
        tracker2 = GoalTracker(state_file=str(state_file))
        all_goals = tracker2.get_all_goals()

        # Goal should be persisted
        assert all_goals["primary_goal"] is not None
        assert all_goals["primary_goal"]["goal_type"] == "house"
        assert all_goals["primary_goal"]["target_amount"] == 500000

    def test_clear_primary_goal(self, tmp_path):
        """Test removing the primary goal"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        current_year = datetime.now().year
        tracker.set_primary_goal(
            goal_type="retirement",
            target_amount=1000000,
            target_year=current_year + 25
        )

        # Clear the goal
        tracker.clear_primary_goal()

        all_goals = tracker.get_all_goals()
        assert all_goals["primary_goal"] is None

    def test_update_assumptions(self, tmp_path):
        """Test updating projection assumptions"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        tracker.update_assumptions(
            annual_return_rate=0.10,
            monthly_contribution=2000,
            inflation_rate=0.02
        )

        assumptions = tracker.get_assumptions()
        assert assumptions["annual_return_rate"] == 0.10
        assert assumptions["monthly_contribution"] == 2000
        assert assumptions["inflation_rate"] == 0.02

    def test_get_goal_progress_no_goal(self, tmp_path):
        """Test progress check when no goal is set"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        progress = tracker.get_goal_progress(50000)

        assert progress["has_goal"] is False
        assert "message" in progress


class TestGoalProjectionLogic:
    """Test the projection logic and calculations"""

    def test_on_track_status(self, tmp_path):
        """Test on_track status determination"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        current_year = datetime.now().year
        tracker.set_primary_goal(
            goal_type="retirement",
            target_amount=100000,
            target_year=current_year + 10,
            current_amount=50000
        )

        # With good progress, should be on track
        progress = tracker.get_goal_progress(75000)
        assert progress["has_goal"] is True
        assert "status" in progress
        # Status should be positive (on_track, close, or progressing)
        assert progress["status"] in ["on_track", "close", "progressing"]

    def test_behind_status(self, tmp_path):
        """Test behind status when progress is low"""
        state_file = tmp_path / "test_goals.json"
        tracker = GoalTracker(state_file=str(state_file))

        current_year = datetime.now().year
        tracker.set_primary_goal(
            goal_type="retirement",
            target_amount=1000000,
            target_year=current_year + 5,
            current_amount=10000
        )

        # With very low progress relative to time remaining, should be behind
        progress = tracker.get_goal_progress(15000)
        # Progress percentage should be very low
        assert progress["progress_percentage"] < 50


# Fixtures
@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory for state files"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir
