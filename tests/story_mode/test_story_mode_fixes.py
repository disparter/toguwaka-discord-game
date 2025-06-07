import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import copy

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from story_mode.progress import DefaultStoryProgressManager
from story_mode.chapter import BaseChapter
from story_mode.story_mode import StoryMode

class TestStoryModeChapterSuffixes(unittest.TestCase):
    """Test cases for handling chapter IDs with suffixes like _success or _failure."""

    def setUp(self):
        """Set up test fixtures."""
        self.progress_manager = DefaultStoryProgressManager()

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "story_progress": {
                "current_year": 1,
                "current_chapter": 4,
                "current_challenge_chapter": None,
                "full_chapter_id": None,
                "completed_chapters": ["1_1", "1_2", "1_3"],
                "completed_challenge_chapters": [],
                "failed_challenge_chapters": [],
                "blocked_chapter_arcs": [],
                "available_chapters": ["1_4"],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {}
            }
        }

    def test_get_current_chapter_with_suffix(self):
        """Test that get_current_chapter returns the full chapter ID when it has a suffix."""
        # Set a chapter ID with a suffix
        self.player_data["story_progress"]["full_chapter_id"] = "1_4_success"

        # Get the current chapter
        chapter_id = self.progress_manager.get_current_chapter(self.player_data)

        # Check that the full chapter ID is returned
        self.assertEqual(chapter_id, "1_4_success")

    def test_set_current_chapter_with_suffix(self):
        """Test that set_current_chapter correctly handles chapter IDs with suffixes."""
        # Set a chapter ID with a suffix
        updated_player_data = self.progress_manager.set_current_chapter(self.player_data, "1_4_success")

        # Check that the full chapter ID is stored
        self.assertEqual(updated_player_data["story_progress"]["full_chapter_id"], "1_4_success")

        # Check that the year and chapter number are correctly parsed
        self.assertEqual(updated_player_data["story_progress"]["current_year"], 1)
        self.assertEqual(updated_player_data["story_progress"]["current_chapter"], 4)

    def test_complete_chapter_with_suffix(self):
        """Test that complete_chapter correctly handles chapter IDs with suffixes."""
        # Set a chapter ID with a suffix
        self.player_data["story_progress"]["full_chapter_id"] = "1_4_success"

        # Complete the chapter
        updated_player_data = self.progress_manager.complete_chapter(self.player_data, "1_4_success")

        # Check that the chapter is added to completed chapters
        self.assertIn("1_4_success", updated_player_data["story_progress"]["completed_chapters"])

        # Check that the full chapter ID is cleared
        self.assertIsNone(updated_player_data["story_progress"]["full_chapter_id"])

