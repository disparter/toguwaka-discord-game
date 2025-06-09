import pytest
import os
import json
from story_mode.story_mode import StoryMode

@pytest.fixture
def story_mode():
    return StoryMode()

@pytest.fixture
def base_path():
    return "data/story_mode/narrative"

@pytest.fixture
def clubs_path(base_path):
    return os.path.join(base_path, "clubs")

def test_club_chapter_sequence(story_mode, clubs_path):
    """Test that club chapters follow the correct sequence."""
    # Arrange
    club_sequences = {
        "club_1": ["club_1_1_intro", "club_1_2_training", "club_1_3_resolution", "club_1_4_final"],
        "club_2": ["club_2_1_intro", "club_2_2_trouble", "club_2_3_resolution", "club_2_4_final"],
        "club_3": ["club_3_1_intro", "club_3_2_trouble", "club_3_3_resolution", "club_3_4_final"],
        "club_4": ["club_4_1_intro", "club_4_4_final"],
        "club_5": ["club_5_1_intro", "club_5_4_final"]
    }

    # Act & Assert
    for club_id, sequence in club_sequences.items():
        for i in range(len(sequence) - 1):
            current_chapter = sequence[i]
            next_chapter = sequence[i + 1]
            
            current_path = os.path.join(clubs_path, f"{current_chapter}.json")
            next_path = os.path.join(clubs_path, f"{next_chapter}.json")
            
            with open(current_path, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                assert current_data['next_chapter'] == next_chapter, \
                    f"Chapter {current_chapter} should point to {next_chapter}" 