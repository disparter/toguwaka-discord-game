import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestStoryModeInitialization(unittest.TestCase):
    """Tests for StoryMode initialization and basic setup."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)

    def test_initialization(self):
        self.assertIsNotNone(self.story_mode)
        self.assertIsInstance(self.story_mode, StoryMode)

class TestStoryModeCurrentChapter(unittest.TestCase):
    """Tests for retrieving the current chapter in StoryMode."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)

    def test_get_current_chapter(self):
        self.story_mode.player_data["story_progress"]["current_chapter"] = "test_chapter"
        mock_chapter = StoryChapter(
            "test_chapter",
            {"next_chapter": None, "branches": []}
        )
        self.story_mode.arc_manager.arcs["main"].chapters["test_chapter"] = mock_chapter
        chapter = self.story_mode.get_current_chapter()
        self.assertIsNotNone(chapter)
        self.assertEqual(chapter.chapter_id, "test_chapter") 