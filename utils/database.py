import sqlite3
import json
import os
import logging
from pathlib import Path
from datetime import datetime

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

    # Check if we need to add HP columns to existing players
    try:
        cursor.execute("PRAGMA table_info(players)")
        columns = cursor.fetchall()
        has_hp_column = any(col[1] == 'hp' for col in columns)
        has_max_hp_column = any(col[1] == 'max_hp' for col in columns)
        has_story_progress_column = any(col[1] == 'story_progress' for col in columns)

        if not has_hp_column:
            logger.info("Adding 'hp' column to players table")
            cursor.execute("ALTER TABLE players ADD COLUMN hp INTEGER DEFAULT 100")
            conn.commit()

        if not has_max_hp_column:
            logger.info("Adding 'max_hp' column to players table")
            cursor.execute("ALTER TABLE players ADD COLUMN max_hp INTEGER DEFAULT 100")
            conn.commit()

        if not has_story_progress_column:
            logger.info("Adding 'story_progress' column to players table")
            cursor.execute("ALTER TABLE players ADD COLUMN story_progress TEXT DEFAULT NULL")
            conn.commit()

        # Update existing players to have default HP values if they don't already
        cursor.execute("UPDATE players SET hp = 100 WHERE hp IS NULL")
        cursor.execute("UPDATE players SET max_hp = 100 WHERE max_hp IS NULL")
        conn.commit()

        rows_updated = cursor.rowcount
        if rows_updated > 0:
            logger.info(f"Updated {rows_updated} players with default HP values")
    except sqlite3.Error as e:
        logger.info(f"Checking players table for HP columns: {e}")
        # If there's an error, it will be handled by the CREATE TABLE statement below

    # Check if events table exists and if it has the completed column
    try:
        cursor.execute("PRAGMA table_info(events)")
        columns = cursor.fetchall()
        has_completed_column = any(col[1] == 'completed' for col in columns)

        if not has_completed_column:
            logger.info("Adding 'completed' column to events table")
            cursor.execute("ALTER TABLE events ADD COLUMN completed BOOLEAN DEFAULT 0")
            conn.commit()
    except sqlite3.Error as e:
        # If the table doesn't exist yet, this will be handled by the CREATE TABLE statement below
        logger.info(f"Checking events table: {e}")

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
        hp INTEGER DEFAULT 100,
        max_hp INTEGER DEFAULT 100,
        story_progress TEXT DEFAULT NULL,
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

    # Create enhanced events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT NOT NULL,
        channel_id INTEGER,
        message_id INTEGER,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        completed BOOLEAN DEFAULT 0,
        participants TEXT DEFAULT '[]',
        data TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create cooldowns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cooldowns (
        user_id INTEGER NOT NULL,
        command TEXT NOT NULL,
        expiry_time TIMESTAMP NOT NULL,
        PRIMARY KEY (user_id, command),
        FOREIGN KEY (user_id) REFERENCES players(user_id)
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

    # Create quiz_questions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quiz_questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        options TEXT NOT NULL,  -- JSON array of options
        correct_option INTEGER NOT NULL,
        difficulty INTEGER NOT NULL DEFAULT 1,
        category TEXT NOT NULL,  -- Subject or theme
        attribute TEXT,  -- Related player attribute (intellect, charisma, dexterity, power)
        min_level INTEGER DEFAULT 1,  -- Minimum player level for this question
        tusd_reward INTEGER DEFAULT 10,  -- TUSD reward for correct answer
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create club_activities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS club_activities (
        activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        club_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,  -- 'duel_win', 'exploration', etc.
        points INTEGER NOT NULL,  -- Contribution points
        week INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (club_id) REFERENCES clubs(club_id),
        FOREIGN KEY (user_id) REFERENCES players(user_id)
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

    # Create system_flags table for storing system-wide flags
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_flags (
        flag_name TEXT PRIMARY KEY,
        flag_value TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Insert default quiz questions
    default_questions = [
        # Intellect questions
        ("Qual é o símbolo químico do ouro?", json.dumps(["Au", "Ag", "Fe", "Cu"]), 0, 2, "Ciências", "intellect", 1, 15),
        ("Quem escreveu 'Dom Quixote'?", json.dumps(["Shakespeare", "Cervantes", "Machado de Assis", "Dante Alighieri"]), 1, 2, "Literatura", "intellect", 1, 15),
        ("Qual é a capital da Austrália?", json.dumps(["Sydney", "Melbourne", "Canberra", "Brisbane"]), 2, 2, "Geografia", "intellect", 1, 15),

        # Charisma questions
        ("Qual destas é uma técnica eficaz de comunicação?", json.dumps(["Interromper frequentemente", "Evitar contato visual", "Escuta ativa", "Falar muito rápido"]), 2, 2, "Comunicação", "charisma", 1, 15),
        ("O que significa empatia?", json.dumps(["Manipular emoções", "Capacidade de entender sentimentos alheios", "Esconder seus sentimentos", "Expressar raiva"]), 1, 2, "Psicologia", "charisma", 1, 15),

        # Dexterity questions
        ("Qual esporte utiliza mais a coordenação motora fina?", json.dumps(["Futebol", "Tiro com arco", "Natação", "Corrida"]), 1, 2, "Esportes", "dexterity", 1, 15),
        ("Qual instrumento musical requer maior destreza manual?", json.dumps(["Bateria", "Violino", "Flauta", "Piano"]), 1, 2, "Música", "dexterity", 1, 15),

        # Power questions
        ("Qual exercício é melhor para desenvolver força?", json.dumps(["Yoga", "Pilates", "Agachamento", "Alongamento"]), 2, 2, "Educação Física", "power_stat", 1, 15),
        ("Qual personagem de Unordinary possui a habilidade mais poderosa?", json.dumps(["John", "Seraphina", "Arlo", "Remi"]), 1, 3, "Unordinary", "power_stat", 3, 25),

        # High-level questions
        ("Qual é o teorema fundamental do cálculo?", json.dumps(["Relaciona a derivada com a integral", "Define números complexos", "Explica a teoria dos conjuntos", "Prova a existência de números primos infinitos"]), 0, 3, "Matemática Avançada", "intellect", 5, 30),
        ("Na série Unordinary, qual é a classificação de poder de John?", json.dumps(["7.0", "7.5", "8.0", "Desconhecido"]), 1, 3, "Unordinary", "intellect", 5, 30)
    ]

    cursor.executemany('''
    INSERT OR IGNORE INTO quiz_questions (question, options, correct_option, difficulty, category, attribute, min_level, tusd_reward)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', default_questions)

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

        # Parse story_progress if it exists and is not None
        if 'story_progress' in player_dict and player_dict['story_progress']:
            try:
                player_dict['story_progress'] = json.loads(player_dict['story_progress'])
            except json.JSONDecodeError:
                logger.error(f"Error parsing story_progress for player {player_dict['user_id']}")

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
    """Sync the local database to S3 if running in AWS.

    The synchronization frequency is controlled by the DB_SYNC_INTERVAL_MINUTES
    environment variable. If not set, the default is 5 minutes.
    """
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
            if now - last_sync_time < timedelta(minutes=sync_interval_minutes):
                logger.info(f"Skipping database sync, last sync was {(now - last_sync_time).total_seconds() / 60:.1f} minutes ago")
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

def update_club_reputation_weekly():
    """Update club reputation based on weekly activities."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get current week and year
        now = datetime.now()
        year, week, _ = now.isocalendar()

        # Get previous week
        prev_week = week - 1
        prev_year = year
        if prev_week <= 0:
            prev_week = 52  # Last week of previous year
            prev_year -= 1

        # Get club activity totals for the previous week
        cursor.execute('''
        SELECT club_id, SUM(points) as total_points
        FROM club_activities
        WHERE week = ? AND year = ?
        GROUP BY club_id
        ''', (prev_week, prev_year))

        club_points = cursor.fetchall()

        # Update club reputation based on activity points
        for club_id, points in club_points:
            reputation_change = points // 2  # Convert points to reputation (adjust ratio as needed)

            cursor.execute('''
            UPDATE clubs
            SET reputation = reputation + ?
            WHERE club_id = ?
            ''', (reputation_change, club_id))

            logger.info(f"Updated club {club_id} reputation by {reputation_change} based on {points} activity points")

        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error updating club reputation: {e}")
        return False
    finally:
        conn.close()

def store_event(event_id, name, description, event_type, channel_id, message_id, start_time, end_time, participants=None, data=None, completed=False):
    """Store an event in the database.

    Args:
        event_id (str): Unique identifier for the event
        name (str): Name of the event
        description (str): Description of the event
        event_type (str): Type of event (e.g., 'tournament', 'quiz', 'duel')
        channel_id (int): Discord channel ID where the event is taking place
        message_id (int): Discord message ID announcing the event
        start_time (datetime): When the event starts
        end_time (datetime): When the event ends
        participants (list, optional): List of participant user IDs. Defaults to None.
        data (dict, optional): Additional event data. Defaults to None.
        completed (bool, optional): Whether the event is completed. Defaults to False.

    Returns:
        bool: True if successful, False otherwise
    """
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
        cursor.execute('''
        INSERT OR REPLACE INTO events 
        (event_id, name, description, type, channel_id, message_id, start_time, end_time, completed, participants, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (event_id, name, description, event_type, channel_id, message_id, start_time, end_time, completed, participants_json, data_json))

        conn.commit()
        logger.info(f"Stored event {event_id} in database")
        return True
    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Error storing event {event_id}: {e}")
        return False
    finally:
        conn.close()

def get_event(event_id):
    """Get an event from the database by ID.

    Args:
        event_id (str): The ID of the event to retrieve

    Returns:
        dict: Event data or None if not found
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT * FROM events WHERE event_id = ?
        ''', (event_id,))

        event = cursor.fetchone()
        if not event:
            return None

        # Convert to dict and parse JSON fields
        event_dict = dict(event)
        event_dict['participants'] = json.loads(event_dict['participants'])
        event_dict['data'] = json.loads(event_dict['data'])

        return event_dict
    except sqlite3.Error as e:
        logger.error(f"Error getting event {event_id}: {e}")
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

# Initialize the database when the module is imported
init_db()
