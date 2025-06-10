import pytest
from unittest.mock import patch, MagicMock
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

@pytest.fixture
def story_mode():
    return StoryMode()

@pytest.fixture
def mock_story_data():
    return {
        "chapters": {
            "1_1_arrival": {
                "path": "data/story_mode/narrative/chapters/1_1_arrival.json",
                "title": "Chegada à Academia",
                "description": "O início da jornada do jogador na Academia Tokugawa.",
                "type": "academic",
                "phase": "prologue",
                "scenes": [
                    {
                        "id": "scene_1",
                        "text": "Bem-vindo à Academia Tokugawa!",
                        "choices": [
                            {
                                "text": "Explorar o campus",
                                "next_scene": "scene_2"
                            }
                        ]
                    }
                ]
            }
        },
        "arcs": {},
        "romance_routes": {},
        "club_arcs": {}
    }

@pytest.fixture
def mock_chapter_data():
    return {
        "scenes": [
            {
                "id": "scene_1",
                "text": "Bem-vindo à Academia Tokugawa!",
                "choices": [
                    {
                        "text": "Explorar o campus",
                        "next_scene": "scene_2"
                    }
                ]
            }
        ]
    }

class TestStoryMode:
    def test_load_story_data_success(self, story_mode, mock_story_data):
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"chapters": {"1_1_arrival": {"path": "data/story_mode/narrative/chapters/1_1_arrival.json", "title": "Chegada à Academia", "description": "O início da jornada do jogador na Academia Tokugawa."}}, "arcs": {}, "romance_routes": {}, "club_arcs": {}}'
            story_mode.story_data = story_mode._load_story_data()
            assert story_mode.story_data == mock_story_data

    def test_load_story_data_file_not_found(self, story_mode):
        with patch('builtins.open', MagicMock(side_effect=FileNotFoundError)):
            story_mode.story_data = story_mode._load_story_data()
            assert story_mode.story_data == {}

    def test_load_chapter_success(self, story_mode, mock_story_data, mock_chapter_data):
        story_mode.story_data = mock_story_data
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"scenes": [{"id": "scene_1", "text": "Bem-vindo à Academia Tokugawa!", "choices": [{"text": "Explorar o campus", "next_scene": "scene_2"}]}]}'
            chapter = story_mode._load_chapter("1_1_arrival")
            assert isinstance(chapter, StoryChapter)
            assert chapter.chapter_id == "1_1_arrival"

    def test_load_chapter_not_found(self, story_mode, mock_story_data):
        story_mode.story_data = mock_story_data
        chapter = story_mode._load_chapter("nonexistent_chapter")
        assert chapter is None

    def test_start_story_success(self, story_mode, mock_story_data, mock_chapter_data):
        story_mode.story_data = mock_story_data
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = '{"scenes": [{"id": "scene_1", "text": "Bem-vindo à Academia Tokugawa!", "choices": [{"text": "Explorar o campus", "next_scene": "scene_2"}]}]}'
            player_data = {"story_progress": {}}
            result = story_mode.start_story(player_data)
            assert "error" not in result
            assert "chapter_data" in result

    def test_start_story_chapter_not_found(self, story_mode, mock_story_data):
        story_mode.story_data = mock_story_data
        player_data = {"story_progress": {"current_chapter": "nonexistent_chapter"}}
        result = story_mode.start_story(player_data)
        assert "error" in result
        assert result["error"] == "Chapter nonexistent_chapter not found"

    def test_validate_story_data_success(self, story_mode, mock_story_data):
        story_mode.story_data = mock_story_data
        errors = story_mode.validate_story()
        assert not errors

    def test_validate_story_data_missing_fields(self, story_mode):
        story_mode.story_data = {}
        errors = story_mode.validate_story()
        assert "Story data is empty" in errors

    def test_validate_story_data_missing_required_fields(self, story_mode):
        story_mode.story_data = {"chapters": {}}
        errors = story_mode.validate_story()
        assert "Missing required field: arcs" in errors
        assert "Missing required field: romance_routes" in errors
        assert "Missing required field: club_arcs" in errors 