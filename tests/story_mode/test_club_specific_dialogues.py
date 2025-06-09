import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestClubSpecificDialogues(unittest.TestCase):
    """Tests for club-specific dialogue handling in StoryMode."""
    def setUp(self):
        # Mock the story structure validation
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.story_mode = StoryMode()
        
        # Mock the arc manager's get_available_chapters method
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={
            "main": ["1_1_arrival"],
            "academic": [],
            "romance": [],
            "club": []
        })
        patcher2.start()
        self.addCleanup(patcher2.stop)
        
        # Mock the arc manager's get_chapter method
        patcher3 = patch.object(self.story_mode.arc_manager, 'get_chapter')
        self.mock_get_chapter = patcher3.start()
        self.addCleanup(patcher3.stop)
        
        # Mock the arc manager's validate_story_structure method
        patcher4 = patch.object(self.story_mode.arc_manager, 'validate_story_structure', return_value={
            "errors": [],
            "warnings": [],
            "arcs": {
                "main": {
                    "errors": [],
                    "warnings": []
                },
                "academic": {
                    "errors": [],
                    "warnings": []
                },
                "romance": {
                    "errors": [],
                    "warnings": []
                },
                "club": {
                    "errors": [],
                    "warnings": []
                }
            }
        })
        patcher4.start()
        self.addCleanup(patcher4.stop)
        
        self.story_mode.player_data["story_progress"]["current_chapter"] = "1_1_arrival"
        self.story_mode.player_data["story_progress"]["club_reputation"] = {
            "martial_arts": 50,
            "archery": 30,
            "tea_ceremony": 20
        }

    def test_club_specific_dialogues(self):
        chapter = StoryChapter(
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
                "branches": []
            }
        )
        self.mock_get_chapter.return_value = chapter
        current_chapter = self.story_mode.get_current_chapter(self.story_mode.player_data)
        self.assertIsNotNone(current_chapter)
        self.assertEqual(current_chapter.chapter_id, "1_1_arrival") 