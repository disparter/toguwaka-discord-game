import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import json
import copy

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from story_mode.story_mode import StoryMode
from story_mode.chapter import BaseChapter, StoryChapter, ChallengeChapter, BranchingChapter

class TestStoryMode(unittest.TestCase):
    """Test cases for the StoryMode class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock data directory
        self.data_dir = "mock_data_dir"

        # Mock the os.makedirs function to avoid creating directories
        with patch('os.makedirs'):
            # Create a StoryMode instance with the mock data directory
            self.story_mode = StoryMode(data_dir=self.data_dir)

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 10,
            "intellect": 10,
            "charisma": 10,
            "power_stat": 10,
            "club_id": 1,
            "story_progress": {
                "current_chapter": "1_1",
                "completed_chapters": [],
                "available_chapters": ["1_1"],
                "current_year": 1,
                "current_chapter_number": 1,
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "faction_reputations": {},
                "powers": {},
                "choices": {}
            }
        }

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_start_story_chapter_not_found(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode handles the case where a chapter is not found."""
        # Mock the load_chapter method to return None
        mock_load_chapter.return_value = None

        # Mock the get_available_chapters method to return an empty list
        with patch('story_mode.story_mode.FileChapterLoader.get_available_chapters', return_value=[]):
            # Start the story
            result = self.story_mode.start_story(self.player_data)

            # Check that an error is returned
            self.assertIn("error", result)
            self.assertEqual(result["error"], "No chapters available")

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    @patch('story_mode.story_mode.FileChapterLoader.get_available_chapters')
    def test_start_story_chapter_found(self, mock_get_available_chapters, mock_load_chapters, mock_load_chapter):
        """Test that the story mode correctly starts a chapter when it is found."""
        # Create a mock chapter
        mock_chapter = MagicMock()
        mock_chapter.start.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": {
                    "npc": "Test NPC",
                    "text": "Test dialogue"
                },
                "choices": [
                    {"text": "Test choice 1", "next_dialogue": 1},
                    {"text": "Test choice 2", "next_dialogue": 2}
                ]
            }
        }

        # Mock the load_chapter method to return the mock chapter
        mock_load_chapter.return_value = mock_chapter

        # Start the story
        result = self.story_mode.start_story(self.player_data)

        # Check that the chapter was started
        mock_chapter.start.assert_called_once()

        # Check that the result contains the expected data
        self.assertIn("chapter_data", result)
        self.assertEqual(result["chapter_data"]["title"], "Test Chapter")
        self.assertEqual(result["chapter_data"]["description"], "Test description")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["npc"], "Test NPC")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["text"], "Test dialogue")
        self.assertEqual(len(result["chapter_data"]["choices"]), 2)

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_process_choice_chapter_not_found(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode handles the case where a chapter is not found when processing a choice."""
        # Mock the load_chapter method to return None
        mock_load_chapter.return_value = None

        # Process a choice
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that an error is returned
        self.assertIn("error", result)
        self.assertEqual(result["error"], f"Chapter not found: {self.player_data['story_progress']['current_chapter']}")

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_process_choice_success(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode correctly processes a choice."""
        # Create a mock chapter
        mock_chapter = MagicMock()
        mock_chapter.process_choice.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": {
                    "npc": "Test NPC",
                    "text": "Test dialogue after choice"
                },
                "choices": [
                    {"text": "Test choice 1", "next_dialogue": 1},
                    {"text": "Test choice 2", "next_dialogue": 2}
                ]
            }
        }

        # Mock the load_chapter method to return the mock chapter
        mock_load_chapter.return_value = mock_chapter

        # Process a choice
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that the choice was processed
        mock_chapter.process_choice.assert_called_once_with(self.player_data, 0)

        # Check that the result contains the expected data
        self.assertIn("chapter_data", result)
        self.assertEqual(result["chapter_data"]["title"], "Test Chapter")
        self.assertEqual(result["chapter_data"]["description"], "Test description")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["npc"], "Test NPC")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["text"], "Test dialogue after choice")
        self.assertEqual(len(result["chapter_data"]["choices"]), 2)

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_process_choice_chapter_complete(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode correctly handles a completed chapter."""
        # Create a mock chapter
        mock_chapter = MagicMock()
        mock_chapter.process_choice.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": None,
                "choices": []
            }
        }
        mock_chapter.complete.return_value = self.player_data
        mock_chapter.get_next_chapter.return_value = "1_2"

        # Create a mock next chapter
        mock_next_chapter = MagicMock()
        mock_next_chapter.start.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Next Chapter",
                "description": "Next chapter description",
                "current_dialogue": {
                    "npc": "Test NPC",
                    "text": "Next chapter dialogue"
                },
                "choices": [
                    {"text": "Next chapter choice 1", "next_dialogue": 1},
                    {"text": "Next chapter choice 2", "next_dialogue": 2}
                ]
            }
        }

        # Mock the load_chapter method to return the mock chapters
        mock_load_chapter.side_effect = lambda chapter_id: mock_chapter if chapter_id == "1_1" else mock_next_chapter

        # Process a choice
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that the chapter was completed and the next chapter was started
        mock_chapter.complete.assert_called_once()
        mock_chapter.get_next_chapter.assert_called_once()
        mock_next_chapter.start.assert_called_once()

        # Check that the result contains the expected data
        self.assertIn("chapter_data", result)
        self.assertEqual(result["chapter_data"]["title"], "Next Chapter")
        self.assertEqual(result["chapter_data"]["description"], "Next chapter description")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["npc"], "Test NPC")
        self.assertEqual(result["chapter_data"]["current_dialogue"]["text"], "Next chapter dialogue")
        self.assertEqual(len(result["chapter_data"]["choices"]), 2)

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_process_choice_chapter_complete_no_next_chapter(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode correctly handles a completed chapter with no next chapter."""
        # Create a mock chapter
        mock_chapter = MagicMock()
        mock_chapter.process_choice.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": None,
                "choices": []
            }
        }
        mock_chapter.complete.return_value = self.player_data
        mock_chapter.get_next_chapter.return_value = None

        # Mock the load_chapter method to return the mock chapter
        mock_load_chapter.return_value = mock_chapter

        # Process a choice
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that the chapter was completed
        mock_chapter.complete.assert_called_once()
        mock_chapter.get_next_chapter.assert_called_once()

        # Check that the result indicates the story is complete
        self.assertIn("chapter_complete", result)
        self.assertTrue(result["chapter_complete"])
        self.assertIn("story_complete", result)
        self.assertTrue(result["story_complete"])
        self.assertEqual(result["chapter_data"]["title"], "Fim da História")

    @patch('story_mode.story_mode.FileChapterLoader.load_chapter')
    @patch('story_mode.story_mode.FileChapterLoader._load_chapters')
    def test_process_choice_chapter_complete_next_chapter_not_found(self, mock_load_chapters, mock_load_chapter):
        """Test that the story mode correctly handles a completed chapter with a next chapter that is not found."""
        # Create a mock chapter
        mock_chapter = MagicMock()
        mock_chapter.process_choice.return_value = {
            "player_data": self.player_data,
            "chapter_data": {
                "title": "Test Chapter",
                "description": "Test description",
                "current_dialogue": None,
                "choices": []
            }
        }
        mock_chapter.complete.return_value = self.player_data
        mock_chapter.get_next_chapter.return_value = "1_2"

        # Mock the load_chapter method to return the mock chapter for the current chapter and None for the next chapter
        mock_load_chapter.side_effect = lambda chapter_id: mock_chapter if chapter_id == "1_1" else None

        # Process a choice
        result = self.story_mode.process_choice(self.player_data, 0)

        # Check that the chapter was completed
        mock_chapter.complete.assert_called_once()
        mock_chapter.get_next_chapter.assert_called_once()

        # Check that the result indicates the story is complete
        self.assertIn("chapter_complete", result)
        self.assertTrue(result["chapter_complete"])
        self.assertIn("story_complete", result)
        self.assertTrue(result["story_complete"])
        self.assertEqual(result["chapter_data"]["title"], "Fim da História")

