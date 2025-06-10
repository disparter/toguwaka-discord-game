"""
Database provider for Academia Tokugawa.

Este módulo é a ÚNICA interface pública para acesso ao banco de dados.
Ele usa exclusivamente DynamoDB para todas as operações.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import boto3
from botocore.exceptions import ClientError

from config import DYNAMODB_PLAYERS_TABLE, DYNAMODB_INVENTORY_TABLE, DYNAMODB_CLUBS_TABLE

logger = logging.getLogger('tokugawa_bot')

# Configurar região padrão para o DynamoDB
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
PLAYERS_TABLE = dynamodb.Table(DYNAMODB_PLAYERS_TABLE)
INVENTORY_TABLE = dynamodb.Table(DYNAMODB_INVENTORY_TABLE)
CLUBS_TABLE = dynamodb.Table(DYNAMODB_CLUBS_TABLE)

# --- Player operations ---
async def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from database."""
    try:
        response = PLAYERS_TABLE.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {str(e)}")
        return None

async def create_player(user_id: str, name: str, **kwargs) -> bool:
    """Create a new player in database."""
    try:
        player_data = {
            'PK': f'PLAYER#{user_id}',
            'SK': 'PROFILE',
            'name': name,
            'level': 1,
            'exp': 0,
            'tusd': 1000,
            'club_id': None,
            'dexterity': 10,
            'intellect': 10,
            'charisma': 10,
            'power_stat': 10,
            'reputation': 0,
            'hp': 100,
            'max_hp': 100,
            'strength_level': 1,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            **kwargs
        }
        PLAYERS_TABLE.put_item(Item=player_data)
        return True
    except Exception as e:
        logger.error(f"Error creating player {user_id}: {str(e)}")
        return False

async def update_player(user_id: str, **kwargs) -> bool:
    """Update player data in database."""
    try:
        # Get current player data
        current_player = await get_player(user_id)
        if not current_player:
            return False

        # Update fields
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}

        for key, value in kwargs.items():
            if key in current_player or key in ['level', 'exp', 'tusd', 'club_id', 'dexterity', 'intellect', 'charisma', 'power_stat', 'reputation', 'hp', 'max_hp', 'strength_level']:
                update_expr += f"#{key} = :{key}, "
                expr_attr_values[f":{key}"] = value
                expr_attr_names[f"#{key}"] = key

        # Always update last_active
        update_expr += "#last_active = :last_active"
        expr_attr_values[":last_active"] = datetime.now().isoformat()
        expr_attr_names["#last_active"] = "last_active"

        PLAYERS_TABLE.update_item(
            Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names
        )
        return True
    except Exception as e:
        logger.error(f"Error updating player {user_id}: {str(e)}")
        return False

async def get_all_players() -> List[Dict[str, Any]]:
    """Get all players from DynamoDB."""
    try:
        response = PLAYERS_TABLE.scan()
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all players: {str(e)}")
        return []

# --- Club operations ---
async def get_club(club_id: str) -> Optional[Dict[str, Any]]:
    """Get club data from database."""
    try:
        response = CLUBS_TABLE.get_item(Key={'PK': f'CLUB#{club_id}', 'SK': 'INFO'})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {str(e)}")
        return None

