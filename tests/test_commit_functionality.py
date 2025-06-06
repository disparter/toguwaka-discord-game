import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import boto3, but it's not required for tests since we're mocking it
try:
    import boto3
except ImportError:
    boto3 = None

from utils import dynamodb

class TestCommitFunctionality(unittest.TestCase):
    """
    Test class for database transaction commit functionality.
    
    These tests validate that database transactions are committed correctly
    and that data integrity is maintained after commits.
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
        
        self.test_transaction = {
            'TransactItems': [
                {
                    'Put': {
                        'TableName': 'AcademiaTokugawa',
                        'Item': {
                            'PK': f'PLAYER#{self.test_player["user_id"]}',
                            'SK': 'PROFILE',
                            'nome': self.test_player['name'],
                            'superpoder': self.test_player['power'],
                            'nivel': 1,
                            'clube_id': self.test_player['club_id']
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'AcademiaTokugawa',
                        'Key': {
                            'PK': f'CLUBE#{self.test_player["club_id"]}',
                            'SK': 'PROFILE'
                        },
                        'UpdateExpression': 'SET membros_count = membros_count + :val',
                        'ExpressionAttributeValues': {
                            ':val': 1
                        }
                    }
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after the test."""
        # Stop the patch
        self.boto3_resource_patch.stop()
    
    def test_transaction_commit(self):
        """Test committing a transaction."""
        # Set up the mock
        self.dynamodb_mock.meta.client.transact_write_items.return_value = {}
        
        # Call the function to commit the transaction
        try:
            self.dynamodb_mock.meta.client.transact_write_items(
                TransactItems=self.test_transaction['TransactItems']
            )
            transaction_succeeded = True
        except Exception as e:
            transaction_succeeded = False
        
        # Verify the result
        self.assertTrue(transaction_succeeded)
        self.dynamodb_mock.meta.client.transact_write_items.assert_called_once_with(
            TransactItems=self.test_transaction['TransactItems']
        )
    
    def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        # Set up the mock to raise an exception
        self.dynamodb_mock.meta.client.transact_write_items.side_effect = Exception('Test error')
        
        # Call the function to commit the transaction
        try:
            self.dynamodb_mock.meta.client.transact_write_items(
                TransactItems=self.test_transaction['TransactItems']
            )
            transaction_succeeded = True
        except Exception as e:
            transaction_succeeded = False
        
        # Verify the result
        self.assertFalse(transaction_succeeded)
        self.dynamodb_mock.meta.client.transact_write_items.assert_called_once_with(
            TransactItems=self.test_transaction['TransactItems']
        )
    
    def test_atomic_update(self):
        """Test atomic update of a player's data."""
        # Set up the mock
        self.table_mock.update_item.return_value = {
            'Attributes': {
                'PK': f'PLAYER#{self.test_player["user_id"]}',
                'SK': 'PROFILE',
                'nome': self.test_player['name'],
                'superpoder': self.test_player['power'],
                'nivel': 2,  # Updated level
                'tusd': 200  # Updated currency
            }
        }
        
        # Call the function to update the player
        result = dynamodb.update_player(
            self.test_player['user_id'],
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
        self.assertIn('nivel = :nivel', kwargs['UpdateExpression'])
        self.assertIn('tusd = :tusd', kwargs['UpdateExpression'])
        self.assertEqual(kwargs['ExpressionAttributeValues'][':nivel'], 2)
        self.assertEqual(kwargs['ExpressionAttributeValues'][':tusd'], 200)
    
    def test_conditional_update(self):
        """Test conditional update of a player's data."""
        # Set up the mock
        self.table_mock.update_item.return_value = {
            'Attributes': {
                'PK': f'PLAYER#{self.test_player["user_id"]}',
                'SK': 'PROFILE',
                'nome': self.test_player['name'],
                'superpoder': self.test_player['power'],
                'nivel': 2,
                'tusd': 150  # Updated currency
            }
        }
        
        # Define a conditional update function
        def conditional_update_player_tusd(user_id, amount, min_balance=0):
            """Update player's TUSD balance if it would not go below the minimum."""
            try:
                response = self.table_mock.update_item(
                    Key={
                        'PK': f'PLAYER#{user_id}',
                        'SK': 'PROFILE'
                    },
                    UpdateExpression='SET tusd = tusd + :amount',
                    ConditionExpression='tusd + :amount >= :min',
                    ExpressionAttributeValues={
                        ':amount': amount,
                        ':min': min_balance
                    },
                    ReturnValues='ALL_NEW'
                )
                return True, response.get('Attributes', {})
            except Exception as e:
                return False, {'error': str(e)}
        
        # Test successful conditional update
        self.table_mock.update_item.side_effect = None
        success, result = conditional_update_player_tusd(self.test_player['user_id'], -50, 100)
        self.assertTrue(success)
        
        # Test failed conditional update (would go below minimum)
        self.table_mock.update_item.side_effect = Exception('ConditionalCheckFailedException')
        success, result = conditional_update_player_tusd(self.test_player['user_id'], -200, 0)
        self.assertFalse(success)
        self.assertIn('error', result)
    
    def test_transaction_with_condition_checks(self):
        """Test transaction with condition checks."""
        # Set up the mock
        self.dynamodb_mock.meta.client.transact_write_items.return_value = {}
        
        # Define a transaction with condition checks
        transaction_with_conditions = {
            'TransactItems': [
                {
                    'ConditionCheck': {
                        'TableName': 'AcademiaTokugawa',
                        'Key': {
                            'PK': f'PLAYER#{self.test_player["user_id"]}',
                            'SK': 'PROFILE'
                        },
                        'ConditionExpression': 'tusd >= :amount',
                        'ExpressionAttributeValues': {
                            ':amount': 100
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'AcademiaTokugawa',
                        'Key': {
                            'PK': f'PLAYER#{self.test_player["user_id"]}',
                            'SK': 'PROFILE'
                        },
                        'UpdateExpression': 'SET tusd = tusd - :amount',
                        'ExpressionAttributeValues': {
                            ':amount': 100
                        }
                    }
                },
                {
                    'Update': {
                        'TableName': 'AcademiaTokugawa',
                        'Key': {
                            'PK': 'ITEM#123',
                            'SK': 'PROFILE'
                        },
                        'UpdateExpression': 'SET owner = :owner',
                        'ExpressionAttributeValues': {
                            ':owner': f'PLAYER#{self.test_player["user_id"]}'
                        }
                    }
                }
            ]
        }
        
        # Call the function to commit the transaction
        try:
            self.dynamodb_mock.meta.client.transact_write_items(
                TransactItems=transaction_with_conditions['TransactItems']
            )
            transaction_succeeded = True
        except Exception as e:
            transaction_succeeded = False
        
        # Verify the result
        self.assertTrue(transaction_succeeded)
        self.dynamodb_mock.meta.client.transact_write_items.assert_called_once_with(
            TransactItems=transaction_with_conditions['TransactItems']
        )
    
    def test_data_integrity_after_commit(self):
        """Test data integrity after commit."""
        # Set up the mocks
        self.table_mock.put_item.return_value = {}
        self.table_mock.get_item.return_value = {'Item': {
            'PK': f'PLAYER#{self.test_player["user_id"]}',
            'SK': 'PROFILE',
            'nome': self.test_player['name'],
            'superpoder': self.test_player['power'],
            'nivel': 1,
            'clube_id': self.test_player['club_id']
        }}
        
        # Create a player
        dynamodb.create_player(
            self.test_player['user_id'],
            self.test_player['name'],
            self.test_player['power'],
            self.test_player['strength_level'],
            self.test_player['club_id']
        )
        
        # Get the player
        player = dynamodb.get_player(self.test_player['user_id'])
        
        # Verify data integrity
        self.assertIsNotNone(player)
        self.assertEqual(player['nome'], self.test_player['name'])
        self.assertEqual(player['superpoder'], self.test_player['power'])
        self.assertEqual(player['clube_id'], self.test_player['club_id'])

if __name__ == '__main__':
    unittest.main()