"""
Database tests for Academia Tokugawa.

This module contains tests for both DynamoDB and SQLite implementations,
ensuring data consistency and proper fallback mechanisms.
"""

import os
import pytest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from utils.db_provider import db_provider, DatabaseType
from utils.database import init_db as init_sqlite, reset_sqlite_db
from utils.dynamodb import init_db as init_dynamo

# Test data
TEST_PLAYER = {
    'user_id': '123456789',
    'name': 'Test Player',
    'power': 100,
    'level': 1,
    'exp': 0,
    'tusd': 1000,
    'club_id': 'TEST_CLUB',
    'dexterity': 10,
    'intellect': 10,
    'charisma': 10,
    'power_stat': 10,
    'reputation': 0,
    'hp': 100,
    'max_hp': 100,
    'inventory': {}
}

TEST_CLUB = {
    'club_id': 'TEST_CLUB',
    'name': 'Test Club',
    'description': 'A test club',
    'leader_id': '123456789',
    'reputation': 0
}

TEST_EVENT = {
    'event_id': 'TEST_EVENT',
    'name': 'Test Event',
    'description': 'A test event',
    'type': 'TEST',
    'channel_id': '123456789',
    'message_id': '987654321',
    'start_time': datetime.now().isoformat(),
    'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
    'completed': False,
    'participants': [],
    'data': {}
}

TEST_ITEM = {
    'item_id': 'TEST_ITEM',
    'name': 'Test Item',
    'description': 'A test item',
    'type': 'WEAPON',
    'rarity': 'COMMON',
    'price': 100,
    'effects': {
        'power': 10,
        'durability': 100
    }
}

@pytest.fixture(scope="session")
def setup_database():
    """Set up test databases."""
    # Initialize SQLite
    init_sqlite()
    
    # Initialize DynamoDB
    init_dynamo()
    
    yield
    
    # Cleanup if needed
    pass

@pytest.fixture(autouse=True, scope='function')
def clean_database():
    reset_sqlite_db()
    yield

def test_database_provider_initialization():
    """Test database provider initialization."""
    assert db_provider is not None
    assert db_provider.current_db_type is not None
    
    # Test database type switching through fallback
    original_type = db_provider.current_db_type
    success = db_provider.fallback_to_sqlite()
    assert success
    assert db_provider.current_db_type == DatabaseType.SQLITE
    
    # Try to switch back to DynamoDB
    if original_type == DatabaseType.DYNAMODB:
        success = db_provider.ensure_dynamo_available()
        assert isinstance(success, bool)

def test_dynamo_availability():
    """Test DynamoDB availability check."""
    dynamo_available = db_provider.ensure_dynamo_available()
    assert isinstance(dynamo_available, bool)
    
    # Test availability after forcing fallback
    db_provider.fallback_to_sqlite()
    assert not db_provider.ensure_dynamo_available()

def test_sqlite_fallback():
    """Test SQLite fallback mechanism."""
    # Force fallback to SQLite
    success = db_provider.fallback_to_sqlite()
    assert success
    assert db_provider.current_db_type == DatabaseType.SQLITE
    
    # Create a test player after fallback
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **{k: v for k, v in TEST_PLAYER.items() if k not in ('user_id', 'name')}
    )
    assert success
    
    # Verify player exists
    player = db_provider.get_db_implementation().get_player(TEST_PLAYER['user_id'])
    assert player is not None

def test_player_operations(setup_database):
    """Test player-related database operations."""
    # Test creating player with invalid data
    success = db_provider.get_db_implementation().create_player(None, None)
    assert not success
    
    # Test creating duplicate player
    extra_fields = {k: v for k, v in TEST_PLAYER.items() if k not in ('user_id', 'name')}
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **extra_fields
    )
    assert success
    
    # Attempt to create duplicate player
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **extra_fields
    )
    assert not success

    # Test getting non-existent player
    player = db_provider.get_db_implementation().get_player('non_existent_id')
    assert player is None

    # Get player
    player = db_provider.get_db_implementation().get_player(TEST_PLAYER['user_id'])
    assert player is not None
    assert player['name'] == TEST_PLAYER['name']
    assert player['power'] == TEST_PLAYER['power']

    # Update player
    update_data = {'power': 200, 'level': 2}
    success = db_provider.get_db_implementation().update_player(
        TEST_PLAYER['user_id'],
        **update_data
    )
    assert success

    # Verify update
    player = db_provider.get_db_implementation().get_player(TEST_PLAYER['user_id'])
    assert player['power'] == 200
    assert player['level'] == 2

    # Test updating non-existent player
    success = db_provider.get_db_implementation().update_player(
        'non_existent_id',
        power=200
    )
    assert not success

