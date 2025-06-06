import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Try to import boto3, but it's not required for tests since we're mocking it
try:
    import boto3
except ImportError:
    boto3 = None

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import dynamodb

class TestDynamoDB(unittest.TestCase):
    """
    Test class for the DynamoDB implementation.
    """

    def setUp(self):
        """Set up the test environment."""
        # Create a mock for the DynamoDB table
        self.table_mock = MagicMock()
        self.dynamodb_mock = MagicMock()
        self.dynamodb_mock.Table.return_value = self.table_mock

        # Create a patch for boto3.resource
        self.boto3_resource_patch = patch('boto3.resource', return_value=self.dynamodb_mock)
        self.boto3_resource_mock = self.boto3_resource_patch.start()

        # Reset the dynamodb module to use our mocks
        dynamodb.dynamodb = self.dynamodb_mock
        dynamodb.table = self.table_mock

        # Test data
        self.test_player = {
            'user_id': 123456789,
            'name': 'Test Player',
            'power': 'Telekinesis',
            'strength_level': 3,
            'club_id': 1
        }

        self.test_club = {
            'club_id': 1,
            'name': 'Test Club',
            'description': 'A club for testing',
            'leader_id': 123456789,
            'members_count': 1,
            'reputation': 100
        }

        self.test_event = {
            'event_id': 'test_event_1',
            'name': 'Test Event',
            'description': 'An event for testing',
            'type': 'test',
            'channel_id': 987654321,
            'message_id': 123456789,
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'participants': [123456789],
            'data': {'test_key': 'test_value'},
            'completed': False
        }

    def tearDown(self):
        """Clean up after the test."""
        # Stop the patch
        self.boto3_resource_patch.stop()

    def test_init_db(self):
        """Test the init_db function."""
        # Set up the mock
        self.table_mock.table_status = 'ACTIVE'

        # Call the function
        result = dynamodb.init_db()

        # Verify the result
        self.assertTrue(result)
        self.boto3_resource_mock.assert_called_once_with('dynamodb', region_name=dynamodb.AWS_REGION)
        self.dynamodb_mock.Table.assert_called_once_with(dynamodb.TABLE_NAME)

    def test_init_db_error(self):
        """Test the init_db function with an error."""
        # Set up the mock to raise an exception
        self.table_mock.table_status = MagicMock(side_effect=Exception('Test error'))

        # Call the function
        result = dynamodb.init_db()

        # Verify the result
        self.assertFalse(result)

    def test_get_player(self):
        """Test the get_player function."""
        # Set up the mock
        self.table_mock.get_item.return_value = {'Item': {
            'PK': f'PLAYER#{self.test_player["user_id"]}',
            'SK': 'PROFILE',
            'nome': self.test_player['name'],
            'superpoder': self.test_player['power'],
            'nivel': 1,
            'clube_id': self.test_player['club_id']
        }}

        # Call the function
        result = dynamodb.get_player(self.test_player['user_id'])

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['nome'], self.test_player['name'])
        self.assertEqual(result['superpoder'], self.test_player['power'])
        self.table_mock.get_item.assert_called_once_with(
            Key={
                'PK': f'PLAYER#{self.test_player["user_id"]}',
                'SK': 'PROFILE'
            }
        )

    def test_get_player_not_found(self):
        """Test the get_player function when the player is not found."""
        # Set up the mock
        self.table_mock.get_item.return_value = {}

        # Call the function
        result = dynamodb.get_player(self.test_player['user_id'])

        # Verify the result
        self.assertIsNone(result)

    def test_create_player(self):
        """Test the create_player function."""
        # Set up the mock
        self.table_mock.put_item.return_value = {}
        self.table_mock.update_item.return_value = {}

        # Call the function
        result = dynamodb.create_player(
            self.test_player['user_id'],
            self.test_player['name'],
            self.test_player['power'],
            self.test_player['strength_level'],
            self.test_player['club_id']
        )

        # Verify the result
        self.assertTrue(result)
        # Check that put_item was called 3 times (profile, inventory, techniques)
        self.assertEqual(self.table_mock.put_item.call_count, 3)
        # Check that update_item was called once (club members)
        self.assertEqual(self.table_mock.update_item.call_count, 1)

    def test_update_player(self):
        """Test the update_player function."""
        # Set up the mock
        self.table_mock.update_item.return_value = {}

        # Call the function
        result = dynamodb.update_player(
            self.test_player['user_id'],
            nome='New Name',
            nivel=2,
            tusd=200
        )

        # Verify the result
        self.assertTrue(result)
        self.table_mock.update_item.assert_called_once()
        # Check that the update expression and values are correct
        args, kwargs = self.table_mock.update_item.call_args
        self.assertIn('UpdateExpression', kwargs)
        self.assertIn('ExpressionAttributeValues', kwargs)
        self.assertIn('nome = :nome', kwargs['UpdateExpression'])
        self.assertIn('nivel = :nivel', kwargs['UpdateExpression'])
        self.assertIn('tusd = :tusd', kwargs['UpdateExpression'])
        self.assertEqual(kwargs['ExpressionAttributeValues'][':nome'], 'New Name')
        self.assertEqual(kwargs['ExpressionAttributeValues'][':nivel'], 2)
        self.assertEqual(kwargs['ExpressionAttributeValues'][':tusd'], 200)

    def test_get_club(self):
        """Test the get_club function."""
        # Set up the mock
        self.table_mock.get_item.return_value = {'Item': {
            'PK': f'CLUBE#{self.test_club["club_id"]}',
            'SK': 'PROFILE',
            'nome': self.test_club['name'],
            'descricao': self.test_club['description'],
            'lider_id': self.test_club['leader_id'],
            'membros_count': self.test_club['members_count'],
            'reputacao': self.test_club['reputation']
        }}

        # Call the function
        result = dynamodb.get_club(self.test_club['club_id'])

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['nome'], self.test_club['name'])
        self.assertEqual(result['descricao'], self.test_club['description'])
        self.table_mock.get_item.assert_called_once_with(
            Key={
                'PK': f'CLUBE#{self.test_club["club_id"]}',
                'SK': 'PROFILE'
            }
        )

    def test_store_event(self):
        """Test the store_event function."""
        # Set up the mock
        self.table_mock.put_item.return_value = {}

        # Call the function
        result = dynamodb.store_event(
            self.test_event['event_id'],
            self.test_event['name'],
            self.test_event['description'],
            self.test_event['type'],
            self.test_event['channel_id'],
            self.test_event['message_id'],
            self.test_event['start_time'],
            self.test_event['end_time'],
            self.test_event['participants'],
            self.test_event['data'],
            self.test_event['completed']
        )

        # Verify the result
        self.assertTrue(result)
        self.table_mock.put_item.assert_called_once()
        # Check that the item is correct
        args, kwargs = self.table_mock.put_item.call_args
        self.assertIn('Item', kwargs)
        item = kwargs['Item']
        self.assertEqual(item['PK'], f'EVENTO#{self.test_event["event_id"]}')
        self.assertEqual(item['SK'], 'PROFILE')
        self.assertEqual(item['nome'], self.test_event['name'])
        self.assertEqual(item['descricao'], self.test_event['description'])
        self.assertEqual(item['tipo'], self.test_event['type'])
        self.assertEqual(item['channel_id'], self.test_event['channel_id'])
        self.assertEqual(item['message_id'], self.test_event['message_id'])
        self.assertEqual(item['start_time'], self.test_event['start_time'])
        self.assertEqual(item['end_time'], self.test_event['end_time'])
        self.assertEqual(item['participantes'], self.test_event['participants'])
        self.assertEqual(item['data'], self.test_event['data'])
        self.assertEqual(item['completed'], self.test_event['completed'])

if __name__ == '__main__':
    unittest.main()
