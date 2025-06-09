import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestClubSpecificDialogues(unittest.TestCase):
    """Tests for loading club-specific dialogues in StoryMode."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)
        self.story_mode.player_data["story_progress"]["current_chapter"] = "club_chapter"
        self.story_mode.player_data["club"] = {"id": 1, "reputation": 0}

    def test_club_specific_dialogues(self):
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter:
            chapter = StoryChapter(
                "club_chapter",
                {
                    "title": "Club Training",
                    "dialogues": ["Welcome to club training!"],
                    "club_specific": {
                        "1": ["Welcome to Flames training!"],
                        "2": ["Welcome to Water training!"]
                    }
                }
            )
            mock_get_chapter.return_value = chapter
            current_chapter = self.story_mode.get_current_chapter(self.story_mode.player_data)
            self.assertIsNotNone(current_chapter)
            self.assertIn("club_specific", current_chapter.data) 