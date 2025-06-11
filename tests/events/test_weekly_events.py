"""
Test module for weekly events functionality.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import discord
from datetime import datetime, timedelta

from src.events.weekly_events import WeeklyEvents
from src.utils.persistence.db_provider import db_provider

class TestWeeklyEvents(unittest.TestCase):
    """Test cases for WeeklyEvents class."""
    
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
        self.event = WeeklyEvents(self.bot)
        
        # Mock database provider
        self.db_patcher = patch('src.events.weekly_events.db_provider')
        self.mock_db = self.db_patcher.start()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.db_patcher.stop()
    
    def test_create_tournament_embed(self):
        """Test creating tournament embed."""
        tournament_data = {
            'name': 'Test Tournament',
            'description': 'Test Description',
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=1),
            'participants': []
        }
        embed = self.event.create_tournament_embed(tournament_data)
        self.assertIsInstance(embed, discord.Embed)
        self.assertEqual(embed.title, "🏆 Test Tournament")
        self.assertIn("Test Description", embed.description)
    
    def test_create_tournament_view(self):
        """Test creating tournament view."""
        tournament_data = {
            'name': 'Test Tournament',
            'description': 'Test Description',
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=1),
            'participants': []
        }
        view = self.event.create_tournament_view(tournament_data)
        self.assertIsInstance(view, discord.ui.View)
        self.assertEqual(len(view.children), 1)
        self.assertIsInstance(view.children[0], discord.ui.Button)
        self.assertEqual(view.children[0].label, "Participar")
    
    def test_handle_tournament_registration(self):
        """Test handling tournament registration."""
        # Mock player data
        player_data = {
            'user_id': str(self.user.id),
            'name': self.user.name,
            'level': 1,
            'exp': 0,
            'reputation': 0
        }
        self.mock_db.get_player.return_value = player_data
        
        # Mock tournament data
        tournament_data = {
            'name': 'Test Tournament',
            'description': 'Test Description',
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(days=1),
            'participants': []
        }
        
        # Test handling registration
        self.event.handle_tournament_registration(self.interaction, tournament_data)
        self.interaction.response.defer.assert_called_once()
        self.interaction.followup.send.assert_called_once()
    
    def test_send_tournament_announcement(self):
        """Test sending tournament announcement."""
        # Mock channel
        self.bot.get_channel.return_value = self.channel
        
        # Mock message
        self.channel.send.return_value = self.message
        
        # Test sending announcement
        message = self.event.send_tournament_announcement()
        self.assertEqual(message, self.message)
        self.channel.send.assert_called_once()
        self.assertTrue(self.message.pin.called)
    
    def test_cleanup_tournament(self):
        """Test cleaning up tournament."""
        # Mock message
        self.message.delete = AsyncMock()
        
        # Test cleanup
        self.event.cleanup_tournament(self.message)
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