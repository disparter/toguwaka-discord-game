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

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent actual log output during tests."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr('logging.getLogger', MagicMock())
        yield

@pytest.fixture(autouse=True)
def mock_discord():
    """Mock Discord.py to prevent actual Discord API calls during tests."""
    mock_client = MagicMock()
    mock_interaction = MagicMock()
    mock_app_commands = MagicMock()
    mock_commands = MagicMock()
    
    with patch('discord.Client', return_value=mock_client), \
         patch('discord.Interaction', return_value=mock_interaction), \
         patch('discord.app_commands', mock_app_commands), \
         patch('discord.ext.commands', mock_commands):
        yield

@pytest.fixture
def mock_ctx():
    """Mock do contexto do comando"""
    ctx = MagicMock()
    ctx.author.id = 123456789
    ctx.author.name = "TestUser"
    ctx.guild.id = 987654321
    ctx.guild.name = "TestGuild"
    return ctx

@pytest.fixture
def mock_bot():
    """Mock básico do bot"""
    bot = MagicMock()
    bot.user.id = 111111111
    bot.user.name = "TestBot"
    return bot

@pytest.fixture
def mock_db():
    """Mock básico do banco de dados"""
    db = MagicMock()
    db.get_player.return_value = {
        "user_id": 123456789,
        "name": "TestUser",
        "level": 1,
        "exp": 0,
        "tusd": 1000,
        "hp": 100,
        "max_hp": 100,
        "strength": 10,
        "agility": 10,
        "intelligence": 10
    }
    return db

@pytest.fixture
def test_player():
    """Dados de teste para um jogador"""
    return {
        "user_id": 123456789,
        "name": "TestUser",
        "level": 1,
        "exp": 0,
        "tusd": 1000,
        "hp": 100,
        "max_hp": 100,
        "strength": 10,
        "agility": 10,
        "intelligence": 10,
        "inventory": {
            "item1": {
                "id": "item1",
                "name": "Test Item",
                "type": "consumable",
                "effect": "heal"
            }
        }
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
