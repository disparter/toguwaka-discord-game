# This file makes the duel directory a Python package

from .duel_calculator import DuelCalculator
from .duel_narrator import DuelNarrator

__all__ = ['DuelCalculator', 'DuelNarrator']