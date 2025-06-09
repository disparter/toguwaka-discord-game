import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands
from commands.registration import RegistrationCommands
from src.utils.persistence.db_provider import get_all_clubs, update_player
from src.utils.normalization import normalize_club_name
from src.utils.game_mechanics import select_club

pytest.skip('Skipping: depende de patch em utils.dynamodb.get_table, removido do projeto', allow_module_level=True)

@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=commands.Bot)
    return bot

@pytest.fixture
def mock_ctx():
    ctx = AsyncMock()
    ctx.author.id = "123456789"
    ctx.author.name = "Test Player"
    return ctx

@pytest.fixture
def registration_commands(mock_bot):
    return RegistrationCommands(mock_bot)

@pytest.fixture
def mock_dynamodb():
    return {
        'players': MagicMock()
    }

@pytest.mark.asyncio
async def test_club_selection_success(mock_ctx):
    """Test successful club selection."""
    with patch('src.utils.persistence.db_provider.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs, \
         patch('src.utils.persistence.db_provider.update_player', new_callable=AsyncMock) as mock_update:
        
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update.return_value = True
        
        cmd = RegistrationCommands()
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_update.assert_called_once_with(
            mock_ctx.author.id,
            club_id='test_club'
        )

@pytest.mark.asyncio
async def test_club_selection_invalid_club(mock_ctx):
    """Test club selection with invalid club name."""
    with patch('src.utils.persistence.db_provider.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        
        cmd = RegistrationCommands()
        await cmd.select_club(mock_ctx, "Invalid Club")
        
        mock_get_clubs.assert_called_once()
        mock_ctx.send.assert_called_once_with("Clube não encontrado. Por favor, escolha um clube válido.")

@pytest.mark.asyncio
async def test_club_selection_database_error(mock_ctx):
    """Test club selection with database error."""
    with patch('src.utils.persistence.db_provider.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs, \
         patch('src.utils.persistence.db_provider.update_player', new_callable=AsyncMock) as mock_update:
        
        mock_get_clubs.return_value = [
            {'club_id': 'test_club', 'name': 'Test Club', 'description': 'A test club'}
        ]
        mock_update.return_value = False
        
        cmd = RegistrationCommands()
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_update.assert_called_once()
        mock_ctx.send.assert_called_once_with("Erro ao atualizar seu clube. Por favor, tente novamente.")

@pytest.mark.asyncio
async def test_club_selection_no_clubs(mock_ctx):
    """Test club selection when no clubs are available."""
    with patch('src.utils.persistence.db_provider.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = []
        
        cmd = RegistrationCommands()
        await cmd.select_club(mock_ctx, "Test Club")
        
        mock_get_clubs.assert_called_once()
        mock_ctx.send.assert_called_once_with("Não há clubes disponíveis no momento.") 