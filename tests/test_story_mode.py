import os

class TestStoryMode:
    def test_image_management(self):
        """Test image management functionality."""
        # Test chapter image
        chapter_image = self.story_mode.get_chapter_image("chapter_1")
        self.assertTrue(os.path.exists(chapter_image))
        
        # Test character image
        character_image = self.story_mode.get_character_image("character_1")
        self.assertTrue(os.path.exists(character_image))
        
        # Test location image
        location_image = self.story_mode.get_location_image("location_1")
        self.assertTrue(os.path.exists(location_image))
        
        # Test image validation
        missing_images = self.story_mode.validate_story_images()
        self.assertEqual(len(missing_images), 0)
        
        # Test with missing image
        self.story_mode.story_data["chapters"]["chapter_1"]["background_image"] = "missing.png"
        missing_images = self.story_mode.validate_story_images()
        self.assertIn("missing", missing_images) 