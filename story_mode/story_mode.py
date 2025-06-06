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

    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs available to the player.
        """
        story_progress = player_data.get("story_progress", {})
        completed_chapters = story_progress.get("completed_chapters", [])
        available_chapters = story_progress.get("available_chapters", [])

        # Add the next sequential chapter if applicable
        current_year = story_progress.get("current_year", 1)
        current_chapter = story_progress.get("current_chapter", 1)
        next_chapter = f"{current_year}_{current_chapter + 1}"

        # Combine all available chapters
        all_available = list(set(available_chapters + [next_chapter]))

        # Filter out completed chapters and ensure they exist
        return [chapter for chapter in all_available if chapter not in completed_chapters and chapter in self.chapters]


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
                events_data = json.load(f)

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

        # Get current chapter
        chapter_id = self.progress_manager.get_current_chapter(player_data)
        chapter = self.chapter_loader.load_chapter(chapter_id)

        if not chapter:
            logger.warning(f"Chapter not found: {chapter_id}, using first chapter")
            # Use the first available chapter
            available_chapters = self.chapter_loader.get_available_chapters(player_data)
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

        # Record the choice
        choice_key = f"choice_{choice_index}"
        self.progress_manager.record_choice(result["player_data"], chapter_id, choice_key, choice_index)

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
                    logger.warning(f"Next chapter not found: {next_chapter_id}. Using fallback chapter or ending story.")
                    # Fallback for the chapter final or a message amigável
                    result = {
                        "player_data": player_data,
                        "chapter_complete": True,
                        "story_complete": True,
                        "message": "Parabéns! Você concluiu todos os capítulos disponíveis até agora."
                    }
            else:
                # No next chapter, story complete
                result = {
                    "player_data": player_data,
                    "chapter_complete": True,
                    "story_complete": True
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

        return {
            "player_data": player_data,
            "event_result": {
                "id": event_id,
                "name": event.get_name(),
                "description": event.get_description(),
                "rewards": event.get_rewards()
            }
        }

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
            "relationships": relationships
        }
