import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode

class TestStoryModeCogInitialization(unittest.TestCase):
    """Tests for StoryModeCog initialization."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_bot = MagicMock()
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789

    def test_cog_initialization(self):
        from src.bot.cogs.story_mode import StoryModeCog
        cog = StoryModeCog(self.mock_bot)
        self.assertIsNotNone(cog)
        self.assertEqual(cog.bot, self.mock_bot) 