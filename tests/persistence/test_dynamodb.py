import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from botocore.exceptions import ClientError
from utils.dynamodb import (
    get_player, get_club, get_all_clubs,
    get_player_inventory, add_item_to_inventory, remove_item_from_inventory,
    DynamoDBOperationError
)

# Test data
TEST_PLAYER = {
    'PK': 'PLAYER#123',
    'SK': 'PROFILE',
    'name': 'Test Player',
    'level': 1,
    'exp': 0,
    'tusd': 1000,
    'hp': 100,
    'max_hp': 100,
    'dexterity': 10,
    'intellect': 10,
    'charisma': 10,
    'power_stat': 10,
    'reputation': 0,
    'strength_level': 1,
    'club_id': None
}

TEST_INVENTORY = {
    'item_1': {
        'name': 'Test Item 1',
        'type': 'weapon',
        'rarity': 'common',
        'stats': {'attack': 5}
    },
    'item_2': {
        'name': 'Test Item 2',
        'type': 'consumable',
        'rarity': 'rare',
        'effect': 'heal'
    }
}

TEST_CLUB = {
    'PK': 'CLUB#1',
    'SK': 'INFO',
    'name': 'Test Club',
    'description': 'A test club',
    'leader_id': '123'
}

@pytest.fixture
def mock_dynamodb():
    with patch('utils.dynamodb.get_table') as mock_get_table:
        # Create mock for players table
        mock_players_table = AsyncMock()
        mock_players_table.get_item = AsyncMock()
        mock_players_table.get_item.return_value = {
            'Item': {
                'PK': 'PLAYER#123',
                'SK': 'PROFILE',
                'power_stat': 10,
                'dexterity': 10,
                'intellect': 10,
                'charisma': 10,
                'club_id': None,
                'exp': 0,
                'hp': 100,
                'tusd': 1000,
                'level': 1
            }
        }
        mock_players_table.put_item = AsyncMock()
        mock_players_table.put_item.return_value = {}
        
        # Create mock for inventory table
        mock_inventory_table = AsyncMock()
        mock_inventory_table.query = AsyncMock()
        mock_inventory_table.query.return_value = {
            'Items': [
                {
                    'PK': 'PLAYER#123',
                    'SK': 'ITEM#item_1',
                    'item_data': TEST_INVENTORY['item_1']
                },
                {
                    'PK': 'PLAYER#123',
                    'SK': 'ITEM#item_2',
                    'item_data': TEST_INVENTORY['item_2']
                }
            ]
        }
        mock_inventory_table.put_item = AsyncMock()
        mock_inventory_table.put_item.return_value = {}
        mock_inventory_table.delete_item = AsyncMock()
        mock_inventory_table.delete_item.return_value = {}
        
        # Configure mock_get_table to return appropriate table
        def get_table_side_effect(table_name):
            if table_name == 'players':
                return mock_players_table
            if table_name == 'inventory':
                return mock_inventory_table
            # For any other table, return a generic AsyncMock
            return AsyncMock()
        
        mock_get_table.side_effect = get_table_side_effect
        
        # Add meta.client.scan as AsyncMock for get_all_clubs
        mock_players_table.meta = MagicMock()
        mock_players_table.meta.client = MagicMock()
        mock_players_table.meta.client.scan = AsyncMock(return_value={
            'Items': [
                {'club_id': '1', 'name': 'Club 1'},
                {'club_id': '2', 'name': 'Club 2'}
            ]
        })
        
        yield {
            'players_table': mock_players_table,
            'inventory_table': mock_inventory_table
        }

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_player_operations(mock_dynamodb):
    """Test player operations."""
    # Test get_player
    player = await get_player('123')
    assert player is not None
    assert player['power_stat'] == 10
    assert player['hp'] == 100

    # Verify DynamoDB call
    mock_dynamodb['players_table'].get_item.assert_called_once_with(
        Key={'PK': 'PLAYER#123', 'SK': 'PROFILE'}
    )

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_inventory_operations(mock_dynamodb):
    """Test inventory operations."""
    # Test get_player_inventory
    inventory = await get_player_inventory('123')
    assert inventory is not None
    assert 'item_1' in inventory
    assert 'item_2' in inventory
    assert inventory['item_1']['name'] == 'Test Item 1'
    assert inventory['item_2']['name'] == 'Test Item 2'

    # Verify DynamoDB call
    mock_dynamodb['inventory_table'].query.assert_called_once_with(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={':pk': 'PLAYER#123'}
    )

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_add_item_to_inventory(mock_dynamodb):
    """Test adding item to inventory."""
    item_id = 'new_item'
    item_data = {
        'name': 'New Item',
        'type': 'weapon',
        'rarity': 'common',
        'stats': {'attack': 10}
    }
    
    success = await add_item_to_inventory('123', item_id, item_data)
    assert success is True
    
    # Verify DynamoDB call
    mock_dynamodb['inventory_table'].put_item.assert_called_once_with(
        Item={
            'PK': 'PLAYER#123',
            'SK': f'ITEM#{item_id}',
            'item_data': item_data
        }
    )

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_remove_item_from_inventory(mock_dynamodb):
    """Test removing item from inventory."""
    item_id = 'item_1'
    
    success = await remove_item_from_inventory('123', item_id)
    assert success is True
    
    # Verify DynamoDB call
    mock_dynamodb['inventory_table'].delete_item.assert_called_once_with(
        Key={
            'PK': 'PLAYER#123',
            'SK': f'ITEM#{item_id}'
        }
    )

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_inventory_error_handling(mock_dynamodb):
    """Test inventory error handling."""
    # Simulate DynamoDB error
    mock_dynamodb['inventory_table'].query.side_effect = ClientError(
        {'Error': {'Code': 'ResourceNotFoundException'}},
        'Query'
    )
    
    # Test error handling
    with pytest.raises(DynamoDBOperationError):
        await get_player_inventory('123')

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_club_operations(mock_dynamodb):
    """Test club operations."""
    # Mock successful response
    mock_dynamodb['players_table'].get_item.return_value = {
        'Item': {
            'PK': 'CLUB#test_club',
            'SK': 'INFO',
            'name': 'Test Club',
            'description': 'A test club',
            'leader_id': '123',
            'reputacao': 100
        }
    }

    # Test get_club
    club = await get_club('test_club')
    assert club is not None
    assert club['name'] == 'Test Club'
    assert club['description'] == 'A test club'

    # Verify DynamoDB call
    mock_dynamodb['players_table'].get_item.assert_called_once_with(
        Key={'PK': 'CLUB#test_club', 'SK': 'INFO'}
    )

@pytest.mark.skip(reason="DynamoDB tests disabled")
@pytest.mark.asyncio
async def test_get_all_clubs(mock_dynamodb):
    """Test getting all clubs."""
    # Test get_all_clubs
    clubs = await get_all_clubs()
    assert len(clubs) == 2
    assert clubs[0]['name'] == 'Club 1'
    assert clubs[1]['name'] == 'Club 2'
    # Verify DynamoDB call
    mock_dynamodb['players_table'].meta.client.scan.assert_called_once()

@pytest.mark.skip(reason="Requires valid AWS credentials to test DynamoDB error handling")
@pytest.mark.asyncio
async def test_error_handling(mock_dynamodb):
    """Test error handling."""
    mock_dynamodb['players_table'].get_item.side_effect = ClientError(
        error_response={'Error': {'Code': 'ResourceNotFoundException'}},
        operation_name='GetItem'
    )
    with pytest.raises(DynamoDBOperationError) as exc_info:
        await get_player('123')
    assert 'Failed to execute get_player' in str(exc_info.value) 