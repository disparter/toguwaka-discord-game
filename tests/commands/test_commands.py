"""
Test module for bot commands.
"""

import pytest
import discord
from unittest.mock import Mock, patch, AsyncMock
from cogs.registration import Registration
from cogs.player_status import PlayerStatus
from src.utils.persistence.db_provider import db_provider

@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = Mock(spec=discord.ext.commands.Bot)
    return bot

@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = Mock(spec=discord.ext.commands.Context)
    ctx.author = Mock(spec=discord.Member)
    ctx.author.id = 123456789
    ctx.author.name = "TestUser"
    ctx.send = AsyncMock()
    return ctx

@pytest.mark.skip(reason="Test needs to be updated to handle async database functions correctly")
@pytest.mark.asyncio
async def test_register_command(mock_bot, mock_ctx):
    """Test the register command."""
    # Create cog instance
    cog = Registration(mock_bot)
    
    # Mock database functions
    with patch.object(db_provider, 'get_player', new_callable=AsyncMock) as mock_get_player, \
         patch.object(db_provider, 'create_player', new_callable=AsyncMock) as mock_create_player:
        
        # Test case: New player
        mock_get_player.return_value = None
        mock_create_player.return_value = True
        
        # Mock the wait_for method to simulate user input
        mock_bot.wait_for = AsyncMock()
        mock_bot.wait_for.side_effect = [
            Mock(content="TestUser"),  # Name
            Mock(content="Test Power"),  # Power
            Mock(content="3"),  # Strength level
            Mock(content="1")  # Club choice
        ]
        
        await cog.register(mock_ctx)
        mock_ctx.send.assert_called()
        mock_create_player.assert_called_once()
        
        # Reset mocks
        mock_ctx.send.reset_mock()
        mock_create_player.reset_mock()
        
        # Test case: Existing player
        mock_get_player.return_value = {'name': 'TestUser', 'level': 1}
        
        await cog.register(mock_ctx)
        mock_ctx.send.assert_called_once()
        mock_create_player.assert_not_called()

@pytest.mark.skip(reason="Test needs to be updated to handle async database functions correctly")
@pytest.mark.asyncio
async def test_status_command(mock_bot, mock_ctx):
    """Test the status command."""
    # Create cog instance
    cog = PlayerStatus(mock_bot)
    
    # Mock database functions
    with patch.object(db_provider, 'get_player', new_callable=AsyncMock) as mock_get_player, \
         patch.object(db_provider, 'get_club', new_callable=AsyncMock) as mock_get_club:
        # Test case: Player exists
        mock_get_player.return_value = {
            'name': 'TestUser',
            'level': 1,
            'exp': 0,
            'tusd': 1000,
            'dexterity': 10,
            'intellect': 10,
            'charisma': 10,
            'power_stat': 10,
            'reputation': 0,
            'hp': 100,
            'max_hp': 100,
            'strength_level': 1,
            'club_id': '1',
            'inventory': {}
        }
        mock_get_club.return_value = {
            'name': 'Test Club',
            'description': 'A test club'
        }
        
        await cog.status(mock_ctx)
        mock_ctx.send.assert_called_once()
        
        # Reset mocks
        mock_ctx.send.reset_mock()
        
        # Test case: Player doesn't exist
        mock_get_player.return_value = None
        
        await cog.status(mock_ctx)
        mock_ctx.send.assert_called_once() 