import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestConditionalChapterNavigation(unittest.TestCase):
    """Tests for conditional navigation between chapters in StoryMode."""
    def setUp(self):
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.story_mode = StoryMode()
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={})
        patcher2.start()
        self.addCleanup(patcher2.stop)
        self.story_mode.player_data["story_progress"]["current_chapter"] = "conditional_chapter"
        self.story_mode.player_data["stats"] = {"strength": 10, "intellect": 5}

    def test_conditional_navigation(self):
        with patch.object(self.story_mode.arc_manager, 'get_chapter') as mock_get_chapter:
            chapter = StoryChapter(
                "conditional_chapter",
                {
                    "choices": [
                        {
                            "text": "Fight",
                            "next_chapter": "combat_1",
                            "requirements": {"strength": 10}
                        },
                        {
                            "text": "Study",
                            "next_chapter": "academic_1",
                            "requirements": {"intellect": 5}
                        }
                    ]
                }
            )
            mock_get_chapter.return_value = chapter
            current_chapter = self.story_mode.get_current_chapter()
            self.assertIsNotNone(current_chapter)
            self.assertIn("choices", current_chapter.data)
            available_choices = [c for c in current_chapter.data["choices"] 
                               if all(self.story_mode.player_data["stats"].get(stat, 0) >= req 
                                     for stat, req in c.get("requirements", {}).items())]
            self.assertEqual(len(available_choices), 2) 