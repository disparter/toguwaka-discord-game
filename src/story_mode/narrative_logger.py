"""
Narrative Logger for Academia Tokugawa.

This module provides logging functionality for narrative events and player choices.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger('tokugawa_bot')

class NarrativeLogger:
    """
    Class for logging narrative events and player choices.
    """
    
    def __init__(self, data_dir: str = "data/story_mode/logs"):
        """
        Initialize the narrative logger.
        
        Args:
            data_dir: Path to the directory for storing logs
        """
        self.data_dir = Path(data_dir)
        self.logs_dir = self.data_dir / "narrative_logs"
        self.analytics_dir = self.data_dir / "analytics"
        
        # Create necessary directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("NarrativeLogger initialized")

    def log_narrative_path(self, player_id: str, chapter_id: str, choice_id: str, 
                          consequences: Dict[str, Any], context: Dict[str, Any] = None) -> bool:
        """
        Log a narrative path taken by a player.
        
        Args:
            player_id: The player's ID
            chapter_id: The chapter ID
            choice_id: The choice ID
            consequences: The consequences of the choice
            context: Additional context for the log
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "player_id": player_id,
                "chapter_id": chapter_id,
                "choice_id": choice_id,
                "consequences": consequences,
                "context": context or {}
            }
            
            # Save log entry
            log_file = self.logs_dir / f"{player_id}_{chapter_id}.json"
            
            # Load existing logs if file exists
            logs = []
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            # Add new log entry
            logs.append(log_entry)
            
            # Save updated logs
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            # Update analytics
            self._update_analytics(chapter_id, choice_id, consequences)
            
            return True
        except Exception as e:
            logger.error(f"Error logging narrative path: {e}")
            return False

    def _update_analytics(self, chapter_id: str, choice_id: str, consequences: Dict[str, Any]) -> None:
        """
        Update analytics data for a narrative choice.
        
        Args:
            chapter_id: The chapter ID
            choice_id: The choice ID
            consequences: The consequences of the choice
        """
        try:
            # Load analytics data
            analytics_file = self.analytics_dir / f"{chapter_id}_analytics.json"
            
            analytics = {
                "choices": {},
                "paths": {},
                "errors": {},
                "total_visits": 0
            }
            
            if analytics_file.exists():
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    analytics = json.load(f)
            
            # Update choice count
            analytics["choices"][choice_id] = analytics["choices"].get(choice_id, 0) + 1
            
            # Update path count
            path_key = f"{chapter_id}_{choice_id}"
            analytics["paths"][path_key] = analytics["paths"].get(path_key, 0) + 1
            
            # Update total visits
            analytics["total_visits"] += 1
            
            # Save updated analytics
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error updating analytics: {e}")

    def get_chapter_analytics(self, chapter_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a specific chapter.
        
        Args:
            chapter_id: The chapter ID
            
        Returns:
            Dictionary containing analytics data
        """
        try:
            analytics_file = self.analytics_dir / f"{chapter_id}_analytics.json"
            
            if analytics_file.exists():
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return {
                "choices": {},
                "paths": {},
                "errors": {},
                "total_visits": 0
            }
        except Exception as e:
            logger.error(f"Error getting chapter analytics: {e}")
            return {
                "choices": {},
                "paths": {},
                "errors": {},
                "total_visits": 0
            }

    def export_analytics_for_dashboard(self) -> Dict[str, Any]:
        """
        Export analytics data for the dashboard.
        
        Returns:
            Dictionary containing analytics data for the dashboard
        """
        try:
            analytics = {
                "most_common_paths": {},
                "most_common_errors": {},
                "total_logs": {
                    "choices": 0,
                    "paths": 0,
                    "errors": 0
                }
            }
            
            # Process all analytics files
            for analytics_file in self.analytics_dir.glob("*_analytics.json"):
                with open(analytics_file, 'r', encoding='utf-8') as f:
                    chapter_analytics = json.load(f)
                    
                    # Update most common paths
                    for path, count in chapter_analytics.get("paths", {}).items():
                        analytics["most_common_paths"][path] = analytics["most_common_paths"].get(path, 0) + count
                    
                    # Update most common errors
                    chapter_id = analytics_file.stem.replace("_analytics", "")
                    if chapter_analytics.get("errors"):
                        analytics["most_common_errors"][chapter_id] = chapter_analytics["errors"]
                    
                    # Update total logs
                    analytics["total_logs"]["choices"] += chapter_analytics.get("total_visits", 0)
                    analytics["total_logs"]["paths"] += len(chapter_analytics.get("paths", {}))
                    analytics["total_logs"]["errors"] += len(chapter_analytics.get("errors", {}))
            
            return analytics
        except Exception as e:
            logger.error(f"Error exporting analytics for dashboard: {e}")
            return {
                "most_common_paths": {},
                "most_common_errors": {},
                "total_logs": {
                    "choices": 0,
                    "paths": 0,
                    "errors": 0
                }
            }

# Create a singleton instance
_narrative_logger = None

def get_narrative_logger() -> NarrativeLogger:
    """
    Get the singleton instance of the narrative logger.
    
    Returns:
        The narrative logger instance
    """
    global _narrative_logger
    if _narrative_logger is None:
        _narrative_logger = NarrativeLogger()
    return _narrative_logger 