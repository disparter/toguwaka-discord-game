import sqlite3
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from utils.db_provider import db_provider, DatabaseType

logger = logging.getLogger('tokugawa_bot')

# Database file path
DB_PATH = Path('data/tokugawa.db')

# Flag to indicate if we're running in AWS
IS_AWS = (
    os.environ.get('AWS_EXECUTION_ENV') is not None or  # Lambda
    os.environ.get('ECS_CONTAINER_METADATA_URI_V4') is not None or  # ECS
    os.environ.get('AWS_CONTAINER_CREDENTIALS_RELATIVE_URI') is not None  # ECS
)

# Flag to indicate if we should reset the database
RESET_DATABASE = os.environ.get('RESET_DATABASE', 'false').lower() == 'true'

def ensure_data_dir():
    """Ensure the data directory exists."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def reset_sqlite_db():
    """Reset the SQLite database by removing the file."""
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            logger.warning("SQLite database file has been reset")
            return True
        except Exception as e:
            logger.error(f"Error resetting SQLite database: {e}")
            return False
    return True  # File doesn't exist, so no need to reset

def init_default_clubs():
    """Initialize default clubs in the database."""
    from story_mode.club_system import ClubSystem
    
    club_system = ClubSystem()
    clubs = club_system.CLUBS
    leaders = club_system.CLUB_LEADERS
    
    for club_id, name in clubs.items():
        description = f"O {name} é um dos clubes mais prestigiados da Academia Tokugawa."
        leader_id = str(club_id)  # Using club_id as leader_id for now
        create_club(str(club_id), name, description, leader_id)

def init_db():
    """Initialize the database and create tables if they don't exist."""
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create players table
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

        # Create clubs table
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

        # Create system_flags table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_flags (
            flag_name TEXT PRIMARY KEY,
            flag_value TEXT,
            updated_at TEXT
        )
        ''')

        # Create events table
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

        # Create cooldowns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cooldowns (
            user_id TEXT,
            command TEXT,
            expiry_time TEXT,
            PRIMARY KEY (user_id, command)
        )
        ''')

        # Create grades table
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

        # Create votes table
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

        # Create quiz_answers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_answers (
            user_id TEXT,
            question_id TEXT,
            is_correct BOOLEAN,
            created_at TEXT,
            PRIMARY KEY (user_id, question_id)
        )
        ''')

        # Create club_activities table
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
        logger.info("Database initialized successfully")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

def handle_db_error(func):
    """Decorator to handle database errors and attempt fallback to SQLite if needed."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            
            # Try to fallback to SQLite if we're not already using it
            try:
                from utils.db_provider import db_provider
                if db_provider.current_db_type != DatabaseType.SQLITE:
                    if db_provider.fallback_to_sqlite():
                        # Retry the operation with SQLite
                        return func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Error during fallback to SQLite: {fallback_error}")
            
            # If we get here, either fallback failed or we're already using SQLite
            raise
    return wrapper

# Apply the error handler to all database functions
@handle_db_error
def get_player(user_id):
    """Get player data from the database.
    
    Args:
        user_id (str): The Discord user ID of the player
        
    Returns:
        dict: Player data if found, None otherwise
    """
    if not user_id:
        logger.warning("Attempted to get player with None or empty user_id")
        return None
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        logger.debug(f"Fetching player data for user_id: {user_id}")
        cursor.execute('''
        SELECT * FROM players WHERE user_id = ?
        ''', (str(user_id),))

        player = cursor.fetchone()
        if player:
            # Convert row to dict and parse JSON fields
            player_dict = dict(player)
            try:
                player_dict['inventory'] = json.loads(player_dict['inventory'])
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing inventory JSON for player {user_id}: {e}")
                player_dict['inventory'] = {}
            logger.debug(f"Successfully retrieved player data for {user_id}")
            return player_dict
            
        logger.debug(f"No player found for user_id: {user_id}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error while getting player {user_id}: {e}")
        return None
    finally:
        conn.close()

@handle_db_error
def create_player(user_id, name, **kwargs):
    """Create a new player in the database, supporting all fields."""
    if not user_id or not name:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check for duplicate
        cursor.execute('SELECT 1 FROM players WHERE user_id = ?', (str(user_id),))
        if cursor.fetchone():
            return False

        # Remove user_id and name from kwargs if present
        kwargs.pop('user_id', None)
        kwargs.pop('name', None)

        # Prepare columns and values
        columns = ['user_id', 'name']
        values = [str(user_id), str(name)]

        # List of all possible columns in the players table
        player_columns = [
            'power', 'level', 'exp', 'tusd', 'club_id', 'dexterity', 'intellect', 'charisma',
            'power_stat', 'reputation', 'hp', 'max_hp', 'inventory', 'strength_level', 'created_at', 'last_active'
        ]

        # Add default values for required fields
        defaults = {
            'power': kwargs.get('power', ''),
            'level': kwargs.get('level', 1),
            'exp': kwargs.get('exp', 0),
            'tusd': kwargs.get('tusd', 1000),
            'club_id': kwargs.get('club_id', None),
            'dexterity': kwargs.get('dexterity', 10),
            'intellect': kwargs.get('intellect', 10),
            'charisma': kwargs.get('charisma', 10),
            'power_stat': kwargs.get('power_stat', 10),
            'reputation': kwargs.get('reputation', 0),
            'hp': kwargs.get('hp', 100),
            'max_hp': kwargs.get('max_hp', 100),
            'inventory': kwargs.get('inventory', '{}'),
            'strength_level': kwargs.get('strength_level', 1),
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }

        # Add all columns and their values
        for col in player_columns:
            columns.append(col)
            value = kwargs.get(col, defaults[col])
            if col == 'inventory' and isinstance(value, dict):
                values.append(json.dumps(value))
            else:
                values.append(value)

        # Create the SQL query
        sql = f"INSERT INTO players ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(values))})"
        
        # Execute the query
        cursor.execute(sql, values)
        conn.commit()
        logger.info(f"Created new player: {name} (ID: {user_id})")
        return True
    except Exception as e:
        logger.error(f"Error creating player {user_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Continue applying @handle_db_error to all other database functions...

def sync_db_to_s3():
    """Sync the local database to S3 if running in AWS.

    The synchronization frequency is controlled by the DB_SYNC_INTERVAL_MINUTES
    environment variable. If not set, the default is 5 minutes.
    """
    # Skip sync if we're using DynamoDB
    from utils.db_provider import db_provider
    if db_provider.current_db_type == db_provider.DatabaseType.DYNAMODB:
        return True

    if not IS_AWS:
        return True

    try:
        # Check if enough time has passed since the last sync
        from datetime import datetime, timedelta

        # Get the sync interval from environment variable, default to 5 minutes
        sync_interval_minutes = int(os.environ.get('DB_SYNC_INTERVAL_MINUTES', '5'))

        # Get the last sync time from system flags
        last_sync_flag = "last_db_sync_time"
        last_sync_str = get_system_flag(last_sync_flag)

        # If we have a last sync time, check if enough time has passed
        if last_sync_str:
            last_sync_time = datetime.fromisoformat(last_sync_str)
            now = datetime.now()

            # If not enough time has passed, skip the sync
            time_since_last_sync = (now - last_sync_time).total_seconds() / 60
            if time_since_last_sync < sync_interval_minutes:
                # Only log if time since last sync is significant (more than 10 minutes)
                if time_since_last_sync > 10:
                    logger.info(f"Skipping database sync, last sync was {time_since_last_sync:.1f} minutes ago")
                return True

        from utils.s3_storage import upload_db_to_s3

        # Upload the database to S3
        if upload_db_to_s3():
            # Update the last sync time
            set_system_flag(last_sync_flag, datetime.now().isoformat())
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
    try:
        if db_provider._current_db_type == DatabaseType.DYNAMODB:
            from utils import dynamodb as db_impl
        else:
            from utils import database as db_impl
            
        return db_impl.update_player(user_id, **kwargs)
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        return False

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

def get_all_players():
    """Get all players from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
    SELECT p.*, c.name as club_name 
    FROM players p
    LEFT JOIN clubs c ON p.club_id = c.club_id
    ''')

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

