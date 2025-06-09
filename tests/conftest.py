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
    """Mock AWS services."""
    mock_dynamodb = MockDynamoDB()
    with patch('boto3.resource') as mock_resource, \
         patch('boto3.client') as mock_client, \
         patch('utils.dynamodb.get_table') as mock_get_table:
        
        # Configure mock resource
        mock_resource.return_value = mock_dynamodb
        
        # Configure mock client
        mock_client.return_value = MagicMock()
        
        # Configure mock get_table
        def get_table_mock(table_name):
            return mock_dynamodb.Table(table_name)
        mock_get_table.side_effect = get_table_mock
        
        yield {
            'resource': mock_resource,
            'client': mock_client,
            'get_table': mock_get_table,
            'dynamodb': mock_dynamodb
        }

@pytest.fixture
def mock_dynamodb(mock_aws):
    """Provide mock DynamoDB instance."""
    return mock_aws['dynamodb']

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