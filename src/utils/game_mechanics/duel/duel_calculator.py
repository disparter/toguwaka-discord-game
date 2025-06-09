"""
Implementation of the duel calculator.
This class is responsible for calculating the outcome of duels between players.
"""
import random
import logging
from typing import Dict, Any
from src.utils.game_mechanics.duel.duel_calculator_interface import IDuelCalculator
from src.utils.game_mechanics.calculators.hp_factor_calculator import HPFactorCalculator
from src.utils.club_perks import (
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

    # Different duel types emphasize different attributes
    ATTRIBUTE_WEIGHTS = {
        "physical": {"dexterity": 0.6, "power_stat": 0.3, "intellect": 0.05, "charisma": 0.05},
        "mental": {"intellect": 0.6, "charisma": 0.2, "dexterity": 0.1, "power_stat": 0.1},
        "strategic": {"intellect": 0.4, "dexterity": 0.3, "power_stat": 0.2, "charisma": 0.1},
        "social": {"charisma": 0.7, "intellect": 0.2, "dexterity": 0.05, "power_stat": 0.05},
        "elemental": {"power_stat": 0.5, "intellect": 0.3, "dexterity": 0.1, "charisma": 0.1}
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

        # Apply Clube das Chamas perk: Boost damage in physical duels
        if duel_type == "physical":
            if challenger.get('club_id') == CLUBE_DAS_CHAMAS:
                original_score = challenger_score
                challenger_score = apply_physical_damage_boost(challenger_score, CLUBE_DAS_CHAMAS, duel_type)
                logger.info(f"Applied Clube das Chamas boost to challenger: {original_score} -> {challenger_score}")

            if opponent.get('club_id') == CLUBE_DAS_CHAMAS:
                original_score = opponent_score
                opponent_score = apply_physical_damage_boost(opponent_score, CLUBE_DAS_CHAMAS, duel_type)
                logger.info(f"Applied Clube das Chamas boost to opponent: {original_score} -> {opponent_score}")

        # Apply Elementalistas perk: Chance to generate weather effects
        if challenger.get('club_id') == ELEMENTALISTAS and should_generate_weather_effect(ELEMENTALISTAS):
            # Weather effect boosts the Elementalistas player's score
            weather_boost = random.uniform(1.1, 1.3)  # 10-30% boost
            challenger_score *= weather_boost
            logger.info(f"Applied Elementalistas weather effect to challenger: {weather_boost:.2f}x boost")

        if opponent.get('club_id') == ELEMENTALISTAS and should_generate_weather_effect(ELEMENTALISTAS):
            # Weather effect boosts the Elementalistas player's score
            weather_boost = random.uniform(1.1, 1.3)  # 10-30% boost
            opponent_score *= weather_boost
            logger.info(f"Applied Elementalistas weather effect to opponent: {weather_boost:.2f}x boost")

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

        # Base rewards
        base_exp_reward = int(30 + (win_margin / 5) + (level_diff * 5))
        base_tusd_reward = int(10 + (win_margin / 10) + (level_diff * 2))

        # Duel type specific bonuses
        duel_type_bonuses = {
            "physical": {"exp": 1.0, "tusd": 1.0, "item_chance": 0.1},
            "mental": {"exp": 1.2, "tusd": 0.9, "item_chance": 0.15},
            "strategic": {"exp": 1.1, "tusd": 1.1, "item_chance": 0.12},
            "social": {"exp": 0.9, "tusd": 1.3, "item_chance": 0.18},
            "elemental": {"exp": 1.3, "tusd": 1.2, "item_chance": 0.2}
        }

        # Apply duel type bonuses
        bonus = duel_type_bonuses.get(duel_type, duel_type_bonuses["physical"])
        exp_reward = int(base_exp_reward * bonus["exp"])
        tusd_reward = int(base_tusd_reward * bonus["tusd"])

        # Chance for bonus rewards (5-15% chance)
        bonus_chance = random.random()
        bonus_rewards = {}

        if bonus_chance < bonus["item_chance"]:
            # Determine bonus reward type based on duel type
            if duel_type == "physical":
                bonus_rewards["item"] = "poção_de_força"
                bonus_rewards["item_name"] = "Poção de Força"
                bonus_rewards["item_description"] = "Aumenta temporariamente sua força física"
            elif duel_type == "mental":
                bonus_rewards["item"] = "pergaminho_de_sabedoria"
                bonus_rewards["item_name"] = "Pergaminho de Sabedoria"
                bonus_rewards["item_description"] = "Aumenta temporariamente seu intelecto"
            elif duel_type == "strategic":
                bonus_rewards["item"] = "mapa_tático"
                bonus_rewards["item_name"] = "Mapa Tático"
                bonus_rewards["item_description"] = "Revela estratégias avançadas de combate"
            elif duel_type == "social":
                bonus_rewards["item"] = "amuleto_de_carisma"
                bonus_rewards["item_name"] = "Amuleto de Carisma"
                bonus_rewards["item_description"] = "Aumenta temporariamente seu carisma"
            elif duel_type == "elemental":
                bonus_rewards["item"] = "cristal_elemental"
                bonus_rewards["item_name"] = "Cristal Elemental"
                bonus_rewards["item_description"] = "Aumenta temporariamente seu poder elemental"

        # Calculate HP loss for the loser based on win margin
        # Higher win margins cause more HP loss
        hp_loss = min(30, max(5, int(win_margin / 3)))

        # Apply Ilusionistas Mentais perk: Reduced energy cost (HP loss) for mental duels
        if duel_type == "mental" and loser.get('club_id') == ILUSIONISTAS_MENTAIS:
            original_hp_loss = hp_loss
            hp_loss = apply_mental_energy_reduction(hp_loss, ILUSIONISTAS_MENTAIS, duel_type)
            logger.info(f"Applied Ilusionistas Mentais energy reduction: {original_hp_loss} -> {hp_loss}")

        # Apply Clube de Combate perk: Increased TUSD rewards when winning duels
        if winner.get('club_id') == CLUBE_DE_COMBATE:
            original_tusd_reward = tusd_reward
            tusd_reward = apply_tusd_reward_boost(tusd_reward, CLUBE_DE_COMBATE, True)
            logger.info(f"Applied Clube de Combate TUSD boost: {original_tusd_reward} -> {tusd_reward}")

        # Create result dictionary with additional info for club perks
        result = {
            "winner": winner,
            "loser": loser,
            "exp_reward": exp_reward,
            "tusd_reward": tusd_reward,
            "duel_type": duel_type,
            "win_margin": win_margin,
            "hp_loss": hp_loss,
            "club_perks_applied": {},
            "bonus_rewards": bonus_rewards
        }

        # Record which club perks were applied
        if duel_type == "physical" and (winner.get('club_id') == CLUBE_DAS_CHAMAS or loser.get('club_id') == CLUBE_DAS_CHAMAS):
            result["club_perks_applied"]["clube_das_chamas"] = "Bônus de dano em duelos físicos"

        if duel_type == "mental" and loser.get('club_id') == ILUSIONISTAS_MENTAIS:
            result["club_perks_applied"]["ilusionistas_mentais"] = "Redução no custo de energia para duelos mentais"

        if (winner.get('club_id') == ELEMENTALISTAS and should_generate_weather_effect(ELEMENTALISTAS)) or \
           (loser.get('club_id') == ELEMENTALISTAS and should_generate_weather_effect(ELEMENTALISTAS)):
            result["club_perks_applied"]["elementalistas"] = "Efeito climático gerado em combate"

        if winner.get('club_id') == CLUBE_DE_COMBATE:
            result["club_perks_applied"]["clube_de_combate"] = "Bônus em recompensas de TUSD ao ganhar duelos"

        return result
