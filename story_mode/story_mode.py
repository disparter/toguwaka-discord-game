from typing import Dict, List, Any, Optional, Union
import json
import logging
import os
from .interfaces import Chapter, Event, NPC, ChapterLoader, EventManager, StoryProgressManager
from .chapter import BaseChapter, StoryChapter, ChallengeChapter, BranchingChapter
from .event import BaseEvent, ClimacticEvent, RandomEvent, SeasonalEvent, DefaultEventManager
from utils.game_mechanics.events.event_interface import IEvent
from utils.game_mechanics.events.random_event import RandomEvent as GameRandomEvent
from .npc import BaseNPC, StudentNPC, FacultyNPC, NPCManager
from .progress import DefaultStoryProgressManager
from .consequences import DynamicConsequencesSystem
from .powers import PowerEvolutionSystem
from .seasonal_events import SeasonalEventSystem
from .companions import CompanionSystem
from .chapter_validator import ChapterValidator
from .narrative_logger import get_narrative_logger
from .validation import get_story_validator
from .arcs.arc_manager import ArcManager
from .image_manager import ImageManager
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

class FileChapterLoader(ChapterLoader):
    """
    Implementation of ChapterLoader that loads chapters from JSON files.
    """
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.chapters: Dict[str, Chapter] = {}
        self._load_chapters()

    def _load_chapters(self) -> None:
        """Load all chapter files from the data directory."""
        chapter_dir = self.data_dir / "chapters"
        if not chapter_dir.exists():
            logger.warning(f"Chapter directory not found: {chapter_dir}")
            return

        for filename in os.listdir(chapter_dir):
            if filename.endswith(".json"):
                try:
                    chapter_id = filename.replace(".json", "")
                    with open(chapter_dir / filename, 'r') as f:
                        chapter_data = json.load(f)
                        self.chapters[chapter_id] = self._create_chapter(chapter_data)
                except Exception as e:
                    logger.error(f"Error loading chapter {filename}: {e}")

    def _create_chapter(self, chapter_data: Dict[str, Any]) -> Chapter:
        """Create a chapter instance based on the chapter type."""
        chapter_type = chapter_data.get("type", "story")
        if chapter_type == "story":
            return StoryChapter(chapter_data)
        elif chapter_type == "challenge":
            return ChallengeChapter(chapter_data)
        elif chapter_type == "branching":
            return BranchingChapter(chapter_data)
        else:
            logger.warning(f"Unknown chapter type: {chapter_type}, defaulting to StoryChapter")
            return StoryChapter(chapter_data)

    def load_chapter(self, chapter_id: str) -> Chapter:
        """Load a chapter by its ID."""
        if chapter_id not in self.chapters:
            raise ValueError(f"Chapter not found: {chapter_id}")
        return self.chapters[chapter_id]

    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """Get a list of chapter IDs available to the player."""
        available_chapters = []
        for chapter_id, chapter in self.chapters.items():
            if self._is_chapter_available(chapter, player_data):
                available_chapters.append(chapter_id)
        return available_chapters

    def _is_chapter_available(self, chapter: Chapter, player_data: Dict[str, Any]) -> bool:
        """Check if a chapter is available to the player."""
        # Check if the chapter is already completed
        completed_chapters = player_data.get("story_progress", {}).get("completed_chapters", [])
        if chapter.get_id() in completed_chapters:
            return False

        # Check chapter requirements
        requirements = chapter.get_requirements()
        if not requirements:
            return True

        # Check player stats
        player_stats = player_data.get("attributes", {})
        for stat, value in requirements.get("stats", {}).items():
            if player_stats.get(stat, 0) < value:
                return False

        # Check completed chapters
        for required_chapter in requirements.get("chapters", []):
            if required_chapter not in completed_chapters:
                return False

        return True

