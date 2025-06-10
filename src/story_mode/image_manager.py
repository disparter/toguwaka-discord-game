import os
import json
from typing import Dict, Optional, List
from pathlib import Path

class ImageManager:
    """
    Manages image assets for the story mode, handling loading, validation, and fallback.
    """
    
    def __init__(self, base_dir: str = "assets/images/story"):
        """
        Initialize the image manager.
        
        Args:
            base_dir: Base directory for story images
        """
        self.base_dir = Path(base_dir)
        self.fallback_image = "image_not_found.png"
        self.image_cache: Dict[str, bool] = {}
        self._validate_directory()
        self._load_image_manifest()
    
    def _validate_directory(self) -> None:
        """Ensure the image directory exists and create if necessary."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create fallback image if it doesn't exist
        fallback_path = self.base_dir / self.fallback_image
        if not fallback_path.exists():
            # Create a simple placeholder image
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (800, 600), color='gray')
            d = ImageDraw.Draw(img)
            d.text((400, 300), "Image Not Found", fill='white')
            img.save(fallback_path)
    
    def _load_image_manifest(self) -> None:
        """Load and validate the image manifest."""
        manifest_path = self.base_dir / "image_manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {
                "images": {},
                "categories": {
                    "characters": [],
                    "locations": [],
                    "events": [],
                    "romantic": [],
                    "clubs": []
                }
            }
            self._update_manifest()
    
    def _update_manifest(self) -> None:
        """Update the image manifest with current files."""
        for image_file in self.base_dir.glob("*.png"):
            if image_file.name != self.fallback_image:
                self.manifest["images"][image_file.stem] = {
                    "path": str(image_file.relative_to(self.base_dir)),
                    "category": self._determine_category(image_file.stem)
                }
        
        # Save updated manifest
        with open(self.base_dir / "image_manifest.json", 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _determine_category(self, image_name: str) -> str:
        """Determine the category of an image based on its name."""
        if "romantic" in image_name:
            return "romantic"
        elif "clube" in image_name:
            return "clubs"
        elif any(name in image_name for name in ["professor", "estudante", "colega"]):
            return "characters"
        elif "tokugawa_academy" in image_name:
            return "locations"
        else:
            return "events"
    
    def get_image_path(self, image_name: str) -> str:
        """
        Get the path to an image, with fallback if not found.
        
        Args:
            image_name: Name of the image file (without extension)
            
        Returns:
            Path to the image file
        """
        if image_name in self.image_cache:
            return self.image_cache[image_name]
        
        image_path = self.base_dir / f"{image_name}.png"
        if image_path.exists():
            self.image_cache[image_name] = str(image_path)
            return str(image_path)
        
        # Return fallback image
        fallback_path = self.base_dir / self.fallback_image
        self.image_cache[image_name] = str(fallback_path)
        return str(fallback_path)
    
    def validate_story_images(self, story_data: Dict) -> List[str]:
        """
        Validate all image references in the story data.
        
        Args:
            story_data: The story data dictionary
            
        Returns:
            List of missing image references
        """
        missing_images = []
        
        def check_node_images(node: Dict) -> None:
            if "background_image" in node:
                image_name = node["background_image"].replace(".png", "")
                if not (self.base_dir / f"{image_name}.png").exists():
                    missing_images.append(image_name)
            
            if "character_images" in node:
                for char_image in node["character_images"]:
                    image_name = char_image.replace(".png", "")
                    if not (self.base_dir / f"{image_name}.png").exists():
                        missing_images.append(image_name)
            
            if "choices" in node:
                for choice in node["choices"]:
                    if "image" in choice:
                        image_name = choice["image"].replace(".png", "")
                        if not (self.base_dir / f"{image_name}.png").exists():
                            missing_images.append(image_name)
        
        # Check main story nodes
        for chapter_id, chapter in story_data.get("chapters", {}).items():
            check_node_images(chapter)
            
            # Check dialogues
            for dialogue in chapter.get("dialogues", []):
                check_node_images(dialogue)
        
        return missing_images
    
    def preload_images(self, image_list: List[str]) -> None:
        """
        Preload a list of images into the cache.
        
        Args:
            image_list: List of image names to preload
        """
        for image_name in image_list:
            self.get_image_path(image_name)
    
    def get_category_images(self, category: str) -> List[str]:
        """
        Get all images in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of image names in the category
        """
        return [
            name for name, data in self.manifest["images"].items()
            if data["category"] == category
        ]
    
    def get_character_image(self, character_id: str) -> Optional[str]:
        """
        Get the featured image for a character.
        
        Args:
            character_id: Character identifier
            
        Returns:
            Path to character image or None if not found
        """
        # Try to find character-specific image
        possible_names = [
            f"{character_id}_intro.png",
            f"{character_id}_friendly.png",
            f"{character_id}_neutral.png"
        ]
        
        for name in possible_names:
            if (self.base_dir / name).exists():
                return str(self.base_dir / name)
        
        return None
    
    def get_location_image(self, location_id: str) -> Optional[str]:
        """
        Get the featured image for a location.
        
        Args:
            location_id: Location identifier
            
        Returns:
            Path to location image or None if not found
        """
        # Try to find location-specific image
        possible_names = [
            f"{location_id}.png",
            f"{location_id}_intro.png",
            f"{location_id}_1.png"
        ]
        
        for name in possible_names:
            if (self.base_dir / name).exists():
                return str(self.base_dir / name)
        
        return None 