import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode

class TestStoryMode(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_story_mode_initialization(self):
        """Test that story mode initializes correctly"""
        self.assertIsNotNone(self.story_mode)
        self.assertIsInstance(self.story_mode, StoryMode)

    def test_get_current_chapter(self):
        """Test getting the current chapter"""
        # Simula o progresso do jogador
        self.story_mode.player_data["story_progress"]["current_chapter"] = "test_chapter"
        # Adiciona um capítulo mock ao arc_manager
        mock_chapter = MagicMock()
        mock_chapter.chapter_id = "test_chapter"
        self.story_mode.arc_manager.arcs["main"].chapters["test_chapter"] = mock_chapter
        chapter = self.story_mode.get_current_chapter()
        self.assertIsNotNone(chapter)
        self.assertEqual(chapter.chapter_id, "test_chapter")

class TestStoryModeIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()
        self.story_mode.player_data["story_progress"]["current_chapter"] = "start"

    def test_story_progression(self):
        """Test basic story progression"""
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter, \
             patch('story_mode.progress.DefaultStoryProgressManager.save_progress') as mock_save:
            # Mock initial chapter
            initial_chapter = MagicMock()
            initial_chapter.chapter_id = "start"
            initial_chapter.chapter_data = {"choices": [{"text": "Continue", "next_chapter": "next"}]}
            mock_get_chapter.return_value = initial_chapter
            # Test initial state
            chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertEqual(chapter.chapter_id, "start")
            # Mock next chapter
            next_chapter = MagicMock()
            next_chapter.chapter_id = "next"
            next_chapter.chapter_data = {"choices": [{"text": "Dummy", "next_chapter": "end"}]}
            mock_get_chapter.return_value = next_chapter
            # Test progression
            self.story_mode.process_choice(self.story_mode.player_data, 0)
            mock_save.assert_called_once()

class TestStoryModeCog(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789

    def test_cog_initialization(self):
        """Test that the story mode cog initializes correctly"""
        from cogs.story_mode import StoryModeCog
        cog = StoryModeCog(self.mock_bot)
        self.assertIsNotNone(cog)
        self.assertEqual(cog.bot, self.mock_bot)

if __name__ == '__main__':
    unittest.main() 