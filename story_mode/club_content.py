from typing import Dict, List, Any, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

class ClubContentManager:
    """
    Manages club-specific content in chapters.
    Handles club-specific dialogue, choices, and effects.
    """
    
    # Club IDs and names
    CLUBS = {
        1: "flames",
        2: "mental",
        3: "political",
        4: "elemental",
        5: "combat"
    }
    
    def __init__(self, data_dir: str):
        """
        Initialize the club content manager.
        
        Args:
            data_dir: Base directory for story data
        """
        self.data_dir = Path(data_dir)
        self.clubs_dir = self.data_dir / "story_mode" / "clubs"
        
    def load_club_chapter(self, chapter_id: str, club_id: int) -> Optional[Dict[str, Any]]:
        """
        Load club-specific chapter data.
        
        Args:
            chapter_id: Chapter ID to load
            club_id: Club ID to get specific content for
            
        Returns:
            Chapter data dictionary or None if not found
        """
        club_name = self.CLUBS.get(club_id)
        if not club_name:
            return None
            
        club_dir = self.clubs_dir / club_name
        chapter_file = club_dir / f"{club_name}_{chapter_id}.json"
        
        if not chapter_file.exists():
            return None
            
        try:
            with open(chapter_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading club chapter {chapter_id} for club {club_name}: {e}")
            return None
            
    def get_club_dialogues(self, chapter_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get all dialogues for a club chapter.
        
        Args:
            chapter_data: Chapter data dictionary
            
        Returns:
            List of dialogue dictionaries
        """
        dialogues = []
        
        # Add initial dialogues
        dialogues.extend(chapter_data.get("dialogues", []))
        
        # Add shared dialogue
        dialogues.extend(chapter_data.get("shared_dialogue", []))
        
        return dialogues
        
    def get_club_choices(self, chapter_data: Dict[str, Any], choice_set: str = "choices") -> List[Dict[str, Any]]:
        """
        Get choices for a club chapter.
        
        Args:
            chapter_data: Chapter data dictionary
            choice_set: Which set of choices to get ("choices" or "choices_2")
            
        Returns:
            List of choice dictionaries
        """
        return chapter_data.get(choice_set, [])
        
    def get_additional_dialogues(self, chapter_data: Dict[str, Any], dialogue_set: str = "additional_dialogues") -> Dict[str, List[Dict[str, str]]]:
        """
        Get additional dialogues for a club chapter.
        
        Args:
            chapter_data: Chapter data dictionary
            dialogue_set: Which set of dialogues to get ("additional_dialogues" or "additional_dialogues_2")
            
        Returns:
            Dictionary of dialogue lists keyed by choice ID
        """
        return chapter_data.get(dialogue_set, {})
        
    def get_club_effects(self, chapter_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get effects for completing a club chapter.
        
        Args:
            chapter_data: Chapter data dictionary
            
        Returns:
            Dictionary of effects
        """
        return {
            "experience": chapter_data.get("completion_exp", 0),
            "tusd": chapter_data.get("completion_tusd", 0),
            "club_reputation": chapter_data.get("club_reputation_gain", 0),
            "skill_gains": chapter_data.get("skill_gains", {}),
            "next_event": chapter_data.get("next_club_event")
        }
        
    def apply_club_effects(self, player_data: Dict[str, Any], effects: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply club-specific effects to player data.
        
        Args:
            player_data: Player data dictionary
            effects: Effects to apply
            
        Returns:
            Updated player data
        """
        if not effects:
            return player_data
            
        # Update experience
        if "experience" in effects:
            player_data["experience"] = player_data.get("experience", 0) + effects["experience"]
            
        # Update TUSD
        if "tusd" in effects:
            player_data["tusd"] = player_data.get("tusd", 0) + effects["tusd"]
            
        # Update club data
        club_data = player_data.get("club", {})
        
        # Update club reputation
        if "club_reputation" in effects:
            club_data["reputation"] = club_data.get("reputation", 0) + effects["club_reputation"]
            
        # Update club experience
        if "experience" in effects:
            club_data["experience"] = club_data.get("experience", 0) + effects["experience"]
            
        # Update skills
        if "skill_gains" in effects:
            skills = player_data.get("skills", {})
            for skill, gain in effects["skill_gains"].items():
                skills[skill] = skills.get(skill, 0) + gain
            player_data["skills"] = skills
            
        # Update next club event
        if "next_event" in effects:
            club_data["next_event"] = effects["next_event"]
            
        player_data["club"] = club_data
        return player_data 