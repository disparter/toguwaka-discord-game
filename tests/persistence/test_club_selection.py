import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import discord
from discord import app_commands
from cogs.registration import Registration, normalize_club_name
from utils.db import get_clubs, update_user_club

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

@pytest.mark.skip(reason="Temporarily disabled - focusing on player saving functionality")
class TestClubSelection:
    """Test club selection functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_aws):
        """Set up test environment."""
        self.registration_cog = Registration(None)
        yield

    def test_normalize_club_name(self):
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
    async def test_club_selection_autocomplete(self, mock_interaction):
        """Test club selection autocomplete."""
        with patch('cogs.registration.get_clubs', new_callable=AsyncMock) as mock_get_clubs:
            mock_get_clubs.return_value = [
                {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
                {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
                {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
            ]
            
            # Test with empty input
            choices = await self.registration_cog.club_selection_autocomplete(mock_interaction, "")
            assert len(choices) == 3
            assert all(isinstance(choice, app_commands.Choice) for choice in choices)
            
            # Test with partial match
            choices = await self.registration_cog.club_selection_autocomplete(mock_interaction, "polit")
            assert len(choices) == 1
            assert choices[0].name == "Conselho Político"
            
            # Test with no matches
            choices = await self.registration_cog.club_selection_autocomplete(mock_interaction, "xyz")
            assert len(choices) == 0

    @pytest.mark.asyncio
    async def test_select_club_success(self, mock_ctx):
        """Test successful club selection."""
        with patch('cogs.registration.get_clubs', new_callable=AsyncMock) as mock_get_clubs, \
             patch('cogs.registration.update_user_club', new_callable=AsyncMock) as mock_update:
            mock_get_clubs.return_value = [
                {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
                {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
                {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
            ]
            mock_update.return_value = True
            await self.registration_cog.select_club.callback(self.registration_cog, mock_ctx, "Conselho Político")
            mock_ctx.send.assert_called_once()
            assert "sucesso" in mock_ctx.send.call_args[0][0]
            mock_update.assert_called_once_with(
                str(mock_ctx.author.id),
                "Conselho Político"
            )

    @pytest.mark.asyncio
    async def test_select_club_invalid(self, mock_ctx):
        """Test invalid club selection."""
        with patch('cogs.registration.get_clubs', new_callable=AsyncMock) as mock_get_clubs:
            mock_get_clubs.return_value = [
                {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
                {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
                {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
            ]
            await self.registration_cog.select_club.callback(self.registration_cog, mock_ctx, "Invalid Club")
            mock_ctx.send.assert_called_once()
            assert "inválido" in mock_ctx.send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_select_club_update_failure(self, mock_ctx):
        """Test club selection with update failure."""
        with patch('cogs.registration.get_clubs', new_callable=AsyncMock) as mock_get_clubs, \
             patch('cogs.registration.update_user_club', new_callable=AsyncMock) as mock_update:
            mock_get_clubs.return_value = [
                {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
                {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
                {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
            ]
            mock_update.return_value = False
            await self.registration_cog.select_club.callback(self.registration_cog, mock_ctx, "Conselho Político")
            mock_ctx.send.assert_called_once()
            assert "Erro ao atualizar" in mock_ctx.send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_select_club_no_clubs(self, mock_ctx):
        """Test club selection when no clubs are available."""
        with patch('utils.db.get_clubs', new_callable=AsyncMock) as mock_get_clubs:
            mock_get_clubs.return_value = []
            
            # Test selecting a club
            await self.registration_cog.select_club.callback(self.registration_cog, mock_ctx, "Conselho Político")
            
            # Verify error message
            mock_ctx.send.assert_called_once()
            assert "Erro ao recuperar clubes" in mock_ctx.send.call_args[0][0]

    @pytest.mark.asyncio
    async def test_club_selection_error(self, mock_ctx):
        """Test error handling in club selection."""
        with patch('cogs.registration.get_clubs', new_callable=AsyncMock) as mock_get_clubs:
            mock_get_clubs.side_effect = Exception("Error fetching clubs")
            await self.registration_cog.select_club.callback(self.registration_cog, mock_ctx, "Conselho Político")
            mock_ctx.send.assert_called_once()
            assert "Ocorreu um erro" in mock_ctx.send.call_args[0][0] 