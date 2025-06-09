"""
Schema e configuração do banco SQLite da Academia Tokugawa.
"""

import sqlite3
import logging
import os
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

# Ensure data directory exists
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

DB_PATH = data_dir / 'tokugawa.db'

def get_db():
    """Get a database connection with proper configuration."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with proper schema and constraints."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Players table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            power TEXT,
            level INTEGER NOT NULL DEFAULT 1,
            exp INTEGER NOT NULL DEFAULT 0,
            tusd INTEGER NOT NULL DEFAULT 1000,
            club_id TEXT,
            dexterity INTEGER NOT NULL DEFAULT 10,
            intellect INTEGER NOT NULL DEFAULT 10,
            charisma INTEGER NOT NULL DEFAULT 10,
            power_stat INTEGER NOT NULL DEFAULT 10,
            reputation INTEGER NOT NULL DEFAULT 0,
            hp INTEGER NOT NULL DEFAULT 100,
            max_hp INTEGER NOT NULL DEFAULT 100,
            strength_level INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL,
            FOREIGN KEY (club_id) REFERENCES clubs(club_id) ON DELETE SET NULL,
            CHECK (level >= 1),
            CHECK (exp >= 0),
            CHECK (tusd >= 0),
            CHECK (dexterity >= 1 AND dexterity <= 10),
            CHECK (intellect >= 1 AND intellect <= 10),
            CHECK (charisma >= 1 AND charisma <= 10),
            CHECK (power_stat >= 1 AND power_stat <= 10),
            CHECK (reputation >= 0),
            CHECK (hp >= 0),
            CHECK (max_hp >= hp),
            CHECK (strength_level >= 1)
        )
        ''')
        
        # Inventory table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            item_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            item_data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
        )
        ''')
        
        # Clubs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            club_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            leader_id TEXT NOT NULL,
            reputation INTEGER NOT NULL DEFAULT 0,
            members_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_active TEXT NOT NULL,
            FOREIGN KEY (leader_id) REFERENCES players(user_id) ON DELETE CASCADE,
            CHECK (reputation >= 0),
            CHECK (members_count >= 0)
        )
        ''')
        
        # System flags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_flags (
            flag_name TEXT PRIMARY KEY,
            flag_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0,
            participants TEXT NOT NULL DEFAULT '[]',
            data TEXT NOT NULL DEFAULT '{}',
            CHECK (completed IN (0, 1))
        )
        ''')
        
        # Cooldowns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id TEXT NOT NULL,
            command TEXT NOT NULL,
            expiry_time TEXT NOT NULL,
            PRIMARY KEY (user_id, command),
            FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
        )
        ''')
        
        # Commit transaction
        conn.commit()
        logger.info("Database schema initialized successfully")
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Error initializing database schema: {e}")
        raise
    finally:
        conn.close()

# Initialize database on module import
init_db() 