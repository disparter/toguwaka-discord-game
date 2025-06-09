import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import discord
from discord import app_commands
from cogs.registration import Registration, normalize_club_name
from utils.persistence.db_provider import get_all_clubs, update_player, get_player, get_club
from utils.normalization import normalize_club_name
import utils.game_mechanics

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
    ctx = MagicMock()
    ctx.author = MagicMock()
    ctx.author.id = 123456789
    ctx.send = AsyncMock()
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
    with patch('cogs.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
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
async def test_select_club_success():
    """Test successful club selection."""
    with patch('utils.game_mechanics.get_player', new_callable=AsyncMock) as mock_get_player, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        
        mock_get_player.return_value = {'id': '123456789', 'club_id': None}
        mock_get_all_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update_player.return_value = True
        
        result = await utils.game_mechanics.select_club("123456789", "Test Club")
        
        mock_get_all_clubs.assert_called_once()
        mock_update_player.assert_called_once_with(
            "123456789",
            club_id='test_club'
        )
        assert result == "Você foi registrado no clube Test Club!"

@pytest.mark.asyncio
async def test_select_club_invalid():
    """Test club selection with invalid club name."""
    with patch('utils.game_mechanics.get_player', new_callable=AsyncMock) as mock_get_player, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
        mock_get_player.return_value = {'id': '123456789', 'club_id': None}
        mock_get_all_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        
        result = await utils.game_mechanics.select_club("123456789", "Invalid Club")
        
        mock_get_all_clubs.assert_called_once()
        assert result == "Clube inválido. Por favor, escolha um clube válido."

@pytest.mark.asyncio
async def test_select_club_database_error():
    """Test club selection with database error."""
    with patch('utils.game_mechanics.get_player', new_callable=AsyncMock) as mock_get_player, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        mock_get_player.return_value = {'id': '123456789', 'club_id': None}
        mock_get_all_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update_player.return_value = False
        
        result = await utils.game_mechanics.select_club("123456789", "Test Club")
        
        mock_get_all_clubs.assert_called_once()
        mock_update_player.assert_called_once()
        assert result == "Você foi registrado no clube Test Club!"

@pytest.mark.asyncio
async def test_select_club_no_clubs():
    """Test club selection when no clubs are available."""
    with patch('utils.game_mechanics.get_player', new_callable=AsyncMock) as mock_get_player, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
        mock_get_player.return_value = {'id': '123456789', 'club_id': None}
        mock_get_all_clubs.return_value = []
        
        result = await utils.game_mechanics.select_club("123456789", "Test Club")
        
        mock_get_all_clubs.assert_called_once()
        assert result == "Clube inválido. Por favor, escolha um clube válido."

@pytest.mark.asyncio
async def test_club_selection_error(mock_ctx):
    """Test error handling in club selection."""
    registration_cog = Registration(None)
    with patch('cogs.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs:
        mock_get_all_clubs.side_effect = Exception("Error fetching clubs")
        await registration_cog.select_club.callback(registration_cog, mock_ctx, "Conselho Político")
        mock_ctx.send.assert_called_once()
        assert "❌ Ocorreu um erro ao processar sua seleção. Por favor, tente novamente." in mock_ctx.send.call_args[0][0] 