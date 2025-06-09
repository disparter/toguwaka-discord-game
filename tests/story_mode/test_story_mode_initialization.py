import unittest
from story_mode.story_mode import StoryMode
from story_mode.chapter_validator import ChapterValidator
import os
import json
from src.utils.game_mechanics.events.event_interface import IEvent

class TestStoryModeInitialization(unittest.TestCase):
    def setUp(self):
        self.story_mode = StoryMode()
        self.validator = ChapterValidator()
        self.base_path = "data/story_mode/narrative"
        self.clubs_path = os.path.join(self.base_path, "clubs")

    def test_club_chapters_exist(self):
        """Test that all club chapter files exist and are valid"""
        club_chapters = [
            "club_1_1_intro", "club_1_2_trouble", "club_1_3_resolution", "club_1_4_final",
            "club_2_1_intro", "club_2_2_trouble", "club_2_3_resolution", "club_2_4_final",
            "club_3_1_intro", "club_3_2_trouble", "club_3_3_resolution", "club_3_4_final",
            "club_4_1_intro", "club_4_4_final",
            "club_5_1_intro", "club_5_4_final"
        ]
        
        for chapter_id in club_chapters:
            file_path = os.path.join(self.clubs_path, f"{chapter_id}.json")
            self.assertTrue(os.path.exists(file_path), f"Chapter file {file_path} does not exist")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                chapter_data = json.load(f)
                self.assertTrue(self.validator.validate_chapter(chapter_data, file_path), 
                              f"Chapter {chapter_id} failed validation")

    def test_club_chapter_structure(self):
        """Test that club chapter files have the correct structure"""
        test_chapter = "club_1_1_intro"
        file_path = os.path.join(self.clubs_path, f"{test_chapter}.json")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            chapter_data = json.load(f)
            
            # Test required fields
            self.assertIn('chapter_id', chapter_data)
            self.assertIn('title', chapter_data)
            self.assertIn('description', chapter_data)
            self.assertIn('phase', chapter_data)
            self.assertIn('requirements', chapter_data)
            self.assertIn('scenes', chapter_data)
            self.assertIn('rewards', chapter_data)
            self.assertIn('next_chapter', chapter_data)
            self.assertIn('flags', chapter_data)
            self.assertIn('metadata', chapter_data)
            
            # Test scene structure
            for scene in chapter_data['scenes']:
                self.assertIn('scene_id', scene)
                self.assertIn('title', scene)
                self.assertIn('description', scene)
                self.assertIn('background', scene)
                self.assertIn('characters', scene)
                self.assertIn('dialogue', scene)
                self.assertIn('choices', scene)

if __name__ == '__main__':
    unittest.main()