def get_quiz_questions(player_data=None, category=None, attribute=None, count=3):
    """Get quiz questions based on player data, category, and/or attribute."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM quiz_questions WHERE 1=1"
    params = []

    # Filter by player level if player_data is provided
    if player_data:
        player_level = player_data.get('level', 1)
        query += " AND min_level <= ?"
        params.append(player_level)

    # Filter by category if provided
    if category:
        query += " AND category = ?"
        params.append(category)

    # Filter by attribute if provided
    if attribute:
        query += " AND attribute = ?"
        params.append(attribute)

    # If player data is provided, prioritize questions related to their strongest attributes
    if player_data:
        # Find player's strongest attribute
        attributes = {
            'intellect': player_data.get('intellect', 5),
            'charisma': player_data.get('charisma', 5),
            'dexterity': player_data.get('dexterity', 5),
            'power_stat': player_data.get('power_stat', 5)
        }
        strongest_attribute = max(attributes, key=attributes.get)

        # Order by matching the strongest attribute first, then by random
        query += f" ORDER BY CASE WHEN attribute = ? THEN 1 ELSE 2 END, RANDOM()"
        params.append(strongest_attribute)
    else:
        # Just random order if no player data
        query += " ORDER BY RANDOM()"

    # Limit the number of questions
    query += " LIMIT ?"
    params.append(count)

    cursor.execute(query, params)
    questions = cursor.fetchall()
    conn.close()

    result = []
    for q in questions:
        question_dict = dict(q)
        # Parse JSON options
        question_dict['options'] = json.loads(question_dict['options'])
        result.append(question_dict)

    return result

def record_quiz_answer(user_id, question_id, is_correct):
    """Record a quiz answer and award TUSD if correct."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get the question to determine the reward
        cursor.execute("SELECT tusd_reward FROM quiz_questions WHERE question_id = ?", (question_id,))
        question = cursor.fetchone()

        if not question:
            logger.error(f"Question with ID {question_id} not found")
            conn.close()
            return False

        tusd_reward = question[0] if is_correct else 0

        # Update player's TUSD if correct
        if is_correct and tusd_reward > 0:
            cursor.execute('''
            UPDATE players 
            SET tusd = tusd + ?
            WHERE user_id = ?
            ''', (tusd_reward, user_id))

            logger.info(f"Awarded {tusd_reward} TUSD to player {user_id} for correct quiz answer")

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error recording quiz answer: {e}")
        return False
    finally:
        conn.close()

