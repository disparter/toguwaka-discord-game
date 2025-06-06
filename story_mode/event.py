from typing import Dict, List, Any, Optional, Union
import json
import logging
import random
from datetime import datetime
from .interfaces import Event, EventManager

logger = logging.getLogger('tokugawa_bot')

class BaseEvent(Event):
    """
    Base implementation of the Event interface.
    Provides common functionality for all event types.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        """
        Initialize an event with its data.
        
        Args:
            event_id: Unique identifier for the event
            data: Dictionary containing event data
        """
        self.event_id = event_id
        self.data = data
        self.name = data.get("name", "Untitled Event")
        self.description = data.get("description", "No description available.")
        self.requirements = data.get("requirements", {})
        self.rewards = data.get("rewards", {})
        self.frequency = data.get("frequency", "once")  # once, daily, weekly, monthly, yearly, random
        
    def get_name(self) -> str:
        """Returns the event name."""
        return self.name
    
    def get_description(self) -> str:
        """Returns the event description."""
        return self.description
    
    def check_trigger_condition(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the event should be triggered for a player.
        """
        # Check if the player meets the requirements
        for req_key, req_value in self.requirements.items():
            if req_key == "level":
                if player_data.get("level", 1) < req_value:
                    return False
            elif req_key == "club_id":
                if player_data.get("club_id") != req_value:
                    return False
            elif req_key in player_data:
                if player_data[req_key] < req_value:
                    return False
        
        # Check if the event has already been triggered based on frequency
        story_progress = player_data.get("story_progress", {})
        triggered_events = story_progress.get("triggered_events", {})
        
        if self.event_id in triggered_events:
            last_trigger = triggered_events[self.event_id]
            current_time = datetime.now()
            
            if self.frequency == "once":
                return False  # Event can only be triggered once
            elif self.frequency == "daily":
                if (current_time - last_trigger).days < 1:
                    return False
            elif self.frequency == "weekly":
                if (current_time - last_trigger).days < 7:
                    return False
            elif self.frequency == "monthly":
                if (current_time - last_trigger).days < 30:
                    return False
            elif self.frequency == "yearly":
                if (current_time - last_trigger).days < 365:
                    return False
        
        return True
    
    def execute(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the event and returns updated player data.
        """
        # Record that the event was triggered
        story_progress = player_data.get("story_progress", {})
        if "triggered_events" not in story_progress:
            story_progress["triggered_events"] = {}
        
        story_progress["triggered_events"][self.event_id] = datetime.now()
        
        # Award rewards
        for reward_type, reward_value in self.rewards.items():
            if reward_type == "exp":
                player_data["exp"] = player_data.get("exp", 0) + reward_value
            elif reward_type == "tusd":
                player_data["tusd"] = player_data.get("tusd", 0) + reward_value
            elif reward_type == "hierarchy_points":
                story_progress["hierarchy_points"] = story_progress.get("hierarchy_points", 0) + reward_value
            elif reward_type == "special_item":
                special_items = story_progress.get("special_items", [])
                if reward_value not in special_items:
                    special_items.append(reward_value)
                story_progress["special_items"] = special_items
        
        # Update player data
        player_data["story_progress"] = story_progress
        
        return player_data
    
    def get_rewards(self) -> Dict[str, Any]:
        """
        Returns the rewards for completing the event.
        """
        return self.rewards


class ClimacticEvent(BaseEvent):
    """
    Implementation of a climactic event that has a major impact on the story.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        super().__init__(event_id, data)
        self.impact = data.get("impact", "minor")  # minor, moderate, major
        self.story_changes = data.get("story_changes", {})
        
    def execute(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the climactic event and applies story changes.
        """
        player_data = super().execute(player_data)
        
        # Apply story changes
        story_progress = player_data["story_progress"]
        
        for change_key, change_value in self.story_changes.items():
            if change_key == "hierarchy_tier":
                story_progress["hierarchy_tier"] = change_value
            elif change_key == "unlock_chapter":
                # Add the chapter to available chapters
                available_chapters = story_progress.get("available_chapters", [])
                if change_value not in available_chapters:
                    available_chapters.append(change_value)
                story_progress["available_chapters"] = available_chapters
            elif change_key == "villain_defeat":
                villain_defeats = story_progress.get("villain_defeats", [])
                if change_value not in villain_defeats:
                    villain_defeats.append(change_value)
                story_progress["villain_defeats"] = villain_defeats
        
        # Update player data
        player_data["story_progress"] = story_progress
        
        return player_data


class RandomEvent(BaseEvent):
    """
    Implementation of a random event that can occur at any time.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        super().__init__(event_id, data)
        self.chance = data.get("chance", 0.1)  # Probability of the event occurring (0-1)
        
    def check_trigger_condition(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the random event should be triggered.
        """
        # First check basic requirements
        if not super().check_trigger_condition(player_data):
            return False
        
        # Then check random chance
        return random.random() < self.chance


class SeasonalEvent(BaseEvent):
    """
    Implementation of a seasonal event that occurs during specific times of the year.
    """
    def __init__(self, event_id: str, data: Dict[str, Any]):
        super().__init__(event_id, data)
        self.start_month = data.get("start_month", 1)
        self.start_day = data.get("start_day", 1)
        self.end_month = data.get("end_month", 1)
        self.end_day = data.get("end_day", 31)
        
    def check_trigger_condition(self, player_data: Dict[str, Any]) -> bool:
        """
        Checks if the seasonal event should be triggered based on the current date.
        """
        # First check basic requirements
        if not super().check_trigger_condition(player_data):
            return False
        
        # Then check if current date is within the event period
        current_date = datetime.now()
        start_date = datetime(current_date.year, self.start_month, self.start_day)
        end_date = datetime(current_date.year, self.end_month, self.end_day)
        
        # Handle events that span across years (e.g., winter events)
        if self.start_month > self.end_month:
            if current_date.month >= self.start_month:
                end_date = datetime(current_date.year + 1, self.end_month, self.end_day)
            else:
                start_date = datetime(current_date.year - 1, self.start_month, self.start_day)
        
        return start_date <= current_date <= end_date


class DefaultEventManager(EventManager):
    """
    Default implementation of the EventManager interface.
    """
    def __init__(self):
        self.events = {}
        self.event_types = {
            "climactic": ClimacticEvent,
            "random": RandomEvent,
            "seasonal": SeasonalEvent,
            "default": BaseEvent
        }
    
    def register_event(self, event: Event) -> None:
        """
        Registers an event with the manager.
        """
        self.events[event.event_id] = event
        logger.info(f"Registered event: {event.get_name()} (ID: {event.event_id})")
    
    def register_event_from_data(self, event_id: str, data: Dict[str, Any]) -> None:
        """
        Creates and registers an event from data.
        """
        event_type = data.get("type", "default")
        event_class = self.event_types.get(event_type, BaseEvent)
        event = event_class(event_id, data)
        self.register_event(event)
    
    def get_available_events(self, player_data: Dict[str, Any]) -> List[Event]:
        """
        Returns a list of events available to the player.
        """
        available_events = []
        
        for event in self.events.values():
            if event.check_trigger_condition(player_data):
                available_events.append(event)
        
        return available_events
    
    def trigger_event(self, event_id: str, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triggers an event and returns updated player data.
        """
        if event_id not in self.events:
            logger.warning(f"Event not found: {event_id}")
            return player_data
        
        event = self.events[event_id]
        
        if not event.check_trigger_condition(player_data):
            logger.warning(f"Event conditions not met: {event_id}")
            return player_data
        
        logger.info(f"Triggering event: {event.get_name()} (ID: {event_id})")
        return event.execute(player_data)
    
    def check_for_events(self, player_data: Dict[str, Any]) -> List[Event]:
        """
        Checks if any events should be triggered for the player.
        """
        return self.get_available_events(player_data)
    
    def load_events_from_file(self, file_path: str) -> None:
        """
        Loads events from a JSON file.
        """
        try:
            with open(file_path, 'r') as f:
                events_data = json.load(f)
            
            for event_id, event_data in events_data.items():
                self.register_event_from_data(event_id, event_data)
            
            logger.info(f"Loaded {len(events_data)} events from {file_path}")
        except Exception as e:
            logger.error(f"Error loading events from {file_path}: {e}")