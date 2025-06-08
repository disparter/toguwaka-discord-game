import json
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger('tokugawa_bot')

class ReputationManager:
    """
    Manages reputation with clubs, NPCs, and factions.
    Handles reputation items and their effects.
    """
    
    def __init__(self, data_dir: str = "data/story_mode"):
        """
        Initialize the reputation manager.
        
        Args:
            data_dir: Path to the directory containing reputation data
        """
        self.data_dir = Path(data_dir)
        self.reputation_dir = self.data_dir / "reputation"
        self.reputation_dir.mkdir(parents=True, exist_ok=True)
        
        # Load reputation data
        self.reputation_data = self._load_reputation_data()
        
        # Active effects cache
        self.active_effects: Dict[str, List[Dict]] = {}
    
    def _load_reputation_data(self) -> Dict:
        """Load reputation data from files."""
        reputation_data = {
            "clubs": {},
            "npcs": {},
            "factions": {}
        }
        
        # Load club reputation
        club_file = self.reputation_dir / "club_reputation.json"
        if club_file.exists():
            with open(club_file, 'r') as f:
                reputation_data["clubs"] = json.load(f)
        
        # Load NPC reputation
        npc_file = self.reputation_dir / "npc_reputation.json"
        if npc_file.exists():
            with open(npc_file, 'r') as f:
                reputation_data["npcs"] = json.load(f)
        
        # Load faction reputation
        faction_file = self.reputation_dir / "faction_reputation.json"
        if faction_file.exists():
            with open(faction_file, 'r') as f:
                reputation_data["factions"] = json.load(f)
        
        return reputation_data
    
    def _save_reputation_data(self) -> None:
        """Save reputation data to files."""
        # Save club reputation
        with open(self.reputation_dir / "club_reputation.json", 'w') as f:
            json.dump(self.reputation_data["clubs"], f, indent=2)
        
        # Save NPC reputation
        with open(self.reputation_dir / "npc_reputation.json", 'w') as f:
            json.dump(self.reputation_data["npcs"], f, indent=2)
        
        # Save faction reputation
        with open(self.reputation_dir / "faction_reputation.json", 'w') as f:
            json.dump(self.reputation_data["factions"], f, indent=2)
    
    def get_reputation(self, target_id: str, target_type: str = "club") -> float:
        """
        Get reputation value for a target.
        
        Args:
            target_id: ID of the target (club, NPC, or faction)
            target_type: Type of target ("club", "npc", or "faction")
            
        Returns:
            Current reputation value
        """
        if target_type not in self.reputation_data:
            logger.error(f"Invalid reputation target type: {target_type}")
            return 0.0
        
        return self.reputation_data[target_type].get(target_id, 0.0)
    
    def modify_reputation(self, target_id: str, amount: float, target_type: str = "club") -> float:
        """
        Modify reputation with a target.
        
        Args:
            target_id: ID of the target
            amount: Amount to modify reputation by
            target_type: Type of target
            
        Returns:
            New reputation value
        """
        if target_type not in self.reputation_data:
            logger.error(f"Invalid reputation target type: {target_type}")
            return 0.0
        
        current = self.get_reputation(target_id, target_type)
        new_value = max(-100.0, min(100.0, current + amount))
        
        self.reputation_data[target_type][target_id] = new_value
        self._save_reputation_data()
        
        return new_value
    
    def apply_reputation_item(self, item_id: str, player_data: Dict) -> Dict[str, float]:
        """
        Apply a reputation item's effects.
        
        Args:
            item_id: ID of the reputation item
            player_data: Player data dictionary
            
        Returns:
            Dictionary of reputation changes
        """
        # Get item data
        item_data = self._get_reputation_item_data(item_id)
        if not item_data:
            logger.error(f"Invalid reputation item: {item_id}")
            return {}
        
        changes = {}
        
        # Apply effects
        for effect in item_data["effects"]:
            target_type = effect["target_type"]
            target_id = effect["target_id"]
            amount = effect["amount"]
            
            # Apply any multipliers from player status
            if "multiplier" in effect:
                amount *= self._calculate_reputation_multiplier(player_data)
            
            # Apply the change
            new_value = self.modify_reputation(target_id, amount, target_type)
            changes[f"{target_type}:{target_id}"] = new_value
            
            # Add to active effects if temporary
            if effect.get("duration"):
                self._add_active_effect(item_id, effect)
        
        return changes
    
    def _get_reputation_item_data(self, item_id: str) -> Optional[Dict]:
        """Get data for a reputation item."""
        items_file = self.reputation_dir / "reputation_items.json"
        if not items_file.exists():
            return None
        
        with open(items_file, 'r') as f:
            items_data = json.load(f)
        
        return items_data.get(item_id)
    
    def _calculate_reputation_multiplier(self, player_data: Dict) -> float:
        """Calculate reputation multiplier based on player status."""
        multiplier = 1.0
        
        # Check for active effects
        for effect in self.active_effects.get("reputation_boost", []):
            if effect["expires_at"] > datetime.now():
                multiplier *= effect["multiplier"]
        
        # Check player status
        if player_data.get("status", {}).get("reputation_boost"):
            multiplier *= player_data["status"]["reputation_boost"]
        
        return multiplier
    
    def _add_active_effect(self, item_id: str, effect: Dict) -> None:
        """Add a temporary effect to active effects."""
        if item_id not in self.active_effects:
            self.active_effects[item_id] = []
        
        effect["expires_at"] = datetime.now() + timedelta(seconds=effect["duration"])
        self.active_effects[item_id].append(effect)
    
    def get_active_effects(self) -> Dict[str, List[Dict]]:
        """Get all active reputation effects."""
        # Clean expired effects
        for item_id, effects in list(self.active_effects.items()):
            self.active_effects[item_id] = [
                effect for effect in effects
                if effect["expires_at"] > datetime.now()
            ]
            
            if not self.active_effects[item_id]:
                del self.active_effects[item_id]
        
        return self.active_effects
    
    def get_reputation_level(self, target_id: str, target_type: str = "club") -> str:
        """
        Get reputation level for a target.
        
        Args:
            target_id: ID of the target
            target_type: Type of target
            
        Returns:
            Reputation level ("hostile", "neutral", "friendly", etc.)
        """
        reputation = self.get_reputation(target_id, target_type)
        
        if reputation <= -75:
            return "hostile"
        elif reputation <= -25:
            return "unfriendly"
        elif reputation <= 25:
            return "neutral"
        elif reputation <= 75:
            return "friendly"
        else:
            return "allied"
    
    def get_reputation_discount(self, target_id: str, target_type: str = "club") -> float:
        """
        Get discount percentage based on reputation.
        
        Args:
            target_id: ID of the target
            target_type: Type of target
            
        Returns:
            Discount percentage (0.0 to 1.0)
        """
        reputation = self.get_reputation(target_id, target_type)
        
        # Calculate discount based on reputation
        if reputation >= 75:
            return 0.25  # 25% discount
        elif reputation >= 50:
            return 0.15  # 15% discount
        elif reputation >= 25:
            return 0.10  # 10% discount
        elif reputation >= 0:
            return 0.05  # 5% discount
        else:
            return 0.0  # No discount 