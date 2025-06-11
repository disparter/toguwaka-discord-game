from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable

class Chapter(ABC):
    """
    Interface for story chapters.
    Following the Single Responsibility Principle, a Chapter is responsible only for
    managing its own content and progression.
    """
    @abstractmethod
    def get_title(self) -> str:
        """Returns the chapter title."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Returns the chapter description."""
        pass
    
    @abstractmethod
    def start(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Starts the chapter for a player.
        Returns data needed to present the chapter to the player.
        """
        pass
    
    @abstractmethod
    def process_choice(self, player_data: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """
        Processes a player's choice and returns the next state.
        """
        pass
    
    @abstractmethod
    def complete(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Completes the chapter and returns updated player data.
        """
        pass
    
    @abstractmethod
    def get_next_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the next chapter based on player choices and state.
        """
        pass


class Event(ABC):
    """
    Interface for story events.
    Events are occurrences that can happen during chapters or independently.
    """
    @abstractmethod
    def get_name(self) -> str:
        """Returns the event name."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Returns the event description."""
        pass
    
    @abstractmethod
    def check_trigger_condition(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the event should be triggered for a player.
        """
        pass
    
    @abstractmethod
    def execute(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the event and returns updated player data.
        """
        pass
    
    @abstractmethod
    def get_rewards(self) -> Dict[str, Any]:
        """
        Returns the rewards for completing the event.
        """
        pass


class NPC(ABC):
    """
    Interface for non-player characters.
    NPCs have their own attributes, dialogues, and relationship with the player.
    """
    @abstractmethod
    def get_name(self) -> str:
        """Returns the NPC's name."""
        pass
    
    @abstractmethod
    def get_background(self) -> Dict[str, str]:
        """Returns the NPC's background information."""
        pass
    
    @abstractmethod
    def get_affinity(self, player_data: Dict[str, Any]) -> int:
        """Returns the player's affinity level with this NPC."""
        pass
    
    @abstractmethod
    def update_affinity(self, player_data: Dict[str, Any], change: int) -> Dict[str, Any]:
        """
        Updates the player's affinity with this NPC and returns updated player data.
        """
        pass
    
    @abstractmethod
    def get_dialogue(self, dialogue_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns a dialogue based on the dialogue ID and player's relationship with the NPC.
        """
        pass


class ChapterLoader(ABC):
    """
    Interface for loading chapters.
    Following the Dependency Inversion Principle, high-level modules should not depend
    on low-level modules but both should depend on abstractions.
    """
    @abstractmethod
    def load_chapter(self, chapter_id: str) -> Chapter:
        """
        Loads a chapter by its ID.
        """
        pass
    
    @abstractmethod
    def get_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs available to the player.
        """
        pass


class EventManager(ABC):
    """
    Interface for managing events.
    The EventManager is responsible for registering, triggering, and managing events.
    """
    @abstractmethod
    def register_event(self, event: Event) -> None:
        """
        Registers an event with the manager.
        """
        pass
    
    @abstractmethod
    def get_available_events(self, player_data: Dict[str, Any]) -> List[Event]:
        """
        Returns a list of events available to the player.
        """
        pass
    
    @abstractmethod
    def trigger_event(self, event_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triggers an event and returns updated player data.
        """
        pass
    
    @abstractmethod
    def check_for_events(self, player_data: Dict[str, Any]) -> List[Event]:
        """
        Checks if any events should be triggered for the player.
        """
        pass


class StoryProgressManager(ABC):
    """
    Interface for managing a player's story progress.
    This follows the Single Responsibility Principle by separating progress tracking
    from other story mode functionality.
    """
    @abstractmethod
    async def get_current_chapter(self, player_data: Dict[str, Any]) -> Optional[str]:
        """
        Returns the ID of the player's current chapter.
        """
        pass
    
    @abstractmethod
    async def set_current_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Sets the player's current chapter and returns updated player data.
        """
        pass
    
    @abstractmethod
    async def complete_chapter(self, player_data: Dict[str, Any], chapter_id: str) -> Dict[str, Any]:
        """
        Marks a chapter as completed and returns updated player data.
        """
        pass
    
    @abstractmethod
    async def record_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str, choice_value: Any) -> Dict[str, Any]:
        """
        Records a player's choice and returns updated player data.
        """
        pass
    
    @abstractmethod
    async def get_completed_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs completed by the player.
        """
        pass
    
    @abstractmethod
    async def get_completed_challenge_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of challenge chapter IDs completed by the player.
        """
        pass
    
    @abstractmethod
    async def get_story_choice(self, player_data: Dict[str, Any], chapter_id: str, choice_key: str) -> Optional[Any]:
        """
        Returns a player's choice for a specific chapter and key.
        """
        pass
    
    @abstractmethod
    async def get_all_story_choices(self, player_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Returns all story choices made by the player.
        """
        pass
    
    @abstractmethod
    async def get_next_available_chapters(self, player_data: Dict[str, Any]) -> List[str]:
        """
        Returns a list of chapter IDs that are available to the player next.
        """
        pass
    
    @abstractmethod
    async def initialize_story_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initializes story progress for a new player.
        """
        pass
    
    @abstractmethod
    async def update_hierarchy_tier(self, player_data: Dict[str, Any], new_tier: int) -> Dict[str, Any]:
        """
        Updates the player's hierarchy tier and returns updated player data.
        """
        pass
    
    @abstractmethod
    async def add_hierarchy_points(self, player_data: Dict[str, Any], points: int) -> Dict[str, Any]:
        """
        Adds hierarchy points to the player and updates tier if necessary.
        """
        pass
    
    @abstractmethod
    async def save_progress(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves player progress to persistent storage.
        """
        pass