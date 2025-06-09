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
        if isinstance(o, Decimal):
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

def init_db():
    """
    Initialize the DynamoDB connection and create tables if they don't exist.
    """
    try:
        logger.info("Initializing DynamoDB connection")
        dynamodb = get_dynamodb_client()
        
        # Check if tables exist and create them if they don't
        for table_name in [TABLES['players'], TABLES['clubs'], TABLES['events'], TABLES['inventory'], TABLES['market'], TABLES['items'], TABLES['club_activities'], TABLES['grades'], TABLES['votes'], TABLES['quiz_questions'], TABLES['quiz_answers'], TABLES['main']]:
            try:
                logger.info(f"Checking table {table_name}")
                # Try to describe the table to check if it exists
                try:
                    dynamodb.meta.client.describe_table(TableName=table_name)
                    logger.info(f"Table {table_name} exists and is active")
                except Exception as e:
                    if hasattr(e, 'response') and e.response['Error']['Code'] in ['ResourceNotFoundException', 'UnrecognizedClientException']:
                        logger.info(f"Creating table {table_name}")
                        create_table(dynamodb, table_name)
                        # Wait for table to be active after creation
                        dynamodb.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                        logger.info(f"Table {table_name} created and is active")
                    else:
                        logger.error(f"Error checking table {table_name}: {e}")
                        raise DynamoDBOperationError(f"Error checking table {table_name}: {e}")
            except Exception as e:
                logger.error(f"Error initializing table {table_name}: {e}")
                raise DynamoDBOperationError(f"Error initializing table {table_name}: {e}")

        logger.info("DynamoDB initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing DynamoDB: {e}")
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
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (DynamoDBError, ClientError, Exception) as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return False
    return wrapper

@handle_dynamo_error
def get_player(user_id):
    """Get a player from DynamoDB."""
    if not user_id:
        logger.warning("get_player called with no user_id")
        return None
        
    try:
        logger.info(f"Attempting to get player with user_id: {user_id}")
        table = get_table(TABLES['players'])
        
        # Get player by primary key
        key = {
            'PK': f"PLAYER#{user_id}",
            'SK': 'PROFILE'
        }
        logger.info(f"Searching with key: {key}")
        
        response = table.get_item(Key=key)
        logger.info(f"Raw DynamoDB response: {response}")
        
        item = response.get('Item')
        if not item:
            logger.warning(f"No player found for user_id: {user_id}")
            return None
            
        logger.info(f"Found player data: {item}")
        
        # Convert Decimal values to int/float
        for k, value in item.items():
            if isinstance(value, Decimal):
                item[k] = int(value) if value % 1 == 0 else float(value)

        # Garantir campos obrigatórios
        defaults = {
            'power_stat': 10,
            'dexterity': 10,
            'intellect': 10,
            'charisma': 10,
            'club_id': None,
            'exp': 0,
            'hp': 100,
            'tusd': 1000,
            'inventory': {},
            'level': 1
        }
        for k, v in defaults.items():
            if k not in item or item[k] is None:
                item[k] = v

        # Desserializar inventário se for string
        if isinstance(item['inventory'], str):
            try:
                item['inventory'] = json.loads(item['inventory'])
            except Exception as e:
                logger.warning(f"Could not decode inventory for player {user_id}: {e}")
                item['inventory'] = {}
        if not isinstance(item['inventory'], dict):
            item['inventory'] = {}

        logger.info(f"Final player data after normalization: {item}")
        return item
    except Exception as e:
        logger.error(f"Error getting player: {e}")
        return None

@handle_dynamo_error
def create_player(user_id, name, **kwargs):
    """Create a new player in DynamoDB."""
    if not user_id or not name:
        return False
        
    try:
        table = get_table(TABLES['players'])
        
        # Create player item with proper key structure
        item = {
            'PK': f"PLAYER#{user_id}",
            'SK': 'PROFILE',
            'user_id': user_id,
            'name': name,
            **kwargs
        }
        
        # Convert numeric values to Decimal
        for key, value in item.items():
            if isinstance(value, (int, float)):
                item[key] = Decimal(str(value))
        
        table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return False

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
            item = response['Item']
            club = {
                'name': item.get('NomeClube', ''),
                'description': item.get('descricao', ''),
                'leader_id': item.get('lider_id', ''),
                'reputacao': item.get('reputacao', 0)
            }
            return club
        return None
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {e}")
        raise DynamoDBOperationError(f"Failed to get club: {e}")