def test_club_operations(setup_database):
    """Test club-related database operations."""
    # Test creating club with invalid data
    success = db_provider.get_db_implementation().create_club(None, None, None, None)
    assert not success
    
    # Test creating duplicate club
    success = db_provider.get_db_implementation().create_club(
        TEST_CLUB['club_id'],
        TEST_CLUB['name'],
        TEST_CLUB['description'],
        TEST_CLUB['leader_id']
    )
    assert success
    
    # Attempt to create duplicate club
    success = db_provider.get_db_implementation().create_club(
        TEST_CLUB['club_id'],
        TEST_CLUB['name'],
        TEST_CLUB['description'],
        TEST_CLUB['leader_id']
    )
    assert not success

    # Test getting non-existent club
    club = db_provider.get_db_implementation().get_club('non_existent_id')
    assert club is None

    # Get club
    club = db_provider.get_db_implementation().get_club(TEST_CLUB['club_id'])
    assert club is not None
    assert club['name'] == TEST_CLUB['name']
    assert club['leader_id'] == TEST_CLUB['leader_id']

    # Update club reputation
    success = db_provider.get_db_implementation().update_club_reputation_weekly(
        TEST_CLUB['club_id'],
        100
    )
    assert success

    # Verify update
    club = db_provider.get_db_implementation().get_club(TEST_CLUB['club_id'])
    assert club['reputation'] == 100

    # Test updating non-existent club
    success = db_provider.get_db_implementation().update_club_reputation_weekly(
        'non_existent_id',
        100
    )
    assert not success

def test_event_operations(setup_database):
    """Test event-related database operations."""
    # Test storing event with invalid data
    success = db_provider.get_db_implementation().store_event(
        None, None, None, None, None, None, None, None, None, None
    )
    assert not success
    
    # Test storing duplicate event
    success = db_provider.get_db_implementation().store_event(
        TEST_EVENT['event_id'],
        TEST_EVENT['name'],
        TEST_EVENT['description'],
        TEST_EVENT['type'],
        TEST_EVENT['channel_id'],
        TEST_EVENT['message_id'],
        TEST_EVENT['start_time'],
        TEST_EVENT['end_time'],
        TEST_EVENT['participants'],
        TEST_EVENT['data']
    )
    assert success
    
    # Attempt to store duplicate event
    success = db_provider.get_db_implementation().store_event(
        TEST_EVENT['event_id'],
        TEST_EVENT['name'],
        TEST_EVENT['description'],
        TEST_EVENT['type'],
        TEST_EVENT['channel_id'],
        TEST_EVENT['message_id'],
        TEST_EVENT['start_time'],
        TEST_EVENT['end_time'],
        TEST_EVENT['participants'],
        TEST_EVENT['data']
    )
    assert not success

    # Test getting non-existent event
    event = db_provider.get_db_implementation().get_event('non_existent_id')
    assert event is None

    # Get event
    event = db_provider.get_db_implementation().get_event(TEST_EVENT['event_id'])
    assert event is not None
    assert event['name'] == TEST_EVENT['name']
    assert event['type'] == TEST_EVENT['type']

    # Update event status
    success = db_provider.get_db_implementation().update_event_status(
        TEST_EVENT['event_id'],
        True
    )
    assert success

    # Verify update
    event = db_provider.get_db_implementation().get_event(TEST_EVENT['event_id'])
    assert event['completed'] is True

    # Test updating non-existent event
    success = db_provider.get_db_implementation().update_event_status(
        'non_existent_id',
        True
    )
    assert not success

def test_item_operations(setup_database):
    """Test item-related database operations."""
    # Test creating item with invalid data
    success = db_provider.get_db_implementation().create_item(
        None, None, None, None, None, None, None
    )
    assert not success
    
    # Test creating duplicate item
    success = db_provider.get_db_implementation().create_item(
        TEST_ITEM['item_id'],
        TEST_ITEM['name'],
        TEST_ITEM['description'],
        TEST_ITEM['type'],
        TEST_ITEM['rarity'],
        TEST_ITEM['price'],
        TEST_ITEM['effects']
    )
    assert success
    
    # Attempt to create duplicate item
    success = db_provider.get_db_implementation().create_item(
        TEST_ITEM['item_id'],
        TEST_ITEM['name'],
        TEST_ITEM['description'],
        TEST_ITEM['type'],
        TEST_ITEM['rarity'],
        TEST_ITEM['price'],
        TEST_ITEM['effects']
    )
    assert not success

    # Test getting non-existent item
    item = db_provider.get_db_implementation().get_item('non_existent_id')
    assert item is None

    # Get item
    item = db_provider.get_db_implementation().get_item(TEST_ITEM['item_id'])
    assert item is not None
    assert item['name'] == TEST_ITEM['name']
    assert item['type'] == TEST_ITEM['type']

    # Update item price
    success = db_provider.get_db_implementation().update_item(
        TEST_ITEM['item_id'],
        price=200
    )
    assert success

    # Verify update
    item = db_provider.get_db_implementation().get_item(TEST_ITEM['item_id'])
    assert item['price'] == 200

    # Test updating non-existent item
    success = db_provider.get_db_implementation().update_item(
        'non_existent_id',
        price=200
    )
    assert not success

