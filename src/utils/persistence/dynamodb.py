"""
DynamoDB implementation for Academia Tokugawa.

This module provides DynamoDB-specific implementations of database operations
using multiple tables for better organization and performance.
"""

import boto3
import json
import os
import logging
from datetime import datetime, time
import decimal
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from typing import Dict, Any, Optional, List

logger = logging.getLogger('tokugawa_bot')

# DynamoDB table names
TABLES = {
    'main': os.environ.get('DYNAMODB_TABLE', 'AcademiaTokugawa'),
    'clubs': os.environ.get('DYNAMODB_CLUBS_TABLE', 'Clubes'),
    'events': os.environ.get('DYNAMODB_EVENTS_TABLE', 'Eventos'),
    'inventory': os.environ.get('DYNAMODB_INVENTORY_TABLE', 'Inventario'),
    'players': os.environ.get('DYNAMODB_PLAYERS_TABLE', 'Jogadores'),
    'market': os.environ.get('DYNAMODB_MARKET_TABLE', 'Mercado'),
    'items': os.environ.get('DYNAMODB_ITEMS_TABLE', 'Itens'),
    'club_activities': os.environ.get('DYNAMODB_CLUB_ACTIVITIES_TABLE', 'ClubActivities'),
    'grades': os.environ.get('DYNAMODB_GRADES_TABLE', 'Notas'),
    'votes': os.environ.get('DYNAMODB_VOTES_TABLE', 'Votos'),
    'quiz_questions': os.environ.get('DYNAMODB_QUIZ_QUESTIONS_TABLE', 'QuizQuestions'),
    'quiz_answers': os.environ.get('DYNAMODB_QUIZ_ANSWERS_TABLE', 'QuizAnswers')
}

# AWS region
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Flag to indicate if we should reset the database
RESET_DATABASE = os.environ.get('RESET_DATABASE', 'false').lower() == 'true'

class DynamoDBError(Exception):
    """Base exception for DynamoDB errors."""
    pass

class DynamoDBConnectionError(DynamoDBError):
    """Exception raised when there are connection issues with DynamoDB."""
    pass

class DynamoDBOperationError(DynamoDBError):
    """Exception raised when there are issues with DynamoDB operations."""
    pass

# Helper class to convert Decimal to float/int for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o) if o % 1 else int(o)
        return super(DecimalEncoder, self).default(o)

def get_dynamodb_client():
    """Get a DynamoDB client with proper error handling."""
    try:
        # Create a session with the default credential provider chain
        session = boto3.Session(region_name=AWS_REGION)
        logger.info(f"Created AWS session for region {AWS_REGION}")
        
        # Create DynamoDB client from the session
        dynamodb = session.resource('dynamodb')
        logger.info("Successfully created DynamoDB client")
        
        return dynamodb
    except (NoCredentialsError, EndpointConnectionError) as e:
        error_msg = f"Failed to create DynamoDB client: {str(e)}"
        logger.error(error_msg)
        raise DynamoDBConnectionError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error creating DynamoDB client: {str(e)}"
        logger.error(error_msg)
        raise DynamoDBConnectionError(error_msg) from e

def get_table(table_name):
    """Get a DynamoDB table by name."""
    try:
        logger.info(f"Attempting to get table: {table_name}")
        dynamodb = get_dynamodb_client()
        table = dynamodb.Table(table_name)
        
        # Test table access by getting table description
        try:
            table.meta.client.describe_table(TableName=table_name)
            logger.info(f"Successfully accessed table {table_name}")
        except Exception as e:
            logger.error(f"Error accessing table {table_name}: {e}")
            raise
            
        return table
    except Exception as e:
        logger.error(f"Error getting table {table_name}: {e}")
        raise DynamoDBConnectionError(f"Failed to get table {table_name}") from e

