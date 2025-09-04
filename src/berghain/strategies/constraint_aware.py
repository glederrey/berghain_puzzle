"""Constraint-aware strategy for the Berghain puzzle."""

from typing import Dict, Any
from .base import DecisionStrategy

# Import from parent package
from ..api import Person, GameState


class ConstraintAwareStrategy(DecisionStrategy):
    """Strategy that considers constraints when making decisions."""
    
    def __init__(self, safety_margin: float = 0.1):
        """Initialize with safety margin.
        
        Args:
            safety_margin: Extra margin above minimum requirements (0.1 = 10% extra)
        """
        self.safety_margin = safety_margin
    
    def decide(self, person: Person, game_state: GameState, current_stats: Dict[str, Any]) -> bool:
        """Make decision based on constraints and current progress."""
        # Always accept if we have space and no constraints to worry about
        if game_state.admitted_count >= 1000:
            return False
            
        if not game_state.constraints:
            return True
        
        # Calculate how much we need of each attribute
        remaining_spots = 1000 - game_state.admitted_count
        
        for constraint in game_state.constraints:
            attr = constraint.attribute
            min_needed = constraint.min_count
            
            # Add safety margin
            target_count = int(min_needed * (1 + self.safety_margin))
            
            current_count = current_stats.get('attribute_counts', {}).get(attr, 0)
            still_needed = target_count - current_count
            
            # If this person has the attribute we need and we still need it
            if person.attributes.get(attr, False) and still_needed > 0:
                return True
                
            # If we desperately need this attribute and this person doesn't have it
            if still_needed > remaining_spots * 0.8 and not person.attributes.get(attr, False):
                return False
        
        # Default to accepting if no urgent constraints
        return True
    
    def get_name(self) -> str:
        return f"ConstraintAware(margin={self.safety_margin})"
