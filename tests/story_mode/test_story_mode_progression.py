import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestStoryModeProgression(unittest.TestCase):
    """Tests for story progression and choice processing in StoryMode."""
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
        self.story_mode.player_data["story_progress"]["current_chapter"] = "start"

    def test_story_progression(self):
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter, \
             patch('story_mode.progress.DefaultStoryProgressManager.save_progress') as mock_save:
            initial_chapter = StoryChapter(
                "start",
                {"choices": [{"text": "Continue", "next_chapter": "next"}]}
            )
            initial_chapter.get_choices = lambda player_data=None: initial_chapter.data["choices"]
            mock_get_chapter.return_value = initial_chapter
            chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertEqual(chapter.chapter_id, "start")
            next_chapter = StoryChapter(
                "next",
                {"choices": [{"text": "Dummy", "next_chapter": "end"}]}
            )
            next_chapter.get_choices = lambda player_data=None: next_chapter.data["choices"]
            mock_get_chapter.return_value = next_chapter
            self.story_mode.process_choice(self.story_mode.player_data, 0)
            mock_save.assert_called_once() 