"""Base strategy class for the Berghain puzzle."""

from abc import ABC, abstractmethod
from typing import Dict, Any

# Import from parent package
from ..api import Person, GameState


class DecisionStrategy(ABC):
    """Abstract base class for decision strategies."""
    
    @abstractmethod
    def decide(self, person: Person, game_state: GameState, current_stats: Dict[str, Any]) -> bool:
        """Decide whether to accept or reject a person.
        
        Args:
            person: The person to evaluate
            game_state: Current game state
            current_stats: Current statistics about admitted people
            
        Returns:
            True to accept, False to reject
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this strategy."""
        pass
    
    def on_game_start(self, game_state: GameState) -> None:
        """Called when a game starts. Override for initialization logic.
        
        Args:
            game_state: Initial game state with constraints and statistics
        """
        pass
    
    def on_decision_made(self, person: Person, decision: bool, game_state: GameState) -> None:
        """Called after each decision is made. Override for learning/adaptation.
        
        Args:
            person: The person that was evaluated
            decision: The decision that was made
            game_state: Updated game state after the decision
        """
        pass