@handle_dynamo_error
def get_all_clubs():
    """Get all clubs from DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        #logger.info("Attempting to scan clubs table")
        response = table.scan()
        #logger.info(f"Raw DynamoDB response: {response}")

        clubs = []
        if 'Items' in response:
            for item in response['Items']:
                # logger.info(f"Processing club item: {item}")
                # Convert the item to a standard format
                club = {
                    'name': item.get('NomeClube', ''),
                    'description': item.get('descricao', ''),
                    'leader_id': item.get('lider_id', ''),
                    'reputacao': item.get('reputacao', 0)
                }
                #logger.info(f"Converted club object: {club}")
                clubs.append(club)
        
        # Sort clubs by name
        sorted_clubs = sorted(clubs, key=lambda x: x['name'])
        # logger.info(f"Final sorted clubs list: {sorted_clubs}")
        return sorted_clubs
    except Exception as e:
        logger.error(f"Error getting all clubs: {e}")
        raise DynamoDBOperationError(f"Failed to get all clubs: {e}")

@handle_dynamo_error
def create_club(club_id, name, description, leader_id):
    """Create a new club in DynamoDB."""
    try:
        table = get_table(TABLES['clubs'])
        club_item = {
            'NomeClube': name,
            'descricao': description,
            'lider_id': leader_id,
            'reputacao': 0,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        logger.info(f"Creating club with item: {club_item}")
        
        table.put_item(Item=club_item)
        # logger.info(f"Successfully created club with name: {name}")
        return True
    except Exception as e:
        logger.error(f"Error creating club {name}: {e}")
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
    """Update a player in DynamoDB."""
    if not user_id:
        return False
        
    try:
        table = get_table(TABLES['players'])
        
        # Build update expression
        update_expr = "SET "
        expr_attr_values = {}
        
        for key, value in kwargs.items():
            if isinstance(value, (int, float)):
                value = Decimal(str(value))
            update_expr += f"#{key} = :{key}, "
            expr_attr_values[f":{key}"] = value
            
        update_expr = update_expr[:-2]  # Remove trailing comma and space
        
        # Add expression attribute names
        expr_attr_names = {f"#{key}": key for key in kwargs.keys()}
        
        # Update player
        table.update_item(
            Key={
                'PK': f"PLAYER#{user_id}",
                'SK': 'PROFILE'
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names
        )
        
        return True
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False

@handle_dynamo_error
def create_item(item_id, name, description, type, rarity, price, effects, **kwargs):
    """Create a new item in DynamoDB."""
    if not item_id or not name or not type or not rarity or price is None:
        return False
        
    # Convert effects to JSON string if it's a dict
    if isinstance(effects, dict):
        effects = json.dumps(effects)
        
    # Create item
    item = {
        'PK': f'ITEM#{item_id}',
        'SK': 'PROFILE',
        'name': name,
        'description': description,
        'type': type,
        'rarity': rarity,
        'price': int(price),
        'effects': effects,
        'created_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        table = get_table(TABLES['items'])
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(PK)'
        )
        logger.info(f"Created new item: {name} ({item_id})")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.warning(f"Item already exists: {item_id}")
            return False
        raise DynamoDBError(f"Error creating item: {str(e)}")

@handle_dynamo_error
def get_top_clubs_by_activity(week=None, year=None, limit=3):
    """Get top clubs by activity points for a specific week."""
    try:
        # If week and year are not provided, use current week
        if week is None or year is None:
            now = datetime.now()
            year, week, _ = now.isocalendar()

        # Get all club activities for the specified week and year
        activities_table = get_table(TABLES['club_activities'])
        clubs_table = get_table(TABLES['clubs'])

        # Query activities for the specified week and year
        response = activities_table.query(
            IndexName='week-year-index',
            KeyConditionExpression='week = :week AND year = :year',
            ExpressionAttributeValues={
                ':week': week,
                ':year': year
            }
        )

        # Create a dictionary to store club points
        club_points = {}

        # Process activities and sum points for each club
        if 'Items' in response:
            for item in response['Items']:
                club_id = item.get('club_id')
                points = item.get('points', 0)
                
                if club_id in club_points:
                    club_points[club_id] += points
                else:
                    club_points[club_id] = points

        # Get club details for clubs with points
        top_clubs = []
        for club_id, total_points in sorted(club_points.items(), key=lambda x: x[1], reverse=True)[:limit]:
            club_response = clubs_table.get_item(Key={'NomeClube': club_id})
            if 'Item' in club_response:
                club = club_response['Item']
                top_clubs.append({
                    'name': club.get('NomeClube', ''),
                    'description': club.get('descricao', ''),
                    'leader_id': club.get('lider_id', ''),
                    'reputacao': club.get('reputacao', 0),
                    'total_points': total_points
                })

        return top_clubs
    except Exception as e:
        logger.error(f"Error getting top clubs by activity: {e}")
        return []

@handle_dynamo_error
def record_club_activity(user_id, activity_type, points=1):
    """Record a club activity for a player's club."""
    try:
        # Get player's club
        players_table = get_table(TABLES['players'])
        player_response = players_table.get_item(Key={'user_id': user_id})
        
        if 'Item' not in player_response:
            logger.info(f"Player {user_id} not found, skipping activity recording")
            return False
            
        player = player_response['Item']
        club_id = player.get('club_id')
        
        if not club_id:
            logger.info(f"Player {user_id} has no club, skipping activity recording")
            return False

        # Get current week and year
        now = datetime.now()
        year, week, _ = now.isocalendar()

        # Record the activity
        activities_table = get_table(TABLES['club_activities'])
        activity_id = f"{club_id}#{user_id}#{activity_type}#{week}#{year}"
        
        activities_table.put_item(
            Item={
                'PK': f"CLUB#{club_id}",
                'SK': f"ACTIVITY#{activity_id}",
                'club_id': club_id,
                'user_id': user_id,
                'activity_type': activity_type,
                'points': points,
                'week': week,
                'year': year,
                'created_at': now.isoformat()
            }
        )

        logger.info(f"Recorded {activity_type} activity for club {club_id} by player {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error recording club activity: {e}")
        return False

