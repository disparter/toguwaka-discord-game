import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import Chapter

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
        with patch('story_mode.progress.DefaultStoryProgressManager.get_current_chapter') as mock_get_chapter:
            mock_get_chapter.return_value = Chapter(
                chapter_id="test_chapter",
                title="Test Chapter",
                content="Test content",
                choices=[]
            )
            chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertIsNotNone(chapter)
            self.assertEqual(chapter.chapter_id, "test_chapter")

class TestStoryModeIntegration(unittest.TestCase):
    def setUp(self):
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()

    def test_story_progression(self):
        """Test basic story progression"""
        with patch('story_mode.progress.DefaultStoryProgressManager.get_current_chapter') as mock_get_chapter, \
             patch('story_mode.progress.DefaultStoryProgressManager.save_progress') as mock_save:
            # Mock initial chapter
            initial_chapter = Chapter(
                chapter_id="start",
                title="Start",
                content="Beginning of story",
                choices=[{"text": "Continue", "next_chapter": "next"}]
            )
            mock_get_chapter.return_value = initial_chapter
            
            # Test initial state
            chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertEqual(chapter.chapter_id, "start")
            
            # Mock next chapter
            next_chapter = Chapter(
                chapter_id="next",
                title="Next",
                content="Next part",
                choices=[]
            )
            mock_get_chapter.return_value = next_chapter
            
            # Test progression
            self.story_mode.make_choice(self.mock_ctx, 0)
            mock_save.assert_called_once()

class TestStoryModeCog(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789

    def test_cog_initialization(self):
        """Test that the story mode cog initializes correctly"""
        from cogs.story_mode_cog import StoryModeCog
        cog = StoryModeCog(self.mock_bot)
        self.assertIsNotNone(cog)
        self.assertEqual(cog.bot, self.mock_bot)

if __name__ == '__main__':
    unittest.main() 