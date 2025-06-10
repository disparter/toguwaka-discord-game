"""
Consequences module for story mode.

This module defines the DynamicConsequencesSystem class that handles the application
and validation of consequences for player choices in the story mode.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger('tokugawa_bot')

class DynamicConsequencesSystem:
    """
    Class for handling consequences of player choices in the story mode.
    """
    
    def __init__(self):
        """Initialize the DynamicConsequencesSystem class."""
        logger.info("DynamicConsequencesSystem class initialized")

    def apply_consequences(self, player_data: Dict[str, Any], choice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply consequences for a player's choice.
        
        Args:
            player_data: The player's current data
            choice_data: The choice data containing consequences
            
        Returns:
            Updated player data with consequences applied
        """
        try:
            # Make a copy of player data to avoid modifying the original
            updated_data = player_data.copy()
            
            # Apply stat changes if any
            if "stat_changes" in choice_data:
                for stat, change in choice_data["stat_changes"].items():
                    if stat in updated_data:
                        updated_data[stat] = updated_data.get(stat, 0) + change
            
            # Apply item rewards if any
            if "item_rewards" in choice_data:
                if "inventory" not in updated_data:
                    updated_data["inventory"] = {}
                
                for item in choice_data["item_rewards"]:
                    item_id = str(item["id"])
                    if item_id in updated_data["inventory"]:
                        updated_data["inventory"][item_id]["quantity"] += 1
                    else:
                        updated_data["inventory"][item_id] = {
                            "id": item["id"],
                            "name": item["name"],
                            "description": item.get("description", ""),
                            "quantity": 1,
                            "type": item.get("type", "consumable"),
                            "rarity": item.get("rarity", "common")
                        }
            
            # Apply currency rewards if any
            if "currency_rewards" in choice_data:
                for currency, amount in choice_data["currency_rewards"].items():
                    if currency in updated_data:
                        updated_data[currency] = updated_data.get(currency, 0) + amount
            
            # Apply reputation changes if any
            if "reputation_change" in choice_data:
                updated_data["reputation"] = updated_data.get("reputation", 0) + choice_data["reputation_change"]
            
            # Apply relationship changes if any
            if "relationship_changes" in choice_data:
                if "relationships" not in updated_data:
                    updated_data["relationships"] = {}
                
                for npc, change in choice_data["relationship_changes"].items():
                    updated_data["relationships"][npc] = updated_data["relationships"].get(npc, 0) + change
            
            return updated_data
            
        except Exception as e:
            logger.error(f"Error applying consequences: {e}")
            return player_data

    def get_available_consequences(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get available consequences for the player's current state.
        
        Args:
            player_data: The player's current data
            
        Returns:
            List of available consequences
        """
        try:
            # This would typically load consequences from a configuration file
            # and filter them based on player state
            return []
        except Exception as e:
            logger.error(f"Error getting available consequences: {e}")
            return []

    def validate_consequences(self, consequences_data: Dict[str, Any]) -> bool:
        """
        Validate if the consequences data is valid.
        
        Args:
            consequences_data: The consequences data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not isinstance(consequences_data, dict):
                return False
            
            # Validate stat changes if present
            if "stat_changes" in consequences_data:
                if not isinstance(consequences_data["stat_changes"], dict):
                    return False
                for stat, change in consequences_data["stat_changes"].items():
                    if not isinstance(change, (int, float)):
                        return False
            
            # Validate item rewards if present
            if "item_rewards" in consequences_data:
                if not isinstance(consequences_data["item_rewards"], list):
                    return False
                for item in consequences_data["item_rewards"]:
                    if not isinstance(item, dict):
                        return False
                    if "id" not in item or "name" not in item:
                        return False
            
            # Validate currency rewards if present
            if "currency_rewards" in consequences_data:
                if not isinstance(consequences_data["currency_rewards"], dict):
                    return False
                for currency, amount in consequences_data["currency_rewards"].items():
                    if not isinstance(amount, (int, float)):
                        return False
            
            # Validate reputation change if present
            if "reputation_change" in consequences_data:
                if not isinstance(consequences_data["reputation_change"], (int, float)):
                    return False
            
            # Validate relationship changes if present
            if "relationship_changes" in consequences_data:
                if not isinstance(consequences_data["relationship_changes"], dict):
                    return False
                for npc, change in consequences_data["relationship_changes"].items():
                    if not isinstance(change, (int, float)):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating consequences: {e}")
            return False 