"""
Interface for experience calculators in the game mechanics.
Following the Interface Segregation Principle, this provides a specific interface
for experience-related calculations.
"""
from abc import ABC, abstractmethod
from src.utils.game_mechanics.calculators.calculator_interface import ICalculator

class IExperienceCalculator(ICalculator):
    """Interface for experience calculators."""
    
    @staticmethod
    @abstractmethod
    def calculate_required_exp(level):
        """Calculate experience required for a specific level."""
        pass
    
    @staticmethod
    @abstractmethod
    def calculate_level(exp):
        """Calculate level based on total experience."""
        pass
    
    @staticmethod
    @abstractmethod
    def calculate_progress(exp, level):
        """Calculate progress to next level as percentage."""
        pass