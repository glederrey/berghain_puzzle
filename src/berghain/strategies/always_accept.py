"""Always accept strategy for the Berghain puzzle."""

from typing import Dict, Any
from .base import DecisionStrategy

# Import from parent package
from ..api import Person, GameState


class AlwaysAcceptStrategy(DecisionStrategy):
    """Strategy that always accepts until venue is full."""
    
    def decide(self, person: Person, game_state: GameState, current_stats: Dict[str, Any]) -> bool:
        """Always accept if there's space."""
        return game_state.admitted_count < 1000
    
    def get_name(self) -> str:
        return "AlwaysAccept"