def record_club_activity(user_id, activity_type, points=1):
    """Record a club activity for a player's club."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get player's club
        cursor.execute("SELECT club_id FROM players WHERE user_id = ?", (user_id,))
        player = cursor.fetchone()

        if not player or not player[0]:
            logger.info(f"Player {user_id} has no club, skipping activity recording")
            conn.close()
            return False

        club_id = player[0]

        # Get current week and year
        now = datetime.now()
        year, week, _ = now.isocalendar()

        # Record the activity
        cursor.execute('''
        INSERT INTO club_activities (club_id, user_id, activity_type, points, week, year)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (club_id, user_id, activity_type, points, week, year))

        logger.info(f"Recorded {activity_type} activity for club {club_id} by player {user_id}")

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error recording club activity: {e}")
        return False
    finally:
        conn.close()

def get_top_clubs_by_activity(week=None, year=None, limit=3):
    """Get top clubs by activity points for a specific week."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # If week and year are not provided, use current week
    if week is None or year is None:
        now = datetime.now()
        year, week, _ = now.isocalendar()

    try:
        cursor.execute('''
        SELECT c.club_id, c.name, c.description, SUM(ca.points) as total_points
        FROM clubs c
        JOIN club_activities ca ON c.club_id = ca.club_id
        WHERE ca.week = ? AND ca.year = ?
        GROUP BY c.club_id
        ORDER BY total_points DESC
        LIMIT ?
        ''', (week, year, limit))

        clubs = cursor.fetchall()
        return [dict(club) for club in clubs]
    except sqlite3.Error as e:
        logger.error(f"Error getting top clubs by activity: {e}")
        return []
    finally:
        conn.close()

def get_system_flag(flag_name):
    """Get the value of a system flag.

    Args:
        flag_name (str): The name of the flag to retrieve

    Returns:
        str: The value of the flag, or None if the flag doesn't exist
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT flag_value FROM system_flags
        WHERE flag_name = ?
        ''', (flag_name,))

        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"Error getting system flag {flag_name}: {e}")
        return None
    finally:
        conn.close()

def set_system_flag(flag_name, flag_value):
    """Set the value of a system flag.

    Args:
        flag_name (str): The name of the flag to set
        flag_value (str): The value to set for the flag

    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO system_flags (flag_name, flag_value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (flag_name, flag_value))

        conn.commit()
        logger.info(f"Set system flag {flag_name} to {flag_value}")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error setting system flag {flag_name}: {e}")
        return False
    finally:
        conn.close()