def test_inventory_operations(setup_database):
    """Test inventory-related database operations."""
    # Create test player and item first
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **{k: v for k, v in TEST_PLAYER.items() if k not in ('user_id', 'name')}
    )
    assert success
    
    success = db_provider.get_db_implementation().create_item(
        TEST_ITEM['item_id'],
        TEST_ITEM['name'],
        TEST_ITEM['description'],
        TEST_ITEM['type'],
        TEST_ITEM['rarity'],
        TEST_ITEM['price'],
        TEST_ITEM['effects']
    )
    assert success
    
    # Test adding item to non-existent player's inventory
    success = db_provider.get_db_implementation().add_item_to_inventory(
        'non_existent_id',
        TEST_ITEM['item_id'],
        1
    )
    assert not success
    
    # Test adding non-existent item to inventory
    success = db_provider.get_db_implementation().add_item_to_inventory(
        TEST_PLAYER['user_id'],
        'non_existent_item',
        1
    )
    assert not success
    
    # Add item to inventory
    success = db_provider.get_db_implementation().add_item_to_inventory(
        TEST_PLAYER['user_id'],
        TEST_ITEM['item_id'],
        1
    )
    assert success
    
    # Get inventory
    inventory = db_provider.get_db_implementation().get_player_inventory(
        TEST_PLAYER['user_id']
    )
    assert inventory is not None
    assert TEST_ITEM['item_id'] in inventory
    assert inventory[TEST_ITEM['item_id']] == 1
    
    # Update item quantity
    success = db_provider.get_db_implementation().update_inventory_item_quantity(
        TEST_PLAYER['user_id'],
        TEST_ITEM['item_id'],
        2
    )
    assert success
    
    # Verify update
    inventory = db_provider.get_db_implementation().get_player_inventory(
        TEST_PLAYER['user_id']
    )
    assert inventory[TEST_ITEM['item_id']] == 2
    
    # Test updating quantity of non-existent item
    success = db_provider.get_db_implementation().update_inventory_item_quantity(
        TEST_PLAYER['user_id'],
        'non_existent_item',
        2
    )
    assert not success

def test_market_operations(setup_database):
    """Test market-related database operations."""
    # Create test player and item first
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **{k: v for k, v in TEST_PLAYER.items() if k not in ('user_id', 'name')}
    )
    assert success
    
    success = db_provider.get_db_implementation().create_item(
        TEST_ITEM['item_id'],
        TEST_ITEM['name'],
        TEST_ITEM['description'],
        TEST_ITEM['type'],
        TEST_ITEM['rarity'],
        TEST_ITEM['price'],
        TEST_ITEM['effects']
    )
    assert success
    
    # Test creating market listing with invalid data
    success = db_provider.get_db_implementation().list_item_for_sale(
        None, None, None
    )
    assert not success
    
    # Test creating duplicate listing
    success = db_provider.get_db_implementation().list_item_for_sale(
        TEST_ITEM['item_id'],
        TEST_PLAYER['user_id'],
        100
    )
    assert success
    
    # Attempt to create duplicate listing
    success = db_provider.get_db_implementation().list_item_for_sale(
        TEST_ITEM['item_id'],
        TEST_PLAYER['user_id'],
        100
    )
    assert not success

    # Test getting non-existent listing
    listing = db_provider.get_db_implementation().get_market_listing('non_existent_id', 'non_existent_seller')
    assert listing is None

def test_data_sync(setup_database):
    """Test data synchronization between databases."""
    # Create test data in first database
    success = db_provider.get_db_implementation().create_player(
        TEST_PLAYER['user_id'],
        TEST_PLAYER['name'],
        **{k: v for k, v in TEST_PLAYER.items() if k not in ('user_id', 'name')}
    )
    assert success
    
    # Try to sync to DynamoDB
    success = db_provider.sync_to_dynamo_if_empty()
    assert isinstance(success, bool)
    
    # Verify data exists in current database
    player = db_provider.get_db_implementation().get_player(TEST_PLAYER['user_id'])
    assert player is not None
    assert player['name'] == TEST_PLAYER['name']

def test_error_handling(setup_database):
    """Test error handling in database operations."""
    # Test handling of invalid database type
    with pytest.raises(AttributeError):
        db_provider.switch_db_type("INVALID_TYPE")
    
    # Test handling of database connection errors
    # This would require mocking the database connection
    # and simulating connection failures
    
    # Test handling of transaction rollbacks
    # This would require implementing transaction support
    # and testing rollback scenarios 