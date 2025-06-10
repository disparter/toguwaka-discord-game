"""
Implementation of the experience calculator.
This class is responsible for all experience-related calculations in the game.
"""
import math
from utils.game_mechanics.constants import BASE_EXP, EXP_LEVELS
from utils.game_mechanics.calculators.experience_calculator_interface import IExperienceCalculator

class ExperienceCalculator(IExperienceCalculator):
    """Calculator for experience-related calculations."""
    
    def __init__(self, base_xp=100, level_multiplier=1.5):
        self.base_xp = base_xp
        self.level_multiplier = level_multiplier
        self.difficulty_multipliers = {
            'easy': 0.5,
            'normal': 1.0,
            'hard': 1.5,
            'expert': 2.0
        }

    @staticmethod
    def calculate_required_exp(level):
        """Calculate experience required for a specific level."""
        if level in EXP_LEVELS:
            return EXP_LEVELS[level]
        return math.floor(BASE_EXP * (level ** 1.5))
    
    @staticmethod
    def calculate_level(exp):
        """Calculate level based on total experience."""
        level = 1
        while level < 50 and exp >= ExperienceCalculator.calculate_required_exp(level + 1):
            level += 1
        return level
    
    @staticmethod
    def calculate_progress(exp, level):
        """Calculate progress to next level as percentage."""
        current_level_exp = ExperienceCalculator.calculate_required_exp(level)
        next_level_exp = ExperienceCalculator.calculate_required_exp(level + 1)
        exp_needed = next_level_exp - current_level_exp
        exp_gained = exp - current_level_exp
        return min(100, max(0, int((exp_gained / exp_needed) * 100)))

    def get_difficulty_multiplier(self, difficulty):
        if difficulty not in self.difficulty_multipliers:
            raise ValueError(f"Invalid difficulty: {difficulty}")
        return self.difficulty_multipliers[difficulty]

    def calculate_base_experience(self, level):
        return int(self.base_xp * (self.level_multiplier ** (max(0, level - 1))))

    def calculate_skill_experience(self, skill_level):
        return int(self.calculate_base_experience(skill_level) * 0.5)

    def calculate_relationship_experience(self, relationship_level):
        return int(self.calculate_base_experience(relationship_level) * 0.5)

    def calculate_quest_experience(self, quest_level):
        return int(self.calculate_base_experience(quest_level) * 1.0)

    def calculate_event_experience(self, event_level):
        return int(self.calculate_base_experience(event_level) * 1.0)

    def calculate_total_experience(self, skill_level, relationship_level, quest_level, event_level):
        return (
            self.calculate_skill_experience(skill_level)
            + self.calculate_relationship_experience(relationship_level)
            + self.calculate_quest_experience(quest_level)
            + self.calculate_event_experience(event_level)
        )

    def calculate_experience_gain(self, base_exp, level):
        """Calculate experience gained based on base experience and level."""
        return int(base_exp / (1 + 0.1 * (level - 1)))

    def calculate_level_up(self, current_exp, current_level):
        """Determine if the player has leveled up based on current experience and level."""
        required_exp = self.calculate_required_exp(current_level + 1)
        return current_exp >= required_exp

    def experience_for_next_level(self, current_level):
        """Calculate experience required to reach the next level."""
        return self.calculate_required_exp(current_level + 1)