@handle_db_error
def update_club_reputation_weekly(club_id, reputation):
    """Update club reputation for the week."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE clubs SET reputation = ? WHERE club_id = ?', (int(reputation), str(club_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def store_event(event_id, name, description, event_type, channel_id, message_id, start_time, end_time, participants=None, data=None, completed=False):
    """Store an event in the database."""
    if not event_id or not name or not event_type or not channel_id or not start_time or not end_time:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Convert datetime objects to strings if needed
    if isinstance(start_time, datetime):
        start_time = start_time.isoformat()
    if isinstance(end_time, datetime):
        end_time = end_time.isoformat()
    # Convert participants list to JSON string
    if participants is None:
        participants = []
    participants_json = json.dumps(participants)
    # Convert data dict to JSON string
    if data is None:
        data = {}
    data_json = json.dumps(data)
    try:
        # Check for duplicate
        cursor.execute('SELECT 1 FROM events WHERE event_id = ?', (event_id,))
        if cursor.fetchone():
            return False
        cursor.execute('''
        INSERT INTO events (event_id, name, description, type, channel_id, message_id, start_time, end_time, completed, participants, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (event_id, name, description, event_type, channel_id, message_id, start_time, end_time, completed, participants_json, data_json))
        conn.commit()
        logger.info(f"Stored event {event_id} in database")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error storing event {event_id}: {e}")
        return False
    finally:
        conn.close()

@handle_db_error
def get_event(event_id):
    """Get event data from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM events WHERE event_id = ?', (str(event_id),))
        event = cursor.fetchone()
        if event:
            event_dict = dict(event)
            # Convert completed from int to bool
            if 'completed' in event_dict:
                event_dict['completed'] = bool(event_dict['completed'])
            return event_dict
        return None
    finally:
        conn.close()

def get_events_by_date(date=None, include_completed=True):
    """Get events for a specific date.

    Args:
        date (datetime, optional): The date to get events for. Defaults to today.
        include_completed (bool, optional): Whether to include completed events. Defaults to True.

    Returns:
        list: List of event dictionaries
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Default to today if no date provided
    if date is None:
        date = datetime.now().date()

    # Format date for SQL query (start and end of day)
    date_start = datetime.combine(date, datetime.min.time()).isoformat()
    date_end = datetime.combine(date, datetime.max.time()).isoformat()

    try:
        if include_completed:
            cursor.execute('''
            SELECT * FROM events 
            WHERE (start_time BETWEEN ? AND ?) OR (end_time BETWEEN ? AND ?)
            ORDER BY start_time ASC
            ''', (date_start, date_end, date_start, date_end))
        else:
            cursor.execute('''
            SELECT * FROM events 
            WHERE ((start_time BETWEEN ? AND ?) OR (end_time BETWEEN ? AND ?)) AND completed = 0
            ORDER BY start_time ASC
            ''', (date_start, date_end, date_start, date_end))

        events = cursor.fetchall()

        # Convert to list of dicts and parse JSON fields
        result = []
        for event in events:
            event_dict = dict(event)
            event_dict['participants'] = json.loads(event_dict['participants'])
            event_dict['data'] = json.loads(event_dict['data'])
            result.append(event_dict)

        return result
    except sqlite3.Error as e:
        logger.error(f"Error getting events for date {date}: {e}")
        return []
    finally:
        conn.close()

def update_event_status(event_id, completed=True, participants=None, data=None):
    """Update an event's status and data.

    Args:
        event_id (str): The ID of the event to update
        completed (bool, optional): Whether the event is completed. Defaults to True.
        participants (list, optional): Updated list of participants. Defaults to None.
        data (dict, optional): Updated event data. Defaults to None.

    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # First get the current event to update only specified fields
        current_event = get_event(event_id)
        if not current_event:
            logger.error(f"Event {event_id} not found for update")
            return False

        # Update participants if provided
        if participants is not None:
            participants_json = json.dumps(participants)
        else:
            participants_json = current_event['participants']
            if isinstance(participants_json, list):
                participants_json = json.dumps(participants_json)

        # Update data if provided
        if data is not None:
            data_json = json.dumps(data)
        else:
            data_json = current_event['data']
            if isinstance(data_json, dict):
                data_json = json.dumps(data_json)

        cursor.execute('''
        UPDATE events
        SET completed = ?, participants = ?, data = ?
        WHERE event_id = ?
        ''', (completed, participants_json, data_json, event_id))

        conn.commit()
        logger.info(f"Updated event {event_id} status to completed={completed}")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating event {event_id}: {e}")
        return False
    finally:
        conn.close()

