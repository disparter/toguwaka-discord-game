"""
Interface for calculators in the game mechanics.
Following the Interface Segregation Principle, this provides a base interface
that specific calculator types will extend.
"""
from abc import ABC, abstractmethod

class ICalculator(ABC):
    """Base interface for all calculators."""
    pass