async def get_all_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from database."""
    try:
        response = CLUBS_TABLE.scan(
            FilterExpression='begins_with(PK, :pk) AND SK = :sk',
            ExpressionAttributeValues={
                ':pk': 'CLUB#',
                ':sk': 'INFO'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all clubs: {str(e)}")
        return []

# --- Event operations ---
async def store_event(*args, **kwargs) -> bool:
    return True

async def get_event(*args, **kwargs) -> Optional[Dict[str, Any]]:
    return None

async def get_events_by_date(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

async def update_event_status(*args, **kwargs) -> bool:
    return True

async def get_active_events(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

# --- Cooldown operations ---
async def store_cooldown(user_id: str, command: str, expiry_time: datetime) -> bool:
    """Store command cooldown in database."""
    try:
        PLAYERS_TABLE.update_item(
            Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'},
            UpdateExpression='SET cooldowns.#command = :expiry',
            ExpressionAttributeValues={':expiry': expiry_time.isoformat()},
            ExpressionAttributeNames={'#command': command}
        )
        return True
    except Exception as e:
        logger.error(f"Error storing cooldown for command {command} for player {user_id}: {str(e)}")
        return False

async def get_cooldown(user_id: str, command: str) -> Optional[datetime]:
    """Get command cooldown from database."""
    try:
        response = PLAYERS_TABLE.get_item(Key={'PK': f'PLAYER#{user_id}', 'SK': 'PROFILE'})
        player = response.get('Item')
        if player and 'cooldowns' in player and command in player['cooldowns']:
            return datetime.fromisoformat(player['cooldowns'][command])
        return None
    except Exception as e:
        logger.error(f"Error getting cooldown for command {command} for player {user_id}: {str(e)}")
        return None

async def get_cooldowns(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

async def clear_expired_cooldowns() -> int:
    """Clear expired cooldowns from database."""
    try:
        # Scan all players
        response = PLAYERS_TABLE.scan()
        cleared = 0
        now = datetime.now()

        for player in response.get('Items', []):
            if 'cooldowns' not in player:
                continue

            # Check each cooldown
            expired_commands = []
            for command, expiry_str in player['cooldowns'].items():
                expiry = datetime.fromisoformat(expiry_str)
                if expiry < now:
                    expired_commands.append(command)
                    cleared += 1

            # Remove expired cooldowns
            if expired_commands:
                update_expr = "REMOVE " + ", ".join([f"cooldowns.#{cmd}" for cmd in expired_commands])
                expr_attr_names = {f"#{cmd}": cmd for cmd in expired_commands}

                PLAYERS_TABLE.update_item(
                    Key={'PK': player['PK'], 'SK': player['SK']},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_attr_names
                )

        return cleared
    except Exception as e:
        logger.error(f"Error clearing expired cooldowns: {str(e)}")
        return 0

# --- System flag operations ---
async def get_system_flag(*args, **kwargs) -> Optional[Any]:
    return None

async def set_system_flag(*args, **kwargs) -> bool:
    return True

# --- Grade operations ---
async def get_player_grades(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

async def update_player_grade(*args, **kwargs) -> bool:
    return True

async def get_monthly_average_grades(*args, **kwargs) -> Dict[str, float]:
    return {}

# --- Voting operations ---
async def add_vote(*args, **kwargs) -> bool:
    return True

async def get_vote_results(*args, **kwargs) -> Dict[str, int]:
    return {}

async def update_player_reputation(*args, **kwargs) -> bool:
    return True

# --- Quiz operations ---
async def get_quiz_questions(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

async def record_quiz_answer(*args, **kwargs) -> bool:
    return True

# --- Init ---
async def init_db() -> bool:
    """Initialize the database."""
    try:
        from src.utils.persistence.dynamodb import init_db as dynamo_init_db
        return dynamo_init_db()
    except Exception as e:
        logger.error(f"Error initializing DynamoDB: {str(e)}")
        return False

def ensure_dynamo_available() -> bool:
    """Check if DynamoDB is available."""
    try:
        # Try to describe tables
        dynamodb_client = boto3.client('dynamodb')
        dynamodb_client.describe_table(TableName=DYNAMODB_PLAYERS_TABLE)
        dynamodb_client.describe_table(TableName=DYNAMODB_INVENTORY_TABLE)
        dynamodb_client.describe_table(TableName=DYNAMODB_CLUBS_TABLE)
        return True
    except Exception as e:
        logger.error(f"DynamoDB is not available: {str(e)}")
        return False

# --- Club NPCs ---
async def get_relevant_npcs(club_id: str) -> List[Dict[str, Any]]:
    """Get NPCs relevant to a specific club."""
    # Hardcoded NPCs for each club
    club_npcs = {
        "clube_das_chamas": [
            {
                "id": "kai_flameheart",
                "name": "Kai Flameheart",
                "role": "Líder",
                "image": "kai_flameheart_intro.png"
            }
        ],
        "clube_politico": [
            {
                "id": "alexander_strategos",
                "name": "Alexander Strategos",
                "role": "Líder",
                "image": "lider_clube_conselho_politico_intro.png"
            }
        ],
        "clube_de_combate": [
            {
                "id": "ryuji_battleborn",
                "name": "Ryuji Battleborn",
                "role": "Líder",
                "image": "ryuji_battleborn_intro.png"
            }
        ],
        "clube_dos_elementalistas": [
            {
                "id": "gaia_naturae",
                "name": "Gaia Naturae",
                "role": "Líder",
                "image": "gaia_naturae_neutral.png"
            }
        ],
        "clube_dos_ilusionistas": [
            {
                "id": "mina_starlight",
                "name": "Mina Starlight",
                "role": "Líder",
                "image": "mina_starlight_intro.png"
            }
        ]
    }
    return club_npcs.get(club_id, [])

# --- Inventory operations ---
async def get_player_inventory(user_id: str) -> Dict[str, Any]:
    """Get player inventory from database."""
    if USE_DYNAMO:
        try:
            response = INVENTORY_TABLE.query(
                KeyConditionExpression='user_id = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            return {item['item_id']: json.loads(item['item_data']) for item in response.get('Items', [])}
        except Exception as e:
            logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
            return {}
    else:
        return _sqlite_get_player_inventory(user_id)

async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add item to player inventory."""
    if USE_DYNAMO:
        try:
            INVENTORY_TABLE.put_item(Item={
                'user_id': user_id,
                'item_id': item_id,
                'item_data': json.dumps(item_data),
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            })
            return True
        except Exception as e:
            logger.error(f"Error adding item {item_id} to inventory for player {user_id}: {str(e)}")
            return False
    else:
        return _sqlite_add_item_to_inventory(user_id, item_id, item_data)

async def remove_item_from_inventory(user_id: str, item_id: str) -> bool:
    """Remove item from player inventory."""
    if USE_DYNAMO:
        try:
            INVENTORY_TABLE.delete_item(
                Key={
                    'user_id': user_id,
                    'item_id': item_id
                }
            )
            return True
        except Exception as e:
            logger.error(f"Error removing item {item_id} from inventory for player {user_id}: {str(e)}")
            return False
    else:
        return _sqlite_remove_item_from_inventory(user_id, item_id)

# --- Outros helpers ---
async def get_top_players(*args, **kwargs) -> list:
    """Get top players by various criteria."""
    try:
        response = PLAYERS_TABLE.scan()
        players = response.get('Items', [])
        return sorted(players, key=lambda x: x.get('exp', 0), reverse=True)
    except Exception as e:
        logger.error(f"Error getting top players: {str(e)}")
        return []

async def get_top_players_by_reputation(*args, **kwargs) -> list:
    """Get top players by reputation."""
    try:
        response = PLAYERS_TABLE.scan()
        players = response.get('Items', [])
        return sorted(players, key=lambda x: x.get('reputation', 0), reverse=True)
    except Exception as e:
        logger.error(f"Error getting top players by reputation: {str(e)}")
        return []

async def get_club_members(club_id: str) -> list:
    """Get all members of a club."""
    try:
        response = PLAYERS_TABLE.scan(
            FilterExpression='club_id = :cid',
            ExpressionAttributeValues={':cid': club_id}
        )
        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting club members: {str(e)}")
        return [] 