import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from utils.game_mechanics.calculators.hp_factor_calculator import HPFactorCalculator
from utils.game_mechanics.constants import HP_FACTOR_THRESHOLD, HP_FACTOR_MIN

class TestHPFactorCalculator(unittest.TestCase):
    """Test cases for the HPFactorCalculator class."""

    def setUp(self):
        self.calculator = HPFactorCalculator()

    def test_calculate_factor_full_hp(self):
        """Test that the calculator returns 1.0 for full HP."""
        self.assertEqual(HPFactorCalculator.calculate_factor(100, 100), 1.0)
        self.assertEqual(HPFactorCalculator.calculate_factor(200, 200), 1.0)

    def test_calculate_factor_above_threshold(self):
        """Test that the calculator returns 1.0 for HP above the threshold."""
        # 75% HP (above 50% threshold)
        self.assertEqual(HPFactorCalculator.calculate_factor(75, 100), 1.0)
        self.assertEqual(HPFactorCalculator.calculate_factor(150, 200), 1.0)

        # Exactly at threshold
        self.assertEqual(HPFactorCalculator.calculate_factor(50, 100), 1.0)
        self.assertEqual(HPFactorCalculator.calculate_factor(100, 200), 1.0)

    def test_calculate_factor_below_threshold(self):
        """Test that the calculator returns a reduced factor for HP below the threshold."""
        # 25% HP (below 50% threshold)
        expected_factor = HP_FACTOR_MIN + (1.0 - HP_FACTOR_MIN) * (0.25 / HP_FACTOR_THRESHOLD)
        self.assertAlmostEqual(HPFactorCalculator.calculate_factor(25, 100), expected_factor)
        self.assertAlmostEqual(HPFactorCalculator.calculate_factor(50, 200), expected_factor)

        # 0% HP (should use minimum factor)
        self.assertEqual(HPFactorCalculator.calculate_factor(0, 100), HP_FACTOR_MIN)
        self.assertEqual(HPFactorCalculator.calculate_factor(0, 200), HP_FACTOR_MIN)

    def test_calculate_factor_zero_max_hp(self):
        """Test that the calculator handles zero max HP gracefully."""
        # Should return 1.0 to avoid division by zero
        self.assertEqual(HPFactorCalculator.calculate_factor(0, 0), 1.0)
        self.assertEqual(HPFactorCalculator.calculate_factor(10, 0), 1.0)

    def test_calculate_factor_negative_hp(self):
        """Test that the calculator handles negative HP values correctly."""
        # Negative current HP should be treated as 0
        self.assertEqual(HPFactorCalculator.calculate_factor(-10, 100), HP_FACTOR_MIN)

        # Negative max HP should be treated as 0
        self.assertEqual(HPFactorCalculator.calculate_factor(10, -100), 1.0)

if __name__ == '__main__':
    unittest.main()
