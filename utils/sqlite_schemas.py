"""
Schemas e helpers para o banco SQLite da Academia Tokugawa.
Inclui funções de inicialização e helpers de conexão.
O arquivo do banco agora é 'tokugawa.db' na raiz do projeto.
"""

import os
import sqlite3
import logging

logger = logging.getLogger('tokugawa_bot')

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'tokugawa.db')
DB_PATH = os.path.abspath(DB_PATH)

def ensure_data_dir():
    # Não precisa criar pasta, banco está na raiz
    pass

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            power TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            tusd INTEGER DEFAULT 1000,
            club_id TEXT,
            dexterity INTEGER DEFAULT 10,
            intellect INTEGER DEFAULT 10,
            charisma INTEGER DEFAULT 10,
            power_stat INTEGER DEFAULT 10,
            reputation INTEGER DEFAULT 0,
            hp INTEGER DEFAULT 100,
            max_hp INTEGER DEFAULT 100,
            inventory TEXT DEFAULT '{}',
            strength_level INTEGER DEFAULT 1,
            created_at TEXT,
            last_active TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clubs (
            club_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            leader_id TEXT,
            reputation INTEGER DEFAULT 0,
            members_count INTEGER DEFAULT 0
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_flags (
            flag_name TEXT PRIMARY KEY,
            flag_value TEXT,
            updated_at TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            type TEXT,
            channel_id TEXT,
            message_id TEXT,
            start_time TEXT,
            end_time TEXT,
            completed BOOLEAN DEFAULT 0,
            participants TEXT DEFAULT '[]',
            data TEXT DEFAULT '{}'
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id TEXT,
            command TEXT,
            expiry_time TEXT,
            PRIMARY KEY (user_id, command)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            user_id TEXT,
            subject TEXT,
            grade INTEGER,
            month INTEGER,
            year INTEGER,
            created_at TEXT,
            PRIMARY KEY (user_id, subject, month, year)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            category TEXT,
            voter_id TEXT,
            candidate_id TEXT,
            week INTEGER,
            year INTEGER,
            created_at TEXT,
            PRIMARY KEY (category, voter_id, week, year)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_answers (
            user_id TEXT,
            question_id TEXT,
            is_correct BOOLEAN,
            created_at TEXT,
            PRIMARY KEY (user_id, question_id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS club_activities (
            user_id TEXT,
            activity_type TEXT,
            points INTEGER,
            week INTEGER,
            year INTEGER,
            created_at TEXT,
            PRIMARY KEY (user_id, activity_type, week, year)
        )
        ''')
        conn.commit()
        logger.info("SQLite database initialized successfully")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error initializing SQLite database: {e}")
        return False
    finally:
        conn.close() 