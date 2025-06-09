import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent actual log output during tests."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr('logging.getLogger', MagicMock())
        yield

@pytest.fixture(autouse=True)
def mock_aws_credentials():
    """Mock AWS credentials to prevent actual AWS calls during tests."""
    with pytest.MonkeyPatch.context() as m:
        m.setenv('AWS_ACCESS_KEY_ID', 'test-key')
        m.setenv('AWS_SECRET_ACCESS_KEY', 'test-secret')
        m.setenv('AWS_DEFAULT_REGION', 'us-east-1')
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
def mock_dynamodb():
    """Mock DynamoDB client and insert mock clubs for tests."""
    with patch('boto3.resource') as mock_resource:
        # Create a mock DynamoDB client
        mock_dynamo = MagicMock()
        mock_resource.return_value = mock_dynamo

        # Create a mock table for clubs
        mock_clubs_table = MagicMock()
        mock_dynamo.Table.return_value = mock_clubs_table

        # Mock the scan response for clubs
        mock_clubs_table.scan.return_value = {
            'Items': [
                {'NomeClube': 'Club1', 'descricao': 'Description1', 'lider_id': 'leader1', 'reputacao': 100},
                {'NomeClube': 'Club2', 'descricao': 'Description2', 'lider_id': 'leader2', 'reputacao': 200},
                {'NomeClube': 'Club3', 'descricao': 'Description3', 'lider_id': 'leader3', 'reputacao': 300}
            ]
        }

        # Mock the get_item response for a club
        mock_clubs_table.get_item.return_value = {
            'Item': {'NomeClube': 'Club1', 'descricao': 'Description1', 'lider_id': 'leader1', 'reputacao': 100}
        }

        yield mock_dynamo 