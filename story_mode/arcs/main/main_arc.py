from typing import Dict, List, Any
import json
import os
import logging
from ..base_arc import BaseArc
from ...interfaces import Chapter

logger = logging.getLogger('tokugawa_bot')

class MainArc(BaseArc):
    """
    Main story arc implementation.
    Handles the primary narrative progression and coordinates with other arcs.
    """
    
    def __init__(self, data_dir: str):
        """
        Initialize the main story arc.
        
        Args:
            data_dir: Base directory for story data
        """
        super().__init__(
            arc_id="main",
            arc_name="Main Story",
            data_dir=os.path.join(data_dir, "main")
        )
        
        # Main story progression attributes
        self.story_phases = {
            "prologue": 0,
            "act_1": 1,
            "act_2": 2,
            "act_3": 3,
            "epilogue": 4
        }
        
        self.required_progress = {
            "act_1": {
                "academic": 20,
                "club": 10,
                "romance": 0
            },
            "act_2": {
                "academic": 40,
                "club": 30,
                "romance": 20
            },
            "act_3": {
                "academic": 60,
                "club": 50,
                "romance": 40
            },
            "epilogue": {
                "academic": 80,
                "club": 70,
                "romance": 60
            }
        }
    
    def _load_arc_data(self) -> None:
        """
        Load main story arc data and chapters from the data/story_mode/arcs/introduction directory.
        """
        import glob
        try:
            # Use the correct absolute path for introduction chapters
            chapters_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "story_mode", "arcs", "introduction")
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
                    chapter_id = os.path.splitext(os.path.basename(chapter_file))[0].replace("chapter_", "")
                    chapter_data["chapter_id"] = chapter_id
                    self.register_chapter(chapter_id, chapter_data)
            logger.info(f"Loaded {len(self.chapters)} main story chapters from directory {chapters_dir}")
        except Exception as e:
            logger.error(f"Error loading main story arc data: {e}")
    
    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any], 
                            completed_chapters: List[str]) -> bool:
        """
        Check if a main story chapter is available to the player.
        
        Args:
            chapter: Chapter to check
            player_data: Current player data
            completed_chapters: List of completed chapter IDs
            
        Returns:
            True if chapter is available, False otherwise
        """
        # Get player's story progress
        story_progress = player_data.get("story_progress", {})
        current_phase = story_progress.get("current_phase", "prologue")
        
        # Check phase requirements
        chapter_phase = chapter.chapter_data.get("phase", "prologue")
        if self.story_phases[chapter_phase] > self.story_phases[current_phase]:
            return False
        
        # Check arc progress requirements
        required_progress = self.required_progress.get(chapter_phase, {})
        if required_progress:
            for arc, required in required_progress.items():
                arc_progress = story_progress.get(f"{arc}_progress", 0)
                if arc_progress < required:
                    return False
        
        # Check prerequisites
        prerequisites = chapter.chapter_data.get("prerequisites", [])
        if prerequisites and not all(p in completed_chapters for p in prerequisites):
            return False
        
        # Check special conditions
        special_conditions = chapter.chapter_data.get("special_conditions", {})
        if special_conditions:
            for condition, value in special_conditions.items():
                if not self._check_special_condition(condition, value, player_data):
                    return False
        
        return True
    
    def _check_special_condition(self, condition: str, value: Any, player_data: Dict[str, Any]) -> bool:
        """
        Check if a special condition is met.
        
        Args:
            condition: Condition to check
            value: Required value
            player_data: Current player data
            
        Returns:
            True if condition is met, False otherwise
        """
        if condition == "has_companion":
            companions = player_data.get("companions", [])
            return value in companions
        elif condition == "min_relationship":
            character_id, min_level = value
            relationships = player_data.get("relationships", {})
            character = relationships.get(character_id, {})
            return character.get("level", 0) >= min_level
        elif condition == "club_membership":
            club_data = player_data.get("club_data", {})
            return value in club_data
        elif condition == "achievement":
            achievements = player_data.get("achievements", [])
            return value in achievements
        return True
    
    def get_story_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed main story status for the player.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing main story status information
        """
        story_progress = player_data.get("story_progress", {})
        current_phase = story_progress.get("current_phase", "prologue")
        
        # Get progress for each arc
        arc_progress = {}
        for arc in ["academic", "club", "romance"]:
            arc_progress[arc] = story_progress.get(f"{arc}_progress", 0)
        
        # Get next phase requirements
        next_phase = self._get_next_phase(current_phase)
        next_phase_requirements = self.required_progress.get(next_phase, {}) if next_phase else None
        
        return {
            "current_phase": current_phase,
            "arc_progress": arc_progress,
            "next_phase": next_phase,
            "next_phase_requirements": next_phase_requirements,
            "completed_chapters": story_progress.get("completed_chapters", []),
            "available_chapters": self.get_available_chapters(player_data),
            "arc_progress": self.get_arc_status(player_data)
        }
    
    def _get_next_phase(self, current_phase: str) -> str:
        """
        Get the next story phase.
        
        Args:
            current_phase: Current story phase
            
        Returns:
            Next phase name or None if at the end
        """
        phases = list(self.story_phases.keys())
        current_index = phases.index(current_phase)
        if current_index < len(phases) - 1:
            return phases[current_index + 1]
        return None
    
    def advance_story_phase(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advance the story to the next phase if requirements are met.
        
        Args:
            player_data: Current player data
            
        Returns:
            Updated player data
        """
        story_progress = player_data.get("story_progress", {})
        current_phase = story_progress.get("current_phase", "prologue")
        
        # Check if we can advance
        next_phase = self._get_next_phase(current_phase)
        if not next_phase:
            return player_data
        
        # Check requirements
        required_progress = self.required_progress.get(next_phase, {})
        can_advance = True
        
        for arc, required in required_progress.items():
            arc_progress = story_progress.get(f"{arc}_progress", 0)
            if arc_progress < required:
                can_advance = False
                break
        
        if can_advance:
            story_progress["current_phase"] = next_phase
            player_data["story_progress"] = story_progress
            logger.info(f"Advanced story to phase: {next_phase}")
        
        return player_data 