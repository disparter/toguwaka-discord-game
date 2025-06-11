import pytest
from unittest.mock import patch, MagicMock
import discord
from cogs.registration import RegistrationCog

@pytest.fixture
def registration_cog(mock_bot):
    return RegistrationCog(mock_bot)

class TestAlterarRegistro:
    @pytest.mark.asyncio
    async def test_alterar_registro_unregistered(self, registration_cog, mock_interaction):
        """Test alterar_registro when player is not registered."""
        with patch('cogs.registration.get_player') as mock_get_player:
            mock_get_player.return_value = None
            
            await registration_cog.alterar_registro(mock_interaction)
            
            mock_interaction.followup.send.assert_called_once_with(
                "Você precisa estar registrado para usar este comando. Use /registrar primeiro.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_alterar_registro_success(self, registration_cog, mock_interaction):
        """Test successful alterar_registro command."""
        with patch('cogs.registration.get_player') as mock_get_player:
            mock_get_player.return_value = {"name": "Test Player"}
            
            await registration_cog.alterar_registro(mock_interaction)
            
            # Verify the view was created with correct buttons
            mock_interaction.followup.send.assert_called_once()
            call_args = mock_interaction.followup.send.call_args
            assert "Selecione o que você deseja alterar:" in call_args[0][0]
            assert isinstance(call_args[1]['view'], discord.ui.View)
            assert len(call_args[1]['view'].children) == 2
            assert call_args[1]['view'].children[0].label == "Alterar Nome"
            assert call_args[1]['view'].children[1].label == "Alterar Poder"

    @pytest.mark.asyncio
    async def test_alterar_nome_modal(self, registration_cog, mock_interaction):
        """Test alterar_nome modal interaction."""
        # Mock the interaction data
        mock_interaction.type = discord.InteractionType.component
        mock_interaction.data = {"custom_id": "alterar_nome"}
        
        # Mock the modal response
        mock_modal_response = MagicMock()
        mock_modal_response.data = {
            "components": [{
                "components": [{
                    "value": "New Name"
                }]
            }]
        }
        
        with patch('cogs.registration.get_player') as mock_get_player, \
             patch('cogs.registration.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"name": "Old Name"}
            
            # Call the interaction handler
            await registration_cog.on_interaction(mock_interaction)
            
            # Verify modal was sent
            mock_interaction.response.send_modal.assert_called_once()
            
            # Simulate modal submission
            modal = mock_interaction.response.send_modal.call_args[0][0]
            await modal.callback(mock_modal_response)
            
            # Verify update was called
            mock_update_player.assert_called_once_with(
                mock_interaction.user.id,
                name="New Name"
            )
            
            # Verify success message
            mock_modal_response.response.send_message.assert_called_once_with(
                "Nome alterado com sucesso para: New Name",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_alterar_poder_modal(self, registration_cog, mock_interaction):
        """Test alterar_poder modal interaction."""
        # Mock the interaction data
        mock_interaction.type = discord.InteractionType.component
        mock_interaction.data = {"custom_id": "alterar_poder"}
        
        # Mock the modal response
        mock_modal_response = MagicMock()
        mock_modal_response.data = {
            "components": [{
                "components": [{
                    "value": "New Power"
                }]
            }]
        }
        
        with patch('cogs.registration.get_player') as mock_get_player, \
             patch('cogs.registration.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"power": "Old Power"}
            
            # Call the interaction handler
            await registration_cog.on_interaction(mock_interaction)
            
            # Verify modal was sent
            mock_interaction.response.send_modal.assert_called_once()
            
            # Simulate modal submission
            modal = mock_interaction.response.send_modal.call_args[0][0]
            await modal.callback(mock_modal_response)
            
            # Verify update was called
            mock_update_player.assert_called_once_with(
                mock_interaction.user.id,
                power="New Power"
            )
            
            # Verify success message
            mock_modal_response.response.send_message.assert_called_once_with(
                "Nome do poder alterado com sucesso para: New Power",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_alterar_nome_validation(self, registration_cog, mock_interaction):
        """Test alterar_nome validation rules."""
        # Mock the interaction data
        mock_interaction.type = discord.InteractionType.component
        mock_interaction.data = {"custom_id": "alterar_nome"}
        
        # Test cases for validation
        test_cases = [
            ("", "O nome não pode estar vazio."),
            ("Ab", "O nome deve ter pelo menos 3 caracteres."),
            ("a" * 101, "O nome é muito longo. Máximo de 100 caracteres.")
        ]
        
        for input_value, expected_message in test_cases:
            # Mock the modal response
            mock_modal_response = MagicMock()
            mock_modal_response.data = {
                "components": [{
                    "components": [{
                        "value": input_value
                    }]
                }]
            }
            
            with patch('cogs.registration.get_player') as mock_get_player:
                mock_get_player.return_value = {"name": "Old Name"}
                
                # Call the interaction handler
                await registration_cog.on_interaction(mock_interaction)
                
                # Simulate modal submission
                modal = mock_interaction.response.send_modal.call_args[0][0]
                await modal.callback(mock_modal_response)
                
                # Verify validation message
                mock_modal_response.response.send_message.assert_called_once_with(
                    expected_message,
                    ephemeral=True
                )
                
                # Reset mocks for next test case
                mock_modal_response.reset_mock()
                mock_interaction.reset_mock()

    @pytest.mark.asyncio
    async def test_alterar_poder_validation(self, registration_cog, mock_interaction):
        """Test alterar_poder validation rules."""
        # Mock the interaction data
        mock_interaction.type = discord.InteractionType.component
        mock_interaction.data = {"custom_id": "alterar_poder"}
        
        # Test cases for validation
        test_cases = [
            ("", "O nome do poder não pode estar vazio."),
            ("Ab", "O nome do poder deve ter pelo menos 3 caracteres."),
            ("a" * 101, "O nome do poder é muito longo. Máximo de 100 caracteres."),
            ("Power 123", "O nome do poder não pode conter números.")
        ]
        
        for input_value, expected_message in test_cases:
            # Mock the modal response
            mock_modal_response = MagicMock()
            mock_modal_response.data = {
                "components": [{
                    "components": [{
                        "value": input_value
                    }]
                }]
            }
            
            with patch('cogs.registration.get_player') as mock_get_player:
                mock_get_player.return_value = {"power": "Old Power"}
                
                # Call the interaction handler
                await registration_cog.on_interaction(mock_interaction)
                
                # Simulate modal submission
                modal = mock_interaction.response.send_modal.call_args[0][0]
                await modal.callback(mock_modal_response)
                
                # Verify validation message
                mock_modal_response.response.send_message.assert_called_once_with(
                    expected_message,
                    ephemeral=True
                )
                
                # Reset mocks for next test case
                mock_modal_response.reset_mock()
                mock_interaction.reset_mock()

    @pytest.mark.asyncio
    async def test_alterar_nome_success(self, registration_cog, mock_interaction):
        """Test successful name change."""
        # Mock player data
        with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
             patch('utils.persistence.db_provider.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"name": "Old Name"}
            
            # Call the command
            await registration_cog.alterar_nome(
                mock_interaction,
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
    async def test_alterar_poder_success(self, registration_cog, mock_interaction):
        """Test successful power name change."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
             patch('utils.persistence.db_provider.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"power": "Old Power"}
            
            await registration_cog.alterar_poder(
                mock_interaction,
                "New Power"
            )
            
            mock_update_player.assert_called_once_with(
                mock_interaction.user.id,
                power="New Power"
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "Nome do poder alterado com sucesso para: New Power",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_unregistered_player_nome(self, registration_cog, mock_interaction):
        """Test name change by unregistered player."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = None
            
            await registration_cog.alterar_nome(
                mock_interaction,
                "New Name"
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "Você precisa estar registrado para usar este comando. Use /registrar primeiro.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_unregistered_player_poder(self, registration_cog, mock_interaction):
        """Test power change by unregistered player."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = None
            
            await registration_cog.alterar_poder(
                mock_interaction,
                "New Power"
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "Você precisa estar registrado para usar este comando. Use /registrar primeiro.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_empty_nome(self, registration_cog, mock_interaction):
        """Test empty name validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"name": "Test Player"}
            
            await registration_cog.alterar_nome(
                mock_interaction,
                ""
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome não pode estar vazio.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_empty_poder(self, registration_cog, mock_interaction):
        """Test empty power validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"power": "Test Power"}
            
            await registration_cog.alterar_poder(
                mock_interaction,
                ""
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome do poder não pode estar vazio.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_nome_too_long(self, registration_cog, mock_interaction):
        """Test name length validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"name": "Test Player"}
            
            long_value = "a" * 101  # 101 characters
            
            await registration_cog.alterar_nome(
                mock_interaction,
                long_value
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome é muito longo. Máximo de 100 caracteres.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_poder_too_long(self, registration_cog, mock_interaction):
        """Test power name length validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"power": "Test Power"}
            
            long_value = "a" * 101  # 101 characters
            
            await registration_cog.alterar_poder(
                mock_interaction,
                long_value
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome do poder é muito longo. Máximo de 100 caracteres.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_nome_too_short(self, registration_cog, mock_interaction):
        """Test minimum name length validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"name": "Test Player"}
            
            await registration_cog.alterar_nome(
                mock_interaction,
                "Ab"  # 2 characters
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome deve ter pelo menos 3 caracteres.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_poder_too_short(self, registration_cog, mock_interaction):
        """Test minimum power name length validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"power": "Test Power"}
            
            await registration_cog.alterar_poder(
                mock_interaction,
                "Ab"  # 2 characters
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome do poder deve ter pelo menos 3 caracteres.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_poder_with_numbers(self, registration_cog, mock_interaction):
        """Test power name with numbers validation."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player:
            mock_get_player.return_value = {"power": "Test Power"}
            
            await registration_cog.alterar_poder(
                mock_interaction,
                "Power 123"  # Contains numbers
            )
            
            mock_interaction.followup.send.assert_called_once_with(
                "O nome do poder não pode conter números.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_interaction_expired_nome(self, registration_cog, mock_interaction):
        """Test handling of expired interaction for name change."""
        mock_interaction.response.defer.side_effect = discord.errors.NotFound("Interaction expired")
        
        await registration_cog.alterar_nome(
            mock_interaction,
            "New Name"
        )
        
        # Verify no followup message was sent
        mock_interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_interaction_expired_poder(self, registration_cog, mock_interaction):
        """Test handling of expired interaction for power change."""
        mock_interaction.response.defer.side_effect = discord.errors.NotFound("Interaction expired")
        
        await registration_cog.alterar_poder(
            mock_interaction,
            "New Power"
        )
        
        # Verify no followup message was sent
        mock_interaction.followup.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_error_nome(self, registration_cog, mock_interaction):
        """Test handling of database errors for name change."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
             patch('utils.persistence.db_provider.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"name": "Test Player"}
            mock_update_player.side_effect = Exception("Database error")
            
            await registration_cog.alterar_nome(
                mock_interaction,
                "New Name"
            )
            
            # Verify error message was sent
            mock_interaction.followup.send.assert_called_once_with(
                "Ocorreu um erro ao processar o diálogo. Por favor, tente novamente.",
                ephemeral=True
            )

    @pytest.mark.asyncio
    async def test_database_error_poder(self, registration_cog, mock_interaction):
        """Test handling of database errors for power change."""
        with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
             patch('utils.persistence.db_provider.update_player') as mock_update_player:
            
            mock_get_player.return_value = {"power": "Test Power"}
            mock_update_player.side_effect = Exception("Database error")
            
            await registration_cog.alterar_poder(
                mock_interaction,
                "New Power"
            )
            
            # Verify error message was sent
            mock_interaction.followup.send.assert_called_once_with(
                "Ocorreu um erro ao processar o diálogo. Por favor, tente novamente.",
                ephemeral=True
            ) 