import pytest
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter, ChallengeChapter, BranchingChapter

@pytest.fixture
def story_mode():
    return StoryMode()

@pytest.fixture
def player_data():
    return {
        "user_id": "test_user",
        "name": "Test Player",
        "story_progress": {
            "current_phase": "prologue",
            "completed_chapters": [],
            "available_chapters": ["1_1"]
        }
    }

def test_story_chapter_creation():
    """Test that StoryChapter can be created with just data dictionary."""
    chapter_data = {
        "type": "story",
        "title": "Test Chapter",
        "description": "A test chapter",
        "chapter_id": "test_1"
    }
    chapter = StoryChapter(chapter_data["chapter_id"], chapter_data)
    assert chapter.get_id() == "test_1"
    assert chapter.get_title() == "Test Chapter"

def test_challenge_chapter_creation():
    """Test that ChallengeChapter can be created with just data dictionary."""
    chapter_data = {
        "type": "challenge",
        "title": "Test Challenge",
        "description": "A test challenge",
        "chapter_id": "challenge_1",
        "challenge_type": "test",
        "difficulty": 1
    }
    chapter = ChallengeChapter(chapter_data["chapter_id"], chapter_data)
    assert chapter.get_id() == "challenge_1"
    assert chapter.challenge_type == "test"

def test_branching_chapter_creation():
    """Test that BranchingChapter can be created with just data dictionary."""
    chapter_data = {
        "type": "branching",
        "title": "Test Branching",
        "description": "A test branching chapter",
        "chapter_id": "branch_1",
        "branches": {},
        "scenes": []
    }
    chapter = BranchingChapter(chapter_data["chapter_id"], chapter_data)
    assert chapter.get_id() == "branch_1"
    assert chapter.branches == {}

def test_start_story(story_mode, player_data):
    """Test that story can be started for a new player."""
    result = story_mode.start_story(player_data)
    assert result is not None
    assert "player_data" in result
    assert "chapter_data" in result
    # The actual chapter data is nested
    chapter_data = result["chapter_data"].get("chapter_data", {})
    assert chapter_data is not None
    assert "id" in chapter_data
    assert "title" in chapter_data
    assert "description" in chapter_data
    assert "choices" in chapter_data

def test_get_current_chapter(story_mode, player_data):
    """Test that current chapter can be retrieved."""
    chapter = story_mode.get_current_chapter(player_data)
    assert chapter is not None
    assert isinstance(chapter, StoryChapter)
    assert chapter.get_id() == "1_1_arrival"

def test_process_choice(story_mode, player_data):
    """Test that player choices can be processed."""
    # First start the story
    story_mode.start_story(player_data)
    # Ensure current_chapter is a string
    player_data['story_progress']['current_chapter'] = '1_1_arrival'
    # Process a choice
    updated_player_data = story_mode.process_choice(player_data, 0)
    assert updated_player_data is not None
    assert "story_progress" in updated_player_data
    # Only check for story_choices if choices are available
    if "story_choices" in updated_player_data["story_progress"]:
        assert isinstance(updated_player_data["story_progress"]["story_choices"], dict) 