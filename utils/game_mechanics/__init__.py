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
