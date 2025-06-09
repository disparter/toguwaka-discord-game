import os
import pytest
from unittest.mock import AsyncMock, patch
from utils.dynamodb import get_all_clubs, update_player

pytestmark = pytest.mark.skip(reason='Desabilitado para evitar dependência do SQLite')

@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client for testing."""
    with patch('utils.dynamodb.get_dynamodb_client') as mock:
        mock_client = AsyncMock()
        mock_table = AsyncMock()
        mock_table.scan.return_value = {'Items': []}
        mock_table.update_item.return_value = {'Attributes': {}}
        mock_client.Table.return_value = mock_table
        mock.return_value = mock_client
        yield mock_client

@pytest.mark.skip(reason="DynamoDB tests disabled")
class TestDatabaseClubs:
    """Test suite for club database operations."""

    @pytest.mark.asyncio
    async def test_get_all_clubs_dynamodb(self, mock_dynamodb):
        """Test getting clubs from DynamoDB."""
        mock_dynamodb.Table.return_value.scan.return_value = {
            'Items': [
                {'name': 'Club A', 'description': 'Description A'},
                {'name': 'Club B', 'description': 'Description B'}
            ]
        }
        clubs = await get_all_clubs()
        assert len(clubs) == 2
        assert clubs[0]['name'] == 'Club A'
        assert clubs[1]['name'] == 'Club B'

    @pytest.mark.asyncio
    async def test_get_all_clubs_empty(self, mock_dynamodb):
        """Test getting clubs when none exist."""
        mock_dynamodb.Table.return_value.scan.return_value = {'Items': []}
        clubs = await get_all_clubs()
        assert len(clubs) == 0

    @pytest.mark.asyncio
    async def test_get_all_clubs_error(self, mock_dynamodb):
        """Test error handling when getting clubs."""
        mock_dynamodb.Table.return_value.scan.side_effect = Exception("Test error")
        with pytest.raises(Exception):
            await get_all_clubs()

    @pytest.mark.asyncio
    async def test_update_player_success(self, mock_dynamodb):
        """Test successful club update for user."""
        mock_dynamodb.Table.return_value.update_item.return_value = {
            'Attributes': {'club': 'Club A'}
        }
        result = await update_player("user123", club="Club A")
        assert result is True
        mock_dynamodb.Table.return_value.update_item.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_player_error(self, mock_dynamodb):
        """Test error handling when updating user club."""
        mock_dynamodb.Table.return_value.update_item.side_effect = Exception("Update failed")
        result = await update_player("user123", club="Club A")
        assert result is None or result is False
        mock_dynamodb.Table.return_value.update_item.assert_awaited_once() 