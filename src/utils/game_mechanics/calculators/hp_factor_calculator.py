"""
Implementation of the HP factor calculator.
This class is responsible for calculating how a player's attributes are affected by their HP.
"""
from decimal import Decimal
from utils.game_mechanics.constants import HP_FACTOR_THRESHOLD, HP_FACTOR_MIN
from utils.game_mechanics.calculators.hp_factor_calculator_interface import IHPFactorCalculator

class HPFactorCalculator(IHPFactorCalculator):
    """Calculadora de fator de HP para eventos"""
    
    @staticmethod
    def calculate_factor(current_hp, max_hp, threshold=Decimal('0.5')):
        """Calcula o fator de HP para eventos
        
        Args:
            current_hp (Decimal): HP atual do personagem
            max_hp (Decimal): HP máximo do personagem
            threshold (Decimal): Threshold para cálculo do fator (default: 0.5)
            
        Returns:
            Decimal: Fator de HP (entre 0.0 e 1.0)
        """
        if max_hp <= 0:
            return Decimal('1.0')
            
        hp_percentage = current_hp / max_hp
        
        # Se HP está em 100%, não há penalidade
        if hp_percentage >= Decimal('1.0'):
            return Decimal('1.0')
            
        # Se HP está acima do threshold, aplica uma pequena redução
        if hp_percentage > threshold:
            return Decimal('0.9')
            
        # Se HP está abaixo do threshold, calcula o fator proporcionalmente
        # Garante que o fator seja menor que 0.7 quando HP está abaixo do threshold
        return Decimal('0.7') + (hp_percentage * Decimal('0.3'))
