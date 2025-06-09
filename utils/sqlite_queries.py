"""
Queries e operações CRUD para o banco SQLite da Academia Tokugawa.
Importa helpers e schema de sqlite_schemas.py.
Todas as funções exportadas são async e delegam para funções internas síncronas.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from utils.sqlite_schemas import get_db, init_db

logger = logging.getLogger('tokugawa_bot')

# --- Player operations ---
def _get_player(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    player = cursor.fetchone()
    conn.close()
    if player:
        return dict(player)
    return None

async def get_player(user_id):
    return _get_player(user_id)

def _create_player(user_id, name, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO players (user_id, name, created_at, last_active)
        VALUES (?, ?, ?, ?)
        ''', (user_id, name, datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return False
    finally:
        conn.close()

async def create_player(user_id, name, **kwargs):
    return _create_player(user_id, name, **kwargs)

def _update_player(user_id, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    try:
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(user_id)
        sql = f'UPDATE players SET {", ".join(fields)} WHERE user_id = ?'
        cursor.execute(sql, values)
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False
    finally:
        conn.close()

async def update_player(user_id, **kwargs):
    return _update_player(user_id, **kwargs)

def _get_all_players():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.*, c.name as club_name 
    FROM players p
    LEFT JOIN clubs c ON p.club_id = c.club_id
    ''')
    players = cursor.fetchall()
    conn.close()
    return [dict(player) for player in players]

async def get_all_players():
    return _get_all_players()

# ... (continue with the rest of the CRUD functions from sqlite.py, adapting to import get_db and init_db from sqlite_schemas.py) 