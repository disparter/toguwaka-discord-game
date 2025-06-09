from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
import json
import logging
from ..interfaces import Chapter, ChapterLoader
from ..chapter import BaseChapter, StoryChapter, ChallengeChapter, BranchingChapter

logger = logging.getLogger('tokugawa_bot')

class BaseArc(ABC):
    """
    Base class for all story arcs in the game.
    Each arc represents a major narrative path (academic, romance, club, etc.).
    """
    
    def __init__(self, arc_id: str, arc_name: str, data_dir: str):
        """
        Initialize a story arc.
        
        Args:
            arc_id: Unique identifier for the arc
            arc_name: Display name of the arc
            data_dir: Directory containing arc data
        """
        self.arc_id = arc_id
        self.arc_name = arc_name
        self.data_dir = data_dir
        self.chapters: Dict[str, Chapter] = {}
        self.chapter_types = {
            "story": StoryChapter,
            "challenge": ChallengeChapter,
            "branching": BranchingChapter,
            "default": BaseChapter
        }
        
        # Load arc data
        self._load_arc_data()
    
    @abstractmethod
    def _load_arc_data(self) -> None:
        """
        Load arc-specific data and chapters.
        Must be implemented by each arc subclass.
        """
        pass
    
    def get_chapter(self, chapter_id: str) -> Optional[Chapter]:
        """
        Get a chapter by its ID.
        Handles chapter suffixes (e.g., "chapter_1_a").
        
        Args:
            chapter_id: ID of the chapter to retrieve
            
        Returns:
            Chapter object if found, None otherwise
        """
        # First try to get the exact chapter
        if chapter_id in self.chapters:
            return self.chapters[chapter_id]
            
        # If not found, try to find a chapter with the same base ID
        base_id = chapter_id.rsplit('_', 1)[0] if '_' in chapter_id else chapter_id
        if base_id in self.chapters:
            # Create a new chapter instance with the suffixed ID
            base_chapter = self.chapters[base_id]
            chapter_data = base_chapter.chapter_data.copy()
            chapter_data["chapter_id"] = chapter_id
            return type(base_chapter)(chapter_id, chapter_data)
            
        return None
    
    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Get list of chapters available to the player in this arc.
        
        Args:
            player_data: Current player data
            
        Returns:
            List of available chapter IDs
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        
        # Filter chapters based on arc-specific requirements
        available = []
        for chapter_id, chapter in self.chapters.items():
            if self._is_chapter_available(chapter, player_data, completed_chapters):
                available.append(chapter_id)
        
        return available
    
    @abstractmethod
    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any], 
                            completed_chapters: List[str]) -> bool:
        """
        Check if a chapter is available to the player.
        Must be implemented by each arc subclass.
        
        Args:
            chapter: Chapter to check
            player_data: Current player data
            completed_chapters: List of completed chapter IDs
            
        Returns:
            True if chapter is available, False otherwise
        """
        pass
    
    def validate_chapter(self, chapter_data: Dict[str, Any]) -> bool:
        """
        Validate chapter data against the schema.
        
        Args:
            chapter_data: Chapter data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation
            if not isinstance(chapter_data, dict):
                return False
                
            required_fields = ["type", "title", "description"]
            if not all(field in chapter_data for field in required_fields):
                return False
                
            # Type-specific validation
            chapter_type = chapter_data.get("type")
            if chapter_type not in self.chapter_types:
                return False
                
            # Additional validation can be added here
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating chapter: {e}")
            return False
    
    def register_chapter(self, chapter_id: str, chapter_data: Dict[str, Any]) -> None:
        """
        Register a new chapter in the arc.
        
        Args:
            chapter_id: ID for the new chapter
            chapter_data: Chapter data
        """
        if not self.validate_chapter(chapter_data):
            logger.error(f"Invalid chapter data for {chapter_id}")
            return
            
        chapter_type = chapter_data.get("type", "default")
        chapter_class = self.chapter_types.get(chapter_type, BaseChapter)
        
        chapter = chapter_class(chapter_id, chapter_data)
        self.chapters[chapter_id] = chapter
        logger.info(f"Registered chapter {chapter_id} in arc {self.arc_id}")
    
    def get_arc_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current status of the arc for the player.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing arc status information
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        
        arc_chapters = [c for c in self.chapters.keys()]
        completed_arc_chapters = [c for c in completed_chapters if c in arc_chapters]
        
        return {
            "arc_id": self.arc_id,
            "arc_name": self.arc_name,
            "total_chapters": len(arc_chapters),
            "completed_chapters": len(completed_arc_chapters),
            "available_chapters": self.get_available_chapters(player_data),
            "progress_percentage": (len(completed_arc_chapters) / len(arc_chapters) * 100) 
                if arc_chapters else 0
        } 