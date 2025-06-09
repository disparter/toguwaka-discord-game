"""
Database provider for Academia Tokugawa.

Este módulo é a ÚNICA interface pública para acesso ao banco de dados.
Ele delega para DynamoDB se USE_DYNAMO=True, ou para SQLite se USE_DYNAMO=False.
Não há fallback automático. O resto do código deve importar APENAS deste provider.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger('tokugawa_bot')

USE_DYNAMO = os.environ.get('USE_DYNAMO', 'false').lower() == 'true'

if USE_DYNAMO:
    from utils import dynamodb as db_impl
    logger.info('Database provider: DynamoDB')
else:
    from utils import sqlite_queries as db_impl
    logger.info('Database provider: SQLite')

# --- Player operations ---
async def get_player(*args, **kwargs) -> Optional[Dict[str, Any]]:
    return await db_impl.get_player(*args, **kwargs)

async def create_player(*args, **kwargs) -> bool:
    return await db_impl.create_player(*args, **kwargs)

async def update_player(*args, **kwargs) -> bool:
    return await db_impl.update_player(*args, **kwargs)

async def get_all_players(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_all_players(*args, **kwargs)

# --- Club operations ---
async def get_club(*args, **kwargs) -> Optional[Dict[str, Any]]:
    return await db_impl.get_club(*args, **kwargs)

async def get_all_clubs(*args, **kwargs) -> List[Dict[str, Any]]:
    return await db_impl.get_all_clubs(*args, **kwargs)

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