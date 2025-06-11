"""
Test configuration for unit tests.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
root_dir = Path(__file__).parent.parent.parent
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Mock DynamoDB tables
mock_table = MagicMock()
mock_table.put_item.return_value = True
mock_table.get_item.return_value = {
    'Item': {
        'usage_count': 2,
        'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
    }
}
mock_table.query.return_value = {'Items': []}
mock_table.scan.return_value = {'Items': [{'PK': 'PLAYER#123456789', 'SK': 'ITEM#test_item#daily'}]}
mock_table.update_item.return_value = True
mock_table.delete_item.return_value = True

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging for all tests."""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger

@pytest.fixture(autouse=True)
def mock_discord():
    """Mock Discord interactions for all tests."""
    with patch('discord.app_commands.Command') as mock_command, \
         patch('discord.app_commands.ContextMenu') as mock_context_menu, \
         patch('discord.app_commands.Group') as mock_group:
        yield {
            'command': mock_command,
            'context_menu': mock_context_menu,
            'group': mock_group
        }

@pytest.fixture(autouse=True)
def mock_db():
    """Mock database operations for all tests."""
    with patch('utils.persistence.db_provider.DBProvider') as mock_db_provider:
        mock_db = MagicMock()
        mock_db_provider.return_value = mock_db
        yield mock_db

# Clean up any cached modules that might interfere with mocking
if 'discord' in sys.modules:
    del sys.modules['discord']
if 'discord.app_commands' in sys.modules:
    del sys.modules['discord.app_commands']

@pytest.fixture
def mock_db_provider():
    """Mock do DBProvider para evitar tentativas de conexão com DynamoDB durante os testes."""
    with patch('utils.persistence.db_provider.DBProvider') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        mock_instance.ensure_dynamo_available.return_value = True
        mock_instance.initialize_tables.return_value = True
        yield mock_instance

@pytest.fixture(autouse=True)
def patch_get_table():
    mock_table = MagicMock()
    mock_table.put_item.return_value = True
    mock_table.get_item.return_value = {
        'Item': {
            'usage_count': 2,
            'expires_at': (datetime.now() + timedelta(days=1)).isoformat()
        }
    }
    mock_table.query.return_value = {'Items': []}
    mock_table.scan.return_value = {'Items': [{'PK': 'PLAYER#123456789', 'SK': 'ITEM#test_item#daily'}]}
    mock_table.update_item.return_value = True
    mock_table.delete_item.return_value = True
    with patch('utils.persistence.dynamodb.get_table', return_value=mock_table):
        yield 