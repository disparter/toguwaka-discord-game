from typing import Dict, List, Any, Optional, Union
import logging
import json
import os
import datetime
from collections import defaultdict

# Set up logging
logger = logging.getLogger('tokugawa_bot')

class NarrativeLogger:
    """Logger for narrative events and player choices."""
    
    def __init__(self, log_dir: str = None):
        """Initialize the narrative logger.
        
        Args:
            log_dir (str, optional): Directory for log files. If None, logging is disabled.
        """
        self.log_dir = log_dir
        self.logger = logging.getLogger('tokugawa_bot')
        
        if log_dir:
            try:
                os.makedirs(log_dir, exist_ok=True)
                self.logger.info(f"Narrative logger initialized with log directory: {log_dir}")
            except Exception as e:
                self.logger.error(f"Failed to create log directory {log_dir}: {e}")
                self.log_dir = None
        else:
            self.logger.info("Narrative logger initialized without file logging")
    
    def log_path(self, user_id: str, path: List[str]) -> None:
        """Log a narrative path taken by a player.
        
        Args:
            user_id (str): The user's ID
            path (List[str]): The sequence of narrative choices
        """
        if not self.log_dir:
            return
            
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'user_id': user_id,
                'path': path
            }
            
            # Log to file
            log_file = os.path.join(self.log_dir, f"{user_id}.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
            # Also log to application logger
            self.logger.info(f"Narrative path logged for user {user_id}: {path}")
        except Exception as e:
            self.logger.error(f"Failed to log narrative path: {e}")
    
    def get_path_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the narrative path history for a user.
        
        Args:
            user_id (str): The user's ID
            limit (int, optional): Maximum number of entries to return
            
        Returns:
            List[Dict[str, Any]]: List of narrative path entries
        """
        if not self.log_dir:
            return []
            
        try:
            log_file = os.path.join(self.log_dir, f"{user_id}.jsonl")
            if not os.path.exists(log_file):
                return []
                
            entries = []
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
                        
            return sorted(entries, key=lambda x: x['timestamp'], reverse=True)[:limit]
        except Exception as e:
            self.logger.error(f"Failed to get path history for user {user_id}: {e}")
            return []

def get_narrative_logger(log_dir: str = None) -> NarrativeLogger:
    """Get a narrative logger instance.
    
    Args:
        log_dir (str, optional): Directory for log files. If None, logging is disabled.
        
    Returns:
        NarrativeLogger: A narrative logger instance
    """
    return NarrativeLogger(log_dir)