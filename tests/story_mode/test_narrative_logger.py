import unittest
import os
import shutil
import json
from story_mode.narrative_logger import get_narrative_logger
from story_mode.validation import get_story_validator
from story_mode.story_mode import StoryMode

class TestNarrativeLogger(unittest.TestCase):
    """Test case for the narrative logger and validation system."""

    def setUp(self):
        """Set up the test environment."""
        # Create a temporary log directory
        self.test_log_dir = "data/logs/narrative_test"
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Initialize the narrative logger with the test directory
        self.narrative_logger = get_narrative_logger(self.test_log_dir)
        
        # Initialize the story validator
        self.validator = get_story_validator()
        
        # Initialize the story mode
        self.story_mode = StoryMode()

    def tearDown(self):
        """Clean up the test environment."""
        # Remove the temporary log directory
        if os.path.exists(self.test_log_dir):
            shutil.rmtree(self.test_log_dir)

    def test_log_choice(self):
        """Test logging a player's choice."""
        # Log a choice
        self.narrative_logger.log_choice("test_player", "1_1", "choice_0", 0)
        
        # Check that the choice was logged
        choice_log_path = os.path.join(self.test_log_dir, "choice_logs.json")
        self.assertTrue(os.path.exists(choice_log_path), "Choice log file was not created")
        
        # Check the content of the choice log
        with open(choice_log_path, 'r') as f:
            choice_logs = json.load(f)
        
        self.assertIn("1_1", choice_logs, "Chapter ID not found in choice logs")
        self.assertIn("choice_0:0", choice_logs["1_1"], "Choice not found in choice logs")
        self.assertEqual(choice_logs["1_1"]["choice_0:0"], 1, "Choice count is incorrect")

    def test_log_path(self):
        """Test logging a player's path."""
        # Log a path
        self.narrative_logger.log_path("test_player", ["1_1", "1_2", "1_3"])
        
        # Check that the path was logged
        path_log_path = os.path.join(self.test_log_dir, "path_logs.json")
        self.assertTrue(os.path.exists(path_log_path), "Path log file was not created")
        
        # Check the content of the path log
        with open(path_log_path, 'r') as f:
            path_logs = json.load(f)
        
        self.assertIn("1_1->1_2->1_3", path_logs, "Path not found in path logs")
        self.assertEqual(path_logs["1_1->1_2->1_3"], 1, "Path count is incorrect")

    def test_log_error(self):
        """Test logging an error."""
        # Log an error
        self.narrative_logger.log_error("test_player", "1_1", "test_error", "Test error message")
        
        # Check that the error was logged
        error_log_path = os.path.join(self.test_log_dir, "error_logs.json")
        self.assertTrue(os.path.exists(error_log_path), "Error log file was not created")
        
        # Check the content of the error log
        with open(error_log_path, 'r') as f:
            error_logs = json.load(f)
        
        self.assertIn("1_1", error_logs, "Chapter ID not found in error logs")
        self.assertIn("test_error", error_logs["1_1"], "Error type not found in error logs")
        self.assertEqual(error_logs["1_1"]["test_error"], 1, "Error count is incorrect")

    def test_validate_chapter_id(self):
        """Test validating a chapter ID."""
        # Valid chapter IDs
        self.assertTrue(self.validator.validate_chapter_id("1_1"), "Valid chapter ID '1_1' was rejected")
        self.assertTrue(self.validator.validate_chapter_id("1_2_success"), "Valid chapter ID '1_2_success' was rejected")
        
        # Invalid chapter IDs
        self.assertFalse(self.validator.validate_chapter_id("invalid"), "Invalid chapter ID 'invalid' was accepted")
        self.assertFalse(self.validator.validate_chapter_id("1-1"), "Invalid chapter ID '1-1' was accepted")

    def test_validate_choice(self):
        """Test validating a player's choice."""
        # Create a player data dictionary
        player_data = {"user_id": "test_player"}
        
        # Create a list of available choices
        available_choices = [
            {"text": "Choice 1", "next_chapter": "1_2"},
            {"text": "Choice 2", "next_dialogue": 3},
            {"text": "Choice 3", "metadata": {"affinity_changes": {"NPC1": 5}}}
        ]
        
        # Valid choice
        result = self.validator.validate_choice(player_data, "1_1", 0, available_choices)
        self.assertTrue(result["valid"], "Valid choice was rejected")
        
        # Invalid choice (index out of range)
        result = self.validator.validate_choice(player_data, "1_1", 3, available_choices)
        self.assertFalse(result["valid"], "Invalid choice index was accepted")
        
        # Invalid choice (missing required metadata)
        available_choices.append({"text": "Invalid choice"})
        result = self.validator.validate_choice(player_data, "1_1", 3, available_choices)
        self.assertFalse(result["valid"], "Choice with missing metadata was accepted")

    def test_validate_affinity_change(self):
        """Test validating an affinity change."""
        # Create a player data dictionary
        player_data = {"user_id": "test_player"}
        
        # Valid affinity change
        result = self.validator.validate_affinity_change(player_data, "NPC1", 5)
        self.assertTrue(result["valid"], "Valid affinity change was rejected")
        
        # Invalid affinity change (empty NPC name)
        result = self.validator.validate_affinity_change(player_data, "", 5)
        self.assertFalse(result["valid"], "Affinity change with empty NPC name was accepted")
        
        # Invalid affinity change (out of bounds)
        result = self.validator.validate_affinity_change(player_data, "NPC1", 15)
        self.assertFalse(result["valid"], "Affinity change out of bounds was accepted")

    def test_validate_conditional(self):
        """Test validating a conditional statement."""
        # Create a player data dictionary
        player_data = {"user_id": "test_player"}
        
        # Valid club_id conditional
        condition = {"type": "club_id", "value": 1}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertTrue(result["valid"], "Valid club_id conditional was rejected")
        
        # Valid affinity conditional
        condition = {"type": "affinity", "npc": "NPC1", "threshold": 5}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertTrue(result["valid"], "Valid affinity conditional was rejected")
        
        # Valid choice conditional
        condition = {"type": "choice", "chapter_id": "1_1", "choice_key": "choice_0", "choice_value": 0}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertTrue(result["valid"], "Valid choice conditional was rejected")
        
        # Invalid conditional (missing type)
        condition = {"value": 1}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertFalse(result["valid"], "Conditional with missing type was accepted")
        
        # Invalid club_id conditional (missing value)
        condition = {"type": "club_id"}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertFalse(result["valid"], "Club ID conditional with missing value was accepted")
        
        # Invalid affinity conditional (missing fields)
        condition = {"type": "affinity", "npc": "NPC1"}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertFalse(result["valid"], "Affinity conditional with missing fields was accepted")
        
        # Invalid choice conditional (missing fields)
        condition = {"type": "choice", "chapter_id": "1_1"}
        result = self.validator.validate_conditional(player_data, condition)
        self.assertFalse(result["valid"], "Choice conditional with missing fields was accepted")

if __name__ == '__main__':
    unittest.main()