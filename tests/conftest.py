"""
Test configuration for Academia Tokugawa.

This module contains pytest fixtures and configuration for testing.
"""

import pytest
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Configura variáveis de ambiente para testes
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"

# Monkey patch para corrigir imports
import builtins
original_import = builtins.__import__

def patched_import(name, *args, **kwargs):
    # Lista de módulos que precisam do prefixo src
    src_modules = ['utils', 'cogs', 'story_mode', 'bot']
    
    # Não modifica imports de bibliotecas externas ou imports relativos
    if (name.startswith(('discord', 'pytest', 'unittest', 'mock', 'asyncio', 'botocore')) or
        name.startswith('.') or
        name.startswith('src.')):
        return original_import(name, *args, **kwargs)
    
    # Verifica se o módulo está na lista e adiciona o prefixo src
    for module in src_modules:
        if name == module or name.startswith(f"{module}."):
            name = f"src.{name}"
            break
    
    return original_import(name, *args, **kwargs)

builtins.__import__ = patched_import

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent actual log output during tests."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr('logging.getLogger', MagicMock())
        yield

@pytest.fixture(autouse=True)
def mock_discord():
    """Mock Discord.py to prevent actual Discord API calls during tests."""
    with pytest.MonkeyPatch.context() as m:
        # Mock discord.Client
        m.setattr('discord.Client', MagicMock)
        
        # Mock discord.Interaction
        m.setattr('discord.Interaction', MagicMock)
        
        # Mock discord.app_commands
        m.setattr('discord.app_commands', MagicMock)
        
        yield 

@pytest.fixture
def mock_ctx():
    """Mock Discord context."""
    ctx = MagicMock()
    ctx.author.id = "123456789"
    ctx.author.name = "Test Player"
    ctx.send = MagicMock()
    return ctx

@pytest.fixture
def test_player():
    """Provide test player data."""
    return {
        "user_id": "123456789",
        "name": "Test Player",
        "level": 1,
        "exp": 0,
        "tusd": 1000,
        "hp": 100,
        "max_hp": 100,
        "dexterity": 10,
        "intellect": 10,
        "charisma": 10,
        "power_stat": 10,
        "reputation": 0,
        "strength_level": 1,
        "club_id": None,
        "created_at": datetime.now().isoformat(),
        "last_active": datetime.now().isoformat()
    }

@pytest.fixture
def test_club():
    """Provide test club data."""
    return {
        "club_id": "TEST_CLUB",
        "name": "Test Club",
        "description": "A test club",
        "leader_id": "123456789",
        "reputation": 0,
        "members": ["123456789"],
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def test_item():
    """Provide test item data."""
    return {
        "item_id": "TEST_ITEM",
        "name": "Test Sword",
        "description": "A test sword",
        "type": "weapon",
        "rarity": "common",
        "price": 100,
        "effects": {
            "power": 10,
            "durability": 100
        }
    }

@pytest.fixture
def test_inventory():
    """Provide test inventory data."""
    return {
        "item_1": {
            "name": "Test Item 1",
            "type": "weapon",
            "rarity": "common",
            "stats": {"attack": 5}
        },
        "item_2": {
            "name": "Test Item 2",
            "type": "consumable",
            "rarity": "rare",
            "effect": "heal"
        }
    }

@pytest.fixture
def mock_db():
    """Mock database operations."""
    with patch('utils.persistence.db_provider.get_player') as mock_get_player, \
         patch('utils.persistence.db_provider.update_player') as mock_update_player, \
         patch('utils.persistence.db_provider.get_club') as mock_get_club, \
         patch('utils.persistence.db_provider.get_player_inventory') as mock_get_inventory, \
         patch('utils.persistence.db_provider.add_item_to_inventory') as mock_add_item, \
         patch('utils.persistence.db_provider.remove_item_from_inventory') as mock_remove_item:
        
        mock_get_player.return_value = None
        mock_update_player.return_value = True
        mock_get_club.return_value = None
        mock_get_inventory.return_value = {}
        mock_add_item.return_value = True
        mock_remove_item.return_value = True
        
        yield {
            'get_player': mock_get_player,
            'update_player': mock_update_player,
            'get_club': mock_get_club,
            'get_inventory': mock_get_inventory,
            'add_item': mock_add_item,
            'remove_item': mock_remove_item
        }

@pytest.fixture
def mock_story_data():
    """Mock story data for testing."""
    return {
        "1_1_arrival": {
            "type": "story",
            "title": "Arrival",
            "description": "The beginning of your journey.",
            "chapter_id": "1_1_arrival",
            "choices": [
                {"description": "Go forward", "result": "next"},
                {"description": "Look around", "result": "explore"}
            ]
        }
    } 