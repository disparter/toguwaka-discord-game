"""
Test module for club selection functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from decimal import Decimal
import discord
from discord import app_commands
from src.bot.cogs.registration import Registration
from src.utils.normalization import normalize_club_name
import src.utils.game_mechanics
from src.utils.persistence.db_provider import db_provider

# Skip SQLite tests
pytest.skip('Skipping SQLite tests as they are disabled', allow_module_level=True)

# Test data
MOCK_CLUBS = [
    {
        'club_id': 'Ilusionistas Mentais',
        'name': 'Ilusionistas Mentais',
        'description': 'O Ilusionistas Mentais é um dos clubes mais prestigiados da Academia Tokugawa.',
        'leader_id': '2',
        'reputacao': Decimal('0')
    },
    {
        'club_id': 'Elementalistas',
        'name': 'Elementalistas',
        'description': 'O Elementalistas é um dos clubes mais prestigiados da Academia Tokugawa.',
        'leader_id': '4',
        'reputacao': Decimal('0')
    },
    {
        'club_id': 'Conselho Político',
        'name': 'Conselho Político',
        'description': 'O Conselho Político é um dos clubes mais prestigiados da Academia Tokugawa.',
        'leader_id': '3',
        'reputacao': Decimal('0')
    }
]

@pytest.fixture
def mock_interaction():
    """Create a mock Discord interaction."""
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.response = AsyncMock()
    return interaction

@pytest.fixture
def mock_ctx():
    """Create a mock context."""
    ctx = Mock()
    ctx.author = Mock()
    ctx.author.id = "123456789"
    ctx.author.name = "TestUser"
    ctx.send = Mock()
    return ctx

def test_normalize_club_name():
    """Test club name normalization."""
    # Test basic normalization
    assert normalize_club_name("Conselho Político") == "conselho politico"
    assert normalize_club_name("ILUSIONISTAS MENTAIS") == "ilusionistas mentais"
    
    # Test with accents
    assert normalize_club_name("Clube das Chamas") == "clube das chamas"
    
    # Test with extra spaces
    assert normalize_club_name("  Elementalistas  ") == "elementalistas"
    
    # Test with special characters
    assert normalize_club_name("Clube-de-Combate") == "clube de combate"

@pytest.mark.asyncio
async def test_club_selection_autocomplete(mock_interaction):
    """Test club selection autocomplete."""
    registration_cog = Registration(None)
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
        mock_get_all_clubs.return_value = [
            {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
            {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
            {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
        ]
        
        # Test with empty input
        choices = await registration_cog.club_selection_autocomplete(mock_interaction, "")
        assert len(choices) == 3
        assert all(isinstance(choice, app_commands.Choice) for choice in choices)
        
        # Test with partial match
        choices = await registration_cog.club_selection_autocomplete(mock_interaction, "polit")
        assert len(choices) == 1
        assert choices[0].name == "Conselho Político"
        
        # Test with no matches
        choices = await registration_cog.club_selection_autocomplete(mock_interaction, "xyz")
        assert len(choices) == 0

@pytest.mark.asyncio
async def test_club_selection_success(mock_ctx):
    """Test successful club selection."""
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_clubs, \
         patch.object(db_provider, 'update_player', new_callable=AsyncMock) as mock_update:
        
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update.return_value = True
        
        from src.bot.cogs.registration import RegistrationCommands
        cmd = RegistrationCommands(Mock())
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_update.assert_called_once_with(
            mock_ctx.author.id,
            club_id='test_club'
        )

@pytest.mark.asyncio
async def test_club_selection_invalid_club(mock_ctx):
    """Test club selection with invalid club name."""
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        
        from src.bot.cogs.registration import RegistrationCommands
        cmd = RegistrationCommands(Mock())
        await cmd.select_club(mock_ctx, "Invalid Club")
        
        mock_get_clubs.assert_called_once()
        mock_ctx.send.assert_called_once_with("Clube não encontrado. Por favor, escolha um clube válido.")

@pytest.mark.asyncio
async def test_club_selection_database_error(mock_ctx):
    """Test club selection with database error."""
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_clubs, \
         patch.object(db_provider, 'update_player', new_callable=AsyncMock) as mock_update:
        
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update.return_value = False
        
        from src.bot.cogs.registration import RegistrationCommands
        cmd = RegistrationCommands(Mock())
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_update.assert_called_once()
        mock_ctx.send.assert_called_once_with("Erro ao atualizar seu clube. Por favor, tente novamente.")

@pytest.mark.asyncio
async def test_club_selection_no_clubs(mock_ctx):
    """Test club selection when no clubs are available."""
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = []
        
        from src.bot.cogs.registration import RegistrationCommands
        cmd = RegistrationCommands(Mock())
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_ctx.send.assert_called_once_with("Não há clubes disponíveis no momento.")

@pytest.mark.asyncio
async def test_club_selection_error(mock_ctx):
    """Test error handling in club selection."""
    registration_cog = Registration(None)
    with patch.object(db_provider, 'get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
        mock_get_all_clubs.side_effect = Exception("Error fetching clubs")
        await registration_cog.select_club.callback(registration_cog, mock_ctx, "Conselho Político")
        mock_ctx.send.assert_called_once()
        assert "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente." in mock_ctx.send.call_args[0][0] 