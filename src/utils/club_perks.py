"""
Club perks utility module for the Academia Tokugawa Discord bot.
This module provides functions to apply club-specific perks to various game mechanics.
"""

import logging

logger = logging.getLogger('tokugawa_bot')

# Club IDs
CLUBE_DAS_CHAMAS = 1
ILUSIONISTAS_MENTAIS = 2
CONSELHO_POLITICO = 3
ELEMENTALISTAS = 4
CLUBE_DE_COMBATE = 5

# Perk configurations
DISCOUNT_PERCENTAGE = 10  # 10% discount for Conselho Político
DAMAGE_BOOST_PERCENTAGE = 15  # 15% more damage for Clube das Chamas
ENERGY_REDUCTION_PERCENTAGE = 20  # 20% less energy cost for Ilusionistas Mentais
WEATHER_EFFECT_CHANCE = 25  # 25% chance to generate weather effects for Elementalistas
TUSD_REWARD_BOOST_PERCENTAGE = 20  # 20% more TUSD rewards for Clube de Combate

def apply_shop_discount(price, club_id):
    """
    Apply a discount to shop items for Conselho Político members.
    
    Args:
        price (int): The original price of the item
        club_id (int): The club ID of the player
        
    Returns:
        int: The discounted price
    """
    if club_id == CONSELHO_POLITICO:
        discount = price * (DISCOUNT_PERCENTAGE / 100)
        discounted_price = int(price - discount)
        logger.info(f"Applied Conselho Político discount: {price} -> {discounted_price}")
        return discounted_price
    return price

def apply_physical_damage_boost(damage, club_id, duel_type):
    """
    Apply a damage boost for Clube das Chamas members in physical duels.
    
    Args:
        damage (int): The original damage
        club_id (int): The club ID of the player
        duel_type (str): The type of duel
        
    Returns:
        int: The boosted damage
    """
    if club_id == CLUBE_DAS_CHAMAS and duel_type == "physical":
        boost = damage * (DAMAGE_BOOST_PERCENTAGE / 100)
        boosted_damage = int(damage + boost)
        logger.info(f"Applied Clube das Chamas damage boost: {damage} -> {boosted_damage}")
        return boosted_damage
    return damage

def apply_mental_energy_reduction(energy_cost, club_id, duel_type):
    """
    Apply an energy cost reduction for Ilusionistas Mentais members in mental duels.
    
    Args:
        energy_cost (int): The original energy cost
        club_id (int): The club ID of the player
        duel_type (str): The type of duel
        
    Returns:
        int: The reduced energy cost
    """
    if club_id == ILUSIONISTAS_MENTAIS and duel_type == "mental":
        reduction = energy_cost * (ENERGY_REDUCTION_PERCENTAGE / 100)
        reduced_cost = max(1, int(energy_cost - reduction))  # Ensure cost is at least 1
        logger.info(f"Applied Ilusionistas Mentais energy reduction: {energy_cost} -> {reduced_cost}")
        return reduced_cost
    return energy_cost

def should_generate_weather_effect(club_id):
    """
    Determine if a weather effect should be generated for Elementalistas members.
    
    Args:
        club_id (int): The club ID of the player
        
    Returns:
        bool: True if a weather effect should be generated, False otherwise
    """
    import random
    if club_id == ELEMENTALISTAS:
        roll = random.randint(1, 100)
        result = roll <= WEATHER_EFFECT_CHANCE
        if result:
            logger.info(f"Elementalistas weather effect triggered (roll: {roll})")
        return result
    return False

def apply_tusd_reward_boost(tusd_reward, club_id, is_duel_winner=False):
    """
    Apply a TUSD reward boost for Clube de Combate members when winning duels.
    
    Args:
        tusd_reward (int): The original TUSD reward
        club_id (int): The club ID of the player
        is_duel_winner (bool): Whether the player won a duel
        
    Returns:
        int: The boosted TUSD reward
    """
    if club_id == CLUBE_DE_COMBATE and is_duel_winner:
        boost = tusd_reward * (TUSD_REWARD_BOOST_PERCENTAGE / 100)
        boosted_reward = int(tusd_reward + boost)
        logger.info(f"Applied Clube de Combate TUSD boost: {tusd_reward} -> {boosted_reward}")
        return boosted_reward
    return tusd_reward

