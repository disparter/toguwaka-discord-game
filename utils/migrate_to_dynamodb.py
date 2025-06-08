import sqlite3
import json
import os
import logging
import boto3
from datetime import datetime
from pathlib import Path
from decimal import Decimal, InvalidOperation, ConversionSyntax

# Import both database modules
from . import database as sqlite_db
from . import dynamodb as dynamo_db

logger = logging.getLogger('tokugawa_bot')

# SQLite database file path
SQLITE_DB_PATH = Path('data/tokugawa.db')

# Helper function to safely convert values to Decimal
def safe_decimal(value):
    try:
        if value is None:
            return Decimal('0')
        return Decimal(str(value))
    except (ValueError, InvalidOperation, ConversionSyntax):
        logger.warning(f"Invalid value for Decimal conversion: {value}, using 0 instead")
        return Decimal('0')

def migrate_players():
    """Migrate players from SQLite to DynamoDB."""
    logger.info("Migrating players...")

    # Get all players from SQLite
    players = sqlite_db.get_all_players()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for player in players:
        user_id = player['user_id']

        # Create player profile in DynamoDB
        # Convert numeric values to Decimal to avoid float type errors
        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'PLAYERS',
                'GSI1SK': player['name'],
                'nome': player['name'],
                'superpoder': player['power'],
                'nivel': safe_decimal(player['level']),
                'exp': safe_decimal(player['exp']),
                'tusd': safe_decimal(player['tusd']),
                'clube_id': player['club_id'],
                'atributos': {
                    'destreza': safe_decimal(player['dexterity']),
                    'intelecto': safe_decimal(player['intellect']),
                    'carisma': safe_decimal(player['charisma']),
                    'poder': safe_decimal(player['power_stat'])
                },
                'reputacao': safe_decimal(player['reputation']),
                'hp': safe_decimal(player['hp']),
                'max_hp': safe_decimal(player['max_hp']),
                'created_at': player['created_at'],
                'last_active': player['last_active']
            }
        )

        # Create inventory in DynamoDB
        inventory = json.loads(player['inventory']) if isinstance(player['inventory'], str) else player['inventory']
        inventory_items = []

        for item_id, quantity in inventory.items():
            inventory_items.append({
                'id': item_id,
                'quantidade': safe_decimal(quantity)
            })

        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'INVENTORY',
                'itens': inventory_items
            }
        )

        # Create techniques in DynamoDB
        techniques = json.loads(player['techniques']) if isinstance(player['techniques'], str) else player['techniques']
        techniques_list = []

        for tech_id, tech_data in techniques.items():
            techniques_list.append({
                'id': tech_id,
                'nome': tech_data.get('name', 'Unknown'),
                'nivel': safe_decimal(tech_data.get('level', 1)),
                'dano': safe_decimal(tech_data.get('damage', 0))
            })

        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'TECHNIQUES',
                'tecnicas': techniques_list
            }
        )

        count += 1
        if count % 10 == 0:
            logger.info(f"Migrated {count} players...")

    logger.info(f"Migrated {count} players successfully.")
    return count

def migrate_clubs():
    """Migrate clubs from SQLite to DynamoDB."""
    logger.info("Migrating clubs...")

    # Get all clubs from SQLite
    clubs = sqlite_db.get_all_clubs()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for club in clubs:
        club_id = club['club_id']

        # Create club profile in DynamoDB
        table.put_item(
            Item={
                'PK': f'CLUBE#{club_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'CLUBES',
                'GSI1SK': club['name'],
                'nome': club['name'],
                'descricao': club['description'],
                'lider_id': club['leader_id'],
                'membros_count': safe_decimal(club['members_count']),
                'reputacao': safe_decimal(club['reputation']),
                'created_at': club['created_at']
            }
        )

        # Get club members
        members = sqlite_db.get_club_members(club_id)
        member_ids = [f'PLAYER#{member["user_id"]}' for member in members]

        # Create club members in DynamoDB
        table.put_item(
            Item={
                'PK': f'CLUBE#{club_id}',
                'SK': 'MEMBROS',
                'membros': member_ids
            }
        )

        count += 1

    logger.info(f"Migrated {count} clubs successfully.")
    return count

def migrate_events():
    """Migrate events from SQLite to DynamoDB."""
    logger.info("Migrating events...")

    # Connect to SQLite database
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all events
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for event in events:
        event_id = event['event_id']

        # Parse JSON fields
        participants = json.loads(event['participants'])
        data_json = json.loads(event['data'])

        # Convert numeric values in data to Decimal
        data = {}
        for key, value in data_json.items():
            if isinstance(value, (int, float)):
                data[key] = safe_decimal(value)
            elif isinstance(value, dict):
                # Handle nested dictionaries
                nested_dict = {}
                for k, v in value.items():
                    if isinstance(v, (int, float)):
                        nested_dict[k] = safe_decimal(v)
                    else:
                        nested_dict[k] = v
                data[key] = nested_dict
            else:
                data[key] = value

        # Create event in DynamoDB
        table.put_item(
            Item={
                'PK': f'EVENTO#{event_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'EVENTOS',
                'GSI1SK': event['name'],
                'nome': event['name'],
                'descricao': event['description'],
                'tipo': event['type'],
                'canal_id': event['channel_id'],
                'mensagem_id': event['message_id'],
                'inicio': event['start_time'],
                'fim': event['end_time'],
                'participantes': participants,
                'dados': data
            }
        )

        count += 1

    conn.close()
    logger.info(f"Migrated {count} events successfully.")
    return count