class TestStoryModeIntegration(unittest.TestCase):
    """Integration tests for the StoryMode class with real chapter data."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a StoryMode instance with the real data directory
        self.story_mode = StoryMode()

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 10,
            "intellect": 10,
            "charisma": 10,
            "power_stat": 10,
            "club_id": 1,
            "story_progress": {
                "current_chapter": "1_1",
                "completed_chapters": [],
                "available_chapters": ["1_1"],
                "current_year": 1,
                "current_chapter_number": 1,
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "faction_reputations": {},
                "powers": {},
                "choices": {}
            }
        }

    def test_all_chapters_reachable(self):
        """Test that all chapters in the story are reachable from the starting chapter."""
        # Start from the first chapter
        current_chapter_id = "1_1"
        visited_chapters = set()
        chapters_to_visit = [current_chapter_id]

        # Traverse all chapters
        while chapters_to_visit:
            current_chapter_id = chapters_to_visit.pop(0)

            # Skip if already visited
            if current_chapter_id in visited_chapters:
                continue

            # Mark as visited
            visited_chapters.add(current_chapter_id)

            # Load the chapter
            chapter = self.story_mode.chapter_loader.load_chapter(current_chapter_id)

            # Skip if chapter not found
            if not chapter:
                continue

            # Get the chapter data
            chapter_data = chapter.data

            # Check if the chapter has a next chapter
            next_chapter = chapter_data.get("next_chapter")
            if next_chapter and next_chapter not in visited_chapters:
                chapters_to_visit.append(next_chapter)

            # Check if the chapter has branches
            branches = chapter_data.get("branches", {})
            for branch in branches.values():
                branch_next_chapter = branch.get("next_chapter")
                if branch_next_chapter and branch_next_chapter not in visited_chapters:
                    chapters_to_visit.append(branch_next_chapter)

        # Get all chapters from the loader
        all_chapters = set(self.story_mode.chapter_loader.chapters.keys())

        # Check that all chapters are reachable
        unreachable_chapters = all_chapters - visited_chapters
        self.assertEqual(unreachable_chapters, set(), f"The following chapters are not reachable: {unreachable_chapters}")

    def test_no_dead_ends(self):
        """Test that there are no dead ends in the story."""
        # Start from the first chapter
        current_chapter_id = "1_1"
        visited_chapters = set()
        chapters_to_visit = [current_chapter_id]
        dead_end_chapters = set()

        # Traverse all chapters
        while chapters_to_visit:
            current_chapter_id = chapters_to_visit.pop(0)

            # Skip if already visited
            if current_chapter_id in visited_chapters:
                continue

            # Mark as visited
            visited_chapters.add(current_chapter_id)

            # Load the chapter
            chapter = self.story_mode.chapter_loader.load_chapter(current_chapter_id)

            # Skip if chapter not found
            if not chapter:
                dead_end_chapters.add(current_chapter_id)
                continue

            # Get the chapter data
            chapter_data = chapter.data

            # Check if the chapter has a next chapter or branches
            has_next = False

            next_chapter = chapter_data.get("next_chapter")
            if next_chapter:
                has_next = True
                if next_chapter not in visited_chapters:
                    chapters_to_visit.append(next_chapter)

            branches = chapter_data.get("branches", {})
            if branches:
                has_next = True
                for branch in branches.values():
                    branch_next_chapter = branch.get("next_chapter")
                    if branch_next_chapter and branch_next_chapter not in visited_chapters:
                        chapters_to_visit.append(branch_next_chapter)

            # If the chapter has no next chapter or branches, it's a dead end
            if not has_next and chapter_data.get("type") != "challenge":
                dead_end_chapters.add(current_chapter_id)

        # Check that there are no dead ends
        self.assertEqual(dead_end_chapters, set(), f"The following chapters are dead ends: {dead_end_chapters}")

    def test_all_choices_lead_somewhere(self):
        """Test that all choices in all chapters lead to valid next dialogues or chapters."""
        # Start from the first chapter
        current_chapter_id = "1_1"
        visited_chapters = set()
        chapters_to_visit = [current_chapter_id]
        invalid_choices = []

        # Traverse all chapters
        while chapters_to_visit:
            current_chapter_id = chapters_to_visit.pop(0)

            # Skip if already visited
            if current_chapter_id in visited_chapters:
                continue

            # Mark as visited
            visited_chapters.add(current_chapter_id)

            # Load the chapter
            chapter = self.story_mode.chapter_loader.load_chapter(current_chapter_id)

            # Skip if chapter not found
            if not chapter:
                continue

            # Get the chapter data
            chapter_data = chapter.data

            # Check all choices in the chapter
            choices = chapter_data.get("choices", [])
            for i, choice in enumerate(choices):
                next_dialogue = choice.get("next_dialogue")
                if next_dialogue is not None:
                    # Check if the next dialogue exists in additional_dialogues
                    additional_dialogues = chapter_data.get("additional_dialogues", {})
                    if str(next_dialogue) not in additional_dialogues and f"success_{next_dialogue}" not in additional_dialogues and f"failure_{next_dialogue}" not in additional_dialogues:
                        invalid_choices.append((current_chapter_id, f"choices[{i}]", f"next_dialogue={next_dialogue}"))

            # Check all choices in additional dialogues
            additional_dialogues = chapter_data.get("additional_dialogues", {})
            for dialogue_id, dialogue in additional_dialogues.items():
                if isinstance(dialogue, list):
                    for i, d in enumerate(dialogue):
                        if "choices" in d:
                            for j, choice in enumerate(d["choices"]):
                                next_dialogue = choice.get("next_dialogue")
                                if next_dialogue is not None:
                                    if str(next_dialogue) not in additional_dialogues and f"success_{next_dialogue}" not in additional_dialogues and f"failure_{next_dialogue}" not in additional_dialogues:
                                        invalid_choices.append((current_chapter_id, f"additional_dialogues[{dialogue_id}][{i}].choices[{j}]", f"next_dialogue={next_dialogue}"))

            # Check all choices in club_specific_dialogues
            club_specific_dialogues = chapter_data.get("club_specific_dialogues", {})
            for club_id, dialogues in club_specific_dialogues.items():
                for i, dialogue in enumerate(dialogues):
                    if "choices" in dialogue:
                        for j, choice in enumerate(dialogue["choices"]):
                            next_dialogue = choice.get("next_dialogue")
                            if next_dialogue is not None:
                                if str(next_dialogue) not in additional_dialogues and f"success_{next_dialogue}" not in additional_dialogues and f"failure_{next_dialogue}" not in additional_dialogues:
                                    invalid_choices.append((current_chapter_id, f"club_specific_dialogues[{club_id}][{i}].choices[{j}]", f"next_dialogue={next_dialogue}"))

            # Get the next chapter
            next_chapter = chapter_data.get("next_chapter")
            if next_chapter and next_chapter not in visited_chapters:
                chapters_to_visit.append(next_chapter)

            # Check branches
            branches = chapter_data.get("branches", {})
            for branch in branches.values():
                branch_next_chapter = branch.get("next_chapter")
                if branch_next_chapter and branch_next_chapter not in visited_chapters:
                    chapters_to_visit.append(branch_next_chapter)

        # Check that there are no invalid choices
        self.assertEqual(invalid_choices, [], f"The following choices are invalid: {invalid_choices}")

    def test_duplicate_chapter_ids(self):
        """Test that there are no duplicate chapter IDs in the story."""
        # Get all chapter files
        chapters_dir = os.path.join(self.story_mode.data_dir, "chapters")
        chapter_ids = {}  # Map chapter_id to filename
        duplicate_ids = {}  # Map chapter_id to list of filenames

        # Check each chapter file
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(chapters_dir, filename)
                with open(file_path, 'r') as f:
                    chapters_data = json.load(f)

                for chapter_id in chapters_data.keys():
                    if chapter_id in chapter_ids:
                        if chapter_id not in duplicate_ids:
                            duplicate_ids[chapter_id] = [chapter_ids[chapter_id]]
                        duplicate_ids[chapter_id].append(filename)
                    else:
                        chapter_ids[chapter_id] = filename

        # Check that there are no duplicate chapter IDs
        self.assertEqual(duplicate_ids, {}, f"The following chapter IDs are duplicated across files: {duplicate_ids}")

    def test_consistent_chapter_id_format(self):
        """Test that all chapter IDs follow a consistent format."""
        # Get all chapter files
        chapters_dir = os.path.join(self.story_mode.data_dir, "chapters")
        inconsistent_ids = {}

        # Define the expected format pattern (numeric IDs like 1_1, 1_2, etc.)
        import re
        numeric_pattern = re.compile(r'^\d+(_\d+)*(_[a-z]+)?$')

        # Check each chapter file
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(chapters_dir, filename)
                with open(file_path, 'r') as f:
                    chapters_data = json.load(f)

                for chapter_id in chapters_data.keys():
                    if not numeric_pattern.match(chapter_id):
                        if filename not in inconsistent_ids:
                            inconsistent_ids[filename] = []
                        inconsistent_ids[filename].append(chapter_id)

        # Check that all chapter IDs follow the consistent format
        self.assertEqual(inconsistent_ids, {}, f"The following chapter IDs have inconsistent format: {inconsistent_ids}")

    def test_all_referenced_chapters_exist(self):
        """Test that all chapters referenced as next_chapter actually exist."""
        # Get all chapter files
        chapters_dir = os.path.join(self.story_mode.data_dir, "chapters")
        all_chapter_ids = set()
        referenced_chapters = set()
        missing_chapters = set()

        # First pass: collect all chapter IDs
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(chapters_dir, filename)
                with open(file_path, 'r') as f:
                    chapters_data = json.load(f)

                for chapter_id in chapters_data.keys():
                    all_chapter_ids.add(chapter_id)

        # Second pass: collect all referenced chapter IDs
        for filename in os.listdir(chapters_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(chapters_dir, filename)
                with open(file_path, 'r') as f:
                    chapters_data = json.load(f)

                for chapter_id, chapter_data in chapters_data.items():
                    # Check next_chapter
                    if "next_chapter" in chapter_data:
                        next_chapter = chapter_data["next_chapter"]
                        referenced_chapters.add(next_chapter)

                    # Check branches
                    if "branches" in chapter_data:
                        for branch_name, branch_data in chapter_data["branches"].items():
                            if "next_chapter" in branch_data:
                                next_chapter = branch_data["next_chapter"]
                                referenced_chapters.add(next_chapter)

        # Find referenced chapters that don't exist
        for chapter_id in referenced_chapters:
            if chapter_id not in all_chapter_ids:
                missing_chapters.add(chapter_id)

        # Check that all referenced chapters exist
        self.assertEqual(missing_chapters, set(), f"The following referenced chapters don't exist: {missing_chapters}")

class TestStoryModeCog(unittest.TestCase):
    """Test cases for the StoryModeCog class."""

    def setUp(self):
        """Set up test fixtures."""
        # Import the StoryModeCog class
        from cogs.story_mode import StoryModeCog

        # Create a mock bot
        self.bot = MagicMock()
        self.bot.config = {"guild_id": 123456789, "admin_role_id": 987654321}

        # Create a StoryModeCog instance
        self.cog = StoryModeCog(self.bot)

        # Create a mock interaction
        self.interaction = MagicMock()
        self.interaction.user.id = 123456789
        self.interaction.channel_id = 123456789
        self.interaction.channel = MagicMock()

        # Create a mock player data
        self.player_data = {
            "user_id": 123456789,
            "name": "Test Player",
            "level": 1,
            "exp": 0,
            "tusd": 100,
            "dexterity": 10,
            "intellect": 10,
            "charisma": 10,
            "power_stat": 10,
            "club_id": 1,
            "story_progress": {
                "current_chapter": "1_1",
                "completed_chapters": [],
                "available_chapters": ["1_1"],
                "current_year": 1,
                "current_chapter_number": 1,
                "hierarchy_tier": 0,
                "hierarchy_points": 0,
                "discovered_secrets": [],
                "special_items": [],
                "character_relationships": {},
                "faction_reputations": {},
                "powers": {},
                "choices": {}
            }
        }

    @patch('cogs.story_mode.get_player')
    @patch('cogs.story_mode.update_player')
    async def test_slash_start_story_messages_ephemeral(self, mock_update_player, mock_get_player):
        """Test that all messages sent by slash_start_story are ephemeral."""
        # Mock the get_player function to return the mock player data
        mock_get_player.return_value = self.player_data

        # Mock the StoryMode.start_story method to return a valid result
        with patch.object(self.cog.story_mode, 'start_story') as mock_start_story:
            mock_start_story.return_value = {
                "player_data": self.player_data,
                "chapter_data": {
                    "title": "Test Chapter",
                    "description": "Test description",
                    "current_dialogue": {
                        "npc": "Test NPC",
                        "text": "Test dialogue"
                    },
                    "choices": [
                        {"text": "Test choice 1", "next_dialogue": 1},
                        {"text": "Test choice 2", "next_dialogue": 2}
                    ]
                }
            }

            # Call the slash_start_story method
            await self.cog.slash_start_story(self.interaction)

            # Check that the interaction.response.defer was called with ephemeral=True
            self.interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Check that interaction.followup.send was called with ephemeral=True
            self.interaction.followup.send.assert_called_once()
            call_args = self.interaction.followup.send.call_args
            self.assertIn('ephemeral', call_args[1])
            self.assertTrue(call_args[1]['ephemeral'])

    @patch('cogs.story_mode.get_player')
    async def test_slash_story_status_messages_ephemeral(self, mock_get_player):
        """Test that all messages sent by slash_story_status are ephemeral."""
        # Mock the get_player function to return the mock player data
        mock_get_player.return_value = self.player_data

        # Mock the StoryMode.get_story_status method to return a valid result
        with patch.object(self.cog.story_mode, 'get_story_status') as mock_get_story_status:
            mock_get_story_status.return_value = {
                "current_chapter": {
                    "id": "1_1",
                    "title": "Test Chapter",
                    "description": "Test description"
                },
                "completed_chapters": [],
                "completed_challenge_chapters": [],
                "hierarchy": {
                    "tier": 0,
                    "points": 0
                },
                "discovered_secrets": [],
                "special_items": [],
                "relationships": [],
                "faction_reputations": {},
                "powers": {}
            }

            # Call the slash_story_status method
            await self.cog.slash_story_status(self.interaction)

            # Check that the interaction.response.defer was called with ephemeral=True
            self.interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Check that interaction.followup.send was called with ephemeral=True
            self.interaction.followup.send.assert_called_once()
            call_args = self.interaction.followup.send.call_args
            self.assertIn('ephemeral', call_args[1])
            self.assertTrue(call_args[1]['ephemeral'])

    @patch('cogs.story_mode.get_player')
    async def test_slash_relacionamento_messages_ephemeral(self, mock_get_player):
        """Test that all messages sent by slash_relacionamento are ephemeral."""
        # Mock the get_player function to return the mock player data
        mock_get_player.return_value = self.player_data

        # Mock the StoryMode.get_story_status method to return a valid result
        with patch.object(self.cog.story_mode, 'get_story_status') as mock_get_story_status:
            mock_get_story_status.return_value = {
                "relationships": [
                    {
                        "npc": "Test NPC",
                        "affinity": 10,
                        "level": "Amigável"
                    }
                ]
            }

            # Call the slash_relacionamento method
            await self.cog.slash_relacionamento(self.interaction)

            # Check that the interaction.response.defer was called with ephemeral=True
            self.interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Check that interaction.followup.send was called with ephemeral=True
            self.interaction.followup.send.assert_called_once()
            call_args = self.interaction.followup.send.call_args
            self.assertIn('ephemeral', call_args[1])
            self.assertTrue(call_args[1]['ephemeral'])

    @patch('cogs.story_mode.get_player')
    async def test_slash_participate_event_messages_ephemeral(self, mock_get_player):
        """Test that all messages sent by slash_participate_event are ephemeral."""
        # Mock the get_player function to return the mock player data
        mock_get_player.return_value = self.player_data

        # Mock the StoryMode.start_story method to return a valid result
        with patch.object(self.cog.story_mode, 'start_story') as mock_start_story:
            mock_start_story.return_value = {
                "available_events": [
                    {
                        "id": "test_event",
                        "name": "Test Event",
                        "description": "Test event description"
                    }
                ]
            }

            # Call the slash_participate_event method
            await self.cog.slash_participate_event(self.interaction)

            # Check that the interaction.response.defer was called with ephemeral=True
            self.interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Check that interaction.followup.send was called with ephemeral=True
            self.interaction.followup.send.assert_called_once()
            call_args = self.interaction.followup.send.call_args
            self.assertIn('ephemeral', call_args[1])
            self.assertTrue(call_args[1]['ephemeral'])

    @patch('cogs.story_mode.get_player')
    @patch('cogs.story_mode.update_player')
    async def test_send_dialogue_or_choices_messages_ephemeral(self, mock_update_player, mock_get_player):
        """Test that all messages sent by _send_dialogue_or_choices are ephemeral."""
        # Mock the channel.send method
        channel = MagicMock()

        # Create a result with a current dialogue
        result = {
            "chapter_data": {
                "current_dialogue": {
                    "npc": "Test NPC",
                    "text": "Test dialogue",
                    "choices": [
                        {"text": "Test choice 1"},
                        {"text": "Test choice 2"}
                    ]
                }
            }
        }

        # Call the _send_dialogue_or_choices method
        await self.cog._send_dialogue_or_choices(channel, 123456789, result)

        # Check that channel.send was called
        channel.send.assert_called_once()

        # Check that the message was sent with a view (for buttons)
        call_args = channel.send.call_args
        self.assertIn('view', call_args[1])

        # We can't directly check if the message is ephemeral because that's handled by the Discord API
        # But we can check that the buttons have callbacks that check the user ID
        view = call_args[1]['view']
        for item in view.children:
            self.assertIsNotNone(item.callback)

    @patch('cogs.story_mode.get_player')
    async def test_choice_callback_checks_user_id(self, mock_get_player):
        """Test that the choice callback checks the user ID."""
        # Create a mock interaction
        interaction = MagicMock()
        interaction.user.id = 987654321  # Different from the user ID in setUp

        # Create a choice callback
        callback = self.cog._create_choice_callback(123456789, 0)

        # Call the callback
        await callback(interaction)

        # Check that interaction.response.send_message was called with the correct message and ephemeral=True
        interaction.response.send_message.assert_called_once_with("Esta não é a sua história!", ephemeral=True)

        # Check that get_player was not called (because the user ID check failed)
        mock_get_player.assert_not_called()

    @patch('cogs.story_mode.get_player')
    async def test_continue_callback_checks_user_id(self, mock_get_player):
        """Test that the continue callback checks the user ID."""
        # Create a mock interaction
        interaction = MagicMock()
        interaction.user.id = 987654321  # Different from the user ID in setUp

        # Create a continue callback
        callback = self.cog._create_continue_callback(123456789)

        # Call the callback
        await callback(interaction)

        # Check that interaction.response.send_message was called with the correct message and ephemeral=True
        interaction.response.send_message.assert_called_once_with("Esta não é a sua história!", ephemeral=True)

        # Check that get_player was not called (because the user ID check failed)
        mock_get_player.assert_not_called()

    @patch('cogs.story_mode.get_player')
    @patch('cogs.story_mode.update_player')
    async def test_notify_about_events_messages_not_ephemeral(self, mock_update_player, mock_get_player):
        """Test that messages sent by _notify_about_events are not ephemeral."""
        # Mock the channel.send method
        channel = MagicMock()

        # Create available events
        available_events = [
            {
                "id": "test_event",
                "name": "Test Event",
                "description": "Test event description"
            }
        ]

        # Call the _notify_about_events method
        await self.cog._notify_about_events(channel, 123456789, available_events)

        # Check that channel.send was called
        channel.send.assert_called_once()

        # Check that the message was sent without ephemeral=True
        call_args = channel.send.call_args
        self.assertNotIn('ephemeral', call_args[1])

if __name__ == '__main__':
    unittest.main()
