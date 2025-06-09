"""
Test configuration for Academia Tokugawa.

This module contains pytest fixtures and configuration for testing.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from tests.mocks.dynamodb_mock import MockDynamoDB
from utils.dynamodb import init_db
from datetime import datetime
from utils.db_provider import db_provider, DatabaseType

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set testing environment
os.environ['IS_TESTING'] = 'true'

# Import mocks
from tests.mocks.dynamodb_mock import mock_dynamodb

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent actual log output during tests."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr('logging.getLogger', MagicMock())
        yield

@pytest.fixture(autouse=True)
def mock_aws_credentials():
    """Mock AWS credentials."""
    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'testing',
        'AWS_SECRET_ACCESS_KEY': 'testing',
        'AWS_SECURITY_TOKEN': 'testing',
        'AWS_SESSION_TOKEN': 'testing',
        'AWS_DEFAULT_REGION': 'us-east-1'
    }):
        yield

@pytest.fixture(autouse=True)
def mock_discord():
    """Mock Discord.py to prevent actual Discord API calls during tests."""
    with pytest.MonkeyPatch.context() as m:
        # Mock discord.Client
        m.setattr('discord.Client', MagicMock)
        
        # Mock discord.Interaction
        m.setattr('discord.Interaction', MagicMock)
        
        # Mock discord.app_commands
        m.setattr('discord.app_commands', MagicMock)
        
        yield 

@pytest.fixture(autouse=True)
def mock_aws():
    """Mock AWS services for all tests."""
    with patch('boto3.resource') as mock_boto3:
        mock_dynamo = MagicMock()
        mock_boto3.return_value = mock_dynamo
        yield mock_dynamo

@pytest.fixture
def mock_dynamodb(mock_aws):
    """Provide mock DynamoDB instance."""
    return mock_aws

@pytest.fixture(autouse=True)
def setup_database(mock_dynamodb):
    """Initialize database for tests."""
    init_db()
    yield
    mock_dynamodb.reset()

@pytest.fixture(autouse=True)
def reset_mock_dynamodb(mock_dynamodb):
    """Reset mock DynamoDB state before each test."""
    mock_dynamodb.reset()
    yield 

@pytest.fixture
def mock_discord():
    """Mock Discord client and context."""
    with patch('discord.ext.commands.Bot') as mock_bot:
        bot = MagicMock()
        bot.command = MagicMock()
        yield bot

@pytest.fixture
def mock_ctx():
    """Mock Discord context."""
    ctx = MagicMock()
    ctx.author.id = "123456789"
    ctx.author.name = "Test Player"
    ctx.send = MagicMock()
    return ctx

@pytest.fixture
def test_player():
    """Provide test player data."""
    return {
        "user_id": "123456789",
        "name": "Test Player",
        "level": 1,
        "xp": 0,
        "gold": 100,
        "hp": 100,
        "attributes": {
            "strength": 5,
            "agility": 5,
            "intelligence": 5
        },
        "inventory": [],
        "club": None,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def test_club():
    """Provide test club data."""
    return {
        "club_id": "TEST_CLUB",
        "name": "Test Club",
        "description": "A test club",
        "leader_id": "123456789",
        "reputation": 0,
        "members": ["123456789"],
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def test_item():
    """Provide test item data."""
    return {
        "item_id": "TEST_ITEM",
        "name": "Test Sword",
        "description": "A test sword",
        "type": "weapon",
        "rarity": "common",
        "price": 100,
        "effects": {
            "power": 10,
            "durability": 100
        }
    }

@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch.object(db_provider.get_db_implementation(), 'get_player') as mock_get_player, \
         patch.object(db_provider.get_db_implementation(), 'update_player') as mock_update_player, \
         patch.object(db_provider.get_db_implementation(), 'get_club') as mock_get_club, \
         patch.object(db_provider.get_db_implementation(), 'get_item') as mock_get_item:
        
        mock_get_player.return_value = None
        mock_update_player.return_value = True
        mock_get_club.return_value = None
        mock_get_item.return_value = None
        
        yield {
            'get_player': mock_get_player,
            'update_player': mock_update_player,
            'get_club': mock_get_club,
            'get_item': mock_get_item
        }

@pytest.fixture
def mock_story_data():
    """Mock story data for testing."""
    return {
        "1_1_arrival": {
            "type": "story",
            "title": "Arrival",
            "description": "The beginning of your journey.",
            "chapter_id": "1_1_arrival",
            "choices": [
                {"description": "Go forward", "result": "next"},
                {"description": "Look around", "result": "explore"}
            ]
        },
        "1_2_explore": {
            "type": "story",
            "title": "Exploration",
            "description": "You find something interesting.",
            "chapter_id": "1_2_explore",
            "choices": [
                {"description": "Investigate", "result": "next"},
                {"description": "Leave", "result": "return"}
            ]
        }
    } 