import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

@pytest.fixture
def story_mode():
    from story_mode.story_mode import StoryMode
    return StoryMode("data/story_mode")

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
                        "type": "dialogue",
                        "dialogue": {
                            "character": {
                                "id": "professor_elementus",
                                "expression": "welcoming"
                            },
                            "text": "Bem-vindo à Academia Tokugawa! Aqui você descobrirá seus poderes e encontrará seu caminho."
                        }
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
                "type": "dialogue",
                "text": "Bem-vindo à Academia Tokugawa!",
                "dialogue": [
                    {
                        "character": "professor_elementus",
                        "text": "Bem-vindo à Academia Tokugawa. Aqui você descobrirá seus poderes e encontrará seu caminho.",
                        "expression": "welcoming"
                    }
                ],
                "choices": [
                    {
                        "text": "Explorar o campus",
                        "type": "story",
                        "effects": {"knowledge": 1},
                        "next_scene": "scene_2"
                    }
                ]
            }
        ]
    }

class TestStoryMode:
    def test_load_story_data_success(self, story_mode, mock_story_data):
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_story_data)
            story_mode.story_data = story_mode._load_story_data()
            assert story_mode.story_data == mock_story_data

    def test_load_story_data_file_not_found(self, story_mode):
        with patch('os.path.exists', return_value=False), \
             patch('builtins.open', MagicMock(side_effect=FileNotFoundError)):
            story_mode.story_data = story_mode._load_story_data()
            assert story_mode.story_data == {}

    @pytest.mark.asyncio
    async def test_load_chapter_success(self, story_mode, mock_story_data, mock_chapter_data):
        from story_mode.chapter import StoryChapter

        story_mode.story_data = mock_story_data
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_chapter_data)
            chapter = await story_mode._load_chapter("1_1_arrival")
            assert isinstance(chapter, dict)
            assert chapter == mock_chapter_data

    @pytest.mark.asyncio
    async def test_load_chapter_not_found(self, story_mode, mock_story_data):
        story_mode.story_data = mock_story_data
        with patch('os.path.exists', return_value=False):
            chapter = await story_mode._load_chapter("nonexistent_chapter")
            assert chapter is None

    @pytest.mark.asyncio
    async def test_start_story_success(self, story_mode, mock_story_data, mock_chapter_data):
        story_mode.story_data = mock_story_data
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', MagicMock()) as mock_open, \
             patch.object(story_mode.progress_manager, 'initialize_story_progress', new=AsyncMock(side_effect=lambda pd: {**pd, "story_progress": {"current_chapter": "1_1_arrival"}})), \
             patch.object(story_mode.progress_manager, 'set_current_chapter', new=AsyncMock(side_effect=lambda pd, ch: {**pd, "story_progress": {"current_chapter": ch}})):
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_chapter_data)
            player_data = {"story_progress": {}}
            result = await story_mode.start_story(player_data)
            assert "story_progress" in result
            assert "current_chapter" in result["story_progress"]

    @pytest.mark.asyncio
    async def test_start_story_chapter_not_found(self, story_mode, mock_story_data):
        story_mode.story_data = mock_story_data
        player_data = {"story_progress": {"current_chapter": "nonexistent_chapter"}}
        result = await story_mode.start_story(player_data)
        assert "story_progress" in result
        assert result["story_progress"]["current_chapter"] == "nonexistent_chapter"

    def test_validate_story_data_success(self, story_mode, mock_story_data):
        # Garante que todos os campos obrigatórios estão presentes e completos
        for chapter in mock_story_data["chapters"].values():
            for scene in chapter.get("scenes", []):
                if scene.get("type") == "dialogue":
                    dialogue = scene.get("dialogue", {})
                    assert isinstance(dialogue, dict), "Dialogue deve ser um dicionário"
                    assert "character" in dialogue, "Dialogue deve ter o campo 'character'"
                    assert "text" in dialogue, "Dialogue deve ter o campo 'text'"
        
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