class TestStoryModeClubSpecificDialogues(unittest.TestCase):
    """Test cases for handling chapters with club-specific dialogues."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock chapter with club-specific dialogues
        self.chapter_data = {
            "type": "story",
            "title": "Test Chapter",
            "description": "Test description",
            "dialogues": [
                {"npc": "Test NPC", "text": "Test dialogue 1"},
                {"npc": "Test NPC", "text": "Test dialogue 2"}
            ],
            "club_dialogues": {
                "1": [
                    {"npc": "Club Leader 1", "text": "Club 1 dialogue"}
                ],
                "2": [
                    {"npc": "Club Leader 2", "text": "Club 2 dialogue"}
                ]
            },
            "choices": [
                {"text": "Test choice 1", "next_dialogue": 1},
                {"text": "Test choice 2", "next_dialogue": 2}
            ]
        }

        self.chapter = BaseChapter("test_chapter", self.chapter_data)

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "club_id": 1,
            "story_progress": {
                "current_year": 1,
                "current_chapter": 1,
                "current_dialogue_index": 0,
                "completed_chapters": [],
                "completed_challenge_chapters": [],
                "failed_challenge_chapters": [],
                "blocked_chapter_arcs": [],
                "available_chapters": ["test_chapter"],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {}
            }
        }

    def test_process_choice_with_club_specific_dialogues(self):
        """Test that process_choice correctly handles chapters with club-specific dialogues."""
        # Process a choice
        result = self.chapter.process_choice(self.player_data, 0)

        # Check that the choice was processed without errors
        self.assertIn("player_data", result)
        self.assertIn("chapter_data", result)

        # Check that the current dialogue index was incremented
        self.assertEqual(result["player_data"]["story_progress"]["current_dialogue_index"], 1)

class TestStoryModeConditionalChapterNavigation(unittest.TestCase):
    """Test cases for conditional chapter navigation with the new chapter 1_4."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a StoryMode instance with a mock data directory
        with patch('os.makedirs'):
            self.story_mode = StoryMode(data_dir="mock_data_dir")

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "story_progress": {
                "current_year": 1,
                "current_chapter": 3,
                "current_challenge_chapter": None,
                "full_chapter_id": "1_3",
                "completed_chapters": ["1_1", "1_2"],
                "completed_challenge_chapters": [],
                "failed_challenge_chapters": [],
                "blocked_chapter_arcs": [],
                "available_chapters": ["1_3"],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {}
            }
        }

        # Create a mock chapter 1_3 (challenge chapter)
        self.chapter_1_3 = MagicMock()
        self.chapter_1_3.chapter_id = "1_3"
        self.chapter_1_3.process_choice.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": None,
                "choices": []
            }
        }
        self.chapter_1_3.complete.return_value = self.player_data
        self.chapter_1_3.get_next_chapter.return_value = "1_4"

        # Create a mock chapter 1_4 (redirect chapter)
        self.chapter_1_4 = MagicMock()
        self.chapter_1_4.chapter_id = "1_4"
        self.chapter_1_4.data = {
            "conditional_next_chapter": {
                "challenge_result": {
                    "success": "1_4_success",
                    "failure": "1_4_failure",
                    "default": "1_4_success"
                }
            }
        }
        self.chapter_1_4.start.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Resultado do Desafio",
                "description": "Redirecionando para o resultado apropriado do seu desafio.",
                "current_dialogue": {"npc": "Narrador", "text": "Redirecionando para o resultado do seu desafio..."},
                "choices": []
            }
        }
        self.chapter_1_4.get_next_chapter.side_effect = lambda player_data: "1_4_success" if player_data["story_progress"].get("challenge_result") == "success" else "1_4_failure"

        # Create mock chapters 1_4_success and 1_4_failure
        self.chapter_1_4_success = MagicMock()
        self.chapter_1_4_success.chapter_id = "1_4_success"
        self.chapter_1_4_success.start.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Sucesso no Primeiro Desafio",
                "description": "Após completar com sucesso seu primeiro desafio, você começa a ganhar reconhecimento na academia.",
                "current_dialogue": {"npc": "Narrador", "text": "Seu sucesso no desafio não passou despercebido."},
                "choices": []
            }
        }

        self.chapter_1_4_failure = MagicMock()
        self.chapter_1_4_failure.chapter_id = "1_4_failure"
        self.chapter_1_4_failure.start.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Fracasso no Primeiro Desafio",
                "description": "Após falhar em seu primeiro desafio, você precisa lidar com as consequências.",
                "current_dialogue": {"npc": "Narrador", "text": "Seu fracasso no desafio foi notado pelos outros estudantes."},
                "choices": []
            }
        }

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    def test_conditional_navigation_success(self, mock_load_chapter):
        """Test that the story mode correctly navigates to the success chapter when the challenge result is success."""
        # Set the challenge result to success
        self.player_data["story_progress"]["challenge_result"] = "success"

        # Mock the load_chapter method to return the appropriate mock chapters
        mock_load_chapter.side_effect = lambda chapter_id: {
            "1_3": self.chapter_1_3,
            "1_4": self.chapter_1_4,
            "1_4_success": self.chapter_1_4_success,
            "1_4_failure": self.chapter_1_4_failure
        }.get(chapter_id)

        # Process a choice to complete chapter 1_3
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that chapter 1_3 was completed
        self.chapter_1_3.complete.assert_called_once()

        # Check that chapter 1_4 was started
        self.chapter_1_4.start.assert_called_once()

        # Check that the current chapter was set to 1_4
        self.assertEqual(self.player_data["story_progress"]["full_chapter_id"], "1_4")

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    def test_conditional_navigation_failure(self, mock_load_chapter):
        """Test that the story mode correctly navigates to the failure chapter when the challenge result is failure."""
        # Set the challenge result to failure
        self.player_data["story_progress"]["challenge_result"] = "failure"

        # Mock the load_chapter method to return the appropriate mock chapters
        mock_load_chapter.side_effect = lambda chapter_id: {
            "1_3": self.chapter_1_3,
            "1_4": self.chapter_1_4,
            "1_4_success": self.chapter_1_4_success,
            "1_4_failure": self.chapter_1_4_failure
        }.get(chapter_id)

        # Process a choice to complete chapter 1_3
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that chapter 1_3 was completed
        self.chapter_1_3.complete.assert_called_once()

        # Check that chapter 1_4 was started
        self.chapter_1_4.start.assert_called_once()

        # Check that the current chapter was set to 1_4
        self.assertEqual(self.player_data["story_progress"]["full_chapter_id"], "1_4")

