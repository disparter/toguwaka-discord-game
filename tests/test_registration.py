import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from src.cogs.registration import RegistrationCog

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
async def test_alterar_nome_success(registration_cog, mock_interaction):
    """Test successful name change."""
    # Mock player data
    with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
         patch('utils.persistence.db_provider.update_player') as mock_update_player:
        
        mock_get_player.return_value = {"name": "Old Name"}
        
        # Call the command
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            "New Name"
        )
        
        # Verify the update was called with correct parameters
        mock_update_player.assert_called_once_with(
            mock_interaction.user.id,
            name="New Name"
        )
        
        # Verify success message was sent
        mock_interaction.followup.send.assert_called_once_with(
            "Nome alterado com sucesso para: New Name",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_alterar_poder_success(registration_cog, mock_interaction):
    """Test successful power name change."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
         patch('utils.persistence.db_provider.update_player') as mock_update_player:
        
        mock_get_player.return_value = {"power_name": "Old Power"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_poder",
            "New Power"
        )
        
        mock_update_player.assert_called_once_with(
            mock_interaction.user.id,
            power_name="New Power"
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "Nome do poder alterado com sucesso para: New Power",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_alterar_descricao_poder_success(registration_cog, mock_interaction):
    """Test successful power description change."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
         patch('utils.persistence.db_provider.update_player') as mock_update_player:
        
        mock_get_player.return_value = {"power_description": "Old Description"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_descricao_poder",
            "New Power Description"
        )
        
        mock_update_player.assert_called_once_with(
            mock_interaction.user.id,
            power_description="New Power Description"
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "Descrição do poder alterada com sucesso para: New Power Description",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_unregistered_player(registration_cog, mock_interaction):
    """Test command usage by unregistered player."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = None
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            "New Name"
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "Você precisa estar registrado para usar este comando. Use /registrar primeiro.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_invalid_command(registration_cog, mock_interaction):
    """Test invalid command usage."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"name": "Test Player"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "invalid_command",
            "New Value"
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "Comando inválido. Use: alterar_nome, alterar_poder ou alterar_descricao_poder",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_empty_value(registration_cog, mock_interaction):
    """Test empty value validation."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"name": "Test Player"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            ""
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "O valor não pode estar vazio.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_value_too_long(registration_cog, mock_interaction):
    """Test value length validation."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"name": "Test Player"}
        
        long_value = "a" * 101  # 101 characters
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            long_value
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "O valor é muito longo. Máximo de 100 caracteres.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_name_too_short(registration_cog, mock_interaction):
    """Test minimum name length validation."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"name": "Test Player"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            "Ab"  # 2 characters
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "O nome deve ter pelo menos 3 caracteres.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_power_name_too_short(registration_cog, mock_interaction):
    """Test minimum power name length validation."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"power_name": "Test Power"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_poder",
            "Ab"  # 2 characters
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "O nome do poder deve ter pelo menos 3 caracteres.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_power_description_too_short(registration_cog, mock_interaction):
    """Test minimum power description length validation."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player:
        mock_get_player.return_value = {"power_description": "Test Description"}
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_descricao_poder",
            "Short"  # 5 characters
        )
        
        mock_interaction.followup.send.assert_called_once_with(
            "A descrição do poder deve ter pelo menos 10 caracteres.",
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_interaction_expired(registration_cog, mock_interaction):
    """Test handling of expired interaction."""
    mock_interaction.response.defer.side_effect = discord.errors.NotFound("Interaction expired")
    
    await registration_cog.registration_command(
        mock_interaction,
        "alterar_nome",
        "New Name"
    )
    
    # Verify no followup message was sent
    mock_interaction.followup.send.assert_not_called()

@pytest.mark.asyncio
async def test_database_error(registration_cog, mock_interaction):
    """Test handling of database errors."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
         patch('utils.persistence.db_provider.update_player') as mock_update_player:
        
        mock_get_player.return_value = {"name": "Test Player"}
        mock_update_player.side_effect = Exception("Database error")
        
        await registration_cog.registration_command(
            mock_interaction,
            "alterar_nome",
            "New Name"
        )
        
        # Verify error message was sent
        mock_interaction.followup.send.assert_called_once_with(
            "Ocorreu um erro ao processar o diálogo. Por favor, tente novamente.",
            ephemeral=True
        ) 