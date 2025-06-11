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
import discord

# Adiciona o diretório src ao PYTHONPATH antes de qualquer importação dos módulos do projeto
root_dir = Path(__file__).parent.parent
src_dir = root_dir / "src"
sys.path.insert(0, str(src_dir))

# Configura variáveis de ambiente para testes
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Patch boto3 e importe db_provider ANTES de qualquer teste
@pytest.fixture(scope="session", autouse=True)
def patch_boto3_and_import_db_provider():
    mock_table = MagicMock()
    mock_table.table_status = "ACTIVE"
    mock_table.put_item.return_value = True
    mock_table.get_item.return_value = {"Item": {}}
    mock_table.query.return_value = {"Items": []}
    mock_table.scan.return_value = {"Items": []}
    mock_table.update_item.return_value = True
    mock_table.delete_item.return_value = True

    mock_resource = MagicMock()
    mock_resource.Table.return_value = mock_table

    mock_client = MagicMock()
    mock_client.describe_table.return_value = {"Table": {"TableStatus": "ACTIVE"}}

    with patch('boto3.resource', return_value=mock_resource), \
         patch('boto3.client', return_value=mock_client):
        # Importa o singleton já mockado
        import utils.persistence.db_provider
        yield

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
    """Create a mock bot for testing."""
    bot = MagicMock()
    bot.user = MagicMock()
    bot.user.display_name = "Test Bot"
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

@pytest.fixture
def mock_interaction():
    """Create a mock interaction for testing."""
    interaction = MagicMock()
    interaction.user = MagicMock()
    interaction.user.id = 123456789
    interaction.user.mention = "<@123456789>"
    interaction.response = MagicMock()
    interaction.followup = MagicMock()
    return interaction

@pytest.fixture(autouse=True)
def mock_db_functions():
    """Mock database functions to avoid circular imports."""
    with patch('utils.persistence.dynamodb_players.get_player') as mock_get_player, \
         patch('utils.persistence.dynamodb_players.update_player') as mock_update_player, \
         patch('utils.persistence.dynamodb_item_usage.track_item_usage') as mock_track_usage, \
         patch('utils.persistence.dynamodb_item_usage.get_item_usage_count') as mock_get_usage_count, \
         patch('utils.persistence.dynamodb_item_usage.increment_item_usage') as mock_increment_usage:
        yield {
            'get_player': mock_get_player,
            'update_player': mock_update_player,
            'track_item_usage': mock_track_usage,
            'get_item_usage_count': mock_get_usage_count,
            'increment_item_usage': mock_increment_usage
        } 