class TestStoryModeChallengeChapterIDs(unittest.TestCase):
    """Test cases for handling challenge chapter IDs with underscores."""

    def setUp(self):
        """Set up test fixtures."""
        self.progress_manager = DefaultStoryProgressManager()

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "story_progress": {
                "current_year": 1,
                "current_chapter": 4,
                "current_challenge_chapter": None,
                "full_chapter_id": None,
                "completed_chapters": ["1_1", "1_2", "1_3"],
                "completed_challenge_chapters": [],
                "failed_challenge_chapters": [],
                "blocked_chapter_arcs": [],
                "available_chapters": ["1_4"],
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "story_choices": {}
            }
        }

    def test_set_current_chapter_with_challenge_id(self):
        """Test that set_current_chapter correctly handles challenge chapter IDs with underscores."""
        # Set a challenge chapter ID with underscores
        updated_player_data = self.progress_manager.set_current_chapter(self.player_data, "challenge_biblioteca_proibida")

        # Check that the full chapter ID is stored
        self.assertEqual(updated_player_data["story_progress"]["full_chapter_id"], "challenge_biblioteca_proibida")

        # Check that it's stored as a challenge chapter
        self.assertEqual(updated_player_data["story_progress"]["current_challenge_chapter"], "challenge_biblioteca_proibida")

        # Check that the year and chapter number are not changed
        self.assertEqual(updated_player_data["story_progress"]["current_year"], 1)
        self.assertEqual(updated_player_data["story_progress"]["current_chapter"], 4)

    def test_get_current_chapter_with_challenge_id(self):
        """Test that get_current_chapter returns the correct challenge chapter ID."""
        # Set a challenge chapter ID with underscores
        self.player_data["story_progress"]["current_challenge_chapter"] = "challenge_biblioteca_proibida"
        self.player_data["story_progress"]["full_chapter_id"] = "challenge_biblioteca_proibida"

        # Get the current chapter
        chapter_id = self.progress_manager.get_current_chapter(self.player_data)

        # Check that the full chapter ID is returned
        self.assertEqual(chapter_id, "challenge_biblioteca_proibida")

    def test_complete_chapter_with_challenge_id(self):
        """Test that complete_chapter correctly handles challenge chapter IDs with underscores."""
        # Set a challenge chapter ID with underscores
        self.player_data["story_progress"]["current_challenge_chapter"] = "challenge_biblioteca_proibida"
        self.player_data["story_progress"]["full_chapter_id"] = "challenge_biblioteca_proibida"

        # Complete the chapter
        updated_player_data = self.progress_manager.complete_chapter(self.player_data, "challenge_biblioteca_proibida")

        # Check that the chapter is added to completed challenge chapters
        self.assertIn("challenge_biblioteca_proibida", updated_player_data["story_progress"]["completed_challenge_chapters"])

        # Check that the current challenge chapter is cleared
        self.assertIsNone(updated_player_data["story_progress"]["current_challenge_chapter"])

        # Check that the full chapter ID is cleared
        self.assertIsNone(updated_player_data["story_progress"]["full_chapter_id"])

if __name__ == '__main__':
    unittest.main()
