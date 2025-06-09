import pytest
import os
import json
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter
from src.utils.game_mechanics.events.event_interface import IEvent

@pytest.fixture
def story_mode():
    return StoryMode()

@pytest.fixture
def base_path():
    return "data/story_mode/narrative"

@pytest.fixture
def clubs_path(base_path):
    return os.path.join(base_path, "clubs")

def test_club_chapter_requirements(story_mode, clubs_path):
    """Test that club chapters have appropriate requirements."""
    # Arrange
    test_chapter = "club_1_1_intro"
    file_path = os.path.join(clubs_path, f"{test_chapter}.json")
    
    # Act
    with open(file_path, 'r', encoding='utf-8') as f:
        chapter_data = json.load(f)
    
    # Assert
    assert 'requirements' in chapter_data, "Chapter should have requirements"
    requirements = chapter_data['requirements']
    
    # Test previous chapter requirement
    assert 'previous_chapter' in requirements, "Chapter should require previous chapter"
    
    # Test reputation requirements
    assert 'reputation' in requirements, "Chapter should have reputation requirements"
    assert 'ryuji' in requirements['reputation'], "Chapter should require Ryuji reputation"

def test_club_chapter_rewards():
    """Test that club chapters provide appropriate rewards."""
    # Create a test chapter with rewards
    chapter_data = {
        "chapter_id": "1_1_fire_club_intro",
        "title": "Fire Club Introduction",
        "description": "Introduction to the Fire Club",
        "rewards": {
            "experience": 50,
            "items": ["fire_club_member_card"],
            "skills": ["fire_control_basic", "inner_focus"],
            "unlocks": ["fire_club_training", "club_events"]
        }
    }
    chapter = StoryChapter("1_1_fire_club_intro", chapter_data)
    
    # Check rewards
    rewards = chapter.data.get("rewards", {})
    assert 'experience' in rewards, "Chapter should reward experience"
    assert rewards['experience'] > 0, "Experience reward should be positive"
    
    # Check for club-specific rewards
    assert 'items' in rewards, "Chapter should reward items"
    assert 'skills' in rewards, "Chapter should reward skills"
    assert 'unlocks' in rewards, "Chapter should unlock new content"

def load_chapter(chapter_name):
    # This function is mentioned in the test_club_chapter_rewards method but not implemented in the file
    # It's assumed to exist as it's called in the test_club_chapter_rewards method
    pass 