import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Get table names from environment variables
PLAYERS_TABLE = os.getenv('DYNAMODB_PLAYERS_TABLE', 'tokugawa-players')
INVENTORY_TABLE = os.getenv('DYNAMODB_INVENTORY_TABLE', 'tokugawa-inventory')

def get_table(table_name: str):
    """Get DynamoDB table resource."""
    return dynamodb.Table(table_name)

# Table schemas
PLAYERS_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id> or CLUB#<club_id>)
    'SK': 'S',  # Sort key (PROFILE or INFO)
    'name': 'S',
    'level': 'N',
    'exp': 'N',
    'tusd': 'N',
    'hp': 'N',
    'max_hp': 'N',
    'dexterity': 'N',
    'intellect': 'N',
    'charisma': 'N',
    'power_stat': 'N',
    'reputation': 'N',
    'strength_level': 'N',
    'club_id': 'S',
    'created_at': 'S',
    'last_active': 'S'
}

INVENTORY_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id>)
    'SK': 'S',  # Sort key (ITEM#<item_id>)
    'item_data': 'M'  # Map containing item details
}

# Default values
DEFAULT_PLAYER_VALUES = {
    'level': 1,
    'exp': 0,
    'tusd': 1000,
    'hp': 100,
    'max_hp': 100,
    'dexterity': 10,
    'intellect': 10,
    'charisma': 10,
    'power_stat': 10,
    'reputation': 0,
    'strength_level': 1,
    'club_id': None
}

# Table names mapping
TABLES = {
    'players': PLAYERS_TABLE,
    'inventory': INVENTORY_TABLE
} 