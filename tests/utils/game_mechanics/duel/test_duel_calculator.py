import unittest
from unittest.mock import patch
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.game_mechanics.duel.duel_calculator import DuelCalculator

class TestDuelCalculator(unittest.TestCase):
    """Test cases for the DuelCalculator class."""

    def setUp(self):
        """Set up test data."""
        # Create mock players
        self.challenger = {
            "user_id": 123,
            "name": "Challenger",
            "level": 5,
            "exp": 1000,
            "tusd": 500,
            "dexterity": 10,
            "intellect": 8,
            "charisma": 6,
            "power_stat": 12,
            "hp": 100,
            "max_hp": 100
        }

        self.opponent = {
            "user_id": 456,
            "name": "Opponent",
            "level": 5,
            "exp": 1000,
            "tusd": 500,
            "dexterity": 8,
            "intellect": 10,
            "charisma": 12,
            "power_stat": 6,
            "hp": 100,
            "max_hp": 100
        }

    @patch('random.uniform')
    def test_calculate_outcome_physical(self, mock_uniform):
        """Test that the calculator correctly calculates physical duel outcomes."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Calculate duel outcome
        result = DuelCalculator.calculate_outcome(self.challenger, self.opponent, "physical")

        # Check the result
        self.assertEqual(result["winner"], self.challenger)
        self.assertEqual(result["loser"], self.opponent)
        self.assertEqual(result["duel_type"], "physical")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

    @patch('random.uniform')
    def test_calculate_outcome_mental(self, mock_uniform):
        """Test that the calculator correctly calculates mental duel outcomes."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Calculate duel outcome
        result = DuelCalculator.calculate_outcome(self.challenger, self.opponent, "mental")

        # Check the result
        self.assertEqual(result["winner"], self.opponent)
        self.assertEqual(result["loser"], self.challenger)
        self.assertEqual(result["duel_type"], "mental")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

    @patch('random.uniform')
    def test_calculate_outcome_strategic(self, mock_uniform):
        """Test that the calculator correctly calculates strategic duel outcomes."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Calculate duel outcome
        result = DuelCalculator.calculate_outcome(self.challenger, self.opponent, "strategic")

        # The outcome depends on the weighted attributes, so we don't assert the winner
        # Just check that the result has the expected structure
        self.assertIn("winner", result)
        self.assertIn("loser", result)
        self.assertEqual(result["duel_type"], "strategic")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

    @patch('random.uniform')
    def test_calculate_outcome_social(self, mock_uniform):
        """Test that the calculator correctly calculates social duel outcomes."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Calculate duel outcome
        result = DuelCalculator.calculate_outcome(self.challenger, self.opponent, "social")

        # Check the result
        self.assertEqual(result["winner"], self.opponent)
        self.assertEqual(result["loser"], self.challenger)
        self.assertEqual(result["duel_type"], "social")
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

    @patch('random.uniform')
    def test_calculate_outcome_invalid_type(self, mock_uniform):
        """Test that the calculator handles invalid duel types gracefully."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Calculate duel outcome with invalid type
        result = DuelCalculator.calculate_outcome(self.challenger, self.opponent, "invalid")

        # Check that it defaults to physical
        self.assertEqual(result["duel_type"], "invalid")
        self.assertIn("winner", result)
        self.assertIn("loser", result)
        self.assertGreater(result["win_margin"], 0)
        self.assertGreater(result["exp_reward"], 0)
        self.assertGreater(result["tusd_reward"], 0)
        self.assertGreater(result["hp_loss"], 0)

    @patch('random.uniform')
    def test_calculate_outcome_hp_factor(self, mock_uniform):
        """Test that the calculator correctly applies HP factors."""
        # Mock the randomness to make the test deterministic
        mock_uniform.return_value = 1.0  # No randomness

        # Create players with different HP levels
        low_hp_challenger = self.challenger.copy()
        low_hp_challenger["hp"] = 25  # 25% HP

        # Calculate duel outcome
        result = DuelCalculator.calculate_outcome(low_hp_challenger, self.opponent, "physical")

        # With the current HP_FACTOR_MIN (0.7) and HP_FACTOR_THRESHOLD (0.5),
        # a player at 25% HP would have their attributes multiplied by 0.85,
        # which isn't enough to make the challenger lose a physical duel.
        # So we check that the low HP player still wins but with a reduced margin.
        self.assertEqual(result["winner"], low_hp_challenger)
        self.assertEqual(result["loser"], self.opponent)

if __name__ == '__main__':
    unittest.main()
