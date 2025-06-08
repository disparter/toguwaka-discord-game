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
from tests.story_mode.test_story_mode import TestStoryMode, TestStoryModeIntegration, TestStoryModeCog
from tests.story_mode.test_story_mode_fixes import TestStoryModeChapterSuffixes, TestStoryModeClubSpecificDialogues, TestStoryModeConditionalChapterNavigation, TestStoryModeChallengeChapterIDs

# Import the new test modules
try:
    from tests.test_dynamodb import TestDynamoDB
    from tests.test_git_operations import TestGitOperations
    from tests.test_commit_functionality import TestCommitFunctionality
except ImportError as e:
    print(f"Warning: Could not import one or more test modules: {e}")

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
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryMode))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeIntegration))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeCog))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeChapterSuffixes))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeClubSpecificDialogues))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeConditionalChapterNavigation))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeChallengeChapterIDs))

    # Add the new test cases
    try:
        test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestDynamoDB))
        test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestGitOperations))
        test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestCommitFunctionality))
    except NameError:
        print("Warning: One or more test classes could not be added to the test suite")

    return test_suite

if __name__ == '__main__':
    # Run the tests
    test_suite = create_test_suite()
    test_runner = unittest.TextTestRunner()
    test_runner.run(test_suite)
