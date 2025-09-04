"""Random decision strategy for the Berghain puzzle."""

import random
from typing import Dict, Any
from .base import DecisionStrategy

# Import from parent package
from ..api import Person, GameState


class RandomStrategy(DecisionStrategy):
    """Random decision strategy for testing."""
    
    def __init__(self, acceptance_rate: float = 0.5):
        """Initialize with acceptance rate.
        
        Args:
            acceptance_rate: Probability of accepting any person
        """
        self.acceptance_rate = acceptance_rate
    
    def decide(self, person: Person, game_state: GameState, current_stats: Dict[str, Any]) -> bool:
        """Make a random decision."""
        return random.random() < self.acceptance_rate
    
    def get_name(self) -> str:
        return f"Random({self.acceptance_rate})"
