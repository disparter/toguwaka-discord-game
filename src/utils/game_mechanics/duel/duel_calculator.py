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
from decimal import Decimal

logger = logging.getLogger('tokugawa_bot')

class DuelCalculator(IDuelCalculator):
    """Calculator for duel-related calculations."""

    def __init__(self):
        """Inicializa a calculadora de duelos"""
        self.hp_calculator = HPFactorCalculator()
        # Define weights for different stats based on duel type
        self.weights = {
            'formal': {
                'power_stat': Decimal('0.3'),
                'dexterity': Decimal('0.2'),
                'intellect': Decimal('0.4'),
                'charisma': Decimal('0.1')
            },
            'informal': {
                'power_stat': Decimal('0.4'),
                'dexterity': Decimal('0.3'),
                'intellect': Decimal('0.2'),
                'charisma': Decimal('0.1')
            },
            'training': {
                'power_stat': Decimal('0.5'),
                'dexterity': Decimal('0.3'),
                'intellect': Decimal('0.1'),
                'charisma': Decimal('0.1')
            },
            'physical': {
                'power_stat': Decimal('0.6'),
                'dexterity': Decimal('0.3'),
                'intellect': Decimal('0.05'),
                'charisma': Decimal('0.05')
            },
            'mental': {
                'power_stat': Decimal('0.1'),
                'dexterity': Decimal('0.1'),
                'intellect': Decimal('0.6'),
                'charisma': Decimal('0.2')
            },
            'strategic': {
                'power_stat': Decimal('0.2'),
                'dexterity': Decimal('0.3'),
                'intellect': Decimal('0.4'),
                'charisma': Decimal('0.1')
            },
            'social': {
                'power_stat': Decimal('0.05'),
                'dexterity': Decimal('0.05'),
                'intellect': Decimal('0.2'),
                'charisma': Decimal('0.7')
            },
            'elemental': {
                'power_stat': Decimal('0.5'),
                'dexterity': Decimal('0.1'),
                'intellect': Decimal('0.3'),
                'charisma': Decimal('0.1')
            }
        }
        
        # Define base rewards
        self.base_rewards = {
            'formal': {
                'exp': 50,
                'tusd': 100
            },
            'informal': {
                'exp': 30,
                'tusd': 50
            },
            'training': {
                'exp': 20,
                'tusd': 30
            },
            'physical': {
                'exp': 40,
                'tusd': 80
            },
            'magical': {
                'exp': 45,
                'tusd': 90
            }
        }
        
        # Define critical hit thresholds and multipliers
        self.critical_hit = {
            'threshold': Decimal('0.85'),  # 85% of max possible score
            'multiplier': Decimal('1.5')   # 50% more rewards
        }
        
        # Define perfect victory threshold
        self.perfect_victory = {
            'threshold': Decimal('0.95'),  # 95% of max possible score
            'multiplier': Decimal('2.0')   # Double rewards
        }
        
        # Define minimum score difference for victory
        self.min_score_diff = Decimal('0.1')  # 10% difference required
        
        # Define HP factor range
        self.hp_factor_range = (Decimal('0.5'), Decimal('1.0'))  # 50% to 100% of max HP
        
        # Define random factor range
        self.random_factor_range = (Decimal('0.9'), Decimal('1.1'))  # ±10% variation

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
        try:
            # Default to physical if invalid type
            weights = self.weights.get(duel_type, self.weights['formal'])

            # Apply HP factor to attributes if available
            challenger_attributes = challenger.copy()
            opponent_attributes = opponent.copy()

            # Calcula o fator de HP para o desafiante e oponente
            challenger_hp_factor = self._calculate_hp_factor(challenger['hp'], challenger['max_hp'])
            opponent_hp_factor = self._calculate_hp_factor(opponent['hp'], opponent['max_hp'])
            
            # Calcula a pontuação base do desafiante usando os pesos do tipo de duelo
            challenger_score = (
                Decimal(str(challenger['power_stat'])) * weights['power_stat'] * challenger_hp_factor +
                Decimal(str(challenger['dexterity'])) * weights['dexterity'] * challenger_hp_factor +
                Decimal(str(challenger['intellect'])) * weights['intellect'] * challenger_hp_factor +
                Decimal(str(challenger['charisma'])) * weights['charisma'] * challenger_hp_factor
            ) * self._get_random_factor()
            
            # Calcula a pontuação base do oponente usando os pesos do tipo de duelo
            opponent_score = (
                Decimal(str(opponent['power_stat'])) * weights['power_stat'] * opponent_hp_factor +
                Decimal(str(opponent['dexterity'])) * weights['dexterity'] * opponent_hp_factor +
                Decimal(str(opponent['intellect'])) * weights['intellect'] * opponent_hp_factor +
                Decimal(str(opponent['charisma'])) * weights['charisma'] * opponent_hp_factor
            ) * self._get_random_factor()
            
            # Calculate score difference
            score_diff = abs(challenger_score - opponent_score)
            max_possible_score = max(challenger_score, opponent_score)
            score_ratio = score_diff / max_possible_score if max_possible_score > 0 else Decimal('0')
            
            # Determine winner and victory type
            winner = challenger if challenger_score > opponent_score else opponent
            victory_type = self._determine_victory_type(score_ratio, winner == challenger)
            
            # Calculate rewards
            base_reward = self.base_rewards[duel_type]
            reward_multiplier = self._calculate_reward_multiplier(victory_type)
            
            rewards = {
                'exp': int(base_reward['exp'] * reward_multiplier),
                'tusd': int(base_reward['tusd'] * reward_multiplier)
            }
            
            # Calcula o dano de HP baseado no tipo de duelo
            if duel_type == "magical":
                # Magical duels cause more HP loss due to elemental damage
                hp_loss = max(int(score_ratio * 30), 5)  # Mínimo de 5 HP
            elif duel_type == "physical":
                # Physical duels cause moderate HP loss
                hp_loss = max(int(score_ratio * 20), 3)  # Mínimo de 3 HP
            elif duel_type == "mental":
                # Mental duels cause less HP loss but more mental strain
                hp_loss = max(int(score_ratio * 15), 2)  # Mínimo de 2 HP
            else:
                # Default HP loss for other types
                hp_loss = max(int(score_ratio * 20), 3)  # Mínimo de 3 HP
            
            return {
                "winner": winner['name'],
                "loser": opponent['name'] if winner == challenger else challenger['name'],
                "duel_type": duel_type,
                "win_margin": float(score_ratio),
                "exp_reward": rewards['exp'],
                "tusd_reward": rewards['tusd'],
                "hp_loss": hp_loss,
                "victory_type": victory_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating duel outcome: {str(e)}")
            raise

    def _calculate_hp_factor(self, current_hp: int, max_hp: int) -> Decimal:
        """Calculate HP factor based on current and max HP."""
        if max_hp <= 0:
            return Decimal('0.5')
        hp_ratio = Decimal(str(current_hp)) / Decimal(str(max_hp))
        return max(self.hp_factor_range[0], min(self.hp_factor_range[1], hp_ratio))

    def _get_random_factor(self) -> Decimal:
        """Get a random factor within the defined range."""
        return Decimal(str(random.uniform(float(self.random_factor_range[0]), float(self.random_factor_range[1]))))

    def _determine_victory_type(self, score_ratio: Decimal, is_challenger_winner: bool) -> str:
        """Determine the type of victory based on score ratio."""
        if score_ratio < self.min_score_diff:
            return 'draw'
        elif score_ratio >= self.perfect_victory['threshold']:
            return 'perfect'
        elif score_ratio >= self.critical_hit['threshold']:
            return 'critical'
        else:
            return 'normal'

    def _calculate_reward_multiplier(self, victory_type: str) -> Decimal:
        """Calculate reward multiplier based on victory type."""
        multipliers = {
            'draw': Decimal('0.5'),
            'normal': Decimal('1.0'),
            'critical': self.critical_hit['multiplier'],
            'perfect': self.perfect_victory['multiplier']
        }
        return multipliers.get(victory_type, Decimal('1.0'))
