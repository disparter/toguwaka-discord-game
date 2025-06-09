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

# Import the story mode test modules
from tests.story_mode.test_story_mode_initialization import TestStoryModeInitialization
from tests.story_mode.test_story_mode_progression import TestStoryModeProgression
from tests.story_mode.test_story_mode_cog import TestStoryModeCogInitialization
from tests.story_mode.test_club_integration import TestStoryModeClubIntegration
from tests.story_mode.test_chapter_suffix_handling import TestChapterSuffixHandling
from tests.story_mode.test_club_specific_dialogues import TestClubSpecificDialogues
from tests.story_mode.test_conditional_chapter_navigation import TestConditionalChapterNavigation
from tests.story_mode.test_challenge_chapter_ids import TestChallengeChapterIds

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

    # Add the story mode test cases
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeInitialization))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeProgression))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeCogInitialization))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestStoryModeClubIntegration))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestChapterSuffixHandling))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestClubSpecificDialogues))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestConditionalChapterNavigation))
    test_suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestChallengeChapterIds))

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
