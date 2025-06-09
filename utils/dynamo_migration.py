import os
import boto3
import logging
from typing import Dict, List, Any
from datetime import datetime
from botocore.exceptions import ClientError
from utils.sqlite_queries import _get_all_players, _get_player_inventory

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Get table names from environment variables
PLAYERS_TABLE = os.getenv('DYNAMODB_PLAYERS_TABLE', 'tokugawa-players')
INVENTORY_TABLE = os.getenv('DYNAMODB_INVENTORY_TABLE', 'tokugawa-inventory')

def create_tables():
    """Create DynamoDB tables if they don't exist."""
    try:
        # Create players table
        players_table = dynamodb.create_table(
            TableName=PLAYERS_TABLE,
            KeySchema=[
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        logger.info(f"Created table {PLAYERS_TABLE}")

        # Create inventory table
        inventory_table = dynamodb.create_table(
            TableName=INVENTORY_TABLE,
            KeySchema=[
                {
                    'AttributeName': 'PK',
                    'KeyType': 'HASH'  # Partition key
                },
                {
                    'AttributeName': 'SK',
                    'KeyType': 'RANGE'  # Sort key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'PK',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'SK',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        logger.info(f"Created table {INVENTORY_TABLE}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            logger.info("Tables already exist")
        else:
            raise

def migrate_inventory(inventory: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    """Migrate inventory data to new format."""
    items = []
    for item_id, item_data in inventory.items():
        items.append({
            'PK': f'PLAYER#{user_id}',
            'SK': f'ITEM#{item_id}',
            'item_data': item_data
        })
    return items

async def migrate_player_data(player: Dict[str, Any], players_table, inventory_table) -> bool:
    """Migrate a single player's data and inventory.
    
    Args:
        player: Player data dictionary
        players_table: DynamoDB players table
        inventory_table: DynamoDB inventory table
        
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        user_id = player['user_id']
        
        # Get and migrate inventory first
        inventory = await _get_player_inventory(user_id)
        if inventory:
            inventory_items = migrate_inventory(inventory, user_id)
            for item in inventory_items:
                inventory_table.put_item(Item=item)
            logger.info(f"Migrated inventory for player {user_id}")
        
        # Then migrate player data
        player_item = {
            'PK': f'PLAYER#{user_id}',
            'SK': 'PROFILE',
            'name': player['name'],
            'level': player.get('level', 1),
            'exp': player.get('exp', 0),
            'tusd': player.get('tusd', 1000),
            'hp': player.get('hp', 100),
            'max_hp': player.get('max_hp', 100),
            'dexterity': player.get('dexterity', 10),
            'intellect': player.get('intellect', 10),
            'charisma': player.get('charisma', 10),
            'power_stat': player.get('power_stat', 10),
            'reputation': player.get('reputation', 0),
            'strength_level': player.get('strength_level', 1),
            'club_id': player.get('club_id'),
            'created_at': player.get('created_at', datetime.now().isoformat()),
            'last_active': player.get('last_active', datetime.now().isoformat())
        }
        
        # Write player data
        players_table.put_item(Item=player_item)
        logger.info(f"Migrated player {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error migrating player {user_id}: {str(e)}")
        return False

async def migrate_data() -> bool:
    """Migrate data from current database to DynamoDB.
    
    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        # Create tables if they don't exist
        create_tables()

        # Get table references
        players_table = dynamodb.Table(PLAYERS_TABLE)
        inventory_table = dynamodb.Table(INVENTORY_TABLE)

        # Get all players from current database
        players = await _get_all_players()
        logger.info(f"Found {len(players)} players to migrate")

        # Migrate each player
        success_count = 0
        for player in players:
            if await migrate_player_data(player, players_table, inventory_table):
                success_count += 1

        logger.info(f"Migration completed. Successfully migrated {success_count} out of {len(players)} players")
        return success_count == len(players)

    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        return False 