@handle_dynamo_error
def get_events_by_date(date=None, include_completed=True):
    """Get events for a specific date from DynamoDB. Args:
        date (datetime, optional): The date to get events for. Defaults to today.
        include_completed (bool, optional): Whether to include completed events. Defaults to True.
    Returns:
        list: List of event dictionaries
    """
    try:
        if date is None:
            date = datetime.now().date()
        date_start = datetime.combine(date, time.min).isoformat()
        date_end = datetime.combine(date, time.max).isoformat()
        table = get_table(TABLES['events'])
        response = table.scan()
        events = []
        for item in response.get('Items', []):
            # Parse times
            start_time = item.get('start_time')
            end_time = item.get('end_time')
            completed = item.get('completed', False)
            # Check if event is in the date range
            in_range = False
            if start_time and date_start <= start_time <= date_end:
                in_range = True
            if end_time and date_start <= end_time <= date_end:
                in_range = True
            if not in_range:
                continue
            if not include_completed and completed:
                continue
            # Parse JSON fields
            item['participantes'] = json.loads(item.get('participantes', '[]'))
            item['data'] = json.loads(item.get('data', '{}'))
            events.append(item)
        return events
    except Exception as e:
        logger.error(f"Error getting events by date from DynamoDB: {e}")
        return []

