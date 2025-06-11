"""
Test module for daily events functionality.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import discord
from datetime import datetime, timedelta

from src.events.daily_events import DailyEvents
from src.utils.persistence.db_provider import db_provider

class TestDailyEvents(unittest.TestCase):
    """Test cases for DailyEvents class."""
    
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
        self.event = DailyEvents(self.bot)
        
        # Mock database provider
        self.db_patcher = patch('src.events.daily_events.db_provider')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.db_patcher.stop()
    
    def test_select_subjects(self):
        """Test selecting subjects for daily events."""
        # Test selecting subjects
        subjects = self.event.select_subjects()
        self.assertIsInstance(subjects, list)
        self.assertEqual(len(subjects), 3)
        self.assertTrue(all(isinstance(s, str) for s in subjects))
    
    def test_create_daily_embed(self):
        """Test creating daily event embed."""
        subjects = ["Math", "Science", "History"]
        embed = self.event.create_daily_embed(subjects)
        self.assertIsInstance(embed, discord.Embed)
        self.assertEqual(embed.title, "📚 Aulas do Dia")
        self.assertIn("Math", embed.description)
        self.assertIn("Science", embed.description)
        self.assertIn("History", embed.description)
    
    def test_create_daily_view(self):
        """Test creating daily event view."""
        subjects = ["Math", "Science", "History"]
        view = self.event.create_daily_view(subjects)
        self.assertIsInstance(view, discord.ui.View)
        self.assertEqual(len(view.children), 3)
        for child in view.children:
            self.assertIsInstance(child, discord.ui.Button)
            self.assertIn(child.label, subjects)
    
    def test_handle_subject_selection(self):
        """Test handling subject selection."""
        # Mock player data
        player_data = {
            'user_id': str(self.user.id),
            'name': self.user.name,
            'level': 1,
            'exp': 0,
            'reputation': 0
        }
        self.mock_db.get_player.return_value = player_data
        
        # Mock update player
        self.mock_db.update_player.return_value = True
        
        # Test handling selection
        self.event.handle_subject_selection(self.interaction, "Math")
        self.interaction.response.defer.assert_called_once()
        self.mock_db.update_player.assert_called_once()
        self.interaction.followup.send.assert_called_once()
    
    def test_send_daily_announcement(self):
        """Test sending daily announcement."""
        # Mock channel
        self.bot.get_channel.return_value = self.channel
        
        # Mock message
        self.channel.send.return_value = self.message
        
        # Test sending announcement
        message = self.event.send_daily_announcement()
        self.assertEqual(message, self.message)
        self.channel.send.assert_called_once()
        self.assertTrue(self.message.pin.called)
    
    def test_cleanup_daily_event(self):
        """Test cleaning up daily event."""
        # Mock message
        self.message.delete = AsyncMock()
        
        # Test cleanup
        self.event.cleanup_daily_event(self.message)
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