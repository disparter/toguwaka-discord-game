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

logger = logging.getLogger('tokugawa_bot')

class FileChapterLoader(ChapterLoader):
    """
    Implementation of ChapterLoader that loads chapters from JSON files.
    """
    def __init__(self, chapters_dir: str):
        """
        Initialize the chapter loader with the directory containing chapter files.

        Args:
            chapters_dir: Path to the directory containing chapter JSON files
        """
        self.chapters_dir = chapters_dir
        self.chapters = {}
        self.chapter_types = {
            "story": StoryChapter,
            "challenge": ChallengeChapter,
            "branching": BranchingChapter,
            "default": BaseChapter
        }

        # Load all chapters from the directory
        self._load_chapters()

    def _load_chapters(self) -> None:
        """
        Loads all chapter files from the chapters directory.
        """
        if not os.path.exists(self.chapters_dir):
            logger.warning(f"Chapters directory not found: {self.chapters_dir}")
            return

        for filename in os.listdir(self.chapters_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.chapters_dir, filename)
                    with open(file_path, 'r') as f:
                        chapters_data = json.load(f)

                    # Check if the data is a dictionary with chapter_id or a single chapter
                    if isinstance(chapters_data, dict):
                        if "chapter_id" in chapters_data:
                            # This is a single chapter definition
                            chapter_id = chapters_data.get("chapter_id")
                            self._register_chapter(chapter_id, chapters_data)
                        else:
                            # This is a dictionary of chapters
                            for chapter_id, chapter_data in chapters_data.items():
                                self._register_chapter(chapter_id, chapter_data)

                    logger.info(f"Loaded chapters from {filename}")
                except Exception as e:
                    logger.error(f"Error loading chapters from {filename}: {e}")

    def _register_chapter(self, chapter_id: str, chapter_data: Dict[str, Any]) -> None:
        """
        Creates and registers a chapter from data.
        """
        chapter_type = chapter_data.get("type", "default")
        chapter_class = self.chapter_types.get(chapter_type, BaseChapter)
        chapter = chapter_class(chapter_id, chapter_data)
        self.chapters[chapter_id] = chapter
        logger.info(f"Registered chapter: {chapter.get_title()} (ID: {chapter_id})")

    def load_chapter(self, chapter_id: str) -> Optional[Chapter]:
        """
        Loads a chapter by its ID.
        """
        return self.chapters.get(chapter_id)

    def get_available_chapters(self, player_data: Dict[str, Any], progress_manager=None) -> List[str]:
        """
        Returns a list of chapter IDs available to the player.

        Args:
            player_data: Player data from the database
            progress_manager: Optional progress manager to use for getting available chapters

        Returns:
            List of available chapter IDs that exist in the loader
        """
        if progress_manager:
            # Use the progress manager to get available chapters
            available_chapters = progress_manager.get_next_available_chapters(player_data)
        else:
            # Fallback to the old implementation
            story_progress = player_data.get("story_progress", {})
            completed_chapters = story_progress.get("completed_chapters", [])
            available_chapters = story_progress.get("available_chapters", [])

            # Add the next sequential chapter if applicable
            current_year = story_progress.get("current_year", 1)
            current_chapter = story_progress.get("current_chapter", 1)
            next_chapter = f"{current_year}_{current_chapter + 1}"

            # Combine all available chapters
            available_chapters = list(set(available_chapters + [next_chapter]))

        # Filter out chapters that don't exist in the loader
        return [chapter for chapter in available_chapters if chapter in self.chapters]