@handle_dynamo_error
def update_event_status(event_id, status):
    """Update the status of an event."""
    try:
        table = get_table(TABLES['events'])
        table.update_item(
            Key={'event_id': event_id},
            UpdateExpression='SET status = :status',
            ExpressionAttributeValues={
                ':status': status
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error updating event status: {e}")
        return False

@handle_dynamo_error
def get_active_events():
    """Stub for get_active_events. Returns an empty list."""
    return []

@handle_dynamo_error
def store_cooldown(*args, **kwargs):
    """Stub for store_cooldown. Returns True."""
    return True

@handle_dynamo_error
def get_cooldowns(*args, **kwargs):
    """Stub for get_cooldowns. Returns an empty list."""
    return []

@handle_dynamo_error
def clear_expired_cooldowns(*args, **kwargs):
    """Stub for clear_expired_cooldowns. Returns True."""
    return True

@handle_dynamo_error
def set_system_flag(*args, **kwargs):
    """Stub for set_system_flag. Returns True."""
    return True

@handle_dynamo_error
def get_player_grades(user_id, subject=None, month=None, year=None):
    """Get player grades from DynamoDB."""
    try:
        table = get_table(TABLES['grades'])
        # Build filter expression
        key_expr = 'user_id = :uid'
        expr_attr = {':uid': user_id}
        if subject:
            key_expr += ' AND subject = :subject'
            expr_attr[':subject'] = subject
        if month:
            key_expr += ' AND month = :month'
            expr_attr[':month'] = int(month)
        if year:
            key_expr += ' AND year = :year'
            expr_attr[':year'] = int(year)
        response = table.scan(
            FilterExpression=key_expr,
            ExpressionAttributeValues=expr_attr
        )
        grades = response.get('Items', [])
        return [dict(g) for g in grades]
    except Exception as e:
        logger.error(f"Error getting grades for user {user_id}: {e}")
        return []

@handle_dynamo_error
def update_player_grade(user_id, subject, grade, month, year):
    """Update or insert a player's grade in DynamoDB."""
    try:
        table = get_table('grades')
        item = {
            'user_id': user_id,
            'subject': subject,
            'grade': int(grade),
            'month': int(month),
            'year': int(year),
            'created_at': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error updating grade for user {user_id}: {e}")
        return False

@handle_dynamo_error
def get_monthly_average_grades(month, year):
    """Get average grades per subject for a given month and year from DynamoDB."""
    try:
        table = get_table('grades')
        response = table.scan(
            FilterExpression='month = :month AND year = :year',
            ExpressionAttributeValues={
                ':month': int(month),
                ':year': int(year)
            }
        )
        grades = response.get('Items', [])
        subject_totals = {}
        subject_counts = {}
        for g in grades:
            subject = g['subject']
            grade = int(g['grade'])
            subject_totals[subject] = subject_totals.get(subject, 0) + grade
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        averages = []
        for subject, total in subject_totals.items():
            averages.append({'subject': subject, 'average': total / subject_counts[subject]})
        return averages
    except Exception as e:
        logger.error(f"Error getting monthly averages: {e}")
        return []

@handle_dynamo_error
def add_vote(category, voter_id, candidate_id, week, year):
    """Add a vote in DynamoDB."""
    try:
        table = get_table('votes')
        item = {
            'category': category,
            'voter_id': voter_id,
            'candidate_id': candidate_id,
            'week': int(week),
            'year': int(year),
            'created_at': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error adding vote: {e}")
        return False

@handle_dynamo_error
def get_vote_results(category, week, year):
    """Get vote results for a category/week/year from DynamoDB."""
    try:
        table = get_table('votes')
        response = table.scan(
            FilterExpression='category = :cat AND week = :week AND year = :year',
            ExpressionAttributeValues={
                ':cat': category,
                ':week': int(week),
                ':year': int(year)
            }
        )
        votes = response.get('Items', [])
        results = {}
        for v in votes:
            candidate = v['candidate_id']
            results[candidate] = results.get(candidate, 0) + 1
        return [{'candidate_id': k, 'votes': v} for k, v in results.items()]
    except Exception as e:
        logger.error(f"Error getting vote results: {e}")
        return []

@handle_dynamo_error
def update_player_reputation(user_id, reputation):
    """Update a player's reputation in DynamoDB."""
    try:
        table = get_table(TABLES['players'])
        table.update_item(
            Key={'user_id': user_id},
            UpdateExpression='SET reputation = :rep',
            ExpressionAttributeValues={':rep': int(reputation)}
        )
        return True
    except Exception as e:
        logger.error(f"Error updating reputation for user {user_id}: {e}")
        return False

@handle_dynamo_error
def get_quiz_questions():
    """Get all quiz questions from DynamoDB."""
    try:
        table = get_table('quiz_questions')
        response = table.scan()
        questions = response.get('Items', [])
        return [dict(q) for q in questions]
    except Exception as e:
        logger.error(f"Error getting quiz questions: {e}")
        return []

@handle_dynamo_error
def record_quiz_answer(user_id, question_id, is_correct):
    """Record a quiz answer for a user in DynamoDB."""
    try:
        table = get_table('quiz_answers')
        item = {
            'user_id': user_id,
            'question_id': question_id,
            'is_correct': bool(is_correct),
            'created_at': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        return True
    except Exception as e:
        logger.error(f"Error recording quiz answer: {e}")
        return False

# Initialize the DynamoDB connection when the module is imported
init_db()
