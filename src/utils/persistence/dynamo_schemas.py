import os
import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Get table names from environment variables
PLAYERS_TABLE = os.getenv('DYNAMODB_PLAYERS_TABLE', 'Jogadores')
INVENTORY_TABLE = os.getenv('DYNAMODB_INVENTORY_TABLE', 'Inventario')
EVENTS_TABLE = os.getenv('DYNAMODB_EVENTS_TABLE', 'Eventos')
COOLDOWNS_TABLE = os.getenv('DYNAMODB_COOLDOWNS_TABLE', 'Cooldowns')
GRADES_TABLE = os.getenv('DYNAMODB_GRADES_TABLE', 'Notas')
MARKET_TABLE = os.getenv('DYNAMODB_MARKET_TABLE', 'Mercado')
ITEMS_TABLE = os.getenv('DYNAMODB_ITEMS_TABLE', 'Itens')
CLUB_ACTIVITIES_TABLE = os.getenv('DYNAMODB_CLUB_ACTIVITIES_TABLE', 'ClubActivities')
QUIZ_QUESTIONS_TABLE = os.getenv('DYNAMODB_QUIZ_QUESTIONS_TABLE', 'QuizQuestions')
QUIZ_ANSWERS_TABLE = os.getenv('DYNAMODB_QUIZ_ANSWERS_TABLE', 'QuizAnswers')
SYSTEM_FLAGS_TABLE = os.getenv('DYNAMODB_SYSTEM_FLAGS_TABLE', 'SystemFlags')
VOTES_TABLE = os.getenv('DYNAMODB_VOTES_TABLE', 'Votos')
MAIN_TABLE = os.getenv('DYNAMODB_TABLE', 'AcademiaTokugawa')

def get_table(table_name: str):
    """Get DynamoDB table resource."""
    return dynamodb.Table(table_name)

# Table schemas
PLAYERS_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id> or CLUB#<club_id>)
    'SK': 'S',  # Sort key (PROFILE or INFO)
    'name': 'S',
    'level': 'N',
    'exp': 'N',
    'tusd': 'N',
    'hp': 'N',
    'max_hp': 'N',
    'dexterity': 'N',
    'intellect': 'N',
    'charisma': 'N',
    'power_stat': 'N',
    'reputation': 'N',
    'strength_level': 'N',
    'club_id': 'S',
    'created_at': 'S',
    'last_active': 'S'
}

INVENTORY_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id>)
    'SK': 'S',  # Sort key (ITEM#<item_id>)
    'item_data': 'M'  # Map containing item details
}

EVENTS_SCHEMA = {
    'PK': 'S',  # Partition key (EVENT#<event_id>)
    'SK': 'S',  # Sort key (TYPE#<event_type>)
    'name': 'S',
    'description': 'S',
    'channel_id': 'S',
    'message_id': 'S',
    'start_time': 'S',
    'end_time': 'S',
    'participants': 'L',  # List of participant IDs
    'data': 'M',  # Map containing event data
    'completed': 'BOOL',
    'created_at': 'S',
    'last_updated': 'S'
}

COOLDOWNS_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id>)
    'SK': 'S',  # Sort key (COMMAND#<command>)
    'expiry_time': 'S',
    'command': 'S',
    'created_at': 'S'
}

GRADES_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id>)
    'SK': 'S',  # Sort key (SUBJECT#<subject>)
    'grade': 'N',
    'subject': 'S',
    'semester': 'N',
    'last_updated': 'S'
}

MARKET_SCHEMA = {
    'PK': 'S',  # Partition key (ITEM#<item_id>)
    'SK': 'S',  # Sort key (MARKET)
    'name': 'S',
    'description': 'S',
    'type': 'S',
    'rarity': 'S',
    'effects': 'M',
    'price': 'N',
    'is_available': 'BOOL',
    'created_at': 'S',
    'last_updated': 'S'
}

ITEMS_SCHEMA = {
    'PK': 'S',  # Partition key (ITEM#<item_id>)
    'SK': 'S',  # Sort key (ITEM)
    'name': 'S',
    'description': 'S',
    'type': 'S',
    'rarity': 'S',
    'effects': 'M',
    'price': 'N',
    'is_available': 'BOOL',
    'created_at': 'S',
    'last_updated': 'S'
}

CLUB_ACTIVITIES_SCHEMA = {
    'PK': 'S',  # Partition key (CLUB#<club_id>)
    'SK': 'S',  # Sort key (ACTIVITY#<activity_id>)
    'name': 'S',
    'description': 'S',
    'start_time': 'S',
    'end_time': 'S',
    'participants': 'L',
    'status': 'S',
    'created_at': 'S',
    'last_updated': 'S'
}

QUIZ_QUESTIONS_SCHEMA = {
    'PK': 'S',  # Partition key (QUIZ#<question_id>)
    'SK': 'S',  # Sort key (QUESTION)
    'question': 'S',
    'options': 'L',  # List of possible answers
    'correct_answer': 'S',
    'difficulty': 'S',
    'category': 'S',
    'created_at': 'S',
    'last_updated': 'S'
}

QUIZ_ANSWERS_SCHEMA = {
    'PK': 'S',  # Partition key (PLAYER#<user_id>)
    'SK': 'S',  # Sort key (QUIZ#<question_id>)
    'answer': 'S',
    'is_correct': 'BOOL',
    'answered_at': 'S'
}

SYSTEM_FLAGS_SCHEMA = {
    'PK': 'S',  # Partition key (SYSTEM)
    'SK': 'S',  # Sort key (FLAG#<flag_name>)
    'value': 'S',
    'last_updated': 'S'
}

VOTES_SCHEMA = {
    'PK': 'S',  # Partition key (VOTE#<vote_id>)
    'SK': 'S',  # Sort key (VOTE)
    'title': 'S',
    'description': 'S',
    'options': 'L',
    'start_time': 'S',
    'end_time': 'S',
    'created_by': 'S',
    'status': 'S',
    'created_at': 'S',
    'last_updated': 'S'
}

# Default values
DEFAULT_PLAYER_VALUES = {
    'level': 1,
    'exp': 0,
    'tusd': 1000,
    'hp': 100,
    'max_hp': 100,
    'dexterity': 10,
    'intellect': 10,
    'charisma': 10,
    'power_stat': 10,
    'reputation': 0,
    'strength_level': 1,
    'club_id': None
}

# Table names mapping
TABLES = {
    'players': PLAYERS_TABLE,
    'inventory': INVENTORY_TABLE,
    'events': EVENTS_TABLE,
    'cooldowns': COOLDOWNS_TABLE,
    'grades': GRADES_TABLE,
    'market': MARKET_TABLE,
    'items': ITEMS_TABLE,
    'club_activities': CLUB_ACTIVITIES_TABLE,
    'quiz_questions': QUIZ_QUESTIONS_TABLE,
    'quiz_answers': QUIZ_ANSWERS_TABLE,
    'system_flags': SYSTEM_FLAGS_TABLE,
    'votes': VOTES_TABLE,
    'main': MAIN_TABLE
} 