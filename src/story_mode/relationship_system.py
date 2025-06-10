"""
Relationship system for the Academia Tokugawa Discord bot.
This module provides a class to manage relationships between players and NPCs.
"""

import logging
import json
from typing import Dict, Any, List, Optional

logger = logging.getLogger('tokugawa_bot')

class RelationshipSystem:
    """
    A class to manage relationships between players and NPCs.
    """
    def __init__(self):
        """
        Initialize the relationship system.
        """
        self.relationship_levels = {
            "inimigo": (-100, -51),
            "hostil": (-50, -21),
            "desconfiado": (-20, -1),
            "neutro": (0, 19),
            "amigável": (20, 49),
            "amigo": (50, 79),
            "próximo": (80, 100)
        }
        logger.info("RelationshipSystem initialized")

    def get_relationship_level(self, affinity: int) -> str:
        """
        Get the relationship level based on affinity.

        Args:
            affinity (int): The affinity value

        Returns:
            str: The relationship level
        """
        for level, (min_value, max_value) in self.relationship_levels.items():
            if min_value <= affinity <= max_value:
                return level
        return "neutro"  # Default to neutral if out of range

    def get_relationships(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all relationships for a player.

        Args:
            player_data (Dict[str, Any]): The player data

        Returns:
            List[Dict[str, Any]]: A list of relationships
        """
        story_progress = player_data.get("story_progress", {})
        if not story_progress:
            return []

        relationships = story_progress.get("relationships", {})
        if not relationships:
            return []

        result = []
        for npc, affinity in relationships.items():
            level = self.get_relationship_level(affinity)
            result.append({
                "npc": npc,
                "affinity": affinity,
                "level": level
            })

        # Sort by affinity (descending)
        result.sort(key=lambda x: x["affinity"], reverse=True)
        return result

    def update_affinity(self, player_data: Dict[str, Any], npc: str, change: int) -> Dict[str, Any]:
        """
        Update the affinity with an NPC.

        Args:
            player_data (Dict[str, Any]): The player data
            npc (str): The NPC name
            change (int): The change in affinity

        Returns:
            Dict[str, Any]: The result of the update
        """
        # Ensure story_progress exists
        if "story_progress" not in player_data:
            player_data["story_progress"] = {}

        # Ensure relationships exists
        if "relationships" not in player_data["story_progress"]:
            player_data["story_progress"]["relationships"] = {}

        # Get current affinity
        current_affinity = player_data["story_progress"]["relationships"].get(npc, 0)

        # Calculate new affinity (clamped between -100 and 100)
        new_affinity = max(-100, min(100, current_affinity + change))

        # Update affinity
        player_data["story_progress"]["relationships"][npc] = new_affinity

        # Get relationship level
        level = self.get_relationship_level(new_affinity)

        logger.info(f"Updated affinity for {npc}: {current_affinity} -> {new_affinity} ({level})")

        return {
            "player_data": player_data,
            "affinity_result": {
                "npc": npc,
                "affinity": new_affinity,
                "level": level,
                "change": change
            }
        }

    def check_relationship_requirement(self, player_data: Dict[str, Any], requirement: Dict[str, Any]) -> bool:
        """
        Check if a player meets a relationship requirement.

        Args:
            player_data (Dict[str, Any]): The player data
            requirement (Dict[str, Any]): The requirement to check

        Returns:
            bool: True if the requirement is met, False otherwise
        """
        if "npc" not in requirement or "min_affinity" not in requirement:
            return True  # No valid requirement specified

        npc = requirement["npc"]
        min_affinity = requirement["min_affinity"]

        # Get current affinity
        story_progress = player_data.get("story_progress", {})
        relationships = story_progress.get("relationships", {})
        current_affinity = relationships.get(npc, 0)

        # Check if requirement is met
        return current_affinity >= min_affinity