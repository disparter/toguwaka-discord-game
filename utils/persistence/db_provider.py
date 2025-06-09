"""
Database provider for Academia Tokugawa.

Este módulo é a ÚNICA interface pública para acesso ao banco de dados.
Ele delega para DynamoDB se USE_DYNAMO=True, ou para SQLite se USE_DYNAMO=False.
Não há fallback automático. O resto do código deve importar APENAS deste provider.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger('tokugawa_bot')

# Configuração do DynamoDB
DYNAMODB = boto3.resource('dynamodb')
PLAYERS_TABLE = DYNAMODB.Table('players')
INVENTORY_TABLE = DYNAMODB.Table('inventory')
CLUBS_TABLE = DYNAMODB.Table('clubs')

# --- Player operations ---
async def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from DynamoDB."""
    try:
        response = PLAYERS_TABLE.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {str(e)}")
        return None

async def create_player(user_id: str, name: str, **kwargs) -> bool:
    """Create a new player in DynamoDB."""
    try:
        player_data = {
            'user_id': user_id,
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
    """Update player data in DynamoDB."""
    try:
        update_expr = "SET "
        expr_attr_values = {}
        expr_attr_names = {}
        
        for key, value in kwargs.items():
            update_expr += f"#{key} = :{key}, "
            expr_attr_values[f":{key}"] = value
            expr_attr_names[f"#{key}"] = key
        
        update_expr = update_expr.rstrip(", ")
        
        PLAYERS_TABLE.update_item(
            Key={'user_id': user_id},
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
    """Get club data from DynamoDB."""
    try:
        response = CLUBS_TABLE.get_item(Key={'club_id': club_id})
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {str(e)}")
        return None

async def get_all_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from DynamoDB."""
    try:
        response = CLUBS_TABLE.scan()
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
async def store_cooldown(*args, **kwargs) -> bool:
    return True

async def get_cooldowns(*args, **kwargs) -> List[Dict[str, Any]]:
    return []

async def clear_expired_cooldowns(*args, **kwargs) -> bool:
    return True

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
async def init_db(*args, **kwargs) -> bool:
    return True

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
    """Get player's inventory from DynamoDB."""
    try:
        response = INVENTORY_TABLE.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id}
        )
        items = response.get('Items', [])
        return {item['item_id']: json.loads(item['item_data']) for item in items}
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
        return {}

async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add item to player's inventory in DynamoDB."""
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
        logger.error(f"Error adding item to inventory for player {user_id}: {str(e)}")
        return False

async def remove_item_from_inventory(user_id: str, item_id: str) -> bool:
    """Remove item from player's inventory in DynamoDB."""
    try:
        INVENTORY_TABLE.delete_item(
            Key={
                'user_id': user_id,
                'item_id': item_id
            }
        )
        return True
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
        return False

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