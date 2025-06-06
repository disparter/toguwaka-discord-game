from typing import Dict, List, Any, Optional, Union
import json
import logging
from .interfaces import NPC

logger = logging.getLogger('tokugawa_bot')

class BaseNPC(NPC):
    """
    Base implementation of the NPC interface.
    Provides common functionality for all NPC types.
    """
    def __init__(self, npc_id: str, data: Dict[str, Any]):
        """
        Initialize an NPC with its data.
        
        Args:
            npc_id: Unique identifier for the NPC
            data: Dictionary containing NPC data
        """
        self.npc_id = npc_id
        self.data = data
        self.name = data.get("name", "Unknown NPC")
        self.background = data.get("background", {})
        self.dialogues = data.get("dialogues", {})
        self.affinity_thresholds = data.get("affinity_thresholds", {
            "hostile": -50,
            "unfriendly": -20,
            "neutral": 0,
            "friendly": 20,
            "close": 50,
            "trusted": 80
        })
        
    def get_name(self) -> str:
        """Returns the NPC's name."""
        return self.name
    
    def get_background(self) -> Dict[str, str]:
        """Returns the NPC's background information."""
        return self.background
    
    def get_affinity(self, player_data: Dict[str, Any]) -> int:
        """Returns the player's affinity level with this NPC."""
        story_progress = player_data.get("story_progress", {})
        character_relationships = story_progress.get("character_relationships", {})
        return character_relationships.get(self.name, 0)
    
    def get_affinity_level(self, player_data: Dict[str, Any]) -> str:
        """Returns the player's affinity level with this NPC as a string."""
        affinity = self.get_affinity(player_data)
        
        if affinity >= self.affinity_thresholds["trusted"]:
            return "trusted"
        elif affinity >= self.affinity_thresholds["close"]:
            return "close"
        elif affinity >= self.affinity_thresholds["friendly"]:
            return "friendly"
        elif affinity >= self.affinity_thresholds["neutral"]:
            return "neutral"
        elif affinity >= self.affinity_thresholds["unfriendly"]:
            return "unfriendly"
        else:
            return "hostile"
    
    def update_affinity(self, player_data: Dict[str, Any], change: int) -> Dict[str, Any]:
        """
        Updates the player's affinity with this NPC and returns updated player data.
        """
        story_progress = player_data.get("story_progress", {})
        character_relationships = story_progress.get("character_relationships", {})
        
        current_affinity = character_relationships.get(self.name, 0)
        new_affinity = current_affinity + change
        
        # Log affinity change
        logger.info(f"Updating affinity with {self.name}: {current_affinity} -> {new_affinity} ({change:+})")
        
        # Check if affinity level changed
        old_level = self._get_affinity_level(current_affinity)
        new_level = self._get_affinity_level(new_affinity)
        
        if old_level != new_level:
            logger.info(f"Affinity level with {self.name} changed: {old_level} -> {new_level}")
        
        # Update affinity
        character_relationships[self.name] = new_affinity
        story_progress["character_relationships"] = character_relationships
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def _get_affinity_level(self, affinity: int) -> str:
        """Helper method to get affinity level from affinity value."""
        if affinity >= self.affinity_thresholds["trusted"]:
            return "trusted"
        elif affinity >= self.affinity_thresholds["close"]:
            return "close"
        elif affinity >= self.affinity_thresholds["friendly"]:
            return "friendly"
        elif affinity >= self.affinity_thresholds["neutral"]:
            return "neutral"
        elif affinity >= self.affinity_thresholds["unfriendly"]:
            return "unfriendly"
        else:
            return "hostile"
    
    def get_dialogue(self, dialogue_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dialogue based on the dialogue ID and player's relationship with the NPC.
        """
        if dialogue_id not in self.dialogues:
            logger.warning(f"Dialogue not found: {dialogue_id} for NPC {self.name}")
            return {"text": f"{self.name} has nothing to say."}
        
        dialogue_options = self.dialogues[dialogue_id]
        
        # Get the player's affinity level with this NPC
        affinity_level = self.get_affinity_level(player_data)
        
        # Check if there's a specific dialogue for this affinity level
        if affinity_level in dialogue_options:
            return dialogue_options[affinity_level]
        
        # Otherwise, use the default dialogue
        if "default" in dialogue_options:
            return dialogue_options["default"]
        
        # If no default, use the first available dialogue
        return next(iter(dialogue_options.values()))


class StudentNPC(BaseNPC):
    """
    Implementation of a student NPC with additional student-specific attributes.
    """
    def __init__(self, npc_id: str, data: Dict[str, Any]):
        super().__init__(npc_id, data)
        self.year = data.get("year", 1)
        self.club_id = data.get("club_id")
        self.power = data.get("power", "Unknown")
        self.hierarchy_tier = data.get("hierarchy_tier", 0)
        
    def get_background(self) -> Dict[str, str]:
        """Returns the student NPC's background information with additional student details."""
        background = super().get_background()
        background.update({
            "year": str(self.year),
            "club": self.club_id,
            "power": self.power,
            "hierarchy_tier": str(self.hierarchy_tier)
        })
        return background


class FacultyNPC(BaseNPC):
    """
    Implementation of a faculty NPC with additional faculty-specific attributes.
    """
    def __init__(self, npc_id: str, data: Dict[str, Any]):
        super().__init__(npc_id, data)
        self.position = data.get("position", "Teacher")
        self.subject = data.get("subject", "Unknown")
        self.years_teaching = data.get("years_teaching", 0)
        
    def get_background(self) -> Dict[str, str]:
        """Returns the faculty NPC's background information with additional faculty details."""
        background = super().get_background()
        background.update({
            "position": self.position,
            "subject": self.subject,
            "years_teaching": str(self.years_teaching)
        })
        return background


class NPCManager:
    """
    Class for managing NPCs in the story mode.
    """
    def __init__(self):
        self.npcs = {}
        self.npc_types = {
            "student": StudentNPC,
            "faculty": FacultyNPC,
            "default": BaseNPC
        }
    
    def register_npc(self, npc: NPC) -> None:
        """
        Registers an NPC with the manager.
        """
        self.npcs[npc.npc_id] = npc
        logger.info(f"Registered NPC: {npc.get_name()} (ID: {npc.npc_id})")
    
    def register_npc_from_data(self, npc_id: str, data: Dict[str, Any]) -> None:
        """
        Creates and registers an NPC from data.
        """
        npc_type = data.get("type", "default")
        npc_class = self.npc_types.get(npc_type, BaseNPC)
        npc = npc_class(npc_id, data)
        self.register_npc(npc)
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """
        Returns an NPC by ID.
        """
        return self.npcs.get(npc_id)
    
    def get_npc_by_name(self, name: str) -> Optional[NPC]:
        """
        Returns an NPC by name.
        """
        for npc in self.npcs.values():
            if npc.get_name() == name:
                return npc
        return None
    
    def get_all_npcs(self) -> List[NPC]:
        """
        Returns all registered NPCs.
        """
        return list(self.npcs.values())
    
    def load_npcs_from_file(self, file_path: str) -> None:
        """
        Loads NPCs from a JSON file.
        """
        try:
            with open(file_path, 'r') as f:
                npcs_data = json.load(f)
            
            for npc_id, npc_data in npcs_data.items():
                self.register_npc_from_data(npc_id, npc_data)
            
            logger.info(f"Loaded {len(npcs_data)} NPCs from {file_path}")
        except Exception as e:
            logger.error(f"Error loading NPCs from {file_path}: {e}")
    
    def update_affinity(self, player_data: Dict[str, Any], npc_name: str, change: int) -> Dict[str, Any]:
        """
        Updates the player's affinity with an NPC by name and returns updated player data.
        """
        npc = self.get_npc_by_name(npc_name)
        if npc:
            return npc.update_affinity(player_data, change)
        
        # If NPC not found, create a temporary NPC to handle the affinity change
        logger.warning(f"NPC not found: {npc_name}, creating temporary NPC for affinity update")
        temp_npc = BaseNPC(f"temp_{npc_name}", {"name": npc_name})
        return temp_npc.update_affinity(player_data, change)