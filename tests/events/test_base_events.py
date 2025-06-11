"""
Test module for base events functionality.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import discord
from datetime import datetime, timedelta

from src.events.base_events import BaseEvent

class TestBaseEvent(unittest.TestCase):
    """Test cases for BaseEvent class."""
    
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
        self.event = BaseEvent(self.bot)
    
    def test_find_channel(self):
        """Test finding a channel."""
        # Test finding channel by ID
        self.bot.get_channel.return_value = self.channel
        channel = self.event.find_channel(self.channel.id)
        self.assertEqual(channel, self.channel)
        self.bot.get_channel.assert_called_once_with(self.channel.id)
        
        # Test finding channel by name
        self.guild.text_channels = [self.channel]
        self.bot.get_channel.return_value = None
        channel = self.event.find_channel("test-channel")
        self.assertEqual(channel, self.channel)
    
    def test_create_basic_embed(self):
        """Test creating a basic embed."""
        embed = self.event.create_basic_embed(
            title="Test Title",
            description="Test Description",
            color=discord.Color.blue()
        )
        self.assertIsInstance(embed, discord.Embed)
        self.assertEqual(embed.title, "Test Title")
        self.assertEqual(embed.description, "Test Description")
        self.assertEqual(embed.color, discord.Color.blue())
    
    def test_cleanup(self):
        """Test cleaning up resources."""
        # Test cleaning up a message
        self.message.delete = AsyncMock()
        self.event.cleanup(message=self.message)
        self.message.delete.assert_called_once()
        
        # Test cleaning up a view
        self.view.stop = Mock()
        self.event.cleanup(view=self.view)
        self.view.stop.assert_called_once()
        
        # Test cleaning up both
        self.message.delete = AsyncMock()
        self.view.stop = Mock()
        self.event.cleanup(message=self.message, view=self.view)
        self.message.delete.assert_called_once()
        self.view.stop.assert_called_once()
    
    def test_send_announcement(self):
        """Test sending an announcement."""
        self.channel.send = AsyncMock(return_value=self.message)
        message = self.event.send_announcement(
            channel=self.channel,
            content="Test Announcement",
            embed=self.embed,
            view=self.view
        )
        self.assertEqual(message, self.message)
        self.channel.send.assert_called_once_with(
            content="Test Announcement",
            embed=self.embed,
            view=self.view
        )
    
    def test_handle_error(self):
        """Test handling errors."""
        error = Exception("Test Error")
        self.interaction.followup.send = AsyncMock()
        self.event.handle_error(self.interaction, error)
        self.interaction.followup.send.assert_called_once_with(
            "Ocorreu um erro ao processar o evento. Por favor, tente novamente mais tarde.",
            ephemeral=True
        ) 