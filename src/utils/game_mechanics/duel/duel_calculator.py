"""
Implementation of the duel calculator.
This class is responsible for calculating the outcome of duels between players.
"""
import random
import logging
import os
from typing import Dict, Any
from utils.game_mechanics.duel.duel_calculator_interface import IDuelCalculator
from utils.game_mechanics.calculators import HPFactorCalculator
from utils.club_perks import (
    CLUBE_DAS_CHAMAS, ILUSIONISTAS_MENTAIS, ELEMENTALISTAS, CLUBE_DE_COMBATE,
    apply_physical_damage_boost, apply_mental_energy_reduction, 
    should_generate_weather_effect, apply_tusd_reward_boost,
    apply_duel_bonus,
    apply_duel_penalty,
    apply_duel_resistance
)

logger = logging.getLogger('tokugawa_bot')

class DuelCalculator(IDuelCalculator):
    """Calculator for duel-related calculations."""

    def __init__(self):
        """Inicializa a calculadora de duelos"""
        self.hp_calculator = HPFactorCalculator()

    # Different duel types emphasize different attributes
    ATTRIBUTE_WEIGHTS = {
        "physical": {"dexterity": 0.6, "power_stat": 0.3, "intellect": 0.05, "charisma": 0.05},
        "mental": {"intellect": 0.6, "charisma": 0.2, "dexterity": 0.1, "power_stat": 0.1},
        "strategic": {"intellect": 0.4, "dexterity": 0.3, "power_stat": 0.2, "charisma": 0.1},
        "social": {"charisma": 0.7, "intellect": 0.2, "dexterity": 0.05, "power_stat": 0.05},
        "elemental": {"power_stat": 0.5, "intellect": 0.3, "dexterity": 0.1, "charisma": 0.1}
    }

    def calculate_outcome(self, challenger: Dict[str, Any], opponent: Dict[str, Any], duel_type: str = "physical") -> Dict[str, Any]:
        """Calculate the outcome of a duel between two players.

        Args:
            challenger (Dict[str, Any]): The challenger's data
            opponent (Dict[str, Any]): The opponent's data
            duel_type (str): The type of duel (physical, mental, strategic, social, elemental)

        Returns:
            Dict[str, Any]: The result of the duel
        """
        # Default to physical if invalid type
        weights = DuelCalculator.ATTRIBUTE_WEIGHTS.get(duel_type, DuelCalculator.ATTRIBUTE_WEIGHTS["physical"])

        # Apply HP factor to attributes if available
        challenger_attributes = challenger.copy()
        opponent_attributes = opponent.copy()

        # Calcula o fator de HP para o desafiante e oponente
        challenger_hp_factor = self.hp_calculator.calculate_factor(challenger['hp'], challenger['max_hp'])
        opponent_hp_factor = self.hp_calculator.calculate_factor(opponent['hp'], opponent['max_hp'])
        
        # Calcula a pontuação base do desafiante usando os pesos do tipo de duelo
        challenger_score = (
            challenger['power_stat'] * weights['power_stat'] * challenger_hp_factor +
            challenger['dexterity'] * weights['dexterity'] +
            challenger['intellect'] * weights['intellect'] +
            challenger['charisma'] * weights['charisma']
        )
        
        # Adiciona um fator aleatório
        challenger_score *= random.uniform(0.8, 1.2)
        
        # Calcula a pontuação base do oponente usando os pesos do tipo de duelo
        opponent_score = (
            opponent['power_stat'] * weights['power_stat'] * opponent_hp_factor +
            opponent['dexterity'] * weights['dexterity'] +
            opponent['intellect'] * weights['intellect'] +
            opponent['charisma'] * weights['charisma']
        )
        
        # Adiciona um fator aleatório
        opponent_score *= random.uniform(0.8, 1.2)
        
        # Determina o vencedor
        if challenger_score > opponent_score:
            winner = challenger['name']
            loser = opponent['name']
            win_margin = challenger_score - opponent_score
        else:
            winner = opponent['name']
            loser = challenger['name']
            win_margin = opponent_score - challenger_score
        
        # Calcula as recompensas baseadas no tipo de duelo
        exp_reward = int(win_margin * 10)
        tusd_reward = int(win_margin * 5)
        
        # Calcula o dano de HP baseado no tipo de duelo
        if duel_type == "magical":
            # Magical duels cause more HP loss due to elemental damage
            hp_loss = int(win_margin * 3)
        elif duel_type == "physical":
            # Physical duels cause moderate HP loss
            hp_loss = int(win_margin * 2)
        elif duel_type == "mental":
            # Mental duels cause less HP loss but more mental strain
            hp_loss = int(win_margin * 1.5)
        else:
            # Default HP loss for other types
            hp_loss = int(win_margin * 2)
        
        return {
            "winner": winner,
            "loser": loser,
            "duel_type": duel_type,
            "win_margin": win_margin,
            "exp_reward": exp_reward,
            "tusd_reward": tusd_reward,
            "hp_loss": hp_loss
        }
