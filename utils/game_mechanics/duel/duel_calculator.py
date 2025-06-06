"""
Implementation of the duel calculator.
This class is responsible for calculating the outcome of duels between players.
"""
import random
from typing import Dict, Any
from utils.game_mechanics.duel.duel_calculator_interface import IDuelCalculator
from utils.game_mechanics.calculators.hp_factor_calculator import HPFactorCalculator

class DuelCalculator(IDuelCalculator):
    """Calculator for duel-related calculations."""
    
    # Different duel types emphasize different attributes
    ATTRIBUTE_WEIGHTS = {
        "physical": {"dexterity": 0.6, "power_stat": 0.3, "intellect": 0.05, "charisma": 0.05},
        "mental": {"intellect": 0.6, "charisma": 0.2, "dexterity": 0.1, "power_stat": 0.1},
        "strategic": {"intellect": 0.4, "dexterity": 0.3, "power_stat": 0.2, "charisma": 0.1},
        "social": {"charisma": 0.7, "intellect": 0.2, "dexterity": 0.05, "power_stat": 0.05}
    }
    
    @staticmethod
    def calculate_outcome(challenger: Dict[str, Any], opponent: Dict[str, Any], duel_type: str) -> Dict[str, Any]:
        """Calculate the outcome of a duel between two players.
        
        Args:
            challenger (Dict[str, Any]): The challenger's data
            opponent (Dict[str, Any]): The opponent's data
            duel_type (str): The type of duel (physical, mental, strategic, social)
            
        Returns:
            Dict[str, Any]: The result of the duel
        """
        # Default to physical if invalid type
        weights = DuelCalculator.ATTRIBUTE_WEIGHTS.get(duel_type, DuelCalculator.ATTRIBUTE_WEIGHTS["physical"])
        
        # Apply HP factor to attributes if available
        challenger_attributes = challenger.copy()
        opponent_attributes = opponent.copy()
        
        # Apply HP factor to challenger if HP data is available
        if 'hp' in challenger and 'max_hp' in challenger:
            hp_factor = HPFactorCalculator.calculate_factor(challenger['hp'], challenger['max_hp'])
            for attr in ['dexterity', 'power_stat', 'intellect', 'charisma']:
                if attr in challenger_attributes:
                    challenger_attributes[attr] = challenger_attributes[attr] * hp_factor
        
        # Apply HP factor to opponent if HP data is available
        if 'hp' in opponent and 'max_hp' in opponent:
            hp_factor = HPFactorCalculator.calculate_factor(opponent['hp'], opponent['max_hp'])
            for attr in ['dexterity', 'power_stat', 'intellect', 'charisma']:
                if attr in opponent_attributes:
                    opponent_attributes[attr] = opponent_attributes[attr] * hp_factor
        
        # Calculate weighted scores
        challenger_score = sum(challenger_attributes[attr] * weight for attr, weight in weights.items())
        opponent_score = sum(opponent_attributes[attr] * weight for attr, weight in weights.items())
        
        # Add randomness factor (±20%)
        challenger_score *= random.uniform(0.8, 1.2)
        opponent_score *= random.uniform(0.8, 1.2)
        
        # Determine winner
        if challenger_score > opponent_score:
            winner = challenger
            loser = opponent
            win_margin = challenger_score - opponent_score
        else:
            winner = opponent
            loser = challenger
            win_margin = opponent_score - challenger_score
        
        # Calculate rewards based on margin and level difference
        level_diff = abs(winner["level"] - loser["level"])
        exp_reward = int(30 + (win_margin / 5) + (level_diff * 5))
        tusd_reward = int(10 + (win_margin / 10) + (level_diff * 2))
        
        # Calculate HP loss for the loser based on win margin
        # Higher win margins cause more HP loss
        hp_loss = min(30, max(5, int(win_margin / 3)))
        
        return {
            "winner": winner,
            "loser": loser,
            "exp_reward": exp_reward,
            "tusd_reward": tusd_reward,
            "duel_type": duel_type,
            "win_margin": win_margin,
            "hp_loss": hp_loss
        }