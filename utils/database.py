import sqlite3
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

# Database file path
DB_PATH = Path('data/tokugawa.db')

# Flag to indicate if we're running in AWS
IS_AWS = os.environ.get('AWS_EXECUTION_ENV') is not None

def ensure_data_dir():
    """Ensure the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize the database with required tables."""
    ensure_data_dir()

    # If running in AWS, try to download the database from S3
    if IS_AWS:
        try:
            from utils.s3_storage import download_db_from_s3, ensure_s3_bucket_exists

            # Ensure the S3 bucket exists
            if ensure_s3_bucket_exists():
                # Try to download the database from S3
                if download_db_from_s3():
                    logger.info("Downloaded database from S3")
                else:
                    logger.warning("Failed to download database from S3, will create a new one")
            else:
                logger.warning("Failed to ensure S3 bucket exists, will create a local database")
        except ImportError:
            logger.warning("s3_storage module not available, skipping S3 download")
        except Exception as e:
            logger.error(f"Error downloading database from S3: {e}")

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
        reputation INTEGER DEFAULT 0,
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

    # Create subjects_grades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects_grades (
        grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        grade REAL DEFAULT 0,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES players(user_id),
        UNIQUE(user_id, subject, month, year)
    )
    ''')

    # Create voting table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voting (
        vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        voter_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        week INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (voter_id) REFERENCES players(user_id),
        FOREIGN KEY (candidate_id) REFERENCES players(user_id),
        UNIQUE(voter_id, category, week, year)
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
        result = True

        # Sync to S3 if running in AWS
        if IS_AWS and result:
            sync_db_to_s3()

        return result
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error creating player: {e}")
        return False
    finally:
        conn.close()

def sync_db_to_s3():
    """Sync the local database to S3 if running in AWS."""
    if not IS_AWS:
        return True

    try:
        from utils.s3_storage import upload_db_to_s3

        # Upload the database to S3
        if upload_db_to_s3():
            logger.info("Uploaded database to S3")
            return True
        else:
            logger.warning("Failed to upload database to S3")
            return False
    except ImportError:
        logger.warning("s3_storage module not available, skipping S3 upload")
        return False
    except Exception as e:
        logger.error(f"Error uploading database to S3: {e}")
        return False

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
        result = cursor.rowcount > 0

        # Sync to S3 if running in AWS
        if IS_AWS and result:
            sync_db_to_s3()

        return result
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

def get_player_grades(user_id, subject=None, month=None, year=None):
    """Get player grades from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM subjects_grades WHERE user_id = ?"
    params = [user_id]

    if subject:
        query += " AND subject = ?"
        params.append(subject)

    if month:
        query += " AND month = ?"
        params.append(month)

    if year:
        query += " AND year = ?"
        params.append(year)

    cursor.execute(query, params)
    grades = cursor.fetchall()

    conn.close()

    return [dict(grade) for grade in grades]

def update_player_grade(user_id, subject, grade, month, year):
    """Update or insert player grade in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Try to update existing grade
        cursor.execute('''
        UPDATE subjects_grades 
        SET grade = ?
        WHERE user_id = ? AND subject = ? AND month = ? AND year = ?
        ''', (grade, user_id, subject, month, year))

        # If no rows were updated, insert a new grade
        if cursor.rowcount == 0:
            cursor.execute('''
            INSERT INTO subjects_grades (user_id, subject, grade, month, year)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, subject, grade, month, year))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating player grade: {e}")
        return False
    finally:
        conn.close()

def get_monthly_average_grades(user_id, month, year):
    """Get player's average grades for a specific month."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    SELECT subject, AVG(grade) as average_grade
    FROM subjects_grades
    WHERE user_id = ? AND month = ? AND year = ?
    GROUP BY subject
    ''', (user_id, month, year))

    averages = cursor.fetchall()
    conn.close()

    return [dict(avg) for avg in averages]

def add_vote(category, voter_id, candidate_id, week, year):
    """Add a vote in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Try to insert the vote
        cursor.execute('''
        INSERT INTO voting (category, voter_id, candidate_id, week, year)
        VALUES (?, ?, ?, ?, ?)
        ''', (category, voter_id, candidate_id, week, year))

        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # If the vote already exists, update it
        cursor.execute('''
        UPDATE voting
        SET candidate_id = ?
        WHERE category = ? AND voter_id = ? AND week = ? AND year = ?
        ''', (candidate_id, category, voter_id, week, year))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error adding vote: {e}")
        return False
    finally:
        conn.close()

def get_vote_results(category, week, year):
    """Get vote results for a specific category, week, and year."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    SELECT candidate_id, COUNT(*) as vote_count
    FROM voting
    WHERE category = ? AND week = ? AND year = ?
    GROUP BY candidate_id
    ORDER BY vote_count DESC
    ''', (category, week, year))

    results = cursor.fetchall()
    conn.close()

    return [dict(result) for result in results]

def update_player_reputation(user_id, reputation_change):
    """Update player reputation in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        UPDATE players
        SET reputation = reputation + ?
        WHERE user_id = ?
        ''', (reputation_change, user_id))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating player reputation: {e}")
        return False
    finally:
        conn.close()

def get_top_players_by_reputation(limit=10):
    """Get top players by reputation."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    SELECT p.*, c.name as club_name 
    FROM players p
    LEFT JOIN clubs c ON p.club_id = c.club_id
    ORDER BY p.reputation DESC, p.level DESC
    LIMIT ?
    ''', (limit,))

    players = cursor.fetchall()
    conn.close()

    return [dict(player) for player in players]

# Initialize the database when the module is imported
init_db()
