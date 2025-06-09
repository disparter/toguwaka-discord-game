from typing import Dict, List, Any
import json
import os
import logging
from ..base_arc import BaseArc
from ...interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class ClubArc(BaseArc):
    """
    Club story arc implementation.
    Handles all club-related chapters and activities.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the club arc.
        
        Args:
            data_dir: Base directory for story data
        """
        super().__init__(
            arc_id="club",
            arc_name="Club Activities",
            data_dir=os.path.join(data_dir, "club")
        )
        
        # Club-specific attributes
        self.club_levels = {
            "novice": 0,
            "intermediate": 30,
            "advanced": 60,
            "expert": 90,
            "master": 100
        }
        
        self.required_attendance = {
            "novice": 5,
            "intermediate": 15,
            "advanced": 30,
            "expert": 50,
            "master": 75
        }
        
        self.achievement_thresholds = {
            "novice": 1,
            "intermediate": 3,
            "advanced": 5,
            "expert": 8,
            "master": 10
        }
    
    def _load_arc_data(self) -> None:
        """
        Load club arc data and chapters from the chapters directory.
        Handles club-specific content in chapters.
        """
        import glob
        try:
            # Load general club chapters
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

            # Load club-specific chapters from the new narrative/clubs directory (flat, no subfolders)
            clubs_dir = os.path.join("data", "story_mode", "narrative", "clubs")
            if os.path.exists(clubs_dir):
                club_files = glob.glob(os.path.join(clubs_dir, "*.json"))
                for club_file in club_files:
                    with open(club_file, 'r') as f:
                        club_data = json.load(f)
                        chapter_id = club_data.get("chapter_id") or os.path.splitext(os.path.basename(club_file))[0]
                        self.register_chapter(chapter_id, club_data)

            logger.info(f"Loaded {len(self.chapters)} club arc chapters")
        except Exception as e:
            logger.error(f"Error loading club arc data: {e}")
    
    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any], 
                            completed_chapters: List[str]) -> bool:
        """
        Check if a club chapter is available to the player.
        
        Args:
            chapter: Chapter to check
            player_data: Current player data
            completed_chapters: List of completed chapter IDs
            
        Returns:
            True if chapter is available, False otherwise
        """
        # Get player's club data
        club_data = player_data.get("club_data", {})
        
        # Check if this is a club-specific chapter
        club_id = chapter.data.get("club_id")
        if club_id:
            club_progress = club_data.get(club_id, {})
            level = club_progress.get("level", "novice")
            attendance = club_progress.get("attendance", 0)
            achievements = club_progress.get("achievements", [])
            
            # Check level requirements
            required_level = chapter.data.get("required_level", "novice")
            if self.club_levels[level] < self.club_levels[required_level]:
                return False
            
            # Check attendance requirements
            required_attendance = chapter.data.get("required_attendance", 0)
            if attendance < required_attendance:
                return False
            
            # Check achievement requirements
            required_achievements = chapter.data.get("required_achievements", [])
            if required_achievements and not all(a in achievements for a in required_achievements):
                return False
        
        # Check prerequisites
        prerequisites = chapter.data.get("prerequisites", [])
        if prerequisites and not all(p in completed_chapters for p in prerequisites):
            return False
        
        return True
    
    def get_club_level(self, experience: int) -> str:
        """
        Get club level based on experience points.
        
        Args:
            experience: Current experience points
            
        Returns:
            Club level name
        """
        for level, threshold in sorted(self.club_levels.items(), key=lambda x: x[1], reverse=True):
            if experience >= threshold:
                return level
        return "novice"
    
    def get_club_status(self, player_data: Dict[str, Any], club_id: str = None) -> Dict[str, Any]:
        """
        Get detailed club status for the player.
        
        Args:
            player_data: Current player data
            club_id: Optional specific club to get status for
            
        Returns:
            Dictionary containing club status information
        """
        club_data = player_data.get("club_data", {})
        
        if club_id:
            # Get status for specific club
            club_progress = club_data.get(club_id, {})
            experience = club_progress.get("experience", 0)
            attendance = club_progress.get("attendance", 0)
            achievements = club_progress.get("achievements", [])
            
            return {
                "club_id": club_id,
                "experience": experience,
                "level": self.get_club_level(experience),
                "attendance": attendance,
                "achievements": achievements,
                "next_level_requirements": self._get_next_level_requirements(experience, attendance, len(achievements)),
                "arc_progress": self.get_arc_status(player_data)
            }
        else:
            # Get status for all clubs
            all_clubs = {}
            for cid, progress in club_data.items():
                experience = progress.get("experience", 0)
                attendance = progress.get("attendance", 0)
                achievements = progress.get("achievements", [])
                
                all_clubs[cid] = {
                    "experience": experience,
                    "level": self.get_club_level(experience),
                    "attendance": attendance,
                    "achievements": achievements,
                    "next_level_requirements": self._get_next_level_requirements(experience, attendance, len(achievements))
                }
            
            return {
                "clubs": all_clubs,
                "arc_progress": self.get_arc_status(player_data)
            }
    
    def _get_next_level_requirements(self, experience: int, attendance: int, achievements: int) -> Dict[str, Any]:
        """
        Get requirements for reaching the next club level.
        
        Args:
            experience: Current experience points
            attendance: Current attendance count
            achievements: Current number of achievements
            
        Returns:
            Dictionary containing next level requirements
        """
        current_level = self.get_club_level(experience)
        next_level = None
        
        # Find next level
        levels = list(self.club_levels.keys())
        current_index = levels.index(current_level)
        if current_index < len(levels) - 1:
            next_level = levels[current_index + 1]
        
        if not next_level:
            return {
                "next_level": None,
                "experience_required": None,
                "attendance_required": None,
                "achievements_required": None
            }
        
        return {
            "next_level": next_level,
            "experience_required": self.club_levels[next_level] - experience,
            "attendance_required": self.required_attendance[next_level] - attendance,
            "achievements_required": self.achievement_thresholds[next_level] - achievements
        } 