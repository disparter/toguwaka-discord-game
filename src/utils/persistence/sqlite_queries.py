"""
Queries e operações CRUD para o banco SQLite da Academia Tokugawa.
Importa helpers e schema de sqlite_schemas.py.
Todas as funções exportadas são async e delegam para funções internas síncronas.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.utils.sqlite_schemas import get_db, init_db

logger = logging.getLogger('tokugawa_bot')

# Default values for player attributes
DEFAULT_PLAYER_VALUES = {
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
    'strength_level': 1
}

def _ensure_default_values(player_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all default values are present in player dictionary."""
    if not player_dict:
        return DEFAULT_PLAYER_VALUES.copy()
    
    for key, value in DEFAULT_PLAYER_VALUES.items():
        if key not in player_dict or player_dict[key] is None:
            player_dict[key] = value
    return player_dict

# --- Player operations ---
def _get_player(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
        player = cursor.fetchone()
        if player:
            player_dict = _ensure_default_values(dict(player))
            # Get inventory items
            cursor.execute("SELECT item_id, item_data FROM inventory WHERE user_id = ?", (user_id,))
            inventory_items = cursor.fetchall()
            player_dict['inventory'] = {item['item_id']: json.loads(item['item_data']) for item in inventory_items}
            return player_dict
        return None
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {e}")
        return None
    finally:
        conn.close()

async def get_player(user_id):
    return _get_player(user_id)

def _create_player(user_id, name, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Prepare player data with defaults
        player_data = {
            'user_id': user_id,
            'name': name,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            **DEFAULT_PLAYER_VALUES,
            **kwargs  # Override defaults with provided values
        }
        
        # Remove inventory from player data if present
        inventory = player_data.pop('inventory', {})
        
        # Build SQL query dynamically
        fields = ', '.join(player_data.keys())
        placeholders = ', '.join(['?' for _ in player_data])
        values = list(player_data.values())
        
        cursor.execute(f'''
        INSERT INTO players ({fields})
        VALUES ({placeholders})
        ''', values)
        
        # Insert inventory items if any
        if inventory:
            now = datetime.now().isoformat()
            for item_id, item_data in inventory.items():
                cursor.execute('''
                INSERT INTO inventory (item_id, user_id, item_data, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ''', (item_id, user_id, json.dumps(item_data), now, now))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error creating player {user_id}: {e}")
        return False
    finally:
        conn.close()

async def create_player(user_id, name, **kwargs):
    return _create_player(user_id, name, **kwargs)

def _update_player(user_id, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Get current player data
        current_player = _get_player(user_id)
        if not current_player:
            return False
            
        # Handle inventory separately
        inventory = kwargs.pop('inventory', None)
        
        # Update player fields
        fields = []
        values = []
        for k, v in kwargs.items():
            if k in DEFAULT_PLAYER_VALUES or k in current_player:
                fields.append(f"{k} = ?")
                values.append(v)
        
        if fields:
            values.append(user_id)
            sql = f'UPDATE players SET {", ".join(fields)} WHERE user_id = ?'
            cursor.execute(sql, values)
        
        # Update inventory if provided
        if inventory is not None:
            # Delete existing inventory
            cursor.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
            
            # Insert new inventory items
            now = datetime.now().isoformat()
            for item_id, item_data in inventory.items():
                cursor.execute('''
                INSERT INTO inventory (item_id, user_id, item_data, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ''', (item_id, user_id, json.dumps(item_data), now, now))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error updating player {user_id}: {e}")
        return False
    finally:
        conn.close()

async def update_player(user_id, **kwargs):
    return _update_player(user_id, **kwargs)

def _get_all_players():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM players")
        players = cursor.fetchall()
        result = []
        for player in players:
            player_dict = _ensure_default_values(dict(player))
            # Get inventory items
            cursor.execute("SELECT item_id, item_data FROM inventory WHERE user_id = ?", (player['user_id'],))
            inventory_items = cursor.fetchall()
            player_dict['inventory'] = {item['item_id']: json.loads(item['item_data']) for item in inventory_items}
            result.append(player_dict)
        return result
    except Exception as e:
        logger.error(f"Error getting all players: {e}")
        return []
    finally:
        conn.close()

async def get_all_players():
    return _get_all_players()

# --- Inventory operations ---
def _get_player_inventory(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT item_id, item_data FROM inventory WHERE user_id = ?", (user_id,))
        items = cursor.fetchall()
        return {item['item_id']: json.loads(item['item_data']) for item in items}
    except Exception as e:
        logger.error(f"Error getting inventory for player {user_id}: {e}")
        return {}
    finally:
        conn.close()

async def get_player_inventory(user_id):
    return _get_player_inventory(user_id)

def _add_item_to_inventory(user_id, item_id, item_data):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        now = datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO inventory (item_id, user_id, item_data, created_at, last_updated)
        VALUES (?, ?, ?, ?, ?)
        ''', (item_id, user_id, json.dumps(item_data), now, now))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error adding item {item_id} to inventory for player {user_id}: {e}")
        return False
    finally:
        conn.close()

async def add_item_to_inventory(user_id, item_id, item_data):
    return _add_item_to_inventory(user_id, item_id, item_data)

def _remove_item_from_inventory(user_id, item_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        cursor.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error removing item {item_id} from inventory for player {user_id}: {e}")
        return False
    finally:
        conn.close()

async def remove_item_from_inventory(user_id, item_id):
    return _remove_item_from_inventory(user_id, item_id)

# --- Club operations ---
def _get_club(club_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM clubs WHERE club_id = ?", (club_id,))
        club = cursor.fetchone()
        return dict(club) if club else None
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {e}")
        return None
    finally:
        conn.close()

async def get_club(club_id):
    return _get_club(club_id)

def _get_all_clubs():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM clubs")
        clubs = cursor.fetchall()
        return [dict(club) for club in clubs]
    except Exception as e:
        logger.error(f"Error getting all clubs: {e}")
        return []
    finally:
        conn.close()

async def get_all_clubs():
    return _get_all_clubs()

# --- Cooldown operations ---
def _store_cooldown(user_id, command, duration_seconds):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        expiry_time = (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
        
        cursor.execute('''
        INSERT OR REPLACE INTO cooldowns (user_id, command, expiry_time)
        VALUES (?, ?, ?)
        ''', (user_id, command, expiry_time))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error storing cooldown for user {user_id}, command {command}: {e}")
        return False
    finally:
        conn.close()

async def store_cooldown(user_id, command, duration_seconds):
    return _store_cooldown(user_id, command, duration_seconds)

def _get_cooldowns(user_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT command, expiry_time FROM cooldowns WHERE user_id = ?", (user_id,))
        cooldowns = cursor.fetchall()
        return {row['command']: row['expiry_time'] for row in cooldowns}
    except Exception as e:
        logger.error(f"Error getting cooldowns for user {user_id}: {e}")
        return {}
    finally:
        conn.close()

async def get_cooldowns(user_id):
    return _get_cooldowns(user_id)

def _clear_expired_cooldowns():
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        now = datetime.now().isoformat()
        cursor.execute("DELETE FROM cooldowns WHERE expiry_time < ?", (now,))
        
        # Commit transaction
        conn.commit()
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error clearing expired cooldowns: {e}")
        return False
    finally:
        conn.close()

async def clear_expired_cooldowns():
    return _clear_expired_cooldowns() 