def get_active_events():
    """Get all active (non-completed) events.

    Returns:
        dict: Dictionary of active events with event_id as keys
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT * FROM events WHERE completed = 0
        ''')

        events = cursor.fetchall()

        # Convert to dict of dicts with event_id as keys
        result = {}
        for event in events:
            event_dict = dict(event)
            event_dict['participants'] = json.loads(event_dict['participants'])
            event_dict['data'] = json.loads(event_dict['data'])

            # Format for compatibility with ACTIVE_EVENTS structure
            event_id = event_dict['event_id']
            result[event_id] = {
                'channel_id': event_dict['channel_id'],
                'message_id': event_dict['message_id'],
                'start_time': event_dict['start_time'],
                'end_time': event_dict['end_time'],
                'participants': event_dict['participants'],
                'data': event_dict['data']
            }

        return result
    except sqlite3.Error as e:
        logger.error(f"Error getting active events: {e}")
        return {}
    finally:
        conn.close()

def store_cooldown(user_id, command, expiry_time):
    """Store a cooldown in the database.

    Args:
        user_id (int): The user ID
        command (str): The command name
        expiry_time (float): Timestamp when the cooldown expires

    Returns:
        bool: True if successful, False otherwise
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert timestamp to datetime
    expiry_datetime = datetime.fromtimestamp(expiry_time).isoformat()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO cooldowns (user_id, command, expiry_time)
        VALUES (?, ?, ?)
        ''', (user_id, command, expiry_datetime))

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error storing cooldown for user {user_id}, command {command}: {e}")
        return False
    finally:
        conn.close()

def get_cooldowns(user_id=None):
    """Get cooldowns from the database.

    Args:
        user_id (int, optional): The user ID to get cooldowns for. If None, get all cooldowns.

    Returns:
        dict: Dictionary of cooldowns with user_id and command as keys
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        if user_id is not None:
            cursor.execute('''
            SELECT * FROM cooldowns WHERE user_id = ?
            ''', (user_id,))
        else:
            cursor.execute('''
            SELECT * FROM cooldowns
            ''')

        cooldowns = cursor.fetchall()

        # Convert to nested dict structure
        result = {}
        for cooldown in cooldowns:
            user_id = cooldown['user_id']
            command = cooldown['command']

            # Convert ISO format to timestamp
            expiry_time = datetime.fromisoformat(cooldown['expiry_time']).timestamp()

            if user_id not in result:
                result[user_id] = {}

            result[user_id][command] = expiry_time

        return result
    except sqlite3.Error as e:
        logger.error(f"Error getting cooldowns: {e}")
        return {}
    finally:
        conn.close()

def clear_expired_cooldowns():
    """Remove expired cooldowns from the database.

    Returns:
        int: Number of cooldowns removed
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()

        cursor.execute('''
        DELETE FROM cooldowns WHERE expiry_time < ?
        ''', (now,))

        removed = cursor.rowcount
        conn.commit()

        if removed > 0:
            logger.info(f"Removed {removed} expired cooldowns")

        return removed
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error clearing expired cooldowns: {e}")
        return 0
    finally:
        conn.close()

def get_club_members(club_id):
    """Get all players who are members of a specific club.

    Args:
        club_id (int): The ID of the club

    Returns:
        list: List of player dictionaries who are members of the club
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT user_id, name, level, power 
        FROM players 
        WHERE club_id = ?
        ORDER BY level DESC, name ASC
        ''', (club_id,))

        members = cursor.fetchall()
        return [dict(member) for member in members]
    except sqlite3.Error as e:
        logger.error(f"Error getting club members for club {club_id}: {e}")
        return []
    finally:
        conn.close()

