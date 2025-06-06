import unittest
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import all test modules
from tests.utils.game_mechanics.calculators.test_experience_calculator import TestExperienceCalculator
from tests.utils.game_mechanics.calculators.test_hp_factor_calculator import TestHPFactorCalculator
from tests.utils.game_mechanics.duel.test_duel_calculator import TestDuelCalculator
from tests.utils.game_mechanics.duel.test_duel_narrator import TestDuelNarrator
from tests.utils.game_mechanics.events.test_random_event import TestRandomEvent
from tests.utils.game_mechanics.events.test_training_event import TestTrainingEvent

# Create a test suite
def create_test_suite():
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestExperienceCalculator))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestHPFactorCalculator))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestDuelCalculator))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestDuelNarrator))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestRandomEvent))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestTrainingEvent))

    return test_suite

if __name__ == '__main__':
    # Run the tests
    test_suite = create_test_suite()
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)
