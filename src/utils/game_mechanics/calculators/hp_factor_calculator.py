"""
Implementation of the HP factor calculator.
This class is responsible for calculating how a player's attributes are affected by their HP.
"""
from utils.game_mechanics.constants import HP_FACTOR_THRESHOLD, HP_FACTOR_MIN
from utils.game_mechanics.calculators.hp_factor_calculator_interface import IHPFactorCalculator

class HPFactorCalculator(IHPFactorCalculator):
    """Calculadora de fator de HP para eventos"""
    
    def __init__(self, threshold=0.5):
        """Inicializa a calculadora com um threshold opcional"""
        self.threshold = threshold
    
    def calculate_factor(self, current_hp, max_hp):
        """Calcula o fator de HP para eventos
        
        Args:
            current_hp (int): HP atual do personagem
            max_hp (int): HP máximo do personagem
            
        Returns:
            float: Fator de HP (entre 0.0 e 1.0)
        """
        if max_hp <= 0:
            return 0.0
            
        hp_percentage = current_hp / max_hp
        
        # Se HP está acima do threshold, aplica uma pequena redução
        if hp_percentage > self.threshold:
            return 0.8
            
        # Se HP está abaixo do threshold, calcula o fator proporcionalmente
        # Garante que o fator seja menor que 0.5 quando HP está abaixo do threshold
        return hp_percentage * 0.4
