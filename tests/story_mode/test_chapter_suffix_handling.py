import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestChapterSuffixHandling(unittest.TestCase):
    """Tests for correct handling of chapter suffixes in StoryMode."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)
        self.story_mode.player_data["story_progress"]["current_chapter"] = "1_1_arrival"

    def test_chapter_suffix_handling(self):
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter:
            chapter = StoryChapter(
                "1_1_arrival",
                {"next_chapter": "1_2_power_awakening", "branches": []}
            )
            mock_get_chapter.return_value = chapter
            current_chapter = self.story_mode.get_current_chapter(self.story_mode.player_data)
            self.assertIsNotNone(current_chapter)
            self.assertEqual(current_chapter.chapter_id, "1_1_arrival") 