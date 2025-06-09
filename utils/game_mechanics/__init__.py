# This file makes the game_mechanics directory a Python package
# It also re-exports the constants and functions from the old game_mechanics module
# to maintain backward compatibility during the transition to SOLID principles

# Import and re-export constants
from utils.game_mechanics.constants import (
    HP_FACTOR_THRESHOLD, HP_FACTOR_MIN, BASE_EXP, EXP_LEVELS,
    STRENGTH_LEVELS, RARITIES, TRAINING_OUTCOMES, RANDOM_EVENTS
)

# Import and re-export classes from their new locations
# Calculators
from utils.game_mechanics.calculators.calculator_interface import ICalculator
from utils.game_mechanics.calculators.experience_calculator_interface import IExperienceCalculator
from utils.game_mechanics.calculators.hp_factor_calculator_interface import IHPFactorCalculator
from utils.game_mechanics.calculators.experience_calculator import ExperienceCalculator
from utils.game_mechanics.calculators.hp_factor_calculator import HPFactorCalculator

# Events
from utils.game_mechanics.events.event_interface import IEvent
from utils.game_mechanics.events.event_base import EventBase
from utils.game_mechanics.events.training_event import TrainingEvent
from utils.game_mechanics.events.random_event import RandomEvent

# Duel
from utils.game_mechanics.duel.duel_calculator_interface import IDuelCalculator
from utils.game_mechanics.duel.duel_narrator_interface import IDuelNarrator
from utils.game_mechanics.duel.duel_calculator import DuelCalculator
from utils.game_mechanics.duel.duel_narrator import DuelNarrator

# Faction
from utils.game_mechanics.faction_reputation import FactionReputationManager

# Provide backward compatibility functions
def calculate_exp_for_level(level):
    """Backward compatibility function for calculate_exp_for_level."""
    return ExperienceCalculator.calculate_required_exp(level)

def calculate_level_from_exp(exp):
    """Backward compatibility function for calculate_level_from_exp."""
    return ExperienceCalculator.calculate_level(exp)

def calculate_exp_progress(exp, level):
    """Backward compatibility function for calculate_exp_progress."""
    return ExperienceCalculator.calculate_progress(exp, level)

def get_random_training_outcome():
    """Backward compatibility function for get_random_training_outcome."""
    return TrainingEvent.get_random_outcome()

def get_random_event():
    """Backward compatibility function for get_random_event."""
    return RandomEvent.get_random_event()

def generate_random_event():
    """Backward compatibility function for generate_random_event."""
    return RandomEvent.create_random_event()

def calculate_duel_outcome(challenger, opponent, duel_type):
    """Backward compatibility function for calculate_duel_outcome."""
    return DuelCalculator.calculate_outcome(challenger, opponent, duel_type)

def calculate_hp_factor(current_hp, max_hp):
    """Backward compatibility function for calculate_hp_factor."""
    return HPFactorCalculator.calculate_factor(current_hp, max_hp)

def generate_duel_narration(duel_result):
    """Backward compatibility function for generate_duel_narration."""
    return DuelNarrator.generate_narration(duel_result)

import re
from typing import Dict, List, Optional, Tuple
from utils.persistence.dynamodb_players import get_player, update_player
from utils.persistence.dynamodb_clubs import get_all_clubs

def normalize_club_name(name: str) -> str:
    """Normalize club name to a valid format."""
    # Convert to lowercase
    name = name.lower()
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Remove special characters
    name = re.sub(r'[^a-z0-9_]', '', name)
    return name

async def select_club(user_id: str, club_id: Optional[str] = None) -> str:
    """Select a club for a player."""
    try:
        # Get player data
        player = await get_player(user_id)
        if not player:
            return "Jogador não encontrado."
        
        # Check if player is already in a club
        if player.get('club_id'):
            return "Você já está em um clube. Não é possível trocar de clube."
        
        # If no club specified, return available clubs
        if not club_id:
            clubs = await get_all_clubs()
            if not clubs:
                return "Nenhum clube disponível no momento."
            return "Por favor, escolha um clube válido."
        
        # Normalize club ID
        club_id = normalize_club_name(club_id)
        
        # Get all clubs to validate club_id
        clubs = await get_all_clubs()
        valid_clubs = [c['club_id'] for c in clubs]
        
        if club_id not in valid_clubs:
            return "Clube inválido. Por favor, escolha um clube válido."
        
        # Update player's club
        await update_player(user_id, club_id=club_id)
        
        # Get club name for response
        club = next((c for c in clubs if c['club_id'] == club_id), None)
        club_name = club['name'] if club else club_id
        
        return f"Você foi registrado no clube {club_name}!"
        
    except Exception as e:
        return f"Erro ao selecionar clube. Por favor, tente novamente mais tarde."

def calculate_exp_gain(player_level: int, enemy_level: int) -> int:
    """Calculate experience gain based on player and enemy levels."""
    level_diff = enemy_level - player_level
    base_exp = 10
    
    if level_diff > 0:
        # Bonus for fighting higher level enemies
        exp_gain = base_exp * (1 + (level_diff * 0.2))
    else:
        # Penalty for fighting lower level enemies
        exp_gain = base_exp * (1 + (level_diff * 0.1))
    
    return max(1, int(exp_gain))

def calculate_level_up(current_level: int, current_exp: int) -> Tuple[int, int]:
    """Calculate new level and remaining experience."""
    exp_needed = current_level * 100  # Base experience needed for next level
    
    if current_exp < exp_needed:
        return current_level, current_exp
    
    new_level = current_level
    remaining_exp = current_exp
    
    while remaining_exp >= exp_needed:
        remaining_exp -= exp_needed
        new_level += 1
        exp_needed = new_level * 100
    
    return new_level, remaining_exp
