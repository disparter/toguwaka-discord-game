"""
Implementation of the HP factor calculator.
This class is responsible for calculating how a player's attributes are affected by their HP.
"""
from src.utils.game_mechanics.constants import HP_FACTOR_THRESHOLD, HP_FACTOR_MIN
from src.utils.game_mechanics.calculators.hp_factor_calculator_interface import IHPFactorCalculator

class HPFactorCalculator(IHPFactorCalculator):
    """Calculator for HP factor-related calculations."""

    @staticmethod
    def calculate_factor(current_hp, max_hp):
        """Calculate the factor that affects player attributes based on HP.

        When HP is above the threshold (default 50%), there's no effect (factor = 1.0).
        When HP is below the threshold, attributes are reduced linearly down to the minimum factor.

        Args:
            current_hp (int): Player's current HP
            max_hp (int): Player's maximum HP

        Returns:
            float: Factor to multiply attributes by (between HP_FACTOR_MIN and 1.0)
        """
        # Ensure we don't divide by zero
        if max_hp <= 0:
            return 1.0

        # Handle negative HP values
        if current_hp < 0:
            current_hp = 0

        # Calculate HP percentage
        hp_percentage = current_hp / max_hp

        # If HP is above the threshold, no effect
        if hp_percentage >= HP_FACTOR_THRESHOLD:
            return 1.0

        # Calculate factor based on how far below threshold the HP is
        # Map hp_percentage from [0, HP_FACTOR_THRESHOLD] to [HP_FACTOR_MIN, 1.0]
        factor = HP_FACTOR_MIN + (1.0 - HP_FACTOR_MIN) * (hp_percentage / HP_FACTOR_THRESHOLD)

        return factor
