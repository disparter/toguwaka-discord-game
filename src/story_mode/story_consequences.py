from typing import Dict, List, Any, Optional, Union
import json
import logging
from datetime import datetime
from .interfaces import StoryProgressManager

logger = logging.getLogger('tokugawa_bot')

class ChoiceTracker:
    """
    Tracks and analyzes patterns in player choices to adapt future events.
    """
    def __init__(self):
        """Initialize the choice tracker."""
        self.choice_categories = {
            "moral": ["good", "neutral", "evil"],
            "approach": ["diplomatic", "aggressive", "stealthy"],
            "loyalty": ["academy", "rebellion", "independent"]
        }
        
        # Define choice patterns that map to specific consequences
        self.choice_patterns = {
            "consistent_good": {
                "category": "moral",
                "pattern": ["good", "good", "good"],
                "consequence": "respected_by_faculty"
            },
            "consistent_evil": {
                "category": "moral",
                "pattern": ["evil", "evil", "evil"],
                "consequence": "feared_by_students"
            },
            "diplomatic_approach": {
                "category": "approach",
                "pattern": ["diplomatic", "diplomatic"],
                "consequence": "political_connections"
            },
            "aggressive_approach": {
                "category": "approach",
                "pattern": ["aggressive", "aggressive"],
                "consequence": "combat_reputation"
            },
            "academy_loyal": {
                "category": "loyalty",
                "pattern": ["academy", "academy"],
                "consequence": "academy_favor"
            },
            "rebellion_sympathizer": {
                "category": "loyalty",
                "pattern": ["rebellion", "rebellion"],
                "consequence": "rebellion_connections"
            }
        }
    
    def categorize_choice(self, chapter_id: str, choice_key: str, choice_metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Categorizes a player choice based on its metadata.
        
        Args:
            chapter_id: ID of the chapter where the choice was made
            choice_key: Key identifying the choice
            choice_metadata: Metadata about the choice
            
        Returns:
            Dictionary with category and value, or None if choice can't be categorized
        """
        if not choice_metadata or "categories" not in choice_metadata:
            return None
            
        categories = choice_metadata.get("categories", {})
        result = {}
        
        for category, value in categories.items():
            if category in self.choice_categories and value in self.choice_categories[category]:
                result[category] = value
                
        return result if result else None
    
    def analyze_choices(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyzes a player's choices to identify patterns.
        
        Args:
            player_data: Player data containing story choices
            
        Returns:
            List of identified patterns and their consequences
        """
        story_progress = player_data.get("story_progress", {})
        story_choices = story_progress.get("story_choices", {})
        choice_categories = story_progress.get("choice_categories", {})
        
        # If no categorized choices, return empty list
        if not choice_categories:
            return []
            
        # Check for patterns
        identified_patterns = []
        
        for pattern_id, pattern_data in self.choice_patterns.items():
            category = pattern_data["category"]
            pattern = pattern_data["pattern"]
            consequence = pattern_data["consequence"]
            
            # Get the player's choices in this category
            player_choices = choice_categories.get(category, [])
            
            # Check if the pattern is present in the player's choices
            if self._check_pattern(player_choices, pattern):
                identified_patterns.append({
                    "pattern_id": pattern_id,
                    "category": category,
                    "consequence": consequence
                })
                
        return identified_patterns
    
    def _check_pattern(self, choices: List[str], pattern: List[str]) -> bool:
        """
        Checks if a pattern is present in a list of choices.
        
        Args:
            choices: List of player choices
            pattern: Pattern to check for
            
        Returns:
            True if pattern is found, False otherwise
        """
        if len(choices) < len(pattern):
            return False
            
        # Check for consecutive pattern
        for i in range(len(choices) - len(pattern) + 1):
            if choices[i:i+len(pattern)] == pattern:
                return True
                
        # Check for non-consecutive but ordered pattern
        if len(pattern) <= 3:  # Only check for short patterns to avoid performance issues
            i, j = 0, 0
            while i < len(choices) and j < len(pattern):
                if choices[i] == pattern[j]:
                    j += 1
                    if j == len(pattern):
                        return True
                i += 1
                
        return False


class FactionReputationSystem:
    """
    Manages player reputation with different factions.
    """
    def __init__(self):
        """Initialize the faction reputation system."""
        # Define factions and their relationships with each other
        self.factions = {
            "academy_administration": {
                "name": "Administração da Academia",
                "description": "A autoridade oficial que governa a Academia Tokugawa.",
                "allies": ["faculty_council"],
                "rivals": ["student_rebellion", "shadow_society"]
            },
            "faculty_council": {
                "name": "Conselho de Professores",
                "description": "Professores influentes que orientam o currículo e as políticas da academia.",
                "allies": ["academy_administration"],
                "rivals": ["student_rebellion"]
            },
            "student_council": {
                "name": "Conselho Estudantil",
                "description": "Representantes eleitos dos estudantes que organizam eventos e mediam disputas.",
                "allies": ["academy_administration"],
                "rivals": ["shadow_society"]
            },
            "student_rebellion": {
                "name": "Rebelião Estudantil",
                "description": "Um grupo clandestino que busca reformar ou derrubar a hierarquia da academia.",
                "allies": ["outcasts"],
                "rivals": ["academy_administration", "faculty_council"]
            },
            "shadow_society": {
                "name": "Sociedade das Sombras",
                "description": "Uma organização secreta com objetivos misteriosos e influência considerável.",
                "allies": ["outcasts"],
                "rivals": ["academy_administration", "student_council"]
            },
            "outcasts": {
                "name": "Párias",
                "description": "Estudantes marginalizados que não se encaixam na estrutura social da academia.",
                "allies": ["student_rebellion", "shadow_society"],
                "rivals": []
            }
        }
        
        # Define reputation levels and their thresholds
        self.reputation_levels = {
            "hated": -100,
            "hostile": -50,
            "unfriendly": -20,
            "neutral": 0,
            "friendly": 20,
            "respected": 50,
            "honored": 80,
            "revered": 100
        }
    
    def initialize_faction_reputation(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initializes faction reputation for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Updated player data with initialized faction reputation
        """
        story_progress = player_data.get("story_progress", {})
        
        if "faction_reputation" not in story_progress:
            faction_reputation = {}
            
            # Initialize all factions with neutral reputation
            for faction_id in self.factions:
                faction_reputation[faction_id] = 0
                
            story_progress["faction_reputation"] = faction_reputation
            player_data["story_progress"] = story_progress
            
            logger.info(f"Initialized faction reputation for player {player_data.get('user_id')}")
            
        return player_data
    
    def update_faction_reputation(self, player_data: Dict[str, Any], faction_id: str, change: int) -> Dict[str, Any]:
        """
        Updates a player's reputation with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            change: Amount to change reputation by
            
        Returns:
            Updated player data
        """
        if faction_id not in self.factions:
            logger.warning(f"Faction not found: {faction_id}")
            return player_data
            
        # Initialize faction reputation if needed
        player_data = self.initialize_faction_reputation(player_data)
        
        story_progress = player_data["story_progress"]
        faction_reputation = story_progress["faction_reputation"]
        
        # Update reputation
        old_reputation = faction_reputation.get(faction_id, 0)
        new_reputation = old_reputation + change
        
        # Cap reputation at min/max values
        new_reputation = max(-100, min(100, new_reputation))
        
        faction_reputation[faction_id] = new_reputation
        
        # Log reputation change
        logger.info(f"Updated reputation with {self.factions[faction_id]['name']}: {old_reputation} -> {new_reputation} ({change:+})")
        
        # Check if reputation level changed
        old_level = self._get_reputation_level(old_reputation)
        new_level = self._get_reputation_level(new_reputation)
        
        if old_level != new_level:
            logger.info(f"Reputation level with {self.factions[faction_id]['name']} changed: {old_level} -> {new_level}")
            
            # Record reputation level change in player history
            if "reputation_history" not in story_progress:
                story_progress["reputation_history"] = []
                
            story_progress["reputation_history"].append({
                "faction": faction_id,
                "old_level": old_level,
                "new_level": new_level,
                "timestamp": datetime.now().isoformat()
            })
        
        # Update allied and rival factions
        faction_data = self.factions[faction_id]
        
        # Allied factions gain a smaller reputation change in the same direction
        for ally_id in faction_data.get("allies", []):
            if ally_id in faction_reputation:
                ally_change = change // 2  # Half the change
                old_ally_rep = faction_reputation[ally_id]
                new_ally_rep = max(-100, min(100, old_ally_rep + ally_change))
                faction_reputation[ally_id] = new_ally_rep
                logger.info(f"Updated allied faction {self.factions[ally_id]['name']}: {old_ally_rep} -> {new_ally_rep} ({ally_change:+})")
        
        # Rival factions lose reputation (opposite direction)
        for rival_id in faction_data.get("rivals", []):
            if rival_id in faction_reputation:
                rival_change = -change // 3  # One third of the change in opposite direction
                old_rival_rep = faction_reputation[rival_id]
                new_rival_rep = max(-100, min(100, old_rival_rep + rival_change))
                faction_reputation[rival_id] = new_rival_rep
                logger.info(f"Updated rival faction {self.factions[rival_id]['name']}: {old_rival_rep} -> {new_rival_rep} ({rival_change:+})")
        
        # Update player data
        story_progress["faction_reputation"] = faction_reputation
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def get_faction_reputation(self, player_data: Dict[str, Any], faction_id: str) -> int:
        """
        Gets a player's reputation with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            
        Returns:
            Reputation value
        """
        if faction_id not in self.factions:
            logger.warning(f"Faction not found: {faction_id}")
            return 0
            
        story_progress = player_data.get("story_progress", {})
        faction_reputation = story_progress.get("faction_reputation", {})
        
        return faction_reputation.get(faction_id, 0)
    
    def get_faction_reputation_level(self, player_data: Dict[str, Any], faction_id: str) -> str:
        """
        Gets a player's reputation level with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            
        Returns:
            Reputation level as a string
        """
        reputation = self.get_faction_reputation(player_data, faction_id)
        return self._get_reputation_level(reputation)
    
    def _get_reputation_level(self, reputation: int) -> str:
        """
        Gets the reputation level for a reputation value.
        
        Args:
            reputation: Reputation value
            
        Returns:
            Reputation level as a string
        """
        if reputation >= self.reputation_levels["revered"]:
            return "revered"
        elif reputation >= self.reputation_levels["honored"]:
            return "honored"
        elif reputation >= self.reputation_levels["respected"]:
            return "respected"
        elif reputation >= self.reputation_levels["friendly"]:
            return "friendly"
        elif reputation >= self.reputation_levels["neutral"]:
            return "neutral"
        elif reputation >= self.reputation_levels["unfriendly"]:
            return "unfriendly"
        elif reputation >= self.reputation_levels["hostile"]:
            return "hostile"
        else:
            return "hated"
    
    def get_all_faction_reputations(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Gets all faction reputations for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Dictionary mapping faction IDs to reputation data
        """
        story_progress = player_data.get("story_progress", {})
        faction_reputation = story_progress.get("faction_reputation", {})
        
        result = {}
        
        for faction_id, reputation in faction_reputation.items():
            if faction_id in self.factions:
                result[faction_id] = {
                    "name": self.factions[faction_id]["name"],
                    "description": self.factions[faction_id]["description"],
                    "reputation": reputation,
                    "level": self._get_reputation_level(reputation)
                }
                
        return result


class MomentsOfDefinition:
    """
    Creates significant consequences based on past choices.
    """
    def __init__(self, choice_tracker: ChoiceTracker, faction_system: FactionReputationSystem):
        """
        Initialize the Moments of Definition system.
        
        Args:
            choice_tracker: ChoiceTracker instance
            faction_system: FactionReputationSystem instance
        """
        self.choice_tracker = choice_tracker
        self.faction_system = faction_system
        
        # Define moments of definition
        self.moments = {
            "academy_loyalty_test": {
                "description": "Sua lealdade à Academia Tokugawa está sendo testada.",
                "trigger_conditions": {
                    "chapter_completed": ["1_5"],
                    "patterns": ["academy_loyal", "rebellion_sympathizer"]
                },
                "outcomes": {
                    "academy_loyal": {
                        "description": "Sua lealdade à Academia foi reconhecida.",
                        "effects": {
                            "faction_reputation": {"academy_administration": 20},
                            "special_item": "Emblema de Lealdade"
                        }
                    },
                    "rebellion_sympathizer": {
                        "description": "Sua simpatia pela Rebelião foi descoberta.",
                        "effects": {
                            "faction_reputation": {"academy_administration": -20, "student_rebellion": 15},
                            "special_item": "Símbolo da Resistência"
                        }
                    }
                }
            },
            "moral_judgment": {
                "description": "Suas escolhas morais definem como os outros te veem.",
                "trigger_conditions": {
                    "chapter_completed": ["2_3"],
                    "patterns": ["consistent_good", "consistent_evil"]
                },
                "outcomes": {
                    "consistent_good": {
                        "description": "Sua reputação como pessoa justa e boa se espalhou.",
                        "effects": {
                            "faction_reputation": {"faculty_council": 15, "student_council": 15},
                            "hierarchy_points": 10
                        }
                    },
                    "consistent_evil": {
                        "description": "Sua reputação como pessoa impiedosa se espalhou.",
                        "effects": {
                            "faction_reputation": {"shadow_society": 15, "outcasts": 10},
                            "hierarchy_points": 5
                        }
                    }
                }
            },
            "approach_recognition": {
                "description": "Seu estilo de resolver problemas é reconhecido.",
                "trigger_conditions": {
                    "chapter_completed": ["1_8", "2_5"],
                    "patterns": ["diplomatic_approach", "aggressive_approach"]
                },
                "outcomes": {
                    "diplomatic_approach": {
                        "description": "Sua habilidade diplomática é reconhecida.",
                        "effects": {
                            "faction_reputation": {"student_council": 15},
                            "special_item": "Broche de Negociador"
                        }
                    },
                    "aggressive_approach": {
                        "description": "Sua abordagem agressiva é temida e respeitada.",
                        "effects": {
                            "faction_reputation": {"outcasts": 15},
                            "special_item": "Luvas de Combate"
                        }
                    }
                }
            }
        }
    
    def check_for_moments(self, player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Checks if any moments of definition should be triggered.
        
        Args:
            player_data: Player data
            
        Returns:
            Moment data if a moment should be triggered, None otherwise
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        triggered_moments = story_progress.get("triggered_moments", [])
        
        # Analyze player choices
        patterns = self.choice_tracker.analyze_choices(player_data)
        pattern_ids = [p["pattern_id"] for p in patterns]
        
        # Check each moment
        for moment_id, moment_data in self.moments.items():
            # Skip if already triggered
            if moment_id in triggered_moments:
                continue
                
            # Check trigger conditions
            trigger_conditions = moment_data["trigger_conditions"]
            
            # Check required chapters
            required_chapters = trigger_conditions.get("chapter_completed", [])
            if not all(chapter in completed_chapters for chapter in required_chapters):
                continue
                
            # Check required patterns
            required_patterns = trigger_conditions.get("patterns", [])
            matching_patterns = [p for p in required_patterns if p in pattern_ids]
            
            if not matching_patterns:
                continue
                
            # Moment should be triggered
            # Determine outcome based on patterns
            outcome_id = matching_patterns[0]  # Use first matching pattern
            outcome = moment_data["outcomes"].get(outcome_id)
            
            if not outcome:
                continue
                
            logger.info(f"Triggering moment of definition: {moment_id} with outcome {outcome_id}")
            
            return {
                "moment_id": moment_id,
                "description": moment_data["description"],
                "outcome_id": outcome_id,
                "outcome_description": outcome["description"],
                "effects": outcome["effects"]
            }
            
        return None
    
    def trigger_moment(self, player_data: Dict[str, Any], moment_id: str, outcome_id: str) -> Dict[str, Any]:
        """
        Triggers a moment of definition and applies its effects.
        
        Args:
            player_data: Player data
            moment_id: ID of the moment
            outcome_id: ID of the outcome
            
        Returns:
            Updated player data
        """
        if moment_id not in self.moments:
            logger.warning(f"Moment not found: {moment_id}")
            return player_data
            
        moment_data = self.moments[moment_id]
        outcome = moment_data["outcomes"].get(outcome_id)
        
        if not outcome:
            logger.warning(f"Outcome not found: {outcome_id} for moment {moment_id}")
            return player_data
            
        # Apply effects
        effects = outcome["effects"]
        story_progress = player_data.get("story_progress", {})
        
        # Faction reputation changes
        for faction_id, change in effects.get("faction_reputation", {}).items():
            player_data = self.faction_system.update_faction_reputation(player_data, faction_id, change)
            
        # Hierarchy points
        if "hierarchy_points" in effects:
            if "hierarchy_points" not in story_progress:
                story_progress["hierarchy_points"] = 0
            story_progress["hierarchy_points"] += effects["hierarchy_points"]
            
        # Special items
        if "special_item" in effects:
            special_items = story_progress.get("special_items", [])
            if effects["special_item"] not in special_items:
                special_items.append(effects["special_item"])
            story_progress["special_items"] = special_items
            
        # Record that this moment was triggered
        triggered_moments = story_progress.get("triggered_moments", [])
        if moment_id not in triggered_moments:
            triggered_moments.append(moment_id)
        story_progress["triggered_moments"] = triggered_moments
        
        # Record moment in history
        if "moment_history" not in story_progress:
            story_progress["moment_history"] = []
            
        story_progress["moment_history"].append({
            "moment_id": moment_id,
            "outcome_id": outcome_id,
            "description": moment_data["description"],
            "outcome_description": outcome["description"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Update player data
        player_data["story_progress"] = story_progress
        
        logger.info(f"Triggered moment of definition: {moment_id} with outcome {outcome_id}")
        
        return player_data


class DynamicConsequencesSystem:
    """
    Main class for the dynamic consequences system.
    Coordinates the interactions between the different components.
    """
    def __init__(self):
        """Initialize the dynamic consequences system."""
        self.choice_tracker = ChoiceTracker()
        self.faction_system = FactionReputationSystem()
        self.moments = MomentsOfDefinition(self.choice_tracker, self.faction_system)
    
    def initialize_player(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initializes the dynamic consequences system for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Updated player data
        """
        # Initialize faction reputation
        player_data = self.faction_system.initialize_faction_reputation(player_data)
        
        # Initialize choice categories if not present
        story_progress = player_data.get("story_progress", {})
        if "choice_categories" not in story_progress:
            story_progress["choice_categories"] = {}
        if "triggered_moments" not in story_progress:
            story_progress["triggered_moments"] = []
        
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def record_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any, choice_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Records a player's choice and updates the dynamic consequences system.
        
        Args:
            player_data: Player data
            chapter_id: ID of the chapter where the choice was made
            choice_key: Key identifying the choice
            choice_value: Value of the choice
            choice_metadata: Metadata about the choice
            
        Returns:
            Updated player data
        """
        # Initialize player if needed
        player_data = self.initialize_player(player_data)
        
        story_progress = player_data["story_progress"]
        
        # Categorize the choice if metadata is provided
        if choice_metadata:
            categories = self.choice_tracker.categorize_choice(chapter_id, choice_key, choice_metadata)
            
            if categories:
                choice_categories = story_progress.get("choice_categories", {})
                
                for category, value in categories.items():
                    if category not in choice_categories:
                        choice_categories[category] = []
                    
                    choice_categories[category].append(value)
                
                story_progress["choice_categories"] = choice_categories
                logger.debug(f"Categorized choice {choice_key} in chapter {chapter_id}: {categories}")
        
        # Check for moments of definition
        moment = self.moments.check_for_moments(player_data)
        
        if moment:
            player_data = self.moments.trigger_moment(player_data, moment["moment_id"], moment["outcome_id"])
            story_progress = player_data["story_progress"]
            
            # Add moment to result
            if "pending_moments" not in story_progress:
                story_progress["pending_moments"] = []
            
            story_progress["pending_moments"].append(moment)
        
        # Update player data
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def update_faction_reputation(self, player_data: Dict[str, Any], faction_id: str, change: int) -> Dict[str, Any]:
        """
        Updates a player's reputation with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            change: Amount to change reputation by
            
        Returns:
            Updated player data
        """
        return self.faction_system.update_faction_reputation(player_data, faction_id, change)
    
    def get_faction_reputation(self, player_data: Dict[str, Any], faction_id: str) -> int:
        """
        Gets a player's reputation with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            
        Returns:
            Reputation value
        """
        return self.faction_system.get_faction_reputation(player_data, faction_id)
    
    def get_faction_reputation_level(self, player_data: Dict[str, Any], faction_id: str) -> str:
        """
        Gets a player's reputation level with a faction.
        
        Args:
            player_data: Player data
            faction_id: ID of the faction
            
        Returns:
            Reputation level as a string
        """
        return self.faction_system.get_faction_reputation_level(player_data, faction_id)
    
    def get_all_faction_reputations(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Gets all faction reputations for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Dictionary mapping faction IDs to reputation data
        """
        return self.faction_system.get_all_faction_reputations(player_data)
    
    def get_pending_moments(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gets pending moments of definition for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            List of pending moments
        """
        story_progress = player_data.get("story_progress", {})
        pending_moments = story_progress.get("pending_moments", [])
        
        return pending_moments
    
    def clear_pending_moments(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clears pending moments of definition for a player.
        
        Args:
            player_data: Player data
            
        Returns:
            Updated player data
        """
        story_progress = player_data.get("story_progress", {})
        story_progress["pending_moments"] = []
        player_data["story_progress"] = story_progress
        
        return player_data