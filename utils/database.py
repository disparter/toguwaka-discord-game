import sqlite3
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

# Database file path
DB_PATH = Path('data/tokugawa.db')

def ensure_data_dir():
    """Ensure the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize the database with required tables."""
    ensure_data_dir()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create players table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        power TEXT NOT NULL,
        strength_level INTEGER NOT NULL,
        club_id INTEGER,
        level INTEGER DEFAULT 1,
        exp INTEGER DEFAULT 0,
        tusd INTEGER DEFAULT 100,
        dexterity INTEGER DEFAULT 5,
        intellect INTEGER DEFAULT 5,
        charisma INTEGER DEFAULT 5,
        power_stat INTEGER DEFAULT 5,
        inventory TEXT DEFAULT '{}',
        techniques TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (club_id) REFERENCES clubs(club_id)
    )
    ''')
    
    # Create clubs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clubs (
        club_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        leader_id INTEGER,
        members_count INTEGER DEFAULT 0,
        reputation INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (leader_id) REFERENCES players(user_id)
    )
    ''')
    
    # Create duels table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS duels (
        duel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenger_id INTEGER NOT NULL,
        opponent_id INTEGER NOT NULL,
        winner_id INTEGER,
        loser_id INTEGER,
        duel_type TEXT NOT NULL,
        duel_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (challenger_id) REFERENCES players(user_id),
        FOREIGN KEY (opponent_id) REFERENCES players(user_id),
        FOREIGN KEY (winner_id) REFERENCES players(user_id),
        FOREIGN KEY (loser_id) REFERENCES players(user_id)
    )
    ''')
    
    # Create items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        type TEXT NOT NULL,
        rarity TEXT NOT NULL,
        price INTEGER NOT NULL,
        effects TEXT DEFAULT '{}'
    )
    ''')
    
    # Create events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        start_date TIMESTAMP,
        end_date TIMESTAMP,
        active BOOLEAN DEFAULT 0,
        participants TEXT DEFAULT '[]'
    )
    ''')
    
    # Insert default clubs
    default_clubs = [
        (1, "Clube das Chamas", "Mestres do fogo e das artes marciais explosivas.", None, 0, 100),
        (2, "Ilusionistas Mentais", "Especialistas em poderes psíquicos e manipulação mental.", None, 0, 100),
        (3, "Conselho Político", "Líderes estrategistas que controlam a política estudantil.", None, 0, 100),
        (4, "Elementalistas", "Dominam os elementos da natureza com precisão científica.", None, 0, 100),
        (5, "Clube de Combate", "Focados em aperfeiçoar técnicas de luta e duelos táticos.", None, 0, 100)
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO clubs (club_id, name, description, leader_id, members_count, reputation)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', default_clubs)
    
    conn.commit()
    conn.close()
    
    logger.info("Database initialized successfully")

def get_player(user_id):
    """Get player data from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
    player = cursor.fetchone()
    
    conn.close()
    
    if player:
        # Convert JSON strings to dictionaries
        player_dict = dict(player)
        player_dict['inventory'] = json.loads(player_dict['inventory'])
        player_dict['techniques'] = json.loads(player_dict['techniques'])
        return player_dict
    
    return None

def create_player(user_id, name, power, strength_level, club_id):
    """Create a new player in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO players (user_id, name, power, strength_level, club_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, name, power, strength_level, club_id))
        
        # Update club members count
        cursor.execute('''
        UPDATE clubs SET members_count = members_count + 1
        WHERE club_id = ?
        ''', (club_id,))
        
        conn.commit()
        logger.info(f"Created new player: {name} (ID: {user_id})")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error creating player: {e}")
        return False
    finally:
        conn.close()

def update_player(user_id, **kwargs):
    """Update player data in the database."""
    if not kwargs:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build the SET part of the query
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    values = list(kwargs.values())
    values.append(user_id)
    
    try:
        cursor.execute(f'''
        UPDATE players SET {set_clause}, last_active = CURRENT_TIMESTAMP
        WHERE user_id = ?
        ''', values)
        
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating player: {e}")
        return False
    finally:
        conn.close()

def get_club(club_id):
    """Get club data from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clubs WHERE club_id = ?", (club_id,))
    club = cursor.fetchone()
    
    conn.close()
    
    if club:
        return dict(club)
    
    return None

def get_all_clubs():
    """Get all clubs from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM clubs ORDER BY reputation DESC")
    clubs = cursor.fetchall()
    
    conn.close()
    
    return [dict(club) for club in clubs]

def get_top_players(limit=10):
    """Get top players by level and exp."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT p.*, c.name as club_name 
    FROM players p
    LEFT JOIN clubs c ON p.club_id = c.club_id
    ORDER BY p.level DESC, p.exp DESC
    LIMIT ?
    ''', (limit,))
    
    players = cursor.fetchall()
    conn.close()
    
    return [dict(player) for player in players]

# Initialize the database when the module is imported
init_db()