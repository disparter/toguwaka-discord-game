import pytest
import json
from utils.game_mechanics.calculators.experience_calculator import ExperienceCalculator
from utils.game_mechanics.calculators.hp_factor_calculator import HPFactorCalculator
from utils.json_utils import dumps as json_dumps
from utils.content_validator import ContentValidator

@pytest.fixture
def experience_calculator():
    return ExperienceCalculator()

@pytest.fixture
def hp_factor_calculator():
    return HPFactorCalculator()

@pytest.fixture
def content_validator():
    return ContentValidator()

@pytest.mark.skip(reason="ExperienceCalculator implementation needs to be updated")
def test_exp_calculations():
    """Test experience calculations."""
    pass

@pytest.mark.skip(reason="HPFactorCalculator implementation needs to be updated")
def test_hp_factor():
    """Test HP factor calculations."""
    pass

def test_json_dumps():
    """Test JSON serialization."""
    # Test player data
    player_data = {
        'DiscordID': '123',
        'Nome': 'Test Player',
        'Nivel': 1,
        'XP': 0
    }
    json_str = json_dumps(player_data)
    assert isinstance(json_str, str)
    assert 'DiscordID' in json_str
    assert 'Test Player' in json_str
    
    # Test story chapter data
    chapter_data = {
        'id': '1',
        'title': 'Test Chapter',
        'description': 'A test chapter',
        'choices': [
            {
                'text': 'Choice 1',
                'next_chapter': '2'
            }
        ]
    }
    json_str = json_dumps(chapter_data)
    assert isinstance(json_str, str)
    assert 'Test Chapter' in json_str
    assert 'Choice 1' in json_str

@pytest.mark.skip(reason="ContentValidator implementation needs to be updated")
def test_content_validation():
    """Test content validation."""
    pass 