import pytest
import sys
import os
from unittest.mock import MagicMock

# Adiciona o diretório src ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Mock do Discord apenas para os módulos que precisam
@pytest.fixture(autouse=True)
def mock_discord():
    """Mock do Discord para testes unitários."""
    # Mock do módulo discord
    discord_mock = MagicMock()
    sys.modules['discord'] = discord_mock
    sys.modules['discord.ext'] = MagicMock()
    sys.modules['discord.ext.commands'] = MagicMock()
    sys.modules['discord.app_commands'] = MagicMock()
    
    yield discord_mock
    
    # Limpa os mocks após os testes
    if 'discord' in sys.modules:
        del sys.modules['discord']
    if 'discord.ext' in sys.modules:
        del sys.modules['discord.ext']
    if 'discord.ext.commands' in sys.modules:
        del sys.modules['discord.ext.commands']
    if 'discord.app_commands' in sys.modules:
        del sys.modules['discord.app_commands'] 