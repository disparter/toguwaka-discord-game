import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter
import pytest

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.author.id = 123456789
    return ctx

@pytest.fixture
def story_mode(mock_ctx):
    with patch.object(StoryMode, '_validate_story_structure', lambda x: None):
        story_mode = StoryMode()
        story_mode.player_data["story_progress"]["current_chapter"] = "1_1_arrival"
        return story_mode

@pytest.fixture
def mock_arc_manager(story_mode):
    with patch.object(story_mode.arc_manager, 'get_available_chapters', return_value={
        "main": ["1_1_arrival", "1_2_power_awakening"],
        "academic": [],
        "romance": [],
        "club": []
    }), \
    patch.object(story_mode.arc_manager, 'validate_story_structure', return_value={
        "errors": [],
        "warnings": [],
        "arcs": {
            "main": {"errors": [], "warnings": []},
            "academic": {"errors": [], "warnings": []},
            "romance": {"errors": [], "warnings": []},
            "club": {"errors": [], "warnings": []}
        }
    }):
        yield story_mode.arc_manager

def test_story_progression_initial_chapter(story_mode, mock_ctx, mock_arc_manager):
    """Test that the initial chapter is correctly loaded and displayed."""
    # Arrange
    initial_chapter = StoryChapter(
        "1_1_arrival",
        {
            "chapter_id": "1_1_arrival",
            "title": "Arrival at the Academy",
            "description": "The beginning of your journey",
            "phase": "introduction",
            "requirements": {},
            "scenes": [],
            "rewards": {},
            "next_chapter": "1_2_power_awakening",
            "flags": {},
            "metadata": {},
            "choices": [{"text": "Continue", "next_chapter": "1_2_power_awakening"}]
        }
    )
    initial_chapter.get_choices = lambda player_data=None: initial_chapter.data["choices"]
    
    with patch.object(story_mode.arc_manager, 'get_chapter', return_value=initial_chapter):
        # Act
        chapter = story_mode.get_current_chapter(mock_ctx)
        
        # Assert
        assert chapter is not None
        assert chapter.chapter_id == "1_1_arrival"
        assert chapter.data["title"] == "Arrival at the Academy"
        assert len(chapter.get_choices()) == 1
        assert chapter.get_choices()[0]["next_chapter"] == "1_2_power_awakening"

def test_story_progression_choice_processing(story_mode):
    """Test that story progression properly handles valid choices."""
    # Arrange
    story_mode.player_data = {
        "user_id": "test_user",
        "story_progress": {
            "current_chapter": "1_1_arrival",
            "story_choices": {}
        },
        "club": {}
    }
    # Mock save_progress to avoid DB/table creation
    story_mode.progress_manager.save_progress = MagicMock()
    # Use a real StoryChapter with the correct structure
    chapter_data = {
        "chapter_id": "1_1_arrival",
        "title": "Arrival",
        "description": "The beginning",
        "choices": [
            {
                "text": "Accept Power",
                "effects": {
                    "next_chapter": "1_2_power_awakening"
                }
            }
        ]
    }
    real_chapter = StoryChapter("1_1_arrival", chapter_data)
    story_mode.arc_manager.get_chapter = lambda x: real_chapter
    # Act
    story_mode.process_choice(story_mode.player_data, 0)
    # Assert
    assert story_mode.player_data["story_progress"]["current_chapter"] == "1_2_power_awakening"

def test_story_progression_invalid_choice(story_mode):
    """Test that story progression properly handles invalid choices."""
    # Arrange
    story_mode.player_data = {
        "user_id": "test_user",
        "story_progress": {
            "current_chapter": "1_1_arrival",
            "story_choices": {}
        },
        "club": {}
    }
    
    # Create a mock chapter with no choices
    mock_chapter = MagicMock(spec=StoryChapter)
    mock_chapter.chapter_id = "1_1_arrival"
    mock_chapter.get_available_choices.return_value = []
    
    story_mode.arc_manager.get_chapter = lambda x: mock_chapter
    
    # Act
    result = story_mode.process_choice(story_mode.player_data, 99)
    
    # Assert
    assert result == story_mode.player_data  # Should return unchanged player data
    assert story_mode.player_data["story_progress"]["current_chapter"] == "1_1_arrival"  # Should not change chapter 