"""
Test module for events manager functionality.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import discord
from datetime import datetime, timedelta

from src.events.events_manager import EventsManager
from src.utils.persistence.db_provider import db_provider

class TestEventsManager(unittest.TestCase):
    """Test cases for EventsManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.bot = Mock(spec=discord.Client)
        self.bot.get_channel = AsyncMock()
        self.bot.get_user = AsyncMock()
        
        # Create a mock guild
        self.guild = Mock(spec=discord.Guild)
        self.guild.id = 123456789
        
        # Create a mock channel
        self.channel = Mock(spec=discord.TextChannel)
        self.channel.id = 987654321
        self.channel.guild = self.guild
        self.channel.send = AsyncMock()
        
        # Create a mock user
        self.user = Mock(spec=discord.User)
        self.user.id = 123456789
        self.user.name = "TestUser"
        
        # Create a mock message
        self.message = Mock(spec=discord.Message)
        self.message.id = 111111111
        self.message.channel = self.channel
        
        # Create a mock embed
        self.embed = Mock(spec=discord.Embed)
        self.embed.title = "Test Event"
        self.embed.description = "Test Description"
        
        # Create a mock view
        self.view = Mock(spec=discord.ui.View)
        
        # Create a mock interaction
        self.interaction = Mock(spec=discord.Interaction)
        self.interaction.user = self.user
        self.interaction.channel = self.channel
        self.interaction.response = AsyncMock()
        self.interaction.followup = AsyncMock()
        
        # Create a mock event
        self.event = EventsManager(self.bot)
        
        # Mock database provider
        self.db_patcher = patch('src.events.events_manager.db_provider')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.db_patcher.stop()
    
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.event.daily_events)
        self.assertIsNotNone(self.event.weekly_events)
        self.assertIsNotNone(self.event.special_events)
    
    def test_start_daily_events(self):
        """Test starting daily events."""
        # Mock daily events
        self.event.daily_events.send_daily_announcement = AsyncMock(return_value=self.message)
        
        # Test starting daily events
        self.event.start_daily_events()
        self.event.daily_events.send_daily_announcement.assert_called_once()
    
    def test_start_weekly_events(self):
        """Test starting weekly events."""
        # Mock weekly events
        self.event.weekly_events.send_tournament_announcement = AsyncMock(return_value=self.message)
        
        # Test starting weekly events
        self.event.start_weekly_events()
        self.event.weekly_events.send_tournament_announcement.assert_called_once()
    
    def test_start_special_events(self):
        """Test starting special events."""
        # Mock special events
        self.event.special_events.send_special_event_announcement = AsyncMock(return_value=self.message)
        
        # Test starting special events
        self.event.start_special_events()
        self.event.special_events.send_special_event_announcement.assert_called_once()
    
    def test_cleanup_events(self):
        """Test cleaning up events."""
        # Mock messages
        self.message.delete = AsyncMock()
        
        # Test cleaning up events
        self.event.cleanup_events([self.message])
        self.message.delete.assert_called_once()
    
    def test_handle_error(self):
        """Test handling errors."""
        error = Exception("Test Error")
        self.interaction.followup.send = AsyncMock()
        self.event.handle_error(self.interaction, error)
        self.interaction.followup.send.assert_called_once_with(
            "Ocorreu um erro ao processar o evento. Por favor, tente novamente mais tarde.",
            ephemeral=True
        ) 