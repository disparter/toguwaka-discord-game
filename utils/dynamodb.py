"""
DynamoDB implementation for Academia Tokugawa.

This module provides DynamoDB-specific implementations of database operations
using multiple tables for better organization and performance.
"""

import boto3
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

logger = logging.getLogger('tokugawa_bot')

# DynamoDB table names
TABLES = {
    'main': os.environ.get('DYNAMODB_TABLE', 'AcademiaTokugawa'),
    'clubs': os.environ.get('DYNAMODB_CLUBS_TABLE', 'Clubes'),
    'events': os.environ.get('DYNAMODB_EVENTS_TABLE', 'Eventos'),
    'inventory': os.environ.get('DYNAMODB_INVENTORY_TABLE', 'Inventario'),
    'players': os.environ.get('DYNAMODB_PLAYERS_TABLE', 'Jogadores'),
    'market': os.environ.get('DYNAMODB_MARKET_TABLE', 'Mercado')
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
        if isinstance(o, Decimal):
            return float(o) if o % 1 else int(o)
        return super(DecimalEncoder, self).default(o)

def get_dynamodb_client():
    """Get a DynamoDB client with proper error handling."""
    try:
        # Create a session with the default credential provider chain
        session = boto3.Session(region_name=AWS_REGION)
        
        # Create DynamoDB client from the session
        dynamodb = session.resource('dynamodb')
        logger.debug(f"DynamoDB client initialized for region {AWS_REGION}")
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
        dynamodb = get_dynamodb_client()
        return dynamodb.Table(table_name)
    except Exception as e:
        logger.error(f"Error getting table {table_name}: {e}")
        raise DynamoDBConnectionError(f"Failed to get table {table_name}") from e

def init_db():
    """
    Initialize the DynamoDB connection and create tables if they don't exist.
    """
    global table
    
    try:
        dynamodb = get_dynamodb_client()
        
        # Check if tables exist and create them if they don't
        for table_name in TABLES.values():
            try:
                table = dynamodb.Table(table_name)
                # Wait for table to be active if it exists
                table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                logger.info(f"Table {table_name} exists and is active")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info(f"Creating table {table_name}")
                    create_table(dynamodb, table_name)
                    # Wait for table to be active after creation
                    dynamodb.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                else:
                    raise

        # Initialize the table variable for global use
        table = get_table(TABLES['main'])
        
        # After successful initialization, distribute data from main table to specialized tables
        try:
            from utils.migrate_to_dynamodb import distribute_data_to_tables
            if distribute_data_to_tables():
                logger.info("Successfully distributed data to specialized tables")
            else:
                logger.warning("Data distribution completed with warnings")
        except Exception as e:
            logger.error(f"Error distributing data to tables: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing DynamoDB: {e}")
        return False

def create_table(dynamodb, table_name):
    """Create a DynamoDB table with appropriate schema."""
    try:
        if table_name == TABLES['main']:
            # Main table with GSI
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'PK', 'KeyType': 'HASH'},
                    {'AttributeName': 'SK', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'PK', 'AttributeType': 'S'},
                    {'AttributeName': 'SK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1PK', 'AttributeType': 'S'},
                    {'AttributeName': 'GSI1SK', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'GSI1',
                        'KeySchema': [
                            {'AttributeName': 'GSI1PK', 'KeyType': 'HASH'},
                            {'AttributeName': 'GSI1SK', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'}
                    }
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['clubs']:
            # Clubs table
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'NomeClube', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'NomeClube', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['events']:
            # Events table
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'EventoID', 'KeyType': 'HASH'},
                    {'AttributeName': 'Tipo', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'EventoID', 'AttributeType': 'S'},
                    {'AttributeName': 'Tipo', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['inventory']:
            # Inventory table
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'JogadorID', 'KeyType': 'HASH'},
                    {'AttributeName': 'ItemID', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'JogadorID', 'AttributeType': 'S'},
                    {'AttributeName': 'ItemID', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        elif table_name == TABLES['players']:
            # Players table
            table = dynamodb.create_table(
                TableName=table_name,
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
            # Market table
            table = dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'ItemID', 'KeyType': 'HASH'},
                    {'AttributeName': 'VendedorID', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'ItemID', 'AttributeType': 'S'},
                    {'AttributeName': 'VendedorID', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )

        # Wait for table to be created
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        logger.info(f"Table {table_name} created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {e}")
        return False

def handle_dynamo_error(func):
    """Decorator to handle DynamoDB errors and attempt fallback to SQLite if needed."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (DynamoDBError, ClientError) as e:
            logger.error(f"DynamoDB error in {func.__name__}: {e}")
            
            # Try to fallback to SQLite
            try:
                from utils.db_provider import db_provider
                if db_provider.fallback_to_sqlite():
                    # Retry the operation with SQLite
                    return func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Error during fallback to SQLite: {fallback_error}")
            
            # If we get here, fallback failed
            raise
    return wrapper

@handle_dynamo_error
def get_player(user_id):
    """Get player data from DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        response = table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' in response:
            player = response['Item']
            # Convert Decimal types to float/int
            return json.loads(json.dumps(player, cls=DecimalEncoder))
        return None
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get player: {e}")

@handle_dynamo_error
def create_player(user_id, name, **kwargs):
    """Create a new player in DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        
        # Process inventory
        inventory = kwargs.get('inventory', {})
        if isinstance(inventory, dict):
            inventory = json.dumps(inventory)

        # Create player profile
        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE',
                'nome': name,
                'inventory': inventory,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat(),
                **kwargs
            }
        )

        logger.info(f"Created new player: {name} (ID: {user_id})")
        return True
    except Exception as e:
        logger.error(f"Error creating player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to create player: {e}")

@handle_dynamo_error
def get_club(club_id):
    """Get club data from DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        response = table.get_item(
            Key={
                'NomeClube': club_id
            }
        )

        if 'Item' in response:
            club = response['Item']
            return json.loads(json.dumps(club, cls=DecimalEncoder))
        return None
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get club: {e}")

@handle_dynamo_error
def create_club(club_id, name, description, leader_id):
    """Create a new club in DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        table.put_item(
            Item={
                'NomeClube': club_id,
                'nome': name,
                'descricao': description,
                'leader_id': leader_id,
                'reputacao': 0,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error creating club {club_id}: {e}")
        raise DynamoDBOperationError(f"Failed to create club: {e}")

@handle_dynamo_error
def get_event(event_id):
    """Get event data from DynamoDB."""
    try:
        table = get_table(TABLES['events'])
        response = table.get_item(
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
def store_event(event_id, name, description, event_type, channel_id, message_id, start_time, end_time, participants=None, data=None):
    """Store an event in DynamoDB."""
    try:
        table = get_table(TABLES['events'])
        table.put_item(
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
def get_player_inventory(user_id):
    """Get player's inventory from DynamoDB."""
    try:
        table = get_table(TABLES['inventory'])
        response = table.query(
            KeyConditionExpression='JogadorID = :uid',
            ExpressionAttributeValues={
                ':uid': user_id
            }
        )

        if 'Items' in response:
            inventory = {}
            for item in response['Items']:
                inventory[item['ItemID']] = int(item['quantidade'])
            return inventory
        return {}
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get inventory: {e}")

@handle_dynamo_error
def add_item_to_inventory(user_id, item_id, quantity):
    """Add an item to player's inventory in DynamoDB."""
    try:
        table = get_table(TABLES['inventory'])
        table.put_item(
            Item={
                'JogadorID': user_id,
                'ItemID': item_id,
                'quantidade': quantity,
                'updated_at': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error adding item {item_id} to inventory for player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to add item to inventory: {e}")

@handle_dynamo_error
def get_market_listing(item_id, seller_id):
    """Get a market listing from DynamoDB."""
    try:
        table = get_table(TABLES['market'])
        response = table.get_item(
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
def list_item_for_sale(item_id, seller_id, price):
    """List an item for sale in DynamoDB."""
    try:
        table = get_table(TABLES['market'])
        table.put_item(
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
def get_system_flag(flag_name):
    """Get a system flag from DynamoDB."""
    try:
        table = get_table(TABLES['main'])
        response = table.get_item(
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
def update_player(user_id, **kwargs):
    """Update player data in DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        update_expression = []
        expression_attribute_values = {}
        for key, value in kwargs.items():
            update_expression.append(f"{key} = :{key}")
            # Serializa dicts para JSON
            if isinstance(value, dict):
                value = json.dumps(value)
            expression_attribute_values[f":{key}"] = value
        update_expression.append("last_active = :last_active")
        expression_attribute_values[":last_active"] = datetime.now().isoformat()
        update_expr = "SET " + ", ".join(update_expression)
        table.update_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expression_attribute_values
        )
        logger.info(f"Updated player {user_id} in DynamoDB: {list(kwargs.keys())}")
        return True
    except Exception as e:
        logger.error(f"Error updating player {user_id}: {e}")
        raise DynamoDBOperationError(f"Failed to update player: {e}")

# Initialize the DynamoDB connection when the module is imported
init_db()
