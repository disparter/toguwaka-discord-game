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

def is_migration_completed(table):
    """
    Check if the migration has already been completed by looking for the migration flag.
    """
    try:
        logger.info("Checking if migration has already been completed...")
        response = table.get_item(
            Key={
                'PK': 'SYSTEM',
                'SK': 'FLAG#migration_completed'
            }
        )
        item = response.get('Item', {})
        is_completed = item.get('flag_value', False)
        logger.info(f"Migration completion status: {is_completed}")
        return is_completed
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def mark_migration_completed(table):
    """
    Mark the migration as completed by setting the migration flag.
    """
    try:
        logger.info("Marking migration as completed...")
        table.put_item(
            Item={
                'PK': 'SYSTEM',
                'SK': 'FLAG#migration_completed',
                'flag_value': True,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        )
        logger.info("Migration marked as completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error marking migration as completed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

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

        # Get club members to calculate members_count
        members = sqlite_db.get_club_members(club_id)
        members_count = len(members)

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
                'membros_count': safe_decimal(members_count),
                'reputacao': safe_decimal(club['reputation']),
                'created_at': club['created_at']
            }
        )

        # Create club members in DynamoDB
        member_ids = [f'PLAYER#{member["user_id"]}' for member in members]
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

def clean_academia_tokugawa_table():
    """
    Clean up the Academia Tokugawa table by removing duplicates and unnecessary data.
    """
    try:
        # Initialize DynamoDB client
        logger.info("Initializing DynamoDB client...")
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'AcademiaTokugawa'))
        logger.info(f"Using DynamoDB table: {table.name}")

        # Check if migration has already been completed
        if is_migration_completed(table):
            logger.info("Migration has already been completed. Skipping.")
            return True

        # Scan the table to get all items
        logger.info("Scanning table for items...")
        response = table.scan()
        items = response.get('Items', [])
        logger.info(f"Found {len(items)} items in the table")

        # Process items to remove duplicates and clean data
        processed_items = {}
        logger.info("Processing items to remove duplicates...")
        
        for item in items:
            pk = item.get('PK')
            sk = item.get('SK')
            
            if not pk or not sk:
                logger.warning(f"Skipping item with missing PK or SK: {item}")
                continue

            # Create a unique key for each item
            key = f"{pk}#{sk}"
            
            # Skip if we've already processed this item
            if key in processed_items:
                logger.debug(f"Skipping duplicate item: {key}")
                continue

            # Clean and process the item
            cleaned_item = {
                'PK': pk,
                'SK': sk,
                'updated_at': datetime.utcnow().isoformat()
            }

            # Add attributes based on the type of item
            if pk.startswith('CLUBE#'):
                if sk == 'PROFILE':
                    cleaned_item.update({
                        'nome': item.get('nome', ''),
                        'descricao': item.get('descricao', ''),
                        'lider_id': item.get('lider_id', ''),
                        'membros_count': safe_decimal(item.get('membros_count', 0)),
                        'reputacao': safe_decimal(item.get('reputacao', 0)),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed club profile: {pk}")
                elif sk == 'MEMBROS':
                    cleaned_item.update({
                        'membros': item.get('membros', []),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed club members: {pk}")
            elif pk.startswith('PLAYER#'):
                if sk == 'PROFILE':
                    cleaned_item.update({
                        'nome': item.get('nome', ''),
                        'nivel': safe_decimal(item.get('nivel', 1)),
                        'exp': safe_decimal(item.get('exp', 0)),
                        'hp': safe_decimal(item.get('hp', 100)),
                        'max_hp': safe_decimal(item.get('max_hp', 100)),
                        'superpoder': item.get('superpoder', ''),
                        'reputacao': safe_decimal(item.get('reputacao', 0)),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat()),
                        'last_active': item.get('last_active', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed player profile: {pk}")
                elif sk == 'INVENTORY':
                    cleaned_item.update({
                        'itens': item.get('itens', []),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed player inventory: {pk}")
                elif sk == 'TECHNIQUES':
                    cleaned_item.update({
                        'tecnicas': item.get('tecnicas', []),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed player techniques: {pk}")
            elif pk == 'SYSTEM':
                if sk.startswith('FLAG#'):
                    cleaned_item.update({
                        'flag_value': item.get('flag_value', False),
                        'created_at': item.get('created_at', datetime.utcnow().isoformat())
                    })
                    logger.debug(f"Processed system flag: {sk}")

            processed_items[key] = cleaned_item

        logger.info(f"Processed {len(processed_items)} unique items")

        # Write back the cleaned items
        logger.info("Writing back cleaned items...")
        with table.batch_writer() as batch:
            for item in processed_items.values():
                batch.put_item(Item=item)
        logger.info("Successfully wrote back cleaned items")

        # Mark migration as completed
        if not mark_migration_completed(table):
            logger.error("Failed to mark migration as completed")
            return False

        logger.info(f"Successfully cleaned Academia Tokugawa table. Processed {len(processed_items)} items.")
        return True

    except Exception as e:
        logger.error(f"Error cleaning Academia Tokugawa table: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def distribute_data_to_tables():
    """
    Distribute data from AcademiaTokugawa table to the respective specialized tables.
    """
    try:
        # Initialize DynamoDB client
        logger.info("Initializing DynamoDB client...")
        dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        main_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'AcademiaTokugawa'))
        
        # Get references to other tables
        tables = {
            'clubs': dynamodb.Table(os.environ.get('DYNAMODB_CLUBS_TABLE', 'Clubes')),
            'events': dynamodb.Table(os.environ.get('DYNAMODB_EVENTS_TABLE', 'Eventos')),
            'inventory': dynamodb.Table(os.environ.get('DYNAMODB_INVENTORY_TABLE', 'Inventario')),
            'players': dynamodb.Table(os.environ.get('DYNAMODB_PLAYERS_TABLE', 'Jogadores')),
            'market': dynamodb.Table(os.environ.get('DYNAMODB_MARKET_TABLE', 'Mercado'))
        }
        
        logger.info("Scanning AcademiaTokugawa table for items...")
        response = main_table.scan()
        items = response.get('Items', [])
        logger.info(f"Found {len(items)} items in AcademiaTokugawa table")
        
        # Process items and distribute to appropriate tables
        for item in items:
            pk = item.get('PK', '')
            sk = item.get('SK', '')
            
            if not pk or not sk:
                logger.warning(f"Skipping item with missing PK or SK: {item}")
                continue
                
            try:
                # Determine target table and map data based on PK prefix
                if pk.startswith('CLUBE#'):
                    if sk == 'PROFILE':
                        # Map club profile data
                        club_data = {
                            'NomeClube': item.get('nome', ''),
                            'descricao': item.get('descricao', ''),
                            'lider_id': item.get('lider_id', ''),
                            'membros_count': item.get('membros_count', 0),
                            'reputacao': item.get('reputacao', 0),
                            'created_at': item.get('created_at', datetime.utcnow().isoformat())
                        }
                        tables['clubs'].put_item(Item=club_data)
                        logger.debug(f"Distributed club profile {pk} to Clubes table")
                    elif sk == 'MEMBROS':
                        # Map club members data
                        club_id = pk.split('#')[1]
                        club_data = {
                            'NomeClube': item.get('nome', ''),
                            'membros': item.get('membros', [])
                        }
                        tables['clubs'].put_item(Item=club_data)
                        logger.debug(f"Distributed club members {pk} to Clubes table")
                
                elif pk.startswith('EVENTO#'):
                    # Map event data
                    event_data = {
                        'EventoID': pk.split('#')[1],
                        'Tipo': sk,
                        'nome': item.get('nome', ''),
                        'descricao': item.get('descricao', ''),
                        'tipo': item.get('tipo', ''),
                        'canal_id': item.get('canal_id', ''),
                        'mensagem_id': item.get('mensagem_id', ''),
                        'inicio': item.get('inicio', ''),
                        'fim': item.get('fim', ''),
                        'participantes': item.get('participantes', []),
                        'dados': item.get('dados', {})
                    }
                    tables['events'].put_item(Item=event_data)
                    logger.debug(f"Distributed event {pk} to Eventos table")
                
                elif pk.startswith('PLAYER#'):
                    if sk == 'INVENTORY':
                        # Map inventory data
                        player_id = pk.split('#')[1]
                        inventory_data = {
                            'JogadorID': player_id,
                            'ItemID': 'INVENTORY',
                            'itens': item.get('itens', [])
                        }
                        tables['inventory'].put_item(Item=inventory_data)
                        logger.debug(f"Distributed inventory {pk} to Inventario table")
                    else:
                        # Map player data
                        player_data = {
                            'PK': pk,
                            'SK': sk,
                            'nome': item.get('nome', ''),
                            'nivel': item.get('nivel', 1),
                            'exp': item.get('exp', 0),
                            'hp': item.get('hp', 100),
                            'max_hp': item.get('max_hp', 100),
                            'superpoder': item.get('superpoder', ''),
                            'reputacao': item.get('reputacao', 0),
                            'created_at': item.get('created_at', datetime.utcnow().isoformat()),
                            'last_active': item.get('last_active', datetime.utcnow().isoformat())
                        }
                        tables['players'].put_item(Item=player_data)
                        logger.debug(f"Distributed player {pk} to Jogadores table")
                
                elif pk.startswith('ITEM#'):
                    # Map market data
                    item_data = {
                        'ItemID': pk.split('#')[1],
                        'VendedorID': item.get('vendedor_id', 'SYSTEM'),
                        'nome': item.get('nome', ''),
                        'descricao': item.get('descricao', ''),
                        'tipo': item.get('tipo', ''),
                        'raridade': item.get('raridade', 'COMMON'),
                        'preco': item.get('preco', 0),
                        'efeitos': item.get('efeitos', {})
                    }
                    tables['market'].put_item(Item=item_data)
                    logger.debug(f"Distributed item {pk} to Mercado table")
                
            except Exception as e:
                logger.error(f"Error distributing item {pk}#{sk}: {e}")
                continue
                
        logger.info("Data distribution completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error distributing data to tables: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error args: {e.args}")
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

    # Clean Academia Tokugawa table
    clean_academia_tokugawa_table()
    
    # Distribute data to specialized tables
    distribute_data_to_tables()