def init_db() -> bool:
    """Initialize DynamoDB tables."""
    try:
        dynamodb = get_dynamodb_client()
        
        # Check if tables exist
        tables = dynamodb.meta.client.list_tables()['TableNames']
        
        # If tables don't exist, create them
        if 'Jogadores' not in tables:
            logger.info("Creating Jogadores table...")
            dynamodb.create_table(
                TableName='Jogadores',
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
        
        if 'Clubes' not in tables:
            logger.info("Creating Clubes table...")
            dynamodb.create_table(
                TableName='Clubes',
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
        
        if 'Inventario' not in tables:
            logger.info("Creating Inventario table...")
            dynamodb.create_table(
                TableName='Inventario',
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'},
                    {'AttributeName': 'item_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
        
        logger.info("DynamoDB tables initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing DynamoDB tables: {str(e)}")
        return False

def create_table(dynamodb, table_name):
    """Create a DynamoDB table."""
    try:
        if table_name == TABLES['players']:
            table = dynamodb.create_table(
                TableName=TABLES['players'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'PlayerNameIndex',
                        'KeySchema': [
                            {'AttributeName': 'name', 'KeyType': 'HASH'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['clubs']:
            table = dynamodb.create_table(
                TableName=TABLES['clubs'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'},
                    {'AttributeName': 'name', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'name', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'ClubNameIndex',
                        'KeySchema': [
                            {'AttributeName': 'name', 'KeyType': 'HASH'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['events']:
            table = dynamodb.create_table(
                TableName=TABLES['events'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'},
                    {'AttributeName': 'type', 'KeyType': 'HASH'},
                    {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'type', 'AttributeType': 'S'},
                    {'AttributeName': 'start_time', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'EventTypeIndex',
                        'KeySchema': [
                            {'AttributeName': 'type', 'KeyType': 'HASH'},
                            {'AttributeName': 'start_time', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {
                            'ProjectionType': 'ALL'
                        }
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['inventory']:
            table = dynamodb.create_table(
                TableName=TABLES['inventory'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['market']:
            table = dynamodb.create_table(
                TableName=TABLES['market'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['items']:
            table = dynamodb.create_table(
                TableName=TABLES['items'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['club_activities']:
            table = dynamodb.create_table(
                TableName=TABLES['club_activities'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['grades']:
            table = dynamodb.create_table(
                TableName=TABLES['grades'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['votes']:
            table = dynamodb.create_table(
                TableName=TABLES['votes'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['quiz_questions']:
            table = dynamodb.create_table(
                TableName=TABLES['quiz_questions'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['quiz_answers']:
            table = dynamodb.create_table(
                TableName=TABLES['quiz_answers'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['main']:
            table = dynamodb.create_table(
                TableName=TABLES['main'],
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        else:
            raise DynamoDBOperationError(f"Unknown table name: {table_name}")
            
        return table
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to create table: {e}")

def handle_dynamo_error(func):
    """Decorator to handle DynamoDB errors."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientError as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise DynamoDBOperationError(f"Failed to execute {func.__name__}: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise DynamoDBOperationError(f"Unexpected error in {func.__name__}: {e}") from e
    return wrapper

@handle_dynamo_error
async def get_event(event_id):
    """Get event data from DynamoDB."""
    try:
        table = get_table(TABLES['events'])
        response = await table.get_item(
            Key={
                'EventoID': event_id,
                'Tipo': 'EVENT'
            }
        )

        if 'Item' in response:
            event = response['Item']
            return json.loads(json.dumps(event, cls=DecimalEncoder))
        return None
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get event: {e}")

@handle_dynamo_error
async def store_event(event_id, name, description, event_type, channel_id, message_id, start_time, end_time, participants=None, data=None):
    """Store an event in DynamoDB."""
    try:
        table = get_table(TABLES['events'])
        await table.put_item(
            Item={
                'EventoID': event_id,
                'Tipo': 'EVENT',
                'nome': name,
                'descricao': description,
                'tipo': event_type,
                'channel_id': channel_id,
                'message_id': message_id,
                'start_time': start_time,
                'end_time': end_time,
                'completed': False,
                'participantes': json.dumps(participants or []),
                'data': json.dumps(data or {}),
                'created_at': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error storing event {event_id}: {e}")
        raise DynamoDBOperationError(f"Failed to store event: {e}")

@handle_dynamo_error
async def get_player_inventory(user_id):
    """Get player's inventory from DynamoDB."""
    try:
        table = get_table(TABLES['inventory'])
        response = await table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'PLAYER#{user_id}'
            }
        )
        
        # Convert items to inventory format
        inventory = {}
        for item in response.get('Items', []):
            item_id = item['SK'].replace('ITEM#', '')
            inventory[item_id] = item['item_data']
        
        return inventory
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get inventory: {e}")

@handle_dynamo_error
async def add_item_to_inventory(user_id, item_id, item_data):
    """Add item to player's inventory."""
    try:
        table = get_table(TABLES['inventory'])
        await table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}',
                'item_data': item_data
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error adding item to inventory for player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to add item to inventory: {e}")

@handle_dynamo_error
async def remove_item_from_inventory(user_id, item_id):
    """Remove item from player's inventory."""
    try:
        table = get_table(TABLES['inventory'])
        await table.delete_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': f'ITEM#{item_id}'
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to remove item from inventory: {e}")

@handle_dynamo_error
async def get_market_listing(item_id, seller_id):
    """Get a market listing from DynamoDB."""
    try:
        table = get_table(TABLES['market'])
        response = await table.get_item(
            Key={
                'ItemID': item_id,
                'VendedorID': seller_id
            }
        )

        if 'Item' in response:
            listing = response['Item']
            return json.loads(json.dumps(listing, cls=DecimalEncoder))
        return None
    except Exception as e:
        logger.error(f"Error getting market listing for item {item_id} by seller {seller_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get market listing: {e}")

@handle_dynamo_error
async def list_item_for_sale(item_id, seller_id, price):
    """List an item for sale in DynamoDB."""
    try:
        table = get_table(TABLES['market'])
        await table.put_item(
            Item={
                'ItemID': item_id,
                'VendedorID': seller_id,
                'preco': price,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error listing item {item_id} by seller {seller_id}: {e}")
        raise DynamoDBOperationError(f"Failed to list item for sale: {e}")

@handle_dynamo_error
async def get_system_flag(flag_name):
    """Get a system flag from DynamoDB."""
    try:
        table = get_table(TABLES['main'])
        response = await table.get_item(
            Key={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}'
            }
        )
        if 'Item' in response:
            return response['Item'].get('value')
        return None
    except Exception as e:
        logger.error(f"Error getting system flag {flag_name}: {e}")
        raise DynamoDBOperationError(f"Failed to get system flag: {e}")

@handle_dynamo_error
async def get_quiz_questions():
    """Get all quiz questions from DynamoDB."""
    try:
        table = get_table('quiz_questions')
        response = await table.scan()
        questions = response.get('Items', [])
        return [dict(q) for q in questions]
    except Exception as e:
        logger.error(f"Error getting quiz questions: {e}")
        return []

@handle_dynamo_error
async def record_quiz_answer(user_id, question_id, is_correct):
    """Record a quiz answer for a user in DynamoDB."""
    try:
        table = get_table('quiz_answers')
        item = {
            'user_id': user_id,
            'question_id': question_id,
            'is_correct': bool(is_correct),
            'created_at': datetime.now().isoformat()
        }
        await table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error recording quiz answer: {e}")
        return False

@handle_dynamo_error
async def put_item(table_name, item):
    """
    Put an item into a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to put the item into
        item (dict): The item to put into the table
        
    Returns:
        dict: The response from DynamoDB
    """
    try:
        table = get_table(table_name)
        response = table.put_item(Item=item)
        logger.info(f"Successfully put item into table {table_name}")
        return response
    except Exception as e:
        logger.error(f"Error putting item into table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to put item into table {table_name}") from e

@handle_dynamo_error
async def get_item(table_name, key):
    """
    Get an item from a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to get the item from
        key (dict): The key of the item to get
        
    Returns:
        dict: The item from DynamoDB, or None if not found
    """
    try:
        table = get_table(table_name)
        response = table.get_item(Key=key)
        item = response.get('Item')
        if item:
            logger.info(f"Successfully retrieved item from table {table_name}")
        else:
            logger.info(f"No item found in table {table_name} with key {key}")
        return item
    except Exception as e:
        logger.error(f"Error getting item from table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to get item from table {table_name}") from e

@handle_dynamo_error
async def query_items(table_name, key_condition_expression, expression_attribute_values=None, filter_expression=None):
    """
    Query items from a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to query
        key_condition_expression (str): The key condition expression for the query
        expression_attribute_values (dict, optional): The expression attribute values
        filter_expression (str, optional): The filter expression for the query
        
    Returns:
        list: The items from DynamoDB matching the query
    """
    try:
        table = get_table(table_name)
        query_params = {
            'KeyConditionExpression': key_condition_expression
        }
        
        if expression_attribute_values:
            query_params['ExpressionAttributeValues'] = expression_attribute_values
            
        if filter_expression:
            query_params['FilterExpression'] = filter_expression
            
        response = table.query(**query_params)
        items = response.get('Items', [])
        
        logger.info(f"Successfully queried {len(items)} items from table {table_name}")
        return items
    except Exception as e:
        logger.error(f"Error querying items from table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to query items from table {table_name}") from e

@handle_dynamo_error
async def scan_items(table_name, filter_expression=None, expression_attribute_values=None):
    """
    Scan items from a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to scan
        filter_expression (str, optional): The filter expression for the scan
        expression_attribute_values (dict, optional): The expression attribute values
        
    Returns:
        list: The items from DynamoDB matching the scan criteria
    """
    try:
        table = get_table(table_name)
        scan_params = {}
        
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
            
        if expression_attribute_values:
            scan_params['ExpressionAttributeValues'] = expression_attribute_values
            
        response = table.scan(**scan_params)
        items = response.get('Items', [])
        
        logger.info(f"Successfully scanned {len(items)} items from table {table_name}")
        return items
    except Exception as e:
        logger.error(f"Error scanning items from table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to scan items from table {table_name}") from e

@handle_dynamo_error
async def update_item(table_name, key, update_expression, expression_attribute_values=None, expression_attribute_names=None):
    """
    Update an item in a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to update the item in
        key (dict): The key of the item to update
        update_expression (str): The update expression for the update
        expression_attribute_values (dict, optional): The expression attribute values
        expression_attribute_names (dict, optional): The expression attribute names
        
    Returns:
        dict: The response from DynamoDB
    """
    try:
        table = get_table(table_name)
        update_params = {
            'Key': key,
            'UpdateExpression': update_expression
        }
        
        if expression_attribute_values:
            update_params['ExpressionAttributeValues'] = expression_attribute_values
            
        if expression_attribute_names:
            update_params['ExpressionAttributeNames'] = expression_attribute_names
            
        response = table.update_item(**update_params)
        logger.info(f"Successfully updated item in table {table_name}")
        return response
    except Exception as e:
        logger.error(f"Error updating item in table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to update item in table {table_name}") from e

@handle_dynamo_error
async def delete_item(table_name, key):
    """
    Delete an item from a DynamoDB table.
    
    Args:
        table_name (str): The name of the table to delete the item from
        key (dict): The key of the item to delete
        
    Returns:
        dict: The response from DynamoDB
    """
    try:
        table = get_table(table_name)
        response = table.delete_item(Key=key)
        logger.info(f"Successfully deleted item from table {table_name}")
        return response
    except Exception as e:
        logger.error(f"Error deleting item from table {table_name}: {e}")
        raise DynamoDBOperationError(f"Failed to delete item from table {table_name}") from e

# Initialize the DynamoDB connection when the module is imported
init_db()
