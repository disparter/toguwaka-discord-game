from typing import Dict, Any

class ChoiceProcessor:
    @staticmethod
    def apply_effects(player_data: Dict[str, Any], effects: Dict[str, Any]) -> None:
        """
        Apply effects from a choice to player data.
        
        Args:
            player_data: Player data to update
            effects: Effects to apply
        """
        # Update attributes
        if "attributes" in effects:
            for stat, value in effects["attributes"].items():
                current = player_data.get("attributes", {}).get(stat, 0)
                player_data.setdefault("attributes", {})[stat] = current + value
                
        # Update relationships
        if "relationships" in effects:
            for npc_id, change in effects["relationships"].items():
                current = player_data.get("relationships", {}).get(npc_id, 0)
                player_data.setdefault("relationships", {})[npc_id] = current + change
                
        # Update faction reputation
        if "faction_reputation" in effects:
            for faction_id, change in effects["faction_reputation"].items():
                current = player_data.get("factions", {})
                if faction_id in current:
                    current[faction_id]["reputation"] = max(0, min(100, current[faction_id]["reputation"] + change))
                else:
                    current[faction_id] = {"reputation": change}
                player_data["factions"] = current 