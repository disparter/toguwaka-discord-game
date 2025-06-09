from typing import Dict, List, Any
import json
import os
import logging
from ..base_arc import BaseArc
from ...interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class RomanceArc(BaseArc):
    """
    Romance story arc implementation.
    Handles all romance-related chapters and character relationships.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the romance arc.
        
        Args:
            data_dir: Base directory for story data
        """
        super().__init__(
            arc_id="romance",
            arc_name="Romance Routes",
            data_dir=os.path.join(data_dir, "romance")
        )
        
        # Romance-specific attributes
        self.relationship_levels = {
            "stranger": 0,
            "acquaintance": 20,
            "friend": 40,
            "close_friend": 60,
            "romantic_interest": 80,
            "partner": 100
        }
        
        self.required_affinity = {
            "romance_route": 60,
            "confession": 80,
            "dating": 90
        }
    
    def _load_arc_data(self) -> None:
        """
        Load romance arc data and chapters from the chapters directory.
        """
        import glob
        try:
            chapters_dir = os.path.join(self.data_dir, "chapters")
            if not os.path.exists(chapters_dir):
                logger.error(f"Chapters directory not found: {chapters_dir}")
                return
            chapter_files = glob.glob(os.path.join(chapters_dir, "*.json"))
            if not chapter_files:
                logger.error(f"No chapter files found in: {chapters_dir}")
                return
            for chapter_file in chapter_files:
                with open(chapter_file, 'r') as f:
                    chapter_data = json.load(f)
                    chapter_id = chapter_data.get("id") or os.path.splitext(os.path.basename(chapter_file))[0]
                    self.register_chapter(chapter_id, chapter_data)
            logger.info(f"Loaded {len(self.chapters)} romance arc chapters from directory {chapters_dir}")
        except Exception as e:
            logger.error(f"Error loading romance arc data: {e}")
    
    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any], 
                            completed_chapters: List[str]) -> bool:
        """
        Check if a romance chapter is available to the player.
        
        Args:
            chapter: Chapter to check
            player_data: Current player data
            completed_chapters: List of completed chapter IDs
            
        Returns:
            True if chapter is available, False otherwise
        """
        # Get player's relationship data
        relationships = player_data.get("relationships", {})
        
        # Check if this is a character-specific chapter
        character_id = chapter.chapter_data.get("character_id")
        if character_id:
            character_relationship = relationships.get(character_id, {})
            affinity = character_relationship.get("affinity", 0)
            
            # Check affinity requirements
            required_affinity = self.required_affinity.get(chapter.chapter_data.get("type", "romance_route"), 0)
            if affinity < required_affinity:
                return False
        
        # Check prerequisites
        prerequisites = chapter.chapter_data.get("prerequisites", [])
        if prerequisites and not all(p in completed_chapters for p in prerequisites):
            return False
            
        # Check relationship status requirements
        required_status = chapter.chapter_data.get("required_relationship_status")
        if required_status and character_id:
            current_status = character_relationship.get("status", "stranger")
            if current_status != required_status:
                return False
        
        return True
    
    def get_relationship_level(self, affinity: int) -> str:
        """
        Get relationship level based on affinity score.
        
        Args:
            affinity: Current affinity score
            
        Returns:
            Relationship level name
        """
        for level, threshold in sorted(self.relationship_levels.items(), key=lambda x: x[1], reverse=True):
            if affinity >= threshold:
                return level
        return "stranger"
    
    def get_romance_status(self, player_data: Dict[str, Any], character_id: str = None) -> Dict[str, Any]:
        """
        Get detailed romance status for the player.
        
        Args:
            player_data: Current player data
            character_id: Optional specific character to get status for
            
        Returns:
            Dictionary containing romance status information
        """
        relationships = player_data.get("relationships", {})
        
        if character_id:
            # Get status for specific character
            character_relationship = relationships.get(character_id, {})
            affinity = character_relationship.get("affinity", 0)
            
            return {
                "character_id": character_id,
                "affinity": affinity,
                "relationship_level": self.get_relationship_level(affinity),
                "status": character_relationship.get("status", "stranger"),
                "available_routes": self._get_available_routes(affinity),
                "arc_progress": self.get_arc_status(player_data)
            }
        else:
            # Get status for all characters
            all_characters = {}
            for char_id, relationship in relationships.items():
                affinity = relationship.get("affinity", 0)
                all_characters[char_id] = {
                    "affinity": affinity,
                    "relationship_level": self.get_relationship_level(affinity),
                    "status": relationship.get("status", "stranger"),
                    "available_routes": self._get_available_routes(affinity)
                }
            
            return {
                "characters": all_characters,
                "arc_progress": self.get_arc_status(player_data)
            }
    
    def _get_available_routes(self, affinity: int) -> List[str]:
        """
        Get list of available romance routes based on affinity.
        
        Args:
            affinity: Current affinity score
            
        Returns:
            List of available route types
        """
        available = []
        for route, required in self.required_affinity.items():
            if affinity >= required:
                available.append(route)
        return available 