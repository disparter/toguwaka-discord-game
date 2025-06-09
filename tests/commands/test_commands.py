import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from discord.ext import commands
from commands.registration import RegistrationCommands
from utils.normalization import normalize_club_name

@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=commands.Bot)
    return bot

@pytest.fixture
def mock_context():
    ctx = AsyncMock()
    ctx.author.id = 123
    ctx.author.name = "Test User"
    ctx.send = AsyncMock()
    return ctx

@pytest.fixture
def registration_commands(mock_bot):
    return RegistrationCommands(mock_bot)

@pytest.mark.asyncio
async def test_normalize_club_name():
    assert normalize_club_name("Clube das Chamas") == "clube das chamas"
    assert normalize_club_name("ILUSIONISTAS MENTAIS") == "ilusionistas mentais"
    assert normalize_club_name("  Clube do Fogo  ") == "clube do fogo"
    assert normalize_club_name("Clube-Das-Chamas") == "clube das chamas"

@pytest.mark.asyncio
async def test_club_selection_success(registration_commands, mock_context):
    with patch('commands.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = [
            {'name': 'Clube das Chamas', 'description': 'Clube de combate'},
            {'name': 'Ilusionistas Mentais', 'description': 'Clube de ilusões'}
        ]
        with patch('commands.registration.update_user_club', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            await registration_commands.select_club.callback(registration_commands, mock_context, "Clube das Chamas")
            mock_update.assert_called_once_with(mock_context.author.id, "Clube das Chamas")
            mock_context.send.assert_called_once_with(
                "✅ Clube selecionado com sucesso!",
                ephemeral=True
            )

@pytest.mark.asyncio
async def test_club_selection_invalid_club(registration_commands, mock_context):
    with patch('commands.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = [
            {'name': 'Clube das Chamas', 'description': 'Clube de combate'},
            {'name': 'Ilusionistas Mentais', 'description': 'Clube de ilusões'}
        ]
        await registration_commands.select_club.callback(registration_commands, mock_context, "Clube Invalido")
        mock_context.send.assert_called_once_with(
            "❌ Clube não encontrado. Use /clubes para ver a lista de clubes disponíveis.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_club_selection_database_error(registration_commands, mock_context):
    with patch('commands.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.side_effect = Exception("Database error")
        await registration_commands.select_club.callback(registration_commands, mock_context, "Clube das Chamas")
        mock_context.send.assert_called_once_with(
            "❌ Erro ao selecionar clube. Tente novamente mais tarde.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_club_selection_no_clubs(registration_commands, mock_context):
    with patch('commands.registration.get_all_clubs', new_callable=AsyncMock) as mock_get_clubs:
        mock_get_clubs.return_value = []
        await registration_commands.select_club.callback(registration_commands, mock_context, "Clube das Chamas")
        mock_context.send.assert_called_once_with(
            "❌ Não há clubes disponíveis no momento.",
            ephemeral=True
        ) 