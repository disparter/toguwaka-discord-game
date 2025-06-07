from typing import Dict, List, Any, Optional, Union
import logging
import json
import os
import datetime
from collections import defaultdict

# Set up logging
logger = logging.getLogger('tokugawa_bot')

class NarrativeLogger:
    """
    A centralized logging system for tracking narrative flows in the story mode.
    This class provides methods for logging player choices, chapter transitions,
    and other relevant events, and for analyzing the logged data.
    """

    def __init__(self, log_dir: str = "data/logs/narrative"):
        """
        Initialize the narrative logger.

        Args:
            log_dir: Path to the directory where logs will be stored
        """
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize in-memory cache for faster access to recent logs
        self.choice_cache = defaultdict(lambda: defaultdict(int))  # {chapter_id: {choice_key: count}}
        self.path_cache = defaultdict(int)  # {path_str: count}
        self.error_cache = defaultdict(lambda: defaultdict(int))  # {chapter_id: {error_type: count}}
        
        # Load existing logs into cache
        self._load_logs_into_cache()
        
        logger.info(f"Narrative logger initialized with log directory: {log_dir}")

    def _load_logs_into_cache(self):
        """
        Load existing logs into the in-memory cache for faster access.
        """
        try:
            # Load choice logs
            choice_log_path = os.path.join(self.log_dir, "choice_logs.json")
            if os.path.exists(choice_log_path):
                with open(choice_log_path, 'r') as f:
                    self.choice_cache = defaultdict(lambda: defaultdict(int), json.load(f))
            
            # Load path logs
            path_log_path = os.path.join(self.log_dir, "path_logs.json")
            if os.path.exists(path_log_path):
                with open(path_log_path, 'r') as f:
                    self.path_cache = defaultdict(int, json.load(f))
            
            # Load error logs
            error_log_path = os.path.join(self.log_dir, "error_logs.json")
            if os.path.exists(error_log_path):
                with open(error_log_path, 'r') as f:
                    self.error_cache = defaultdict(lambda: defaultdict(int), json.load(f))
            
            logger.info("Loaded existing narrative logs into cache")
        except Exception as e:
            logger.error(f"Error loading narrative logs into cache: {e}")

    def _save_cache_to_logs(self):
        """
        Save the in-memory cache to log files.
        """
        try:
            # Save choice logs
            choice_log_path = os.path.join(self.log_dir, "choice_logs.json")
            with open(choice_log_path, 'w') as f:
                json.dump(dict(self.choice_cache), f)
            
            # Save path logs
            path_log_path = os.path.join(self.log_dir, "path_logs.json")
            with open(path_log_path, 'w') as f:
                json.dump(dict(self.path_cache), f)
            
            # Save error logs
            error_log_path = os.path.join(self.log_dir, "error_logs.json")
            with open(error_log_path, 'w') as f:
                json.dump(dict(self.error_cache), f)
            
            logger.debug("Saved narrative logs cache to files")
        except Exception as e:
            logger.error(f"Error saving narrative logs cache to files: {e}")

    def log_choice(self, player_id: str, chapter_id: str, choice_key: str, choice_value: Any):
        """
        Log a player's choice in a chapter.

        Args:
            player_id: ID of the player
            chapter_id: ID of the chapter
            choice_key: Key identifying the choice
            choice_value: Value of the choice
        """
        try:
            # Create a log entry
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "player_id": player_id,
                "chapter_id": chapter_id,
                "choice_key": choice_key,
                "choice_value": choice_value
            }
            
            # Write to detailed log file
            detailed_log_path = os.path.join(self.log_dir, "detailed_choice_logs.jsonl")
            with open(detailed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update cache
            choice_str = f"{choice_key}:{choice_value}"
            self.choice_cache[chapter_id][choice_str] += 1
            
            # Save cache periodically (every 10 logs)
            if sum(sum(counts.values()) for counts in self.choice_cache.values()) % 10 == 0:
                self._save_cache_to_logs()
            
            logger.debug(f"Logged choice: {player_id} chose {choice_key}={choice_value} in chapter {chapter_id}")
        except Exception as e:
            logger.error(f"Error logging choice: {e}")

    def log_path(self, player_id: str, path: List[str]):
        """
        Log a player's path through the story.

        Args:
            player_id: ID of the player
            path: List of chapter IDs representing the player's path
        """
        try:
            # Create a log entry
            path_str = "->".join(path)
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "player_id": player_id,
                "path": path,
                "path_str": path_str
            }
            
            # Write to detailed log file
            detailed_log_path = os.path.join(self.log_dir, "detailed_path_logs.jsonl")
            with open(detailed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update cache
            self.path_cache[path_str] += 1
            
            # Save cache periodically (every 10 logs)
            if sum(self.path_cache.values()) % 10 == 0:
                self._save_cache_to_logs()
            
            logger.debug(f"Logged path: {player_id} followed path {path_str}")
        except Exception as e:
            logger.error(f"Error logging path: {e}")

    def log_error(self, player_id: str, chapter_id: str, error_type: str, error_message: str):
        """
        Log an error that occurred during story progression.

        Args:
            player_id: ID of the player
            chapter_id: ID of the chapter where the error occurred
            error_type: Type of error
            error_message: Error message
        """
        try:
            # Create a log entry
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "player_id": player_id,
                "chapter_id": chapter_id,
                "error_type": error_type,
                "error_message": error_message
            }
            
            # Write to detailed log file
            detailed_log_path = os.path.join(self.log_dir, "detailed_error_logs.jsonl")
            with open(detailed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update cache
            self.error_cache[chapter_id][error_type] += 1
            
            # Save cache immediately for errors
            self._save_cache_to_logs()
            
            logger.error(f"Narrative error: {player_id} encountered {error_type} in chapter {chapter_id}: {error_message}")
        except Exception as e:
            logger.error(f"Error logging narrative error: {e}")

    def log_validation_error(self, player_id: str, chapter_id: str, validation_type: str, details: Dict[str, Any]):
        """
        Log a validation error that occurred during story progression.

        Args:
            player_id: ID of the player
            chapter_id: ID of the chapter where the error occurred
            validation_type: Type of validation error (e.g., "choice", "affinity", "conditional")
            details: Additional details about the validation error
        """
        try:
            # Create a log entry
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "player_id": player_id,
                "chapter_id": chapter_id,
                "validation_type": validation_type,
                "details": details
            }
            
            # Write to detailed log file
            detailed_log_path = os.path.join(self.log_dir, "detailed_validation_logs.jsonl")
            with open(detailed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update error cache
            error_type = f"validation_{validation_type}"
            self.error_cache[chapter_id][error_type] += 1
            
            # Save cache immediately for validation errors
            self._save_cache_to_logs()
            
            logger.warning(f"Validation error: {player_id} encountered {validation_type} validation error in chapter {chapter_id}: {details}")
        except Exception as e:
            logger.error(f"Error logging validation error: {e}")

    def log_chapter_transition(self, player_id: str, from_chapter_id: str, to_chapter_id: str, transition_type: str = "normal"):
        """
        Log a player's transition from one chapter to another.

        Args:
            player_id: ID of the player
            from_chapter_id: ID of the chapter the player is transitioning from
            to_chapter_id: ID of the chapter the player is transitioning to
            transition_type: Type of transition (e.g., "normal", "conditional", "choice")
        """
        try:
            # Create a log entry
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "player_id": player_id,
                "from_chapter_id": from_chapter_id,
                "to_chapter_id": to_chapter_id,
                "transition_type": transition_type
            }
            
            # Write to detailed log file
            detailed_log_path = os.path.join(self.log_dir, "detailed_transition_logs.jsonl")
            with open(detailed_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update path cache with this transition
            transition_str = f"{from_chapter_id}->{to_chapter_id}"
            self.path_cache[transition_str] += 1
            
            # Save cache periodically
            if sum(self.path_cache.values()) % 10 == 0:
                self._save_cache_to_logs()
            
            logger.debug(f"Logged chapter transition: {player_id} transitioned from {from_chapter_id} to {to_chapter_id} ({transition_type})")
        except Exception as e:
            logger.error(f"Error logging chapter transition: {e}")

    def get_most_common_choices(self, chapter_id: str = None, limit: int = 10) -> Dict[str, Dict[str, int]]:
        """
        Get the most common choices made by players.

        Args:
            chapter_id: Optional chapter ID to filter choices
            limit: Maximum number of choices to return per chapter

        Returns:
            Dictionary mapping chapter IDs to dictionaries mapping choice strings to counts
        """
        result = {}
        
        if chapter_id:
            # Filter by chapter ID
            chapter_choices = self.choice_cache.get(chapter_id, {})
            sorted_choices = sorted(chapter_choices.items(), key=lambda x: x[1], reverse=True)[:limit]
            result[chapter_id] = dict(sorted_choices)
        else:
            # Get choices for all chapters
            for ch_id, choices in self.choice_cache.items():
                sorted_choices = sorted(choices.items(), key=lambda x: x[1], reverse=True)[:limit]
                result[ch_id] = dict(sorted_choices)
        
        return result

    def get_most_common_paths(self, limit: int = 10) -> Dict[str, int]:
        """
        Get the most common paths taken by players.

        Args:
            limit: Maximum number of paths to return

        Returns:
            Dictionary mapping path strings to counts
        """
        sorted_paths = sorted(self.path_cache.items(), key=lambda x: x[1], reverse=True)[:limit]
        return dict(sorted_paths)

    def get_most_common_errors(self, chapter_id: str = None, limit: int = 10) -> Dict[str, Dict[str, int]]:
        """
        Get the most common errors encountered by players.

        Args:
            chapter_id: Optional chapter ID to filter errors
            limit: Maximum number of errors to return per chapter

        Returns:
            Dictionary mapping chapter IDs to dictionaries mapping error types to counts
        """
        result = {}
        
        if chapter_id:
            # Filter by chapter ID
            chapter_errors = self.error_cache.get(chapter_id, {})
            sorted_errors = sorted(chapter_errors.items(), key=lambda x: x[1], reverse=True)[:limit]
            result[chapter_id] = dict(sorted_errors)
        else:
            # Get errors for all chapters
            for ch_id, errors in self.error_cache.items():
                sorted_errors = sorted(errors.items(), key=lambda x: x[1], reverse=True)[:limit]
                result[ch_id] = dict(sorted_errors)
        
        return result

    def get_chapter_analytics(self, chapter_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a specific chapter.

        Args:
            chapter_id: ID of the chapter to analyze

        Returns:
            Dictionary containing analytics data for the chapter
        """
        # Get choices for this chapter
        choices = self.get_most_common_choices(chapter_id)
        
        # Get errors for this chapter
        errors = self.get_most_common_errors(chapter_id)
        
        # Get paths that include this chapter
        paths_with_chapter = {}
        for path_str, count in self.path_cache.items():
            if chapter_id in path_str.split("->"):
                paths_with_chapter[path_str] = count
        
        # Sort paths by count
        sorted_paths = sorted(paths_with_chapter.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "chapter_id": chapter_id,
            "choices": choices.get(chapter_id, {}),
            "errors": errors.get(chapter_id, {}),
            "paths": dict(sorted_paths),
            "total_visits": sum(1 for path_str in self.path_cache if chapter_id in path_str.split("->"))
        }

    def get_player_journey(self, player_id: str) -> Dict[str, Any]:
        """
        Get a player's journey through the story.

        Args:
            player_id: ID of the player

        Returns:
            Dictionary containing the player's journey data
        """
        # This would require scanning the detailed logs
        # For simplicity, we'll return a placeholder
        return {
            "player_id": player_id,
            "message": "Player journey analysis requires scanning detailed logs, which is not implemented in this version."
        }

    def export_analytics_for_dashboard(self) -> Dict[str, Any]:
        """
        Export analytics data in a format compatible with the decision dashboard.

        Returns:
            Dictionary containing analytics data for the dashboard
        """
        return {
            "most_common_choices": self.get_most_common_choices(),
            "most_common_paths": self.get_most_common_paths(),
            "most_common_errors": self.get_most_common_errors(),
            "total_logs": {
                "choices": sum(sum(counts.values()) for counts in self.choice_cache.values()),
                "paths": sum(self.path_cache.values()),
                "errors": sum(sum(counts.values()) for counts in self.error_cache.values())
            }
        }

# Singleton instance
_narrative_logger = None

def get_narrative_logger(log_dir: str = "data/logs/narrative") -> NarrativeLogger:
    """
    Get the singleton instance of the narrative logger.

    Args:
        log_dir: Path to the directory where logs will be stored

    Returns:
        The narrative logger instance
    """
    global _narrative_logger
    if _narrative_logger is None:
        _narrative_logger = NarrativeLogger(log_dir)
    return _narrative_logger