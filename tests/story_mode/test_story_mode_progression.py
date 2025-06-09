import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import unittest
from unittest.mock import MagicMock, patch
from story_mode.story_mode import StoryMode
from story_mode.chapter import StoryChapter

class TestStoryModeProgression(unittest.TestCase):
    """Tests for story progression and choice processing in StoryMode."""
    def setUp(self):
        # Mock the story structure validation
        patcher = patch.object(StoryMode, '_validate_story_structure', lambda x: None)
        patcher.start()
        self.addCleanup(patcher.stop)
        
        self.mock_ctx = MagicMock()
        self.mock_ctx.author.id = 123456789
        self.story_mode = StoryMode()
        
        # Mock the arc manager's get_available_chapters method
        patcher2 = patch.object(self.story_mode.arc_manager, 'get_available_chapters', return_value={
            "main": ["1_1_arrival", "1_2_power_awakening"],
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

    def test_story_progression(self):
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
        self.mock_get_chapter.return_value = initial_chapter
        
        with patch('story_mode.progress.DefaultStoryProgressManager.save_progress') as mock_save:
            chapter = self.story_mode.get_current_chapter(self.mock_ctx)
            self.assertIsNotNone(chapter)
            self.assertEqual(chapter.chapter_id, "1_1_arrival")
            
            next_chapter = StoryChapter(
                "1_2_power_awakening",
                {
                    "chapter_id": "1_2_power_awakening",
                    "title": "Power Awakening",
                    "description": "Discover your powers",
                    "phase": "introduction",
                    "requirements": {},
                    "scenes": [],
                    "rewards": {},
                    "next_chapter": "1_3_first_day",
                    "flags": {},
                    "metadata": {},
                    "choices": [{"text": "Dummy", "next_chapter": "1_3_first_day"}]
                }
            )
            next_chapter.get_choices = lambda player_data=None: next_chapter.data["choices"]
            self.mock_get_chapter.return_value = next_chapter
            
            self.story_mode.process_choice(self.story_mode.player_data, 0)
            mock_save.assert_called_once() 