class StoryMode:
    """
    Main class for the story mode system.
    Coordinates the interactions between the different components.
    """
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize the story mode system.

        Args:
            base_dir: Path to the base directory containing story mode data
        """
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "story_mode"
        self.logs_dir = self.base_dir / "logs"
        self.images_dir = self.base_dir / "assets" / "images" / "story"
        
        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.arc_manager = ArcManager(str(self.data_dir))
        self.event_manager = EventManager(str(self.data_dir))
        self.npc_manager = NPCManager(str(self.data_dir))
        self.image_manager = ImageManager(str(self.images_dir))
        self.progress_manager = DefaultStoryProgressManager()
        self.consequences_system = DynamicConsequencesSystem()
        self.power_system = PowerEvolutionSystem()
        self.seasonal_event_system = SeasonalEventSystem()
        self.companion_system = CompanionSystem()

        # Initialize narrative logger
        self.narrative_logger = get_narrative_logger(str(self.logs_dir / "narrative"))

        # Initialize story validator
        self.validator = get_story_validator()

        # Load and validate story structure
        self.story_data = self._load_story_data()
        self._validate_story_structure()
        
        # Initialize player data
        self.player_data = self._initialize_player_data()
        
        # Preload images for current chapter
        self._preload_current_images()

        logger.info("Story mode system initialized")

    def _load_story_data(self) -> Dict[str, Any]:
        """
        Loads all story data from the story mode directory.
        """
        story_data = {}
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json"):
                try:
                    file_path = self.data_dir / filename
                    with open(file_path, 'r') as f:
                        story_data[filename.replace(".json", "")] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading story data from {filename}: {e}")
        return story_data

    def _validate_story_structure(self) -> None:
        """
        Validates the story structure.
        """
        validation_results = self.arc_manager.validate_story_structure()
        if validation_results["errors"]:
            logger.error("Story structure validation failed:")
            for error in validation_results["errors"]:
                logger.error(f"- {error}")
        if validation_results["warnings"]:
            logger.warning("Story structure validation warnings:")
            for warning in validation_results["warnings"]:
                logger.warning(f"- {warning}")

    def _initialize_player_data(self) -> Dict[str, Any]:
        """
        Initializes player data.
        """
        story_progress = {
            "current_phase": "prologue",
            "completed_chapters": [],
            "academic_progress": 0,
            "club_progress": 0,
            "romance_progress": 0
        }
        
        player_data = {
            "story_progress": story_progress,
            "attributes": {},
            "relationships": {},
            "factions": {}
        }
        
        # Get available chapters
        available_chapters = self.arc_manager.get_available_chapters(player_data)
        story_progress["available_chapters"] = available_chapters
        
        # Log story start
        self.narrative_logger.log_story_start(player_data)
        
        return player_data

    def _preload_current_images(self) -> None:
        """Preload images for the current chapter and its dependencies."""
        current_chapter = self.get_current_chapter()
        if not current_chapter:
            return
        
        images_to_preload = []
        
        # Add background image
        if "background_image" in current_chapter:
            images_to_preload.append(current_chapter["background_image"].replace(".png", ""))
        
        # Add character images
        if "character_images" in current_chapter:
            images_to_preload.extend([
                img.replace(".png", "") for img in current_chapter["character_images"]
            ])
        
        # Add choice images
        if "choices" in current_chapter:
            for choice in current_chapter["choices"]:
                if "image" in choice:
                    images_to_preload.append(choice["image"].replace(".png", ""))
        
        # Preload images
        self.image_manager.preload_images(images_to_preload)

    def get_chapter_image(self, chapter_id: str) -> str:
        """
        Get the background image for a chapter.
        
        Args:
            chapter_id: Chapter identifier
            
        Returns:
            Path to the chapter's background image
        """
        chapter = self.arc_manager.get_chapter(chapter_id)
        if not chapter or "background_image" not in chapter:
            return self.image_manager.get_image_path("image_not_found")
        
        return self.image_manager.get_image_path(
            chapter["background_image"].replace(".png", "")
        )

    def get_character_image(self, character_id: str) -> str:
        """
        Get the image for a character.
        
        Args:
            character_id: Character identifier
            
        Returns:
            Path to the character's image
        """
        image_path = self.image_manager.get_character_image(character_id)
        if not image_path:
            return self.image_manager.get_image_path("image_not_found")
        return image_path

    def get_location_image(self, location_id: str) -> str:
        """
        Get the image for a location.
        
        Args:
            location_id: Location identifier
            
        Returns:
            Path to the location's image
        """
        image_path = self.image_manager.get_location_image(location_id)
        if not image_path:
            return self.image_manager.get_image_path("image_not_found")
        return image_path

    def validate_story_images(self) -> List[str]:
        """
        Validate all image references in the story.
        
        Returns:
            List of missing image references
        """
        return self.image_manager.validate_story_images(self.story_data)

    def start_story(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the story for a new player.
        
        Args:
            player_data: Initial player data
            
        Returns:
            Updated player data
        """
        # Initialize story progress
        story_progress = {
            "current_phase": "prologue",
            "completed_chapters": [],
            "academic_progress": 0,
            "club_progress": 0,
            "romance_progress": 0
        }
        
        player_data["story_progress"] = story_progress
        
        # Get available chapters
        available_chapters = self.arc_manager.get_available_chapters(player_data)
        story_progress["available_chapters"] = available_chapters
        
        # Log story start
        self.narrative_logger.log_story_start(player_data)
        
        return player_data

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Process a player's choice in the current chapter.
        
        Args:
            player_data: Current player data
            choice_index: Index of the chosen option
            
        Returns:
            Updated player data
        """
        # Get current chapter
        current_chapter_id = player_data.get("story_progress", {}).get("current_chapter")
        if not current_chapter_id:
            logger.error("No current chapter found")
            return player_data
            
        chapter = self.arc_manager.get_chapter(current_chapter_id)
        if not chapter:
            logger.error(f"Chapter not found: {current_chapter_id}")
            return player_data
        
        # Process the choice
        try:
            # Get choice data
            choices = chapter.chapter_data.get("choices", [])
            if choice_index >= len(choices):
                logger.error(f"Invalid choice index: {choice_index}")
                return player_data
                
            choice = choices[choice_index]
            
            # Apply choice effects
            if "affinity_change" in choice:
                for npc_id, change in choice["affinity_change"].items():
                    player_data = self.update_affinity(player_data, npc_id, change)
            
            # Check for attribute requirements
            if "attribute_check" in choice:
                attribute = choice["attribute_check"]
                threshold = choice.get("threshold", 0)
                player_attributes = player_data.get("attributes", {})
                attribute_value = player_attributes.get(attribute, 0)
                
                if attribute_value < threshold:
                    # Handle failed check
                    next_dialogue = choice.get("failure_dialogue", 0)
                else:
                    # Handle successful check
                    next_dialogue = choice.get("success_dialogue", 0)
            else:
                next_dialogue = choice.get("next_dialogue", 0)
            
            # Update chapter progress
            if next_dialogue == -1:  # Chapter complete
                player_data = self.arc_manager.process_chapter_completion(player_data, current_chapter_id)
                
                # Get next chapter
                next_chapter = chapter.chapter_data.get("next_chapter")
                if next_chapter:
                    player_data["story_progress"]["current_chapter"] = next_chapter
                else:
                    # Check branches
                    branches = chapter.chapter_data.get("branches", {})
                    for branch_id, branch_data in branches.items():
                        conditions = branch_data.get("conditions", {})
                        if self._check_branch_conditions(conditions, player_data):
                            player_data["story_progress"]["current_chapter"] = branch_data["next_chapter"]
                            break
            
            # Log choice
            self.narrative_logger.log_choice(player_data, current_chapter_id, choice_index)
            
        except Exception as e:
            logger.error(f"Error processing choice: {e}")
        
        return player_data

    def _check_branch_conditions(self, conditions: Dict[str, Any], player_data: Dict[str, Any]) -> bool:
        """
        Check if branch conditions are met.
        
        Args:
            conditions: Branch conditions to check
            player_data: Current player data
            
        Returns:
            True if conditions are met, False otherwise
        """
        # Check choice condition
        if "choice" in conditions:
            last_choice = player_data.get("story_progress", {}).get("last_choice")
            if last_choice != conditions["choice"]:
                return False
        
        # Check check result condition
        if "check_result" in conditions:
            last_check = player_data.get("story_progress", {}).get("last_check_result")
            if last_check != conditions["check_result"]:
                return False
        
        return True

    def update_affinity(self, player_data: Dict[str, Any], npc_id: str, change: int) -> Dict[str, Any]:
        """
        Update affinity with an NPC.
        
        Args:
            player_data: Current player data
            npc_id: ID of the NPC
            change: Amount to change affinity by
            
        Returns:
            Updated player data
        """
        relationships = player_data.get("relationships", {})
        npc_relationship = relationships.get(npc_id, {})
        
        current_affinity = npc_relationship.get("affinity", 0)
        new_affinity = max(0, min(100, current_affinity + change))
        
        npc_relationship["affinity"] = new_affinity
        relationships[npc_id] = npc_relationship
        player_data["relationships"] = relationships
        
        # Log affinity change
        self.narrative_logger.log_affinity_change(player_data, npc_id, change)
        
        return player_data

    def get_story_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the current status of the story.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing story status information
        """
        return self.arc_manager.get_detailed_status(player_data)

    def get_faction_reputation(self, player_data: Dict[str, Any], faction_id: str) -> int:
        """
        Get player's reputation with a faction.
        
        Args:
            player_data: Current player data
            faction_id: ID of the faction
            
        Returns:
            Reputation value
        """
        factions = player_data.get("factions", {})
        return factions.get(faction_id, {}).get("reputation", 0)

    def get_faction_reputation_level(self, player_data: Dict[str, Any], faction_id: str) -> str:
        """
        Get player's reputation level with a faction.
        
        Args:
            player_data: Current player data
            faction_id: ID of the faction
            
        Returns:
            Reputation level name
        """
        reputation = self.get_faction_reputation(player_data, faction_id)
        
        if reputation >= 80:
            return "exalted"
        elif reputation >= 60:
            return "honored"
        elif reputation >= 40:
            return "friendly"
        elif reputation >= 20:
            return "neutral"
        else:
            return "hostile"

    def get_all_faction_reputations(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Get player's reputation with all factions.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary mapping faction IDs to reputation information
        """
        factions = player_data.get("factions", {})
        result = {}
        
        for faction_id, faction_data in factions.items():
            reputation = faction_data.get("reputation", 0)
            result[faction_id] = {
                "reputation": reputation,
                "level": self.get_faction_reputation_level(player_data, faction_id)
            }
        
        return result

    def update_faction_reputation(self, player_data: Dict[str, Any], faction_id: str, change: int) -> Dict[str, Any]:
        """
        Update player's reputation with a faction.
        
        Args:
            player_data: Current player data
            faction_id: ID of the faction
            change: Amount to change reputation by
            
        Returns:
            Updated player data
        """
        factions = player_data.get("factions", {})
        faction_data = factions.get(faction_id, {})
        
        current_reputation = faction_data.get("reputation", 0)
        new_reputation = max(0, min(100, current_reputation + change))
        
        faction_data["reputation"] = new_reputation
        factions[faction_id] = faction_data
        player_data["factions"] = factions
        
        return player_data

    def initialize_player_power(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Initialize a power for the player.
        
        Args:
            player_data: Current player data
            power_id: ID of the power to initialize
            
        Returns:
            Updated player data
        """
        return self.power_system.initialize_power(player_data, power_id)

    def get_player_power(self, player_data: Dict[str, Any], power_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a player's power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power to get
            
        Returns:
            Power information if found, None otherwise
        """
        return self.power_system.get_power(player_data, power_id)

    def get_power_status(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a player's power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power to get status for
            
        Returns:
            Dictionary containing power status information
        """
        return self.power_system.get_power_status(player_data, power_id)

    def unlock_skill_node(self, player_data: Dict[str, Any], power_id: str, node_id: str) -> Dict[str, Any]:
        """
        Unlock a skill node in a power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            node_id: ID of the node to unlock
            
        Returns:
            Updated player data
        """
        return self.power_system.unlock_skill_node(player_data, power_id, node_id)

    def perform_awakening_ritual(self, player_data: Dict[str, Any], power_id: str, ritual_id: str) -> Dict[str, Any]:
        """
        Perform an awakening ritual for a power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            ritual_id: ID of the ritual to perform
            
        Returns:
            Updated player data
        """
        return self.power_system.perform_awakening_ritual(player_data, power_id, ritual_id)

    def complete_power_challenge(self, player_data: Dict[str, Any], power_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Complete a power challenge.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            challenge_id: ID of the challenge to complete
            
        Returns:
            Updated player data
        """
        return self.power_system.complete_challenge(player_data, power_id, challenge_id)

    def get_available_skill_nodes(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Get list of available skill nodes for a power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            
        Returns:
            List of available skill nodes
        """
        return self.power_system.get_available_skill_nodes(player_data, power_id)

    def get_available_awakening_rituals(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Get list of available awakening rituals for a power.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            
        Returns:
            List of available awakening rituals
        """
        return self.power_system.get_available_awakening_rituals(player_data, power_id)

    def get_available_power_challenges(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Get list of available power challenges.
        
        Args:
            player_data: Current player data
            power_id: ID of the power
            
        Returns:
            List of available power challenges
        """
        return self.power_system.get_available_challenges(player_data, power_id)

    def get_current_season_events(self, player_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get current seasonal events.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary mapping event types to lists of available events
        """
        return self.seasonal_event_system.get_current_events(player_data)

    def participate_in_seasonal_event(self, player_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Participate in a seasonal event.
        
        Args:
            player_data: Current player data
            event_id: ID of the event to participate in
            
        Returns:
            Updated player data
        """
        return self.seasonal_event_system.participate_in_event(player_data, event_id)

    def participate_in_mini_game(self, player_data: Dict[str, Any], festival_id: str, mini_game_id: str) -> Dict[str, Any]:
        """
        Participate in a festival mini-game.
        
        Args:
            player_data: Current player data
            festival_id: ID of the festival
            mini_game_id: ID of the mini-game to play
            
        Returns:
            Updated player data
        """
        return self.seasonal_event_system.play_mini_game(player_data, festival_id, mini_game_id)

    def attempt_festival_challenge(self, player_data: Dict[str, Any], festival_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Attempt a festival challenge.
        
        Args:
            player_data: Current player data
            festival_id: ID of the festival
            challenge_id: ID of the challenge to attempt
            
        Returns:
            Updated player data
        """
        return self.seasonal_event_system.attempt_challenge(player_data, festival_id, challenge_id)

    def get_seasonal_event_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get status of current seasonal events.
        
        Args:
            player_data: Current player data
            
        Returns:
            Dictionary containing seasonal event status information
        """
        return self.seasonal_event_system.get_event_status(player_data)

    def get_available_companions(self, player_data: Dict[str, Any], chapter_id: str) -> List[Dict[str, Any]]:
        """
        Get list of available companions for a chapter.
        
        Args:
            player_data: Current player data
            chapter_id: ID of the chapter
            
        Returns:
            List of available companions
        """
        return self.companion_system.get_available_companions(player_data, chapter_id)

    def get_recruited_companions(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get list of recruited companions.
        
        Args:
            player_data: Current player data
            
        Returns:
            List of recruited companions
        """
        return self.companion_system.get_recruited_companions(player_data)

    def get_active_companion(self, player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the currently active companion.
        
        Args:
            player_data: Current player data
            
        Returns:
            Active companion data if any, None otherwise
        """
        return self.companion_system.get_active_companion(player_data)

    def recruit_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Recruit a new companion.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion to recruit
            
        Returns:
            Updated player data
        """
        return self.companion_system.recruit_companion(player_data, companion_id)

    def activate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Activate a companion.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion to activate
            
        Returns:
            Updated player data
        """
        return self.companion_system.activate_companion(player_data, companion_id)

    def deactivate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Deactivate a companion.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion to deactivate
            
        Returns:
            Updated player data
        """
        return self.companion_system.deactivate_companion(player_data, companion_id)

    def advance_companion_arc(self, player_data: Dict[str, Any], companion_id: str, progress_amount: int) -> Dict[str, Any]:
        """
        Advance a companion's story arc.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion
            progress_amount: Amount of progress to add
            
        Returns:
            Updated player data
        """
        return self.companion_system.advance_arc(player_data, companion_id, progress_amount)

    def complete_companion_mission(self, player_data: Dict[str, Any], companion_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Complete a companion mission.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion
            mission_id: ID of the mission to complete
            
        Returns:
            Updated player data
        """
        return self.companion_system.complete_mission(player_data, companion_id, mission_id)

    def perform_sync_ability(self, player_data: Dict[str, Any], companion_id: str, ability_id: str) -> Dict[str, Any]:
        """
        Perform a sync ability with a companion.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion
            ability_id: ID of the ability to perform
            
        Returns:
            Updated player data
        """
        return self.companion_system.perform_sync_ability(player_data, companion_id, ability_id)

    def get_companion_status(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a companion.
        
        Args:
            player_data: Current player data
            companion_id: ID of the companion
            
        Returns:
            Dictionary containing companion status information
        """
        return self.companion_system.get_companion_status(player_data, companion_id)

    def get_all_power_types(self) -> Dict[str, Any]:
        """
        Get information about all available power types.
        
        Returns:
            Dictionary containing power type information
        """
        return self.power_system.get_all_power_types()
