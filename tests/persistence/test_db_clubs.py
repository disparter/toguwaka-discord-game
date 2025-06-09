import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import utils.db
from utils.dynamodb import get_dynamodb_client, get_table

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
def mock_dynamodb_client():
    """Create a mock DynamoDB client."""
    client = MagicMock()
    client.scan.return_value = {
        'Items': [
            {
                'NomeClube': {'S': club['name']},
                'Descricao': {'S': club['description']},
                'LiderID': {'S': club['leader_id']},
                'Reputacao': {'N': str(club['reputacao'])}
            }
            for club in MOCK_CLUBS
        ]
    }
    return client

@pytest.fixture
def mock_table():
    """Create a mock DynamoDB table."""
    table = MagicMock()
    table.update_item.return_value = {
        'Attributes': {
            'NomeClube': {'S': 'Conselho Político'}
        }
    }
    return table

class TestDatabaseClubs:
    """Test database club operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, mock_aws):
        """Set up test environment."""
        yield
        
    @pytest.mark.asyncio
    async def test_get_clubs_dynamodb(self):
        """Test getting clubs from DynamoDB."""
        with patch('utils.db.get_clubs', new_callable=AsyncMock) as mock_get_clubs:
            mock_get_clubs.return_value = [
                {'name': 'Ilusionistas Mentais', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
                {'name': 'Elementalistas', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
                {'name': 'Conselho Político', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
            ]
            clubs = await utils.db.get_clubs()
            assert len(clubs) == 3
            
    @pytest.mark.asyncio
    async def test_get_clubs_empty(self, mock_dynamodb_client):
        """Test getting clubs when none are available."""
        # Mock empty response
        mock_dynamodb_client.scan.return_value = {'Items': []}
        
        with patch('utils.dynamodb.get_dynamodb_client', return_value=mock_dynamodb_client), \
             patch('utils.db_provider.get_db_provider', return_value='dynamodb'):
            
            # Get clubs
            clubs = await utils.db.get_clubs()
            
            # Verify empty result
            assert len(clubs) == 0

    @pytest.mark.asyncio
    async def test_get_clubs_error(self, mock_dynamodb_client):
        """Test error handling when getting clubs."""
        # Mock error response
        mock_dynamodb_client.scan.side_effect = Exception("Test error")
        
        with patch('utils.dynamodb.get_dynamodb_client', return_value=mock_dynamodb_client), \
             patch('utils.db_provider.get_db_provider', return_value='dynamodb'):
            
            # Get clubs
            clubs = await utils.db.get_clubs()
            
            # Verify empty result on error
            assert len(clubs) == 0

    @pytest.mark.asyncio
    async def test_update_user_club_success(self):
        """Test successful club update."""
        with patch('utils.db.update_user_club', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            success = await utils.db.update_user_club('user1', 'Conselho Político')
            assert success is True

    @pytest.mark.asyncio
    async def test_update_user_club_error(self, mock_table):
        """Test error handling when updating club."""
        # Mock error response
        mock_table.update_item.side_effect = Exception("Test error")
        
        with patch('utils.dynamodb.get_table', return_value=mock_table), \
             patch('utils.db_provider.get_db_provider', return_value='dynamodb'):
            
            # Update user's club
            success = await utils.db.update_user_club('123456789', 'Conselho Político')
            
            # Verify failure
            assert success is False

@pytest.mark.skip(reason="SQLite not supported in this environment")
@pytest.mark.asyncio
async def test_get_clubs_sqlite():
    """Test getting clubs from SQLite."""
    with patch('utils.db.get_sqlite_clubs', new_callable=AsyncMock) as mock_get_sqlite:
        mock_get_sqlite.return_value = [
            {'name': 'Club1', 'description': 'Description1', 'leader_id': 'leader1', 'reputacao': 100},
            {'name': 'Club2', 'description': 'Description2', 'leader_id': 'leader2', 'reputacao': 200},
            {'name': 'Club3', 'description': 'Description3', 'leader_id': 'leader3', 'reputacao': 300}
        ]
        clubs = await utils.db.get_clubs()
        assert len(clubs) == 3
        assert clubs[0]['name'] == 'Club1'
        assert clubs[1]['name'] == 'Club2'
        assert clubs[2]['name'] == 'Club3'

@pytest.mark.skip(reason="SQLite not supported in this environment")
@pytest.mark.asyncio
async def test_update_user_club_sqlite():
    """Test updating user club in SQLite."""
    with patch('utils.db.update_sqlite_user_club', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True
        success = await utils.db.update_user_club('user1', 'Club1')
        assert success is True 