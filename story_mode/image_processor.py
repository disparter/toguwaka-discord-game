from typing import Dict, Any, List
from pathlib import Path

class ImageProcessor:
    def __init__(self, images_dir: str):
        self.images_dir = Path(images_dir)

    def get_chapter_image(self, chapter_id: str) -> str:
        """
        Get the background image for a chapter.
        
        Args:
            chapter_id: Chapter identifier
            
        Returns:
            Path to the chapter's background image
        """
        chapter = self.arc_manager.get_chapter(chapter_id)
        if not chapter or "background_image" not in chapter:
            return 
        
        return self.image_manager.get_image_path(
            chapter["background_image"].replace(".png", "")
        )

    def get_character_image(self, character_id: str) -> str:
        """
        Get the image for a character.
        
        Args:
            character_id: Character identifier
            
        Returns:
            Path to the character's image
        """
        image_path = self.image_manager.get_character_image(character_id)
        if not image_path:
            return self.image_manager.get_image_path("image_not_found")
        return image_path

    def get_location_image(self, location_id: str) -> str:
        """
        Get the image for a location.
        
        Args:
            location_id: Location identifier
            
        Returns:
            Path to the location's image
        """
        image_path = self.image_manager.get_location_image(location_id)
        if not image_path:
            return self.image_manager.get_image_path("image_not_found")
        return image_path

    def validate_story_images(self, story_data: Dict[str, Any]) -> List[str]:
        """
        Validate all image references in the story.
        
        Returns:
            List of missing image references
        """
        return self.image_manager.validate_story_images(story_data) 