def get_relevant_npcs(club_id):
    """Get all NPCs that are relevant to a specific club.
    Reads NPCs from the npcs.json file and returns those with matching club_id.
    Also includes hardcoded NPCs for each club for backward compatibility.

    Args:
        club_id (int): The ID of the club

    Returns:
        list: List of NPC dictionaries relevant to the club
    """
    # Hardcoded NPCs for each club (for backward compatibility)
    club_npcs = {
        1: [  # Clube das Chamas
            {"name": "Mestre Kaji", "role": "Mentor"},
            {"name": "Akira Himura", "role": "Veterano"}
        ],
        2: [  # Ilusionistas Mentais
            {"name": "Professora Yumiko", "role": "Mentora"},
            {"name": "Hiro Nakamura", "role": "Veterano"}
        ],
        3: [  # Conselho Político
            {"name": "Diretor Tanaka", "role": "Mentor"},
            {"name": "Miyuki Sato", "role": "Veterana"}
        ],
        4: [  # Elementalistas
            {"name": "Dr. Mizuki", "role": "Mentor"},
            {"name": "Kaito Watanabe", "role": "Veterano"}
        ],
        5: [  # Clube de Combate
            {"name": "Sensei Takeshi", "role": "Mentor"},
            {"name": "Ryu Kobayashi", "role": "Veterano"}
        ]
    }

    # Get NPCs from npcs.json file
    npcs_from_file = []
    try:
        import os
        import json
        npcs_file_path = os.path.join('data', 'story_mode', 'npcs', 'npcs.json')
        if os.path.exists(npcs_file_path):
            with open(npcs_file_path, 'r') as f:
                npcs_data = json.load(f)

                # Find NPCs with matching club_id
                for npc_id, npc in npcs_data.items():
                    if npc.get('club_id') == club_id:
                        # Check if this NPC is a club leader
                        if npc_id == "lider_conselho_politico" or "leader" in npc_id.lower():
                            role = "Líder"
                        else:
                            role = npc.get('type', 'Membro').capitalize()

                        npcs_from_file.append({
                            "name": npc.get('name', 'Unknown'),
                            "role": role
                        })
    except Exception as e:
        logger.error(f"Error loading NPCs from file: {e}")

    # Combine hardcoded NPCs with NPCs from file
    result = club_npcs.get(club_id, []) + npcs_from_file

    return result

@handle_db_error
def create_club(club_id, name, description, leader_id, **kwargs):
    """Create a new club in the database."""
    if not club_id or not name or not leader_id:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check for duplicate
        cursor.execute('SELECT 1 FROM clubs WHERE club_id = ?', (str(club_id),))
        if cursor.fetchone():
            return False
        cursor.execute('''
        INSERT INTO clubs (club_id, name, description, leader_id)
        VALUES (?, ?, ?, ?)''', (str(club_id), str(name), str(description), str(leader_id)))
        conn.commit()
        return True
    finally:
        conn.close()

@handle_db_error
def create_item(item_id, name, description, type, rarity, price, effects, **kwargs):
    """Create a new item in the database."""
    if not item_id or not name or not type or not rarity or price is None:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check for duplicate
        cursor.execute('SELECT 1 FROM items WHERE item_id = ?', (str(item_id),))
        if cursor.fetchone():
            return False
        effects_json = json.dumps(effects) if isinstance(effects, dict) else effects
        cursor.execute('''
        INSERT INTO items (item_id, name, description, type, rarity, price, effects)
        VALUES (?, ?, ?, ?, ?, ?, ?)''', (str(item_id), str(name), str(description), str(type), str(rarity), int(price), effects_json))
        conn.commit()
        return True
    finally:
        conn.close()

@handle_db_error
def add_item_to_inventory(user_id, item_id, quantity, **kwargs):
    """Add an item to a player's inventory in the database."""
    if not user_id or not item_id or quantity is None:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check player exists
        cursor.execute('SELECT inventory FROM players WHERE user_id = ?', (str(user_id),))
        row = cursor.fetchone()
        if not row:
            return False
        # Check item exists
        cursor.execute('SELECT 1 FROM items WHERE item_id = ?', (str(item_id),))
        if not cursor.fetchone():
            return False
        inventory = json.loads(row[0]) if row[0] else {}
        inventory[str(item_id)] = inventory.get(str(item_id), 0) + int(quantity)
        cursor.execute('UPDATE players SET inventory = ? WHERE user_id = ?', (json.dumps(inventory), str(user_id)))
        conn.commit()
        return True
    finally:
        conn.close()

