import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from cogs.registration import RegistrationCog

@pytest.fixture
def mock_bot():
    return MagicMock()

@pytest.fixture
def mock_interaction():
    interaction = AsyncMock(spec=discord.Interaction)
    interaction.user.id = 123456789
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction

@pytest.fixture
def registration_cog(mock_bot):
    return RegistrationCog(mock_bot)

@pytest.mark.asyncio
async def test_register_already_registered(registration_cog, mock_interaction):
    """Test registration when player already exists."""
    with patch('cogs.registration.get_player') as mock_get_player:
        mock_get_player.return_value = {"name": "Test Player"}
        
        await registration_cog.slash_register(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once_with(
            f"{mock_interaction.user.mention}, você já está registrado na Academia Tokugawa!",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_register_new_player(registration_cog, mock_interaction):
    """Test registration for new player."""
    with patch('cogs.registration.get_player') as mock_get_player:
        mock_get_player.return_value = None
        
        await registration_cog.slash_register(mock_interaction)
        
        mock_interaction.response.send_message.assert_called_once_with(
            "Para iniciar o processo de registro completo, use o comando de texto `!ingressar`.\n"
            "O processo de registro interativo requer múltiplas etapas que funcionam melhor com comandos de texto.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_register_interaction_expired(registration_cog, mock_interaction):
    """Test registration when interaction expires."""
    mock_interaction.response.send_message.side_effect = discord.errors.NotFound("Interaction expired")
    
    await registration_cog.slash_register(mock_interaction)
    
    # Verify no error was raised
    assert True 