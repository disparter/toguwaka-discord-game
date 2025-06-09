import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
import pytest

class TestStoryModeCogInitialization(unittest.TestCase):
    """Tests for StoryModeCog initialization."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_bot = MagicMock()
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789

    @pytest.mark.asyncio
    async def test_cog_initialization(self):
        with patch('discord.app_commands.command', new_callable=MagicMock) as mock_command:
            mock_command.return_value = lambda f: f
            from src.bot.cogs.story_mode import StoryModeCog
            bot = MagicMock()
            cog = StoryModeCog(bot)
            assert cog is not None 