"""
Configuration settings for Academia Tokugawa bot.
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
STORY_MODE_DIR = DATA_DIR / 'story_mode'
LOGS_DIR = DATA_DIR / 'logs'

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
STORY_MODE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database settings
USE_DYNAMO = os.getenv('USE_DYNAMODB', 'false').lower() == 'true'
DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'AcademiaTokugawa')
DYNAMODB_CLUBS_TABLE = os.getenv('DYNAMODB_CLUBS_TABLE', 'Clubes')
DYNAMODB_EVENTS_TABLE = os.getenv('DYNAMODB_EVENTS_TABLE', 'Eventos')
DYNAMODB_INVENTORY_TABLE = os.getenv('DYNAMODB_INVENTORY_TABLE', 'Inventario')
DYNAMODB_PLAYERS_TABLE = os.getenv('DYNAMODB_PLAYERS_TABLE', 'Jogadores')
DYNAMODB_MARKET_TABLE = os.getenv('DYNAMODB_MARKET_TABLE', 'Mercado')
DYNAMODB_ITEMS_TABLE = os.getenv('DYNAMODB_ITEMS_TABLE', 'Itens')
DYNAMODB_CLUB_ACTIVITIES_TABLE = os.getenv('DYNAMODB_CLUB_ACTIVITIES_TABLE', 'ClubActivities')
DYNAMODB_GRADES_TABLE = os.getenv('DYNAMODB_GRADES_TABLE', 'Notas')
DYNAMODB_VOTES_TABLE = os.getenv('DYNAMODB_VOTES_TABLE', 'Votos')
DYNAMODB_QUIZ_QUESTIONS_TABLE = os.getenv('DYNAMODB_QUIZ_QUESTIONS_TABLE', 'QuizQuestions')
DYNAMODB_QUIZ_ANSWERS_TABLE = os.getenv('DYNAMODB_QUIZ_ANSWERS_TABLE', 'QuizAnswers')

# AWS settings
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# Bot settings
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0'))

# Story mode settings
STORY_MODE_ENABLED = os.getenv('STORY_MODE_ENABLED', 'true').lower() == 'true'
STORY_MODE_DEBUG = os.getenv('STORY_MODE_DEBUG', 'false').lower() == 'true'

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = LOGS_DIR / 'tokugawa.log'

# Game settings
DEFAULT_PLAYER_VALUES = {
    'level': 1,
    'exp': 0,
    'tusd': 1000,
    'club_id': None,
    'dexterity': 10,
    'intellect': 10,
    'charisma': 10,
    'power_stat': 10,
    'reputation': 0,
    'hp': 100,
    'max_hp': 100,
    'strength_level': 1
}

# Story mode paths
STORY_MODE_PATHS = {
    'narrative': STORY_MODE_DIR / 'narrative',
    'events': STORY_MODE_DIR / 'events',
    'npcs': STORY_MODE_DIR / 'npcs',
    'logs': STORY_MODE_DIR / 'logs',
    'analytics': STORY_MODE_DIR / 'analytics'
}

# Create story mode directories
for path in STORY_MODE_PATHS.values():
    path.mkdir(parents=True, exist_ok=True) 
