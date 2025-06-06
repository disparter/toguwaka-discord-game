"""
Implementation of the experience calculator.
This class is responsible for all experience-related calculations in the game.
"""
import math
from utils.game_mechanics.constants import BASE_EXP, EXP_LEVELS
from utils.game_mechanics.calculators.experience_calculator_interface import IExperienceCalculator

class ExperienceCalculator(IExperienceCalculator):
    """Calculator for experience-related calculations."""
    
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