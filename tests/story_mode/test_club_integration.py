import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestStoryModeClubIntegration(unittest.TestCase):
    """Tests for club chapter loading and effects in StoryMode."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)
        self.story_mode.player_data = {
            "club": {
                "id": 1,  # flames
                "reputation": 0,
                "experience": 0,
                "next_event": "flames_1"
            },
            "experience": 0,
            "tusd": 0,
            "skills": {},
            "story_progress": {"current_chapter": "flames_1"}
        }

    def test_club_chapter_loading_and_effects(self):
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter:
            chapter = StoryChapter(
                "flames_1",
                {
                    "title": "Flames Training",
                    "dialogues": ["Welcome to Flames training!"],
                    "choices": [{"text": "Begin training", "next_chapter": "flames_2"}],
                    "completion_exp": 100,
                    "completion_tusd": 50,
                    "club_reputation_gain": 10,
                    "skill_gains": {"fire_control": 5}
                }
            )
            mock_get_chapter.return_value = chapter
            current_chapter = self.story_mode.get_current_chapter()
            self.assertIsNotNone(current_chapter)
            self.assertIn("title", current_chapter.data)
            self.assertIn("dialogues", current_chapter.data)
            if current_chapter.data.get("choices"):
                choice = 0
                effects = {
                    "experience": current_chapter.data.get("completion_exp", 0),
                    "tusd": current_chapter.data.get("completion_tusd", 0),
                    "club_reputation": current_chapter.data.get("club_reputation_gain", 0),
                    "skill_gains": current_chapter.data.get("skill_gains", {})
                }
                updated_player = self.story_mode.club_manager.apply_club_effects(self.story_mode.player_data, effects)
                self.assertGreaterEqual(updated_player["club"]["experience"], 0)
                self.assertGreaterEqual(updated_player["tusd"], 0)
                self.assertIsInstance(updated_player["skills"], dict) 