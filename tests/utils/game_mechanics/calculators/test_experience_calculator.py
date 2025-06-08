import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from utils.game_mechanics.calculators.experience_calculator import ExperienceCalculator
from utils.game_mechanics.constants import BASE_EXP

class TestExperienceCalculator(unittest.TestCase):
    """Test cases for the ExperienceCalculator class."""

    def setUp(self):
        self.calculator = ExperienceCalculator()

    def test_calculate_required_exp(self):
        """Test that the calculator correctly calculates experience required for a level."""
        # Test level 1
        self.assertEqual(ExperienceCalculator.calculate_required_exp(1), BASE_EXP)

        # Test level 10
        expected_exp_level_10 = int(BASE_EXP * (10 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_required_exp(10), expected_exp_level_10)

        # Test level 50
        expected_exp_level_50 = int(BASE_EXP * (50 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_required_exp(50), expected_exp_level_50)

    def test_calculate_level(self):
        """Test that the calculator correctly calculates level from experience."""
        # Test level 1
        self.assertEqual(ExperienceCalculator.calculate_level(0), 1)
        self.assertEqual(ExperienceCalculator.calculate_level(BASE_EXP - 1), 1)

        # Test level 2
        level_2_exp = int(BASE_EXP * (2 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_level(BASE_EXP), 1)
        self.assertEqual(ExperienceCalculator.calculate_level(level_2_exp - 1), 1)
        self.assertEqual(ExperienceCalculator.calculate_level(level_2_exp), 2)

        # Test level 10
        level_10_exp = int(BASE_EXP * (10 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_level(level_10_exp), 10)

        # Test level 50
        level_50_exp = int(BASE_EXP * (50 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_level(level_50_exp), 50)

    def test_calculate_progress(self):
        """Test that the calculator correctly calculates progress to next level."""
        # Test 0% progress
        level_1_exp = BASE_EXP
        level_2_exp = int(BASE_EXP * (2 ** 1.5))
        self.assertEqual(ExperienceCalculator.calculate_progress(level_1_exp, 1), 0)

        # Test 50% progress
        mid_exp = level_1_exp + (level_2_exp - level_1_exp) / 2
        self.assertEqual(ExperienceCalculator.calculate_progress(mid_exp, 1), 50)

        # Test 100% progress (should be capped at 100)
        self.assertEqual(ExperienceCalculator.calculate_progress(level_2_exp, 1), 100)

        # Test progress for higher levels
        level_9_exp = int(BASE_EXP * (9 ** 1.5))
        level_10_exp = int(BASE_EXP * (10 ** 1.5))
        mid_exp = level_9_exp + (level_10_exp - level_9_exp) / 2
        self.assertEqual(ExperienceCalculator.calculate_progress(mid_exp, 9), 50)

    def test_calculate_experience_gain(self):
        """Test basic experience gain calculation"""
        base_exp = 100
        level = 1
        exp_gain = self.calculator.calculate_experience_gain(base_exp, level)
        self.assertGreater(exp_gain, 0)
        self.assertIsInstance(exp_gain, int)

    def test_calculate_level_up(self):
        """Test level up calculation"""
        current_exp = 1000
        current_level = 1
        new_level = self.calculator.calculate_level_up(current_exp, current_level)
        self.assertGreaterEqual(new_level, current_level)

    def test_experience_for_next_level(self):
        """Test experience required for next level"""
        current_level = 1
        exp_needed = self.calculator.experience_for_next_level(current_level)
        self.assertGreater(exp_needed, 0)
        self.assertIsInstance(exp_needed, int)

    def test_level_scaling(self):
        """Test that experience scales with level"""
        base_exp = 100
        exp_gain_low = self.calculator.calculate_experience_gain(base_exp, 1)
        exp_gain_high = self.calculator.calculate_experience_gain(base_exp, 10)
        self.assertLess(exp_gain_high, exp_gain_low)  # Higher levels should get less exp

if __name__ == '__main__':
    unittest.main()
