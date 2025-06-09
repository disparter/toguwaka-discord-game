import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands
from commands.registration import RegistrationCommands
from utils.db_provider import get_all_clubs, update_player
from utils.normalization import normalize_club_name
from utils.game_mechanics import select_club

@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=commands.Bot)
    return bot

@pytest.fixture
def mock_context():
    context = type('MockContext', (), {})()
    context.author = type('Author', (), {})()
    context.author.id = '123456789'
    context.send = AsyncMock()
    return context

@pytest.fixture
def registration_commands(mock_bot):
    return RegistrationCommands(mock_bot)

@pytest.fixture
def mock_dynamodb():
    return {
        'players': MagicMock()
    }

@pytest.mark.asyncio
async def test_club_selection_success(mock_context):
    with patch('utils.dynamodb.get_table') as mock_get_table, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        players_table = type('PlayersTable', (), {})()
        players_table.get_item = AsyncMock(return_value={'Item': {'user_id': mock_context.author.id, 'club_id': None}})
        players_table.scan = AsyncMock(return_value={'Items': [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]})
        players_table.put_item = AsyncMock()
        players_table.meta = MagicMock()
        mock_get_table.side_effect = lambda name: players_table
        mock_get_all_clubs.return_value = [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]
        mock_update_player.return_value = None
        result = await select_club(mock_context.author.id, "clube_das_chamas")
        assert result == "Você foi registrado no clube Clube das Chamas!"

@pytest.mark.asyncio
async def test_club_selection_invalid_club(mock_context):
    with patch('utils.dynamodb.get_table') as mock_get_table, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        players_table = type('PlayersTable', (), {})()
        players_table.get_item = AsyncMock(return_value={'Item': {'user_id': mock_context.author.id, 'club_id': None}})
        players_table.scan = AsyncMock(return_value={'Items': [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]})
        players_table.put_item = AsyncMock()
        players_table.meta = MagicMock()
        mock_get_table.side_effect = lambda name: players_table
        mock_get_all_clubs.return_value = [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]
        mock_update_player.return_value = None
        result = await select_club(mock_context.author.id, "invalid_club")
        assert result == "Clube inválido. Por favor, escolha um clube válido."

@pytest.mark.asyncio
async def test_club_selection_database_error(mock_context):
    with patch('utils.dynamodb.get_table') as mock_get_table, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        players_table = type('PlayersTable', (), {})()
        players_table.get_item = AsyncMock(side_effect=Exception("Database error"))
        players_table.scan = AsyncMock(return_value={'Items': [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]})
        players_table.put_item = AsyncMock()
        players_table.meta = MagicMock()
        mock_get_table.side_effect = lambda name: players_table
        mock_get_all_clubs.return_value = [{'club_id': 'clube_das_chamas', 'name': 'Clube das Chamas'}]
        mock_update_player.return_value = None
        result = await select_club(mock_context.author.id, "clube_das_chamas")
        assert result == "Erro ao selecionar clube. Por favor, tente novamente mais tarde."

@pytest.mark.asyncio
async def test_club_selection_no_clubs(mock_context):
    with patch('utils.dynamodb.get_table') as mock_get_table, \
         patch('utils.game_mechanics.get_all_clubs', new_callable=AsyncMock) as mock_get_all_clubs, \
         patch('utils.game_mechanics.update_player', new_callable=AsyncMock) as mock_update_player:
        players_table = type('PlayersTable', (), {})()
        players_table.get_item = AsyncMock(return_value={'Item': {'user_id': mock_context.author.id, 'club_id': None}})
        players_table.scan = AsyncMock(return_value={'Items': []})
        players_table.put_item = AsyncMock()
        players_table.meta = MagicMock()
        mock_get_table.side_effect = lambda name: players_table
        mock_get_all_clubs.return_value = []
        mock_update_player.return_value = None
        result = await select_club(mock_context.author.id, None)
        assert result == "Nenhum clube disponível no momento." 