class StoryMode:
    """
    Main class for the story mode system.
    Coordinates the interactions between the different components.
    """
    def __init__(self, data_dir: str = "data/story_mode"):
        """
        Initialize the story mode system.

        Args:
            data_dir: Path to the directory containing story mode data
        """
        self.data_dir = data_dir

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "chapters"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "events"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "npcs"), exist_ok=True)

        # Initialize components
        self.chapter_loader = FileChapterLoader(os.path.join(data_dir, "chapters"))
        self.event_manager = DefaultEventManager()
        self.npc_manager = NPCManager()
        self.progress_manager = DefaultStoryProgressManager()
        self.consequences_system = DynamicConsequencesSystem()
        self.power_system = PowerEvolutionSystem()
        self.seasonal_event_system = SeasonalEventSystem()
        self.companion_system = CompanionSystem()

        # Load events and NPCs
        self._load_events()
        self._load_npcs()

        logger.info("Story mode system initialized")

    def _load_events(self) -> None:
        """
        Loads all event files from the events directory.
        Also creates game events from the new SOLID architecture.
        """
        events_dir = os.path.join(self.data_dir, "events")
        if not os.path.exists(events_dir):
            logger.warning(f"Events directory not found: {events_dir}")
            return

        for filename in os.listdir(events_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(events_dir, filename)
                    self.event_manager.load_events_from_file(file_path)

                    # Also create game events from the same file
                    self._create_game_events_from_file(file_path)
                except Exception as e:
                    logger.error(f"Error loading events from {filename}: {e}")

    def _create_game_events_from_file(self, file_path: str) -> None:
        """
        Creates game events from a JSON file using the new SOLID architecture.

        Args:
            file_path: Path to the JSON file containing event data
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Check if the data is a dictionary with an "event_templates" key
            if isinstance(data, dict) and "event_templates" in data:
                events_data = data.get("event_templates", [])

                # If events_data is a list, process each item with an index as event_id
                if isinstance(events_data, list):
                    for index, event_data in enumerate(events_data):
                        event_id = f"event_{index}"
                        # Create a game event using the new SOLID architecture
                        if event_data.get("type") == "random":
                            # Create a random event
                            game_event = GameRandomEvent(
                                event_data.get("title", "Untitled Event"),
                                event_data.get("description", "No description available."),
                                event_data.get("type", "neutral"),
                                event_data.get("effect", {})
                            )

                            # Register the event with the event manager
                            # This would be implemented in a future update to fully integrate
                            # the new event system with the story mode
                            logger.info(f"Created game event: {game_event.get_title()} (ID: {event_id})")
                else:
                    # If events_data is a dictionary, process it as before
                    for event_id, event_data in events_data.items():
                        # Create a game event using the new SOLID architecture
                        if event_data.get("type") == "random":
                            # Create a random event
                            game_event = GameRandomEvent(
                                event_data.get("title", "Untitled Event"),
                                event_data.get("description", "No description available."),
                                event_data.get("type", "neutral"),
                                event_data.get("effect", {})
                            )

                            # Register the event with the event manager
                            # This would be implemented in a future update to fully integrate
                            # the new event system with the story mode
                            logger.info(f"Created game event: {game_event.get_title()} (ID: {event_id})")
            else:
                # If the data doesn't have the expected structure, process it as before
                for event_id, event_data in data.items():
                    # Create a game event using the new SOLID architecture
                    if event_data.get("type") == "random":
                        # Create a random event
                        game_event = GameRandomEvent(
                            event_data.get("title", "Untitled Event"),
                            event_data.get("description", "No description available."),
                            event_data.get("type", "neutral"),
                            event_data.get("effect", {})
                        )

                        # Register the event with the event manager
                        # This would be implemented in a future update to fully integrate
                        # the new event system with the story mode
                        logger.info(f"Created game event: {game_event.get_title()} (ID: {event_id})")

            logger.info(f"Created game events from {file_path}")
        except Exception as e:
            logger.error(f"Error creating game events from {file_path}: {e}")

    def _load_npcs(self) -> None:
        """
        Loads all NPC files from the NPCs directory.
        """
        npcs_dir = os.path.join(self.data_dir, "npcs")
        if not os.path.exists(npcs_dir):
            logger.warning(f"NPCs directory not found: {npcs_dir}")
            return

        for filename in os.listdir(npcs_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(npcs_dir, filename)
                    self.npc_manager.load_npcs_from_file(file_path)
                except Exception as e:
                    logger.error(f"Error loading NPCs from {filename}: {e}")

    def start_story(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts or continues the story mode for a player.

        Args:
            player_data: Player data from the database

        Returns:
            Dict containing updated player data and current chapter data
        """
        # Initialize story progress if needed
        player_data = self.progress_manager.initialize_story_progress(player_data)

        # Initialize dynamic consequences system
        player_data = self.consequences_system.initialize_player(player_data)

        # Get current chapter
        chapter_id = self.progress_manager.get_current_chapter(player_data)
        chapter = self.chapter_loader.load_chapter(chapter_id)

        if not chapter:
            logger.warning(f"Chapter not found: {chapter_id}, using first chapter")
            # Use the first available chapter
            available_chapters = self.chapter_loader.get_available_chapters(player_data, self.progress_manager)
            if available_chapters:
                chapter_id = available_chapters[0]
                chapter = self.chapter_loader.load_chapter(chapter_id)
                player_data = self.progress_manager.set_current_chapter(player_data, chapter_id)
            else:
                logger.error("No chapters available")
                return {"error": "No chapters available"}

        # Start the chapter
        result = chapter.start(player_data)

        # Check for events
        available_events = self.event_manager.check_for_events(result["player_data"])
        if available_events:
            result["available_events"] = [
                {
                    "id": event.event_id,
                    "name": event.get_name(),
                    "description": event.get_description()
                }
                for event in available_events
            ]

        # Check for pending moments of definition
        pending_moments = self.consequences_system.get_pending_moments(result["player_data"])
        if pending_moments:
            result["pending_moments"] = pending_moments

        # Check for available companions in the current chapter
        available_companions = self.get_available_companions(result["player_data"], chapter_id)
        if available_companions:
            result["available_companions"] = available_companions

        # Check for available seasonal events
        available_seasonal_events = self.get_current_season_events(result["player_data"])
        if available_seasonal_events:
            result["available_seasonal_events"] = available_seasonal_events

        return result

    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Processes a player's choice in the current chapter.

        Args:
            player_data: Player data from the database
            choice_index: Index of the chosen option

        Returns:
            Dict containing updated player data and next chapter state
        """
        # Get current chapter
        chapter_id = self.progress_manager.get_current_chapter(player_data)
        chapter = self.chapter_loader.load_chapter(chapter_id)

        if not chapter:
            logger.error(f"Chapter not found: {chapter_id}")
            return {"error": f"Chapter not found: {chapter_id}"}

        # Process the choice
        result = chapter.process_choice(player_data, choice_index)

        # Record the choice in the progress manager
        choice_key = f"choice_{choice_index}"
        self.progress_manager.record_choice(result["player_data"], chapter_id, choice_key, choice_index)

        # Get choice metadata if available
        choice_metadata = None
        if "chapter_data" in result and "choices" in result["chapter_data"]:
            choices = result["chapter_data"]["choices"]
            if choices and len(choices) > choice_index:
                choice_metadata = choices[choice_index].get("metadata", {})

        # Record the choice in the consequences system
        result["player_data"] = self.consequences_system.record_choice(
            result["player_data"], 
            chapter_id, 
            choice_key, 
            choice_index,
            choice_metadata
        )

        # Check if the chapter is complete
        if "current_dialogue" not in result["chapter_data"] or result["chapter_data"]["current_dialogue"] is None:
            # Complete the chapter
            player_data = chapter.complete(result["player_data"])

            # Get the next chapter
            next_chapter_id = chapter.get_next_chapter(player_data)
            if next_chapter_id:
                # Set the next chapter as current
                player_data = self.progress_manager.set_current_chapter(player_data, next_chapter_id)

                # Start the next chapter
                next_chapter = self.chapter_loader.load_chapter(next_chapter_id)
                if next_chapter:
                    result = next_chapter.start(player_data)
                else:
                    logger.warning(f"Next chapter not found: {next_chapter_id} for player {player_data.get('user_id')}. Story will be marked as complete.")
                    # Fallback for the chapter final or a message amigável
                    result = {
                        "player_data": player_data,
                        "chapter_complete": True,
                        "story_complete": True,
                        "message": "Parabéns! Você concluiu todos os capítulos disponíveis até agora.",
                        "chapter_data": {
                            "title": "Fim da História",
                            "description": "Você chegou ao fim dos capítulos disponíveis. Mais conteúdo será adicionado em breve!",
                            "current_dialogue": None,
                            "choices": []
                        }
                    }
            else:
                # No next chapter, story complete
                result = {
                    "player_data": player_data,
                    "chapter_complete": True,
                    "story_complete": True,
                    "chapter_data": {
                        "title": "Fim da História",
                        "description": "Você concluiu todos os capítulos disponíveis. Parabéns!",
                        "current_dialogue": None,
                        "choices": []
                    }
                }

        # Check for events
        available_events = self.event_manager.check_for_events(result["player_data"])
        if available_events:
            result["available_events"] = [
                {
                    "id": event.event_id,
                    "name": event.get_name(),
                    "description": event.get_description()
                }
                for event in available_events
            ]

        # Check for pending moments of definition
        pending_moments = self.consequences_system.get_pending_moments(result["player_data"])
        if pending_moments:
            result["pending_moments"] = pending_moments
            # Clear pending moments after adding them to the result
            result["player_data"] = self.consequences_system.clear_pending_moments(result["player_data"])

        # Check for available companions in the current chapter
        chapter_id = self.progress_manager.get_current_chapter(result["player_data"])
        available_companions = self.get_available_companions(result["player_data"], chapter_id)
        if available_companions:
            result["available_companions"] = available_companions

        # Check for available seasonal events
        available_seasonal_events = self.get_current_season_events(result["player_data"])
        if available_seasonal_events:
            result["available_seasonal_events"] = available_seasonal_events

        return result

    def trigger_event(self, player_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Triggers an event for a player.

        Args:
            player_data: Player data from the database
            event_id: ID of the event to trigger

        Returns:
            Dict containing updated player data and event result
        """
        # Initialize dynamic consequences system if needed
        player_data = self.consequences_system.initialize_player(player_data)

        # Trigger the event
        player_data = self.event_manager.trigger_event(event_id, player_data)

        # Get the event for result data
        event = None
        for e in self.event_manager.events.values():
            if e.event_id == event_id:
                event = e
                break

        if not event:
            logger.warning(f"Event not found: {event_id}")
            return {"player_data": player_data, "error": f"Event not found: {event_id}"}

        # Apply event effects to faction reputation if specified in event data
        if hasattr(event, 'data') and 'faction_effects' in event.data:
            faction_effects = event.data.get('faction_effects', {})
            for faction_id, change in faction_effects.items():
                player_data = self.update_faction_reputation(player_data, faction_id, change)
                logger.info(f"Event {event_id} changed reputation with faction {faction_id} by {change}")

        # Check for pending moments of definition
        pending_moments = self.consequences_system.get_pending_moments(player_data)
        result = {
            "player_data": player_data,
            "event_result": {
                "id": event_id,
                "name": event.get_name(),
                "description": event.get_description(),
                "rewards": event.get_rewards()
            }
        }

        if pending_moments:
            result["pending_moments"] = pending_moments
            # Clear pending moments after adding them to the result
            result["player_data"] = self.consequences_system.clear_pending_moments(result["player_data"])

        # Check for available companions in the current chapter
        chapter_id = self.progress_manager.get_current_chapter(result["player_data"])
        available_companions = self.get_available_companions(result["player_data"], chapter_id)
        if available_companions:
            result["available_companions"] = available_companions

        # Check for available seasonal events
        available_seasonal_events = self.get_current_season_events(result["player_data"])
        if available_seasonal_events:
            result["available_seasonal_events"] = available_seasonal_events

        return result

    def update_affinity(self, player_data: Dict[str, Any], npc_name: str, change: int) -> Dict[str, Any]:
        """
        Updates a player's affinity with an NPC.

        Args:
            player_data: Player data from the database
            npc_name: Name of the NPC
            change: Amount to change affinity by

        Returns:
            Dict containing updated player data
        """
        player_data = self.npc_manager.update_affinity(player_data, npc_name, change)

        # Get the NPC for result data
        npc = self.npc_manager.get_npc_by_name(npc_name)

        if not npc:
            logger.warning(f"NPC not found: {npc_name}")
            return {"player_data": player_data, "error": f"NPC not found: {npc_name}"}

        # Get the new affinity level
        affinity = npc.get_affinity(player_data)
        affinity_level = npc.get_affinity_level(player_data)

        return {
            "player_data": player_data,
            "affinity_result": {
                "npc": npc_name,
                "affinity": affinity,
                "level": affinity_level
            }
        }

    def get_story_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the current status of a player's story progress.

        Args:
            player_data: Player data from the database

        Returns:
            Dict containing story status information
        """
        # Initialize story progress if needed
        player_data = self.progress_manager.initialize_story_progress(player_data)

        # Initialize dynamic consequences system
        player_data = self.consequences_system.initialize_player(player_data)

        story_progress = player_data.get("story_progress", {})

        # Get current chapter
        chapter_id = self.progress_manager.get_current_chapter(player_data)
        chapter = self.chapter_loader.load_chapter(chapter_id)

        chapter_info = None
        if chapter:
            chapter_info = {
                "id": chapter_id,
                "title": chapter.get_title(),
                "description": chapter.get_description()
            }

        # Get completed chapters
        completed_chapters = self.progress_manager.get_completed_chapters(player_data)
        completed_challenge_chapters = self.progress_manager.get_completed_challenge_chapters(player_data)

        # Get hierarchy information
        hierarchy_tier = story_progress.get("hierarchy_tier", 0)
        hierarchy_points = story_progress.get("hierarchy_points", 0)

        # Get discovered secrets
        discovered_secrets = story_progress.get("discovered_secrets", [])

        # Get special items
        special_items = story_progress.get("special_items", [])

        # Get character relationships
        character_relationships = story_progress.get("character_relationships", {})

        # Format relationships with levels
        relationships = []
        for npc_name, affinity in character_relationships.items():
            npc = self.npc_manager.get_npc_by_name(npc_name)
            if npc:
                level = npc.get_affinity_level(player_data)
            else:
                # Create a temporary NPC to get the level
                temp_npc = BaseNPC(f"temp_{npc_name}", {"name": npc_name})
                level = temp_npc.get_affinity_level(player_data)

            relationships.append({
                "npc": npc_name,
                "affinity": affinity,
                "level": level
            })

        # Sort relationships by affinity
        relationships.sort(key=lambda x: x["affinity"], reverse=True)

        # Get faction reputations
        faction_reputations = self.get_all_faction_reputations(player_data)

        # Get player powers
        powers = story_progress.get("powers", {})
        power_status = {}

        for power_id in powers:
            power_status[power_id] = self.get_power_status(player_data, power_id)

        return {
            "current_chapter": chapter_info,
            "completed_chapters": completed_chapters,
            "completed_challenge_chapters": completed_challenge_chapters,
            "hierarchy": {
                "tier": hierarchy_tier,
                "points": hierarchy_points
            },
            "discovered_secrets": discovered_secrets,
            "special_items": special_items,
            "relationships": relationships,
            "faction_reputations": faction_reputations,
            "powers": power_status
        }

    def get_faction_reputation(self, player_data: Dict[str, Any], faction_id: str) -> int:
        """
        Gets a player's reputation with a faction.

        Args:
            player_data: Player data from the database
            faction_id: ID of the faction

        Returns:
            Reputation value
        """
        return self.consequences_system.get_faction_reputation(player_data, faction_id)

    def get_faction_reputation_level(self, player_data: Dict[str, Any], faction_id: str) -> str:
        """
        Gets a player's reputation level with a faction.

        Args:
            player_data: Player data from the database
            faction_id: ID of the faction

        Returns:
            Reputation level as a string
        """
        return self.consequences_system.get_faction_reputation_level(player_data, faction_id)

    def get_all_faction_reputations(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Gets all faction reputations for a player.

        Args:
            player_data: Player data from the database

        Returns:
            Dictionary mapping faction IDs to reputation data
        """
        return self.consequences_system.get_all_faction_reputations(player_data)

    def update_faction_reputation(self, player_data: Dict[str, Any], faction_id: str, change: int) -> Dict[str, Any]:
        """
        Updates a player's reputation with a faction.

        Args:
            player_data: Player data from the database
            faction_id: ID of the faction
            change: Amount to change reputation by

        Returns:
            Updated player data
        """
        return self.consequences_system.update_faction_reputation(player_data, faction_id, change)

    def initialize_player_power(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Initializes a player's power.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            Updated player data
        """
        return self.power_system.initialize_player_power(player_data, power_id)

    def get_player_power(self, player_data: Dict[str, Any], power_id: str) -> Optional[Dict[str, Any]]:
        """
        Gets a player's power progress.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            Power progress data or None if not found
        """
        return self.power_system.get_player_power(player_data, power_id)

    def get_power_status(self, player_data: Dict[str, Any], power_id: str) -> Dict[str, Any]:
        """
        Gets the status of a player's power.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            Dictionary containing power status information
        """
        return self.power_system.get_power_status(player_data, power_id)

    def unlock_skill_node(self, player_data: Dict[str, Any], power_id: str, node_id: str) -> Dict[str, Any]:
        """
        Unlocks a skill node for a player.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type
            node_id: ID of the skill node

        Returns:
            Updated player data and result information
        """
        return self.power_system.unlock_skill_node(player_data, power_id, node_id)

    def perform_awakening_ritual(self, player_data: Dict[str, Any], power_id: str, ritual_id: str) -> Dict[str, Any]:
        """
        Performs an awakening ritual for a player.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type
            ritual_id: ID of the awakening ritual

        Returns:
            Updated player data and result information
        """
        return self.power_system.perform_awakening_ritual(player_data, power_id, ritual_id)

    def complete_power_challenge(self, player_data: Dict[str, Any], power_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Completes a power challenge for a player.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type
            challenge_id: ID of the power challenge

        Returns:
            Updated player data and result information
        """
        return self.power_system.complete_power_challenge(player_data, power_id, challenge_id)

    def get_available_skill_nodes(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets skill nodes available for unlocking.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            List of available skill nodes
        """
        return self.power_system.get_available_skill_nodes(player_data, power_id)

    def get_available_awakening_rituals(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets awakening rituals available for performing.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            List of available awakening rituals
        """
        return self.power_system.get_available_awakening_rituals(player_data, power_id)

    def get_available_power_challenges(self, player_data: Dict[str, Any], power_id: str) -> List[Dict[str, Any]]:
        """
        Gets power challenges available for attempting.

        Args:
            player_data: Player data from the database
            power_id: ID of the power type

        Returns:
            List of available power challenges
        """
        return self.power_system.get_available_power_challenges(player_data, power_id)

    # Seasonal Event System methods
    def get_current_season_events(self, player_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Gets events available in the current season for a player.

        Args:
            player_data: Player data

        Returns:
            Dictionary mapping event types to lists of available events
        """
        return self.seasonal_event_system.get_current_season_events(player_data)

    def participate_in_seasonal_event(self, player_data: Dict[str, Any], event_id: str) -> Dict[str, Any]:
        """
        Allows a player to participate in a seasonal event.

        Args:
            player_data: Player data
            event_id: ID of the seasonal event

        Returns:
            Updated player data and result information
        """
        return self.seasonal_event_system.participate_in_seasonal_event(player_data, event_id)

    def participate_in_mini_game(self, player_data: Dict[str, Any], festival_id: str, mini_game_id: str) -> Dict[str, Any]:
        """
        Allows a player to participate in a mini-game at an academy festival.

        Args:
            player_data: Player data
            festival_id: ID of the academy festival
            mini_game_id: ID of the mini-game

        Returns:
            Updated player data and result information
        """
        return self.seasonal_event_system.participate_in_mini_game(player_data, festival_id, mini_game_id)

    def attempt_festival_challenge(self, player_data: Dict[str, Any], festival_id: str, challenge_id: str) -> Dict[str, Any]:
        """
        Allows a player to attempt an exclusive challenge at an academy festival.

        Args:
            player_data: Player data
            festival_id: ID of the academy festival
            challenge_id: ID of the challenge

        Returns:
            Updated player data and result information
        """
        return self.seasonal_event_system.attempt_festival_challenge(player_data, festival_id, challenge_id)

    def get_seasonal_event_status(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gets the status of a player's participation in seasonal events.

        Args:
            player_data: Player data

        Returns:
            Dictionary containing seasonal event status information
        """
        return self.seasonal_event_system.get_seasonal_event_status(player_data)

    # Companion System methods
    def get_available_companions(self, player_data: Dict[str, Any], chapter_id: str) -> List[Dict[str, Any]]:
        """
        Gets companions available for recruitment in the current chapter.

        Args:
            player_data: Player data
            chapter_id: Current chapter ID

        Returns:
            List of available companions
        """
        return self.companion_system.get_available_companions(player_data, chapter_id)

    def get_recruited_companions(self, player_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Gets companions that have been recruited by the player.

        Args:
            player_data: Player data

        Returns:
            List of recruited companions
        """
        return self.companion_system.get_recruited_companions(player_data)

    def get_active_companion(self, player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gets the currently active companion.

        Args:
            player_data: Player data

        Returns:
            Active companion data or None if no active companion
        """
        return self.companion_system.get_active_companion(player_data)

    def recruit_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Recruits a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to recruit

        Returns:
            Updated player data and result information
        """
        return self.companion_system.recruit_companion(player_data, companion_id)

    def activate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Activates a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to activate

        Returns:
            Updated player data and result information
        """
        return self.companion_system.activate_companion(player_data, companion_id)

    def deactivate_companion(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Deactivates a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion to deactivate

        Returns:
            Updated player data and result information
        """
        return self.companion_system.deactivate_companion(player_data, companion_id)

    def advance_companion_arc(self, player_data: Dict[str, Any], companion_id: str, progress_amount: int) -> Dict[str, Any]:
        """
        Advances a companion's story arc.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            progress_amount: Amount to advance the arc progress

        Returns:
            Updated player data and result information
        """
        return self.companion_system.advance_companion_arc(player_data, companion_id, progress_amount)

    def complete_companion_mission(self, player_data: Dict[str, Any], companion_id: str, mission_id: str) -> Dict[str, Any]:
        """
        Completes a mission in a companion's story arc.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            mission_id: ID of the mission to complete

        Returns:
            Updated player data and result information
        """
        return self.companion_system.complete_companion_mission(player_data, companion_id, mission_id)

    def perform_sync_ability(self, player_data: Dict[str, Any], companion_id: str, ability_id: str) -> Dict[str, Any]:
        """
        Performs a synchronization ability with a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion
            ability_id: ID of the sync ability to perform

        Returns:
            Updated player data and result information
        """
        return self.companion_system.perform_sync_ability(player_data, companion_id, ability_id)

    def get_companion_status(self, player_data: Dict[str, Any], companion_id: str) -> Dict[str, Any]:
        """
        Gets detailed status information for a companion.

        Args:
            player_data: Player data
            companion_id: ID of the companion

        Returns:
            Dictionary containing companion status information
        """
        return self.companion_system.get_companion_status(player_data, companion_id)

    def get_all_power_types(self) -> Dict[str, Any]:
        """
        Gets all registered power types.

        Returns:
            Dictionary mapping power type IDs to PowerType instances
        """
        return self.power_system.get_all_power_types()
