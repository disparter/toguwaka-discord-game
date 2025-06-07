"""
Player Choice Tracking System for Dynamic Consequences

This module implements a system to track player choices and their consequences over time,
enabling dynamic storytelling based on player decisions.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class PlayerChoiceTracker:
    """
    Tracks player choices and their patterns over time to influence future events.
    """
    
    def __init__(self, player_id):
        """
        Initialize the choice tracker for a specific player.
        
        Args:
            player_id (str): The unique identifier for the player
        """
        self.player_id = player_id
        self.choices = []
        self.choice_patterns = defaultdict(int)
        self.faction_reputation = defaultdict(int)
        self.defining_moments = []
        self.load_data()
    
    def load_data(self):
        """Load player choice data from storage if it exists."""
        try:
            file_path = f"data/player_data/{self.player_id}/choices.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.choices = data.get('choices', [])
                    self.choice_patterns = defaultdict(int, data.get('choice_patterns', {}))
                    self.faction_reputation = defaultdict(int, data.get('faction_reputation', {}))
                    self.defining_moments = data.get('defining_moments', [])
        except Exception as e:
            print(f"Error loading player choice data: {e}")
    
    def save_data(self):
        """Save player choice data to storage."""
        try:
            file_path = f"data/player_data/{self.player_id}/choices.json"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            data = {
                'choices': self.choices,
                'choice_patterns': dict(self.choice_patterns),
                'faction_reputation': dict(self.faction_reputation),
                'defining_moments': self.defining_moments
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving player choice data: {e}")
    
    def record_choice(self, event_id, choice_id, choice_type, consequences, context=None):
        """
        Record a player's choice and update patterns.
        
        Args:
            event_id (str): The ID of the event where the choice was made
            choice_id (str): The ID of the choice made
            choice_type (str): The type of choice (e.g., 'academic', 'social', 'combat')
            consequences (dict): The consequences of the choice
            context (dict, optional): Additional context about the choice
        """
        choice_data = {
            'event_id': event_id,
            'choice_id': choice_id,
            'choice_type': choice_type,
            'consequences': consequences,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.choices.append(choice_data)
        
        # Update choice patterns
        self.choice_patterns[choice_type] += 1
        self.choice_patterns[choice_id] += 1
        
        # Update faction reputation if applicable
        if 'faction_reputation' in consequences:
            for faction, change in consequences['faction_reputation'].items():
                self.faction_reputation[faction] += change
        
        # Check if this is a defining moment
        if consequences.get('is_defining_moment', False):
            self.defining_moments.append({
                'event_id': event_id,
                'choice_id': choice_id,
                'timestamp': datetime.now().isoformat(),
                'description': consequences.get('defining_moment_description', ''),
                'impact': consequences.get('defining_moment_impact', {})
            })
        
        self.save_data()
    
    def get_choice_pattern(self, choice_type=None):
        """
        Get the pattern of choices made by the player.
        
        Args:
            choice_type (str, optional): Filter by choice type
            
        Returns:
            dict: The pattern of choices
        """
        if choice_type:
            return {k: v for k, v in self.choice_patterns.items() 
                   if k == choice_type or k.startswith(f"{choice_type}_")}
        return dict(self.choice_patterns)
    
    def get_dominant_choice_type(self):
        """
        Get the player's dominant choice type.
        
        Returns:
            str: The most frequent choice type
        """
        choice_types = {k: v for k, v in self.choice_patterns.items() 
                       if k in ['academic', 'social', 'physical', 'strategic', 
                               'elemental', 'mental', 'political', 'combat', 
                               'mystery', 'cultural']}
        
        if not choice_types:
            return None
            
        return max(choice_types.items(), key=lambda x: x[1])[0]
    
    def get_faction_reputation(self, faction=None):
        """
        Get the player's reputation with factions.
        
        Args:
            faction (str, optional): A specific faction to get reputation for
            
        Returns:
            dict or int: The reputation with all factions or a specific faction
        """
        if faction:
            return self.faction_reputation.get(faction, 0)
        return dict(self.faction_reputation)
    
    def get_defining_moments(self):
        """
        Get the player's defining moments.
        
        Returns:
            list: The defining moments
        """
        return self.defining_moments
    
    def predict_future_choices(self, choice_type):
        """
        Predict the player's future choices based on past patterns.
        
        Args:
            choice_type (str): The type of choice to predict
            
        Returns:
            dict: Prediction data with probabilities for different options
        """
        # Get relevant patterns for this choice type
        patterns = self.get_choice_pattern(choice_type)
        
        # If no patterns exist, return equal probabilities
        if not patterns or sum(patterns.values()) == 0:
            return {'prediction': 'unknown', 'confidence': 0}
        
        # Find the most common choice in this category
        most_common = max(patterns.items(), key=lambda x: x[1])
        
        # Calculate confidence based on consistency of choices
        total_choices = sum(patterns.values())
        confidence = most_common[1] / total_choices if total_choices > 0 else 0
        
        return {
            'prediction': most_common[0],
            'confidence': confidence,
            'patterns': patterns
        }
    
    def get_choice_history(self, limit=10, choice_type=None, event_id=None):
        """
        Get the player's choice history.
        
        Args:
            limit (int, optional): Maximum number of choices to return
            choice_type (str, optional): Filter by choice type
            event_id (str, optional): Filter by event ID
            
        Returns:
            list: The choice history
        """
        filtered_choices = self.choices
        
        if choice_type:
            filtered_choices = [c for c in filtered_choices if c['choice_type'] == choice_type]
            
        if event_id:
            filtered_choices = [c for c in filtered_choices if c['event_id'] == event_id]
            
        # Return most recent choices first
        return sorted(filtered_choices, key=lambda x: x['timestamp'], reverse=True)[:limit]