@handle_db_error
def list_item_for_sale(item_id, seller_id, price, **kwargs):
    """List an item for sale in the market."""
    if not item_id or not seller_id or price is None:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check item exists
        cursor.execute('SELECT 1 FROM items WHERE item_id = ?', (str(item_id),))
        if not cursor.fetchone():
            return False
        # Check seller exists
        cursor.execute('SELECT 1 FROM players WHERE user_id = ?', (str(seller_id),))
        if not cursor.fetchone():
            return False
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS market (
            item_id TEXT,
            seller_id TEXT,
            price INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (item_id, seller_id)
        )''')
        # Check for duplicate
        cursor.execute('SELECT 1 FROM market WHERE item_id = ? AND seller_id = ?', (str(item_id), str(seller_id)))
        if cursor.fetchone():
            return False
        cursor.execute('''
        INSERT INTO market (item_id, seller_id, price)
        VALUES (?, ?, ?)''', (str(item_id), str(seller_id), int(price)))
        conn.commit()
        return True
    finally:
        conn.close()

@handle_db_error
def get_item(item_id, **kwargs):
    """Get item data from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM items WHERE item_id = ?', (str(item_id),))
        item = cursor.fetchone()
        if item:
            item_dict = dict(item)
            item_dict['effects'] = json.loads(item_dict['effects']) if item_dict['effects'] else {}
            return item_dict
        return None
    finally:
        conn.close()

@handle_db_error
def get_market_listing(item_id, seller_id, **kwargs):
    """Get a market listing from the SQLite market table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute('''
        SELECT * FROM market WHERE item_id = ? AND seller_id = ?
        ''', (str(item_id), str(seller_id)))
        listing = cursor.fetchone()
        if listing:
            return dict(listing)
        return None
    finally:
        conn.close()

@handle_db_error
def update_item(item_id, **kwargs):
    """Update item fields in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(str(item_id))
        sql = f'UPDATE items SET {", ".join(fields)} WHERE item_id = ?'
        cursor.execute(sql, values)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

@handle_db_error
def get_player_inventory(user_id, **kwargs):
    """Get player's inventory as a dict."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT inventory FROM players WHERE user_id = ?', (str(user_id),))
        row = cursor.fetchone()
        if row and row[0]:
            return json.loads(row[0])
        return {}
    finally:
        conn.close()

@handle_db_error
def update_market_listing(item_id, seller_id, **kwargs):
    """Update a market listing (e.g., price) in the SQLite market table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        values.extend([str(item_id), str(seller_id)])
        sql = f'UPDATE market SET {", ".join(fields)} WHERE item_id = ? AND seller_id = ?'
        cursor.execute(sql, values)
        conn.commit()
        return True
    finally:
        conn.close()

@handle_db_error
def update_inventory_item_quantity(user_id, item_id, quantity, **kwargs):
    """Update the quantity of an item in a player's inventory."""
    if not user_id or not item_id or quantity is None:
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check player exists
        cursor.execute('SELECT inventory FROM players WHERE user_id = ?', (str(user_id),))
        row = cursor.fetchone()
        if not row:
            return False
        # Check item exists
        cursor.execute('SELECT 1 FROM items WHERE item_id = ?', (str(item_id),))
        if not cursor.fetchone():
            return False
        inventory = json.loads(row[0]) if row[0] else {}
        if str(item_id) not in inventory:
            return False
        inventory[str(item_id)] = int(quantity)
        cursor.execute('UPDATE players SET inventory = ? WHERE user_id = ?', (json.dumps(inventory), str(user_id)))
        conn.commit()
        return True
    finally:
        conn.close()

def add_strength_level_column():
    """Add strength_level column to players table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(players)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'strength_level' not in columns:
            cursor.execute('ALTER TABLE players ADD COLUMN strength_level INTEGER DEFAULT 1')
            conn.commit()
            logger.info("Added strength_level column to players table")
            return True
        return False
    except sqlite3.Error as e:
        logger.error(f"Error adding strength_level column: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# Helper to reset SQLite DB (for schema updates)
def reset_sqlite_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

# Initialize the database when the module is imported
init_db()
# Add strength_level column if it doesn't exist
add_strength_level_column()