def migrate_cooldowns():
    """Migrate cooldowns from SQLite to DynamoDB."""
    logger.info("Migrating cooldowns...")

    # Connect to SQLite database
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all cooldowns
    cursor.execute("SELECT * FROM cooldowns")
    cooldowns = cursor.fetchall()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for cooldown in cooldowns:
        user_id = cooldown['user_id']
        command = cooldown['command']

        # Create cooldown in DynamoDB
        # Convert expiry_time to datetime string if it's a timestamp
        expiry_time = cooldown['expiry_time']
        if isinstance(expiry_time, (int, float)):
            expiry_time = datetime.fromtimestamp(expiry_time).isoformat()

        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'COOLDOWN#{command}',
                'expiry_time': expiry_time
            }
        )

        count += 1

    conn.close()
    logger.info(f"Migrated {count} cooldowns successfully.")
    return count

def migrate_system_flags():
    """Migrate system flags from SQLite to DynamoDB."""
    logger.info("Migrating system flags...")

    # Connect to SQLite database
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all system flags
    cursor.execute("SELECT * FROM system_flags")
    flags = cursor.fetchall()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for flag in flags:
        flag_name = flag['flag_name']

        # Create system flag in DynamoDB
        table.put_item(
            Item={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}',
                'flag_value': flag['flag_value'],
                'updated_at': flag['updated_at']
            }
        )

        count += 1

    conn.close()
    logger.info(f"Migrated {count} system flags successfully.")
    return count

def migrate_items():
    """Migrate items from SQLite to DynamoDB."""
    logger.info("Migrating items...")

    # Connect to SQLite database
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all items
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    count = 0

    # Get DynamoDB table reference
    from utils import dynamodb as dynamo_db
    table = dynamo_db.get_table(dynamo_db.TABLES['main'])

    for item in items:
        item_id = item['item_id']

        # Parse effects JSON
        effects_json = json.loads(item['effects'])

        # Convert numeric values in effects to Decimal
        effects = {}
        for key, value in effects_json.items():
            if isinstance(value, (int, float)):
                effects[key] = safe_decimal(value)
            else:
                effects[key] = value

        # Create item in DynamoDB
        table.put_item(
            Item={
                'PK': f'ITEM#{item_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'ITEMS',
                'GSI1SK': item['type'],
                'nome': item['name'],
                'descricao': item['description'],
                'tipo': item['type'],
                'raridade': item['rarity'],
                'preco': safe_decimal(item['price']),
                'efeitos': effects
            }
        )

        count += 1

    conn.close()
    logger.info(f"Migrated {count} items successfully.")
    return count

def migrate_all():
    """Migrate all data from SQLite to DynamoDB."""
    logger.info("Starting migration from SQLite to DynamoDB...")

    try:
        # Check if SQLite database exists
        if not os.path.exists(SQLITE_DB_PATH):
            logger.error(f"SQLite database file not found: {SQLITE_DB_PATH}")
            return False

        # Initialize DynamoDB and get table reference
        try:
            from utils import dynamodb as dynamo_db
            if not dynamo_db.init_db():
                logger.error("Failed to initialize DynamoDB")
                return False
            
            # Get a fresh table reference after initialization
            table = dynamo_db.get_table(dynamo_db.TABLES['main'])
            logger.info(f"DynamoDB table {dynamo_db.TABLES['main']} is accessible")
        except Exception as e:
            logger.error(f"Error accessing DynamoDB table: {e}")
            logger.error("Make sure the table exists and AWS credentials are properly configured")
            return False

        # Migrate in order of dependencies
        try:
            clubs_count = migrate_clubs()
            logger.info(f"Migrated {clubs_count} clubs")
        except Exception as e:
            logger.error(f"Error migrating clubs: {e}")
            return False

        try:
            players_count = migrate_players()
            logger.info(f"Migrated {players_count} players")
        except Exception as e:
            logger.error(f"Error migrating players: {e}")
            return False

        try:
            events_count = migrate_events()
            logger.info(f"Migrated {events_count} events")
        except Exception as e:
            logger.error(f"Error migrating events: {e}")
            return False

        try:
            cooldowns_count = migrate_cooldowns()
            logger.info(f"Migrated {cooldowns_count} cooldowns")
        except Exception as e:
            logger.error(f"Error migrating cooldowns: {e}")
            return False

        try:
            system_flags_count = migrate_system_flags()
            logger.info(f"Migrated {system_flags_count} system flags")
        except Exception as e:
            logger.error(f"Error migrating system flags: {e}")
            return False

        try:
            items_count = migrate_items()
            logger.info(f"Migrated {items_count} items")
        except Exception as e:
            logger.error(f"Error migrating items: {e}")
            return False

        logger.info(f"""
        Migration completed successfully:
        - {clubs_count} clubs
        - {players_count} players
        - {events_count} events
        - {cooldowns_count} cooldowns
        - {system_flags_count} system flags
        - {items_count} items
        """)

        return True
    except Exception as e:
        logger.error(f"Error during migration: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run migration
    migrate_all()
