"""
Interface for HP factor calculators in the game mechanics.
Following the Interface Segregation Principle, this provides a specific interface
for HP factor-related calculations.
"""
from abc import ABC, abstractmethod
from utils.game_mechanics.calculators.calculator_interface import ICalculator

class IHPFactorCalculator(ICalculator):
    """Interface for HP factor calculators."""
    
    @staticmethod
    @abstractmethod
    def calculate_factor(current_hp, max_hp):
        """Calculate the factor that affects player attributes based on HP."""
        pass