def get_club_perk_description(club_id):
    """
    Get a description of the perks for a specific club.
    
    Args:
        club_id (int): The club ID
        
    Returns:
        str: A description of the club's perks
    """
    if club_id == CLUBE_DAS_CHAMAS:
        return f"Bônus de {DAMAGE_BOOST_PERCENTAGE}% de dano em duelos físicos"
    elif club_id == ILUSIONISTAS_MENTAIS:
        return f"Redução de {ENERGY_REDUCTION_PERCENTAGE}% no custo de energia para duelos mentais"
    elif club_id == CONSELHO_POLITICO:
        return f"Desconto de {DISCOUNT_PERCENTAGE}% em itens da loja"
    elif club_id == ELEMENTALISTAS:
        return f"Chance de {WEATHER_EFFECT_CHANCE}% de gerar efeitos climáticos em combates"
    elif club_id == CLUBE_DE_COMBATE:
        return f"Bônus de {TUSD_REWARD_BOOST_PERCENTAGE}% em recompensas de TUSD ao ganhar duelos"
    else:
        return "Sem bônus de clube"

def apply_duel_bonus(damage, energy_cost, club_id, duel_type):
    """
    Apply all relevant duel bonuses for a club member.
    
    Args:
        damage (int): The original damage
        energy_cost (int): The original energy cost
        club_id (int): The club ID of the player
        duel_type (str): The type of duel ("physical" or "mental")
        
    Returns:
        tuple: (modified_damage, modified_energy_cost)
    """
    modified_damage = apply_physical_damage_boost(damage, club_id, duel_type)
    modified_energy_cost = apply_mental_energy_reduction(energy_cost, club_id, duel_type)
    return modified_damage, modified_energy_cost

def apply_duel_penalty(damage, energy_cost, club_id, duel_type):
    """
    Apply penalties for club members in certain duel types.
    
    Args:
        damage (int): The original damage
        energy_cost (int): The original energy cost
        club_id (int): The club ID of the player
        duel_type (str): The type of duel ("physical" or "mental")
        
    Returns:
        tuple: (modified_damage, modified_energy_cost)
    """
    # Clube das Chamas members have reduced damage in mental duels
    if club_id == CLUBE_DAS_CHAMAS and duel_type == "mental":
        damage = int(damage * 0.8)  # 20% damage reduction
        logger.info(f"Applied Clube das Chamas mental duel penalty: damage reduced by 20%")
    
    # Ilusionistas Mentais members have increased energy cost in physical duels
    if club_id == ILUSIONISTAS_MENTAIS and duel_type == "physical":
        energy_cost = int(energy_cost * 1.2)  # 20% energy cost increase
        logger.info(f"Applied Ilusionistas Mentais physical duel penalty: energy cost increased by 20%")
    
    return damage, energy_cost

def apply_duel_resistance(damage, club_id, duel_type):
    """
    Apply resistance bonuses for club members in certain duel types.
    
    Args:
        damage (int): The original damage
        club_id (int): The club ID of the player
        duel_type (str): The type of duel ("physical" or "mental")
        
    Returns:
        int: The modified damage after applying resistance
    """
    # Clube das Chamas members have increased resistance to physical damage
    if club_id == CLUBE_DAS_CHAMAS and duel_type == "physical":
        damage = int(damage * 0.8)  # 20% damage reduction
        logger.info(f"Applied Clube das Chamas physical resistance: damage reduced by 20%")
    
    # Ilusionistas Mentais members have increased resistance to mental damage
    if club_id == ILUSIONISTAS_MENTAIS and duel_type == "mental":
        damage = int(damage * 0.8)  # 20% damage reduction
        logger.info(f"Applied Ilusionistas Mentais mental resistance: damage reduced by 20%")
    
    return damage