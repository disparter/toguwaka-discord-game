import boto3
import json
import os
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger('tokugawa_bot')

# DynamoDB table name
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'AcademiaTokugawa')

# AWS region
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(TABLE_NAME)

# Helper class to convert Decimal to float/int for JSON serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 else int(o)
        return super(DecimalEncoder, self).default(o)

def init_db():
    """
    Initialize the DynamoDB connection.
    This function is called when the module is imported.
    """
    try:
        # Check if the table exists
        table.table_status
        logger.info(f"Connected to DynamoDB table: {TABLE_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error connecting to DynamoDB: {e}")
        return False

# Player operations
def get_player(user_id):
    """
    Get player data from DynamoDB.

    Args:
        user_id (int): The Discord user ID

    Returns:
        dict: Player data or None if not found
    """
    try:
        response = table.get_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        logger.error(f"Error getting player {user_id}: {e}")
        return None

def create_player(user_id, name, power, strength_level, club_id):
    """
    Create a new player in DynamoDB.

    Args:
        user_id (int): The Discord user ID
        name (str): Player name
        power (str): Player power
        strength_level (int): Player strength level
        club_id (int): Club ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create player profile
        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'PLAYERS',
                'GSI1SK': name,
                'nome': name,
                'superpoder': power,
                'nivel': 1,
                'exp': 0,
                'tusd': 100,
                'clube_id': club_id,
                'atributos': {
                    'destreza': 5,
                    'intelecto': 5,
                    'carisma': 5,
                    'poder': strength_level
                },
                'reputacao': 0,
                'hp': 100,
                'max_hp': 100,
                'created_at': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
        )

        # Create empty inventory
        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'INVENTORY',
                'itens': []
            }
        )

        # Create empty techniques
        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': 'TECHNIQUES',
                'tecnicas': []
            }
        )

        # Update club members count
        if club_id:
            update_club_members_count(club_id, 1)

            # Add player to club members
            table.update_item(
                Key={
                    'PK': f'CLUBE#{club_id}',
                    'SK': 'MEMBROS'
                },
                UpdateExpression="SET membros = list_append(if_not_exists(membros, :empty_list), :player)",
                ExpressionAttributeValues={
                    ':player': [f'PLAYER#{user_id}'],
                    ':empty_list': []
                }
            )

        logger.info(f"Created new player: {name} (ID: {user_id})")
        return True
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return False

def update_player(user_id, **kwargs):
    """
    Update player data in DynamoDB.

    Args:
        user_id (int): The Discord user ID
        **kwargs: Fields to update

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Build update expression
        update_expression = "SET last_active = :last_active"
        expression_values = {
            ':last_active': datetime.now().isoformat()
        }

        # Add each field to update expression
        for key, value in kwargs.items():
            # Handle dictionary values
            if isinstance(value, dict):
                if key == 'atributos':
                    # Special handling for atributos field
                    for attr_key, attr_value in value.items():
                        update_expression += f", atributos.{attr_key} = :attr_{attr_key}"
                        expression_values[f':attr_{attr_key}'] = attr_value
                else:
                    # For other dictionary fields, store as a map
                    update_expression += f", {key} = :{key}"
                    # Convert any nested dictionaries to a format DynamoDB can handle
                    processed_value = json.loads(json.dumps(value), parse_float=Decimal)
                    expression_values[f':{key}'] = processed_value
            else:
                update_expression += f", {key} = :{key}"
                expression_values[f':{key}'] = value

        # Update player profile
        table.update_item(
            Key={
                'PK': f'PLAYER#{user_id}',
                'SK': 'PROFILE'
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )

        logger.info(f"Updated player {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating player {user_id}: {e}")
        return False

# Club operations
def get_club(club_id):
    """
    Get club data from DynamoDB.

    Args:
        club_id (int): The club ID

    Returns:
        dict: Club data or None if not found
    """
    try:
        response = table.get_item(
            Key={
                'PK': f'CLUBE#{club_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        logger.error(f"Error getting club {club_id}: {e}")
        return None

def get_all_clubs():
    """
    Get all clubs from DynamoDB.

    Returns:
        list: List of club dictionaries
    """
    try:
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :pk',
            ExpressionAttributeValues={
                ':pk': 'CLUBES'
            }
        )

        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting all clubs: {e}")
        return []

def update_club_members_count(club_id, change):
    """
    Update club members count in DynamoDB.

    Args:
        club_id (int): The club ID
        change (int): The change in members count (positive or negative)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        table.update_item(
            Key={
                'PK': f'CLUBE#{club_id}',
                'SK': 'PROFILE'
            },
            UpdateExpression="SET membros_count = if_not_exists(membros_count, :zero) + :change",
            ExpressionAttributeValues={
                ':change': change,
                ':zero': 0
            }
        )

        logger.info(f"Updated club {club_id} members count by {change}")
        return True
    except Exception as e:
        logger.error(f"Error updating club {club_id} members count: {e}")
        return False

def get_club_members(club_id):
    """
    Get all players who are members of a specific club.

    Args:
        club_id (int): The ID of the club

    Returns:
        list: List of player dictionaries who are members of the club
    """
    try:
        response = table.get_item(
            Key={
                'PK': f'CLUBE#{club_id}',
                'SK': 'MEMBROS'
            }
        )

        if 'Item' not in response:
            return []

        member_ids = response['Item'].get('membros', [])
        members = []

        # Get each member's profile
        for member_id in member_ids:
            player_id = member_id.split('#')[1]
            player = get_player(player_id)
            if player:
                members.append({
                    'user_id': player_id,
                    'name': player.get('nome'),
                    'level': player.get('nivel'),
                    'power': player.get('superpoder')
                })

        return members
    except Exception as e:
        logger.error(f"Error getting club members for club {club_id}: {e}")
        return []

# Event operations
def store_event(event_id, name, description, event_type, channel_id, message_id, start_time, end_time, participants=None, data=None, completed=False):
    """
    Store an event in DynamoDB.

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
    try:
        # Convert datetime objects to strings if needed
        if isinstance(start_time, datetime):
            start_time = start_time.isoformat()
        if isinstance(end_time, datetime):
            end_time = end_time.isoformat()

        # Default values
        if participants is None:
            participants = []
        if data is None:
            data = {}

        table.put_item(
            Item={
                'PK': f'EVENTO#{event_id}',
                'SK': 'PROFILE',
                'GSI1PK': 'EVENTOS',
                'GSI1SK': event_type,
                'nome': name,
                'descricao': description,
                'tipo': event_type,
                'channel_id': channel_id,
                'message_id': message_id,
                'start_time': start_time,
                'end_time': end_time,
                'completed': completed,
                'participantes': participants,
                'data': data,
                'created_at': datetime.now().isoformat()
            }
        )

        logger.info(f"Stored event {event_id} in DynamoDB")
        return True
    except Exception as e:
        logger.error(f"Error storing event {event_id}: {e}")
        return False

def get_event(event_id):
    """
    Get an event from DynamoDB by ID.

    Args:
        event_id (str): The ID of the event to retrieve

    Returns:
        dict: Event data or None if not found
    """
    try:
        response = table.get_item(
            Key={
                'PK': f'EVENTO#{event_id}',
                'SK': 'PROFILE'
            }
        )

        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        return None

# Cooldown operations
def store_cooldown(user_id, command, expiry_time):
    """
    Store a cooldown in DynamoDB.

    Args:
        user_id (int): The user ID
        command (str): The command name
        expiry_time (float): Timestamp when the cooldown expires

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert timestamp to datetime
        expiry_datetime = datetime.fromtimestamp(expiry_time).isoformat()

        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'COOLDOWN#{command}',
                'expiry_time': expiry_datetime
            }
        )

        logger.info(f"Stored cooldown for user {user_id}, command {command}")
        return True
    except Exception as e:
        logger.error(f"Error storing cooldown for user {user_id}, command {command}: {e}")
        return False

def get_cooldowns(user_id=None):
    """
    Get cooldowns from DynamoDB.

    Args:
        user_id (int, optional): The user ID to get cooldowns for. If None, get all cooldowns.

    Returns:
        dict: Dictionary of cooldowns with user_id and command as keys
    """
    try:
        result = {}

        if user_id is not None:
            # Query cooldowns for a specific user
            response = table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':pk': f'PLAYER#{user_id}',
                    ':sk_prefix': 'COOLDOWN#'
                }
            )

            # Process results
            for item in response.get('Items', []):
                command = item['SK'].split('#')[1]
                expiry_time = datetime.fromisoformat(item['expiry_time']).timestamp()

                if user_id not in result:
                    result[user_id] = {}

                result[user_id][command] = expiry_time
        else:
            # For all users, we need to scan with a filter
            # Note: This is not efficient for large datasets
            response = table.scan(
                FilterExpression='begins_with(SK, :sk_prefix)',
                ExpressionAttributeValues={
                    ':sk_prefix': 'COOLDOWN#'
                }
            )

            # Process results
            for item in response.get('Items', []):
                player_id = item['PK'].split('#')[1]
                command = item['SK'].split('#')[1]
                expiry_time = datetime.fromisoformat(item['expiry_time']).timestamp()

                if player_id not in result:
                    result[player_id] = {}

                result[player_id][command] = expiry_time

        return result
    except Exception as e:
        logger.error(f"Error getting cooldowns: {e}")
        return {}

def clear_expired_cooldowns():
    """
    Remove expired cooldowns from DynamoDB.

    Returns:
        int: Number of cooldowns removed
    """
    try:
        now = datetime.now().isoformat()
        removed = 0

        # Scan for expired cooldowns
        response = table.scan(
            FilterExpression='begins_with(SK, :sk_prefix) AND expiry_time < :now',
            ExpressionAttributeValues={
                ':sk_prefix': 'COOLDOWN#',
                ':now': now
            }
        )

        # Delete expired cooldowns
        for item in response.get('Items', []):
            table.delete_item(
                Key={
                    'PK': item['PK'],
                    'SK': item['SK']
                }
            )
            removed += 1

        if removed > 0:
            logger.info(f"Removed {removed} expired cooldowns")

        return removed
    except Exception as e:
        logger.error(f"Error clearing expired cooldowns: {e}")
        return 0

# System flag operations
def get_system_flag(flag_name):
    """
    Get the value of a system flag.

    Args:
        flag_name (str): The name of the flag to retrieve

    Returns:
        str: The value of the flag, or None if the flag doesn't exist
    """
    try:
        response = table.get_item(
            Key={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}'
            }
        )

        if 'Item' in response:
            return response['Item'].get('flag_value')
        return None
    except Exception as e:
        logger.error(f"Error getting system flag {flag_name}: {e}")
        return None

def set_system_flag(flag_name, flag_value):
    """
    Set the value of a system flag.

    Args:
        flag_name (str): The name of the flag to set
        flag_value (str): The value to set for the flag

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        table.put_item(
            Item={
                'PK': 'SYSTEM',
                'SK': f'FLAG#{flag_name}',
                'flag_value': flag_value,
                'updated_at': datetime.now().isoformat()
            }
        )

        logger.info(f"Set system flag {flag_name} to {flag_value}")
        return True
    except Exception as e:
        logger.error(f"Error setting system flag {flag_name}: {e}")
        return False

# Market operations
def add_market_item(item_id, seller_id, name, description, price, quantity=1):
    """
    Add an item to the market.

    Args:
        item_id (str): The item ID
        seller_id (int): The seller's user ID
        name (str): Item name
        description (str): Item description
        price (int): Item price in TUSD
        quantity (int, optional): Item quantity. Defaults to 1.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        table.put_item(
            Item={
                'PK': f'MERCADO#{item_id}',
                'SK': f'SELLER#{seller_id}',
                'GSI1PK': 'MERCADO',
                'GSI1SK': name,
                'nome': name,
                'descricao': description,
                'preco': price,
                'quantidade': quantity,
                'vendedor_id': seller_id,
                'created_at': datetime.now().isoformat()
            }
        )

        logger.info(f"Added item {item_id} to market by seller {seller_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding item to market: {e}")
        return False

def get_market_items():
    """
    Get all items in the market.

    Returns:
        list: List of market item dictionaries
    """
    try:
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :pk',
            ExpressionAttributeValues={
                ':pk': 'MERCADO'
            }
        )

        return response.get('Items', [])
    except Exception as e:
        logger.error(f"Error getting market items: {e}")
        return []

# Grade operations
def get_player_grades(user_id, subject=None, month=None, year=None):
    """
    Get player grades from DynamoDB.

    Args:
        user_id (int): The user ID
        subject (str, optional): Filter by subject. Defaults to None.
        month (int, optional): Filter by month. Defaults to None.
        year (int, optional): Filter by year. Defaults to None.

    Returns:
        list: List of grade dictionaries
    """
    try:
        # Query grades for the player
        response = table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk_prefix)',
            ExpressionAttributeValues={
                ':pk': f'PLAYER#{user_id}',
                ':sk_prefix': 'GRADE#'
            }
        )

        grades = []

        for item in response.get('Items', []):
            # Parse the SK to get subject, month, year
            # Format: GRADE#SUBJECT#MONTH#YEAR
            parts = item['SK'].split('#')
            if len(parts) >= 4:
                grade_subject = parts[1]
                grade_month = int(parts[2])
                grade_year = int(parts[3])

                # Apply filters
                if subject and grade_subject != subject:
                    continue
                if month and grade_month != month:
                    continue
                if year and grade_year != year:
                    continue

                grades.append({
                    'grade_id': item.get('grade_id', 0),
                    'user_id': user_id,
                    'subject': grade_subject,
                    'grade': item.get('grade', 0),
                    'month': grade_month,
                    'year': grade_year,
                    'created_at': item.get('created_at')
                })

        return grades
    except Exception as e:
        logger.error(f"Error getting player grades for user {user_id}: {e}")
        return []

def update_player_grade(user_id, subject, grade, month, year):
    """
    Update or insert player grade in DynamoDB.

    Args:
        user_id (int): The user ID
        subject (str): The subject
        grade (float): The grade value
        month (int): The month
        year (int): The year

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Generate a unique grade ID if needed
        grade_id = f"{user_id}_{subject}_{month}_{year}"

        table.put_item(
            Item={
                'PK': f'PLAYER#{user_id}',
                'SK': f'GRADE#{subject}#{month}#{year}',
                'grade_id': grade_id,
                'grade': grade,
                'subject': subject,
                'month': month,
                'year': year,
                'created_at': datetime.now().isoformat()
            }
        )

        logger.info(f"Updated grade for user {user_id}, subject {subject}, month {month}, year {year}")
        return True
    except Exception as e:
        logger.error(f"Error updating player grade: {e}")
        return False

def get_monthly_average_grades(user_id, month, year):
    """
    Get player's average grades for a specific month.

    Args:
        user_id (int): The user ID
        month (int): The month
        year (int): The year

    Returns:
        list: List of dictionaries with subject and average_grade
    """
    try:
        # Get all grades for the user in the specified month and year
        grades = get_player_grades(user_id, month=month, year=year)

        # Group by subject and calculate average
        subject_grades = {}
        for grade in grades:
            subject = grade['subject']
            if subject not in subject_grades:
                subject_grades[subject] = []
            subject_grades[subject].append(grade['grade'])

        # Calculate averages
        averages = []
        for subject, grades_list in subject_grades.items():
            average = sum(grades_list) / len(grades_list)
            averages.append({
                'subject': subject,
                'average_grade': average
            })

        return averages
    except Exception as e:
        logger.error(f"Error getting monthly average grades for user {user_id}: {e}")
        return []

# Voting operations
def add_vote(category, voter_id, candidate_id, week, year):
    """
    Add a vote in DynamoDB.

    Args:
        category (str): The voting category
        voter_id (int): The voter's user ID
        candidate_id (int): The candidate's user ID
        week (int): The week number
        year (int): The year

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        table.put_item(
            Item={
                'PK': f'VOTE#{category}#{week}#{year}',
                'SK': f'VOTER#{voter_id}',
                'GSI1PK': f'VOTE#{category}#{week}#{year}',
                'GSI1SK': f'CANDIDATE#{candidate_id}',
                'voter_id': voter_id,
                'candidate_id': candidate_id,
                'category': category,
                'week': week,
                'year': year,
                'created_at': datetime.now().isoformat()
            }
        )

        logger.info(f"Added vote from {voter_id} for {candidate_id} in category {category}")
        return True
    except Exception as e:
        logger.error(f"Error adding vote: {e}")
        return False

def get_vote_results(category, week, year):
    """
    Get vote results for a specific category, week, and year.

    Args:
        category (str): The voting category
        week (int): The week number
        year (int): The year

    Returns:
        list: List of dictionaries with candidate_id and vote_count
    """
    try:
        # Query votes for the category, week, and year
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :pk',
            ExpressionAttributeValues={
                ':pk': f'VOTE#{category}#{week}#{year}'
            }
        )

        # Count votes for each candidate
        vote_counts = {}
        for item in response.get('Items', []):
            candidate_id = item['candidate_id']
            if candidate_id not in vote_counts:
                vote_counts[candidate_id] = 0
            vote_counts[candidate_id] += 1

        # Format results
        results = []
        for candidate_id, vote_count in vote_counts.items():
            results.append({
                'candidate_id': candidate_id,
                'vote_count': vote_count
            })

        # Sort by vote count (descending)
        results.sort(key=lambda x: x['vote_count'], reverse=True)

        return results
    except Exception as e:
        logger.error(f"Error getting vote results: {e}")
        return []

# Quiz operations
def get_quiz_questions(player_data=None, category=None, attribute=None, count=3):
    """
    Get quiz questions based on player data, category, and/or attribute.

    Args:
        player_data (dict, optional): Player data for personalization. Defaults to None.
        category (str, optional): Filter by category. Defaults to None.
        attribute (str, optional): Filter by attribute. Defaults to None.
        count (int, optional): Number of questions to return. Defaults to 3.

    Returns:
        list: List of question dictionaries
    """
    try:
        # Query questions from DynamoDB
        filter_expression = None
        expression_values = {}

        if category:
            filter_expression = 'category = :category'
            expression_values[':category'] = category

        if attribute:
            if filter_expression:
                filter_expression += ' AND attribute = :attribute'
            else:
                filter_expression = 'attribute = :attribute'
            expression_values[':attribute'] = attribute

        if player_data:
            player_level = player_data.get('nivel', 1)
            if filter_expression:
                filter_expression += ' AND min_level <= :level'
            else:
                filter_expression = 'min_level <= :level'
            expression_values[':level'] = player_level

        # Query questions
        if filter_expression:
            response = table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_values
            )
        else:
            response = table.scan(
                FilterExpression='begins_with(PK, :pk)',
                ExpressionAttributeValues={
                    ':pk': 'QUIZ#'
                }
            )

        questions = response.get('Items', [])

        # Shuffle and limit
        import random
        random.shuffle(questions)
        questions = questions[:count]

        # Format questions
        result = []
        for q in questions:
            result.append({
                'question_id': q.get('question_id', 0),
                'question': q.get('question', ''),
                'options': q.get('options', []),
                'correct_option': q.get('correct_option', 0),
                'difficulty': q.get('difficulty', 1),
                'category': q.get('category', ''),
                'attribute': q.get('attribute', ''),
                'min_level': q.get('min_level', 1),
                'tusd_reward': q.get('tusd_reward', 10)
            })

        return result
    except Exception as e:
        logger.error(f"Error getting quiz questions: {e}")
        return []

def record_quiz_answer(user_id, question_id, is_correct):
    """
    Record a quiz answer and award TUSD if correct.

    Args:
        user_id (int): The user ID
        question_id (int): The question ID
        is_correct (bool): Whether the answer was correct

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get the question to determine the reward
        response = table.get_item(
            Key={
                'PK': f'QUIZ#{question_id}',
                'SK': 'PROFILE'
            }
        )

        tusd_reward = 0
        if 'Item' in response:
            tusd_reward = response['Item'].get('tusd_reward', 10) if is_correct else 0

        # Update player's TUSD if correct
        if is_correct and tusd_reward > 0:
            table.update_item(
                Key={
                    'PK': f'PLAYER#{user_id}',
                    'SK': 'PROFILE'
                },
                UpdateExpression='SET tusd = tusd + :reward',
                ExpressionAttributeValues={
                    ':reward': tusd_reward
                }
            )

            logger.info(f"Awarded {tusd_reward} TUSD to player {user_id} for correct quiz answer")

        return True
    except Exception as e:
        logger.error(f"Error recording quiz answer: {e}")
        return False

# Initialize the DynamoDB connection when the module is imported
init_db()
