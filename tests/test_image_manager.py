import unittest
import os
import json
import shutil
from pathlib import Path
from story_mode.image_manager import ImageManager

class TestImageManager(unittest.TestCase):
    """Test suite for the ImageManager class."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path("test_assets/images/story")
        self.image_manager = ImageManager(str(self.test_dir))
        
        # Create test images
        self.test_images = {
            "character_1_intro.png": "character",
            "location_1.png": "location",
            "romantic_scene_1.png": "romantic",
            "clube_das_chamas_intro.png": "clubs",
            "event_1.png": "events"
        }
        
        for image_name in self.test_images:
            (self.test_dir / image_name).touch()
    
    def tearDown(self):
        """Clean up test environment."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test ImageManager initialization."""
        self.assertTrue(self.test_dir.exists())
        self.assertTrue((self.test_dir / "image_not_found.png").exists())
        self.assertTrue((self.test_dir / "image_manifest.json").exists())
    
    def test_image_manifest(self):
        """Test image manifest creation and loading."""
        manifest_path = self.test_dir / "image_manifest.json"
        self.assertTrue(manifest_path.exists())
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        self.assertIn("images", manifest)
        self.assertIn("categories", manifest)
        
        # Check if test images are in manifest
        for image_name in self.test_images:
            self.assertIn(image_name.replace(".png", ""), manifest["images"])
    
    def test_get_image_path(self):
        """Test getting image paths."""
        # Test existing image
        path = self.image_manager.get_image_path("character_1_intro")
        self.assertEqual(path, str(self.test_dir / "character_1_intro.png"))
        
        # Test non-existing image (should return fallback)
        path = self.image_manager.get_image_path("non_existing")
        self.assertEqual(path, str(self.test_dir / "image_not_found.png"))
    
    def test_validate_story_images(self):
        """Test story image validation."""
        story_data = {
            "chapters": {
                "chapter_1": {
                    "background_image": "location_1.png",
                    "character_images": ["character_1_intro.png"],
                    "choices": [
                        {"image": "event_1.png"}
                    ]
                }
            }
        }
        
        missing = self.image_manager.validate_story_images(story_data)
        self.assertEqual(len(missing), 0)
        
        # Test with missing image
        story_data["chapters"]["chapter_1"]["background_image"] = "missing.png"
        missing = self.image_manager.validate_story_images(story_data)
        self.assertIn("missing", missing)
    
    def test_preload_images(self):
        """Test image preloading."""
        images_to_preload = ["character_1_intro", "location_1"]
        self.image_manager.preload_images(images_to_preload)
        
        # Check if images are in cache
        for image_name in images_to_preload:
            self.assertIn(image_name, self.image_manager.image_cache)
    
    def test_get_category_images(self):
        """Test getting images by category."""
        character_images = self.image_manager.get_category_images("characters")
        self.assertIn("character_1_intro", character_images)
        
        location_images = self.image_manager.get_category_images("locations")
        self.assertIn("location_1", location_images)
    
    def test_get_character_image(self):
        """Test getting character images."""
        # Test with existing image
        path = self.image_manager.get_character_image("character_1")
        self.assertEqual(path, str(self.test_dir / "character_1_intro.png"))
        
        # Test with non-existing character
        path = self.image_manager.get_character_image("non_existing")
        self.assertIsNone(path)
    
    def test_get_location_image(self):
        """Test getting location images."""
        # Test with existing image
        path = self.image_manager.get_location_image("location_1")
        self.assertEqual(path, str(self.test_dir / "location_1.png"))
        
        # Test with non-existing location
        path = self.image_manager.get_location_image("non_existing")
        self.assertIsNone(path)
    
    def test_determine_category(self):
        """Test image category determination."""
        categories = {
            "romantic_scene_1": "romantic",
            "clube_das_chamas_intro": "clubs",
            "professor_quantum_intro": "characters",
            "tokugawa_academy_1": "locations",
            "event_1": "events"
        }
        
        for image_name, expected_category in categories.items():
            category = self.image_manager._determine_category(image_name)
            self.assertEqual(category, expected_category)

if __name__ == '__main__':
    unittest.main() 