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
from utils.dynamodb import (
    get_player as dynamo_get_player,
    get_club as dynamo_get_club,
    get_all_clubs as dynamo_get_all_clubs,
    get_player_inventory as dynamo_get_inventory,
    add_item_to_inventory as dynamo_add_item,
    remove_item_from_inventory as dynamo_remove_item,
    DynamoDBOperationError
)
from utils.sqlite_queries import (
    _get_player as sqlite_get_player,
    _get_club as sqlite_get_club,
    _get_all_clubs as sqlite_get_all_clubs,
    _get_player_inventory as sqlite_get_inventory,
    _add_item_to_inventory as sqlite_add_item,
    _remove_item_from_inventory as sqlite_remove_item
)

logger = logging.getLogger('tokugawa_bot')

USE_DYNAMO = os.environ.get('USE_DYNAMO', 'false').lower() == 'true'

if USE_DYNAMO:
    from utils import dynamodb as db_impl
    logger.info('Database provider: DynamoDB')
else:
    from utils import sqlite_queries as db_impl
    logger.info('Database provider: SQLite')

# --- Player operations ---
async def get_player(user_id: str) -> Optional[Dict[str, Any]]:
    """Get player data from the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_get_player(user_id)
        else:
            return await sqlite_get_player(user_id)
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {str(e)}")
        return None

async def create_player(*args, **kwargs) -> bool:
    return await db_impl.create_player(*args, **kwargs)

async def update_player(*args, **kwargs) -> bool:
    return await db_impl.update_player(*args, **kwargs)

async def get_all_players(*args, **kwargs) -> List[Dict[str, Any]]:
    """Get all players from the database.
    
    Returns:
        List[Dict[str, Any]]: List of player dictionaries with default values for missing fields.
    """
    try:
        players = await db_impl.get_all_players(*args, **kwargs)
        
        # Ensure all players have default values for required fields
        for player in players:
            # Set default values for missing fields
            player.setdefault('name', 'Unknown')
            player.setdefault('level', 1)
            player.setdefault('exp', 0)
            player.setdefault('tusd', 1000)
            player.setdefault('club_id', None)
            player.setdefault('dexterity', 10)
            player.setdefault('intellect', 10)
            player.setdefault('charisma', 10)
            player.setdefault('power_stat', 10)
            player.setdefault('reputation', 0)
            player.setdefault('hp', 100)
            player.setdefault('max_hp', 100)
            player.setdefault('inventory', '{}')
            player.setdefault('strength_level', 1)
            
            # Ensure inventory is a dictionary
            if isinstance(player['inventory'], str):
                try:
                    player['inventory'] = json.loads(player['inventory'])
                except Exception:
                    player['inventory'] = {}
            
            # Ensure club_name is set
            if 'club_name' not in player:
                if player['club_id']:
                    try:
                        club = await get_club(player['club_id'])
                        player['club_name'] = club['name'] if club else 'Sem clube'
                    except Exception as e:
                        logger.error(f"Error getting club {player['club_id']}: {e}")
                        player['club_name'] = 'Sem clube'
                else:
                    player['club_name'] = 'Sem clube'
        
        return players
    except Exception as e:
        logger.error(f"Error in get_all_players: {e}")
        return []

# --- Club operations ---
async def get_club(club_id: str) -> Optional[Dict[str, Any]]:
    """Get club data from the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_get_club(club_id)
        else:
            return await sqlite_get_club(club_id)
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {str(e)}")
        return None

async def get_all_clubs() -> List[Dict[str, Any]]:
    """Get all clubs from the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_get_all_clubs()
        else:
            return await sqlite_get_all_clubs()
    except Exception as e:
        logger.error(f"Error getting all clubs: {str(e)}")
        return []

async def get_top_clubs_by_activity(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_top_clubs_by_activity(*args, **kwargs)

async def record_club_activity(*args, **kwargs) -> bool:
    return await db_impl.record_club_activity(*args, **kwargs)

# --- Event operations ---
async def store_event(*args, **kwargs) -> bool:
    return await db_impl.store_event(*args, **kwargs)

async def get_event(*args, **kwargs) -> Optional[Dict[str, Any]]:
    return await db_impl.get_event(*args, **kwargs)

async def get_events_by_date(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_events_by_date(*args, **kwargs)

async def update_event_status(*args, **kwargs) -> bool:
    return await db_impl.update_event_status(*args, **kwargs)

async def get_active_events(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_active_events(*args, **kwargs)

# --- Cooldown operations ---
async def store_cooldown(*args, **kwargs) -> bool:
    return await db_impl.store_cooldown(*args, **kwargs)

async def get_cooldowns(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_cooldowns(*args, **kwargs)

async def clear_expired_cooldowns(*args, **kwargs) -> bool:
    return await db_impl.clear_expired_cooldowns(*args, **kwargs)

# --- System flag operations ---
async def get_system_flag(*args, **kwargs) -> Optional[Any]:
    return await db_impl.get_system_flag(*args, **kwargs)

async def set_system_flag(*args, **kwargs) -> bool:
    return await db_impl.set_system_flag(*args, **kwargs)

# --- Grade operations ---
async def get_player_grades(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_player_grades(*args, **kwargs)

async def update_player_grade(*args, **kwargs) -> bool:
    return await db_impl.update_player_grade(*args, **kwargs)

async def get_monthly_average_grades(*args, **kwargs) -> Dict[str, float]:
    return await db_impl.get_monthly_average_grades(*args, **kwargs)

# --- Voting operations ---
async def add_vote(*args, **kwargs) -> bool:
    return await db_impl.add_vote(*args, **kwargs)

async def get_vote_results(*args, **kwargs) -> Dict[str, int]:
    return await db_impl.get_vote_results(*args, **kwargs)

async def update_player_reputation(*args, **kwargs) -> bool:
    return await db_impl.update_player_reputation(*args, **kwargs)

# --- Quiz operations ---
async def get_quiz_questions(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_quiz_questions(*args, **kwargs)

async def record_quiz_answer(*args, **kwargs) -> bool:
    return await db_impl.record_quiz_answer(*args, **kwargs)

# --- Init ---
async def init_db(*args, **kwargs) -> bool:
    return await db_impl.init_db(*args, **kwargs)

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

async def get_player_inventory(user_id: str) -> Dict[str, Any]:
    """Get player's inventory from the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_get_inventory(user_id)
        else:
            return await sqlite_get_inventory(user_id)
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {str(e)}")
        return {}

async def add_item_to_inventory(user_id: str, item_id: str, item_data: Dict[str, Any]) -> bool:
    """Add item to player's inventory in the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_add_item(user_id, item_id, item_data)
        else:
            return await sqlite_add_item(user_id, item_id, item_data)
    except Exception as e:
        logger.error(f"Error adding item to inventory for player {user_id}: {str(e)}")
        return False

async def remove_item_from_inventory(user_id: str, item_id: str) -> bool:
    """Remove item from player's inventory in the appropriate database."""
    try:
        if USE_DYNAMO:
            return await dynamo_remove_item(user_id, item_id)
        else:
            return await sqlite_remove_item(user_id, item_id)
    except Exception as e:
        logger.error(f"Error removing item from inventory for player {user_id}: {str(e)}")
        return False 