from typing import Dict, List, Any
import json
import os
import logging
from ..base_arc import BaseArc
from ...interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class AcademicArc(BaseArc):
    """
    Academic story arc implementation.
    Handles all academic-related chapters and progression.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the academic arc.
        
        Args:
            data_dir: Base directory for story data
        """
        super().__init__(
            arc_id="academic",
            arc_name="Academic Journey",
            data_dir=os.path.join(data_dir, "academic")
        )
        
        # Academic-specific attributes
        self.required_courses = {
            "year_1": ["history", "literature", "mathematics"],
            "year_2": ["advanced_history", "advanced_literature", "advanced_mathematics"],
            "year_3": ["specialized_history", "specialized_literature", "specialized_mathematics"]
        }
        
        self.min_grades = {
            "year_1": 60,
            "year_2": 70,
            "year_3": 80
        }
    
    def _load_arc_data(self) -> None:
        """
        Load academic arc data and chapters from the chapters directory.
        """
        import glob
        try:
            chapters_dir = os.path.join("data", "story_mode", "narrative", "academic")
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
            logger.info(f"Loaded {len(self.chapters)} academic arc chapters from directory {chapters_dir}")
        except Exception as e:
            logger.error(f"Error loading academic arc data: {e}")
    
    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any], 
                            completed_chapters: List[str]) -> bool:
        """
        Check if an academic chapter is available to the player.
        
        Args:
            chapter: Chapter to check
            player_data: Current player data
            completed_chapters: List of completed chapter IDs
            
        Returns:
            True if chapter is available, False otherwise
        """
        # Get player's academic progress
        academic_progress = player_data.get("academic_progress", {})
        current_year = academic_progress.get("current_year", 1)
        
        # Check year requirements
        chapter_year = self._get_chapter_year(chapter.chapter_id)
        if chapter_year > current_year:
            return False
            
        # Check prerequisites
        prerequisites = chapter.chapter_data.get("prerequisites", [])
        if prerequisites and not all(p in completed_chapters for p in prerequisites):
            return False
            
        # Check course requirements
        required_courses = self.required_courses.get(f"year_{chapter_year}", [])
        completed_courses = academic_progress.get("completed_courses", [])
        
        if required_courses and not all(c in completed_courses for c in required_courses):
            return False
            
        # Check grade requirements
        min_grade = self.min_grades.get(f"year_{chapter_year}", 60)
        current_gpa = academic_progress.get("current_gpa", 0)
        
        if current_gpa < min_grade:
            return False
            
        return True
    
    def _get_chapter_year(self, chapter_id: str) -> int:
        """
        Extract the year from a chapter ID.
        
        Args:
            chapter_id: Chapter ID to parse
            
        Returns:
            Year number (1, 2, or 3)
        """
        try:
            # Assuming chapter IDs follow format: "year_X_chapter_Y"
            year_part = chapter_id.split("_")[1]
            return int(year_part)
        except (IndexError, ValueError):
            return 1  # Default to year 1 if parsing fails
    
    def get_academic_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed academic status for the player.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing academic status information
        """
        academic_progress = player_data.get("academic_progress", {})
        
        return {
            "current_year": academic_progress.get("current_year", 1),
            "current_gpa": academic_progress.get("current_gpa", 0),
            "completed_courses": academic_progress.get("completed_courses", []),
            "current_courses": academic_progress.get("current_courses", []),
            "required_courses": self.required_courses.get(f"year_{academic_progress.get('current_year', 1)}", []),
            "min_required_grade": self.min_grades.get(f"year_{academic_progress.get('current_year', 1)}", 60),
            "arc_progress": self.get_arc_status(player_data)
        } 