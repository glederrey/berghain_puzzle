"""Constraint-aware strategy for the Berghain puzzle."""

from typing import Dict, Any
import random
from .base import DecisionStrategy

# Import from parent package
from ..api import Person, GameState


class Scenario1Strategy(DecisionStrategy):
    """Enhanced strategy that uses statistical information and strict no-attribute controls."""
    
    def __init__(self, initial_tolerance: float = 0.20, final_tolerance: float = 0.02, strictness_start: float = 0.1):
        """Initialize with dynamic tolerance that decreases over time.
        
        Args:
            initial_tolerance: Starting tolerance when venue is empty (0.20 = 20% tolerance)
            final_tolerance: Final tolerance when venue is nearly full (0.02 = 2% tolerance)
            strictness_start: When to start reducing tolerance (0.1 = after 10% of venue filled)
        """
        self.initial_tolerance = initial_tolerance
        self.final_tolerance = final_tolerance
        self.strictness_start = strictness_start
        self._constraints = []
        self._relative_frequencies = {}
        self._correlations = {}
        self._attribute_statistics = None
    
    def _calculate_current_tolerance(self, admitted_count: int) -> float:
        """Calculate current tolerance based on how full the venue is.
        
        Args:
            admitted_count: Number of people currently admitted
            
        Returns:
            Current tolerance value
        """
        # Calculate progress through the venue (0.0 to 1.0)
        progress = admitted_count / 1000.0

        if progress >= 0.95:
            return 0
        
        # Before strictness_start, use initial tolerance
        if progress <= self.strictness_start:
            return self.initial_tolerance
        
        # After strictness_start, linearly interpolate to final tolerance
        # Calculate how far we are in the strictness phase
        strictness_progress = (progress - self.strictness_start) / (1.0 - self.strictness_start)
        strictness_progress = min(1.0, max(0.0, strictness_progress))  # Clamp to [0,1]
        
        # Linear interpolation between initial and final tolerance
        current_tolerance = self.initial_tolerance - (self.initial_tolerance - self.final_tolerance) * strictness_progress
        
        return current_tolerance
    
    def _calculate_no_attributes_target_with_statistics(self) -> float:
        """Calculate target percentage for people with no attributes using statistical data.
        
        Uses relative frequencies and correlations to estimate how many people
        will naturally have no constraint attributes.
        
        Returns:
            Target percentage for people with no attributes (0.0 to 1.0)
        """
        if not self._constraints or not self._relative_frequencies:
            # Fallback to basic calculation
            return self._calculate_no_attributes_target_basic()
        
        # Calculate probability that a random person has NONE of the constraint attributes
        # This uses the inclusion-exclusion principle with correlations
        
        constraint_attrs = [c.attribute for c in self._constraints]
        
        if len(constraint_attrs) == 1:
            # Simple case: P(not A) = 1 - P(A)
            attr = constraint_attrs[0]
            freq = self._relative_frequencies.get(attr, 0.5)
            return 1.0 - freq
        
        elif len(constraint_attrs) == 2:
            # Two attributes: P(not A and not B) = 1 - P(A or B)
            # P(A or B) = P(A) + P(B) - P(A and B)
            attr1, attr2 = constraint_attrs
            freq1 = self._relative_frequencies.get(attr1, 0.5)
            freq2 = self._relative_frequencies.get(attr2, 0.5)
            
            # Estimate P(A and B) using correlation
            correlation = self._correlations.get(attr1, {}).get(attr2, 0.0)
            # P(A and B) ≈ P(A) * P(B) * (1 + correlation)
            # But this is approximate - correlation doesn't directly give us joint probability
            # Use a more conservative estimate
            joint_prob = freq1 * freq2 * (1 + max(0, correlation))
            joint_prob = min(joint_prob, min(freq1, freq2))  # Can't exceed individual frequencies
            
            prob_either = freq1 + freq2 - joint_prob
            prob_neither = 1.0 - prob_either
            
            return max(0.05, min(0.8, prob_neither))  # Clamp to reasonable bounds
        
        else:
            # More than 2 attributes - use approximation
            # Assume independence as approximation (correlations make this complex)
            prob_none = 1.0
            for constraint in self._constraints:
                attr = constraint.attribute
                freq = self._relative_frequencies.get(attr, 0.5)
                prob_none *= (1.0 - freq)
            
            return max(0.05, min(0.8, prob_none))
    
    def _calculate_no_attributes_target_basic(self) -> float:
        """Basic fallback calculation for no-attributes target."""
        if not self._constraints:
            return 0.4
        
        # Conservative estimate based on constraint requirements
        max_constraint_percentage = max(c.min_count / 1000.0 for c in self._constraints)
        total_constraint_percentage = sum(c.min_count / 1000.0 for c in self._constraints)
        
        # Assume some overlap between constraints
        estimated_constraint_coverage = max(max_constraint_percentage, total_constraint_percentage * 0.6)
        no_attr_target = 1.0 - estimated_constraint_coverage
        
        return max(0.1, min(0.7, no_attr_target))
    
    def _decide_no_attributes_person(self, admitted_count: int, current_stats: Dict[str, Any], show_progress: bool = True) -> bool:
        """Decide whether to accept a person with no attributes using statistical targets.
        
        Much more restrictive approach using statistical information to set realistic targets.
        
        Args:
            admitted_count: Number of people currently admitted
            current_stats: Current statistics about admitted people
            
        Returns:
            True to accept, False to reject
        """
        # Calculate progress through the venue
        progress = admitted_count / 1000.0
        
        # Count current people with no attributes
        admitted_people = current_stats.get('admitted_people', [])
        current_no_attr_count = sum(1 for person in admitted_people 
                                   if all(not person.get(attr, False) for attr in person))
        
        # Calculate current percentage among admitted people
        current_no_attr_percentage = (current_no_attr_count / len(admitted_people)) if admitted_people else 0
        
        # Use statistical target calculation
        target_percentage = self._calculate_no_attributes_target_with_statistics()
        
        if show_progress and admitted_count % 50 == 0:  # Print target occasionally
            print(f"  📊 No-attr target: {target_percentage:.1%} (based on frequencies)")
        
        # If we're already over-represented, be extremely selective
        if current_no_attr_percentage > (target_percentage + 0.02):  # Very tight tolerance
            if show_progress:
                print(f"  🚫 No-attr over-represented ({current_no_attr_percentage:.1%} vs target {target_percentage:.1%})")
            return False
        
        # MUCH more restrictive base rates
        if progress <= 0.05:
            # Very early game: still be selective (20%)
            base_rate = 0.2
        elif progress <= 0.15:
            # Early game: low acceptance rate (15%)
            base_rate = 0.15
        elif progress <= 0.3:
            # Early-mid game: lower rate (10%)
            base_rate = 0.1
        elif progress <= 0.5:
            # Mid game: very low rate (5%)
            base_rate = 0.05
        elif progress <= 0.7:
            # Late-mid game: extremely low rate (2%)
            base_rate = 0.02
        elif progress <= 0.9:
            # Late game: barely accept (1%)
            base_rate = 0.01
        else:
            # Final stage: almost never accept
            base_rate = 0.005
        
        # Adjust rate based on how close we are to target
        if current_no_attr_percentage < (target_percentage - 0.1):
            # We need significantly more, small boost
            acceptance_rate = min(0.3, base_rate * 1.5)
        elif current_no_attr_percentage < (target_percentage - 0.03):
            # We need some more, tiny boost
            acceptance_rate = min(0.2, base_rate * 1.2)
        elif current_no_attr_percentage < target_percentage:
            # Close to target, use base rate
            acceptance_rate = base_rate
        else:
            # At or above target, be extremely selective
            acceptance_rate = base_rate * 0.1
        
        # Additional constraint: if we have constraint attributes that are under-represented,
        # be even more selective about no-attribute people
        if self._constraints and admitted_people:
            any_constraint_struggling = False
            for constraint in self._constraints:
                attr = constraint.attribute
                current_count = current_stats.get('attribute_counts', {}).get(attr, 0)
                required_count = constraint.min_count
                current_attr_percentage = current_count / len(admitted_people)
                target_attr_percentage = required_count / 1000.0
                
                # If any constraint is significantly behind target
                if current_attr_percentage < (target_attr_percentage - 0.05):
                    any_constraint_struggling = True
                    break
            
            if any_constraint_struggling:
                acceptance_rate *= 0.5  # Be even more selective
                if show_progress:
                    print(f"  ⚠️  Constraint attributes struggling, reducing no-attr acceptance")
        
        # Use random decision based on acceptance rate
        decision = random.random() < acceptance_rate
        
        if show_progress:
            if decision:
                print(f"  ✅ Accepting no-attr person ({current_no_attr_percentage:.1%} current vs {target_percentage:.1%} target, rate {acceptance_rate:.1%})")
            else:
                print(f"  🚫 Rejecting no-attr person ({current_no_attr_percentage:.1%} current vs {target_percentage:.1%} target, rate {acceptance_rate:.1%})")
            
        return decision
    
    def _calculate_expected_attribute_yield(self, attr: str, remaining_people: int) -> float:
        """Calculate expected number of people with attribute based on relative frequency.
        
        Args:
            attr: Attribute name
            remaining_people: Number of people still to be seen
            
        Returns:
            Expected count of people with this attribute
        """
        if not self._relative_frequencies:
            return remaining_people * 0.5  # Default 50% assumption
        
        frequency = self._relative_frequencies.get(attr, 0.5)
        return remaining_people * frequency
    
    def decide(self, person: Person, game_state: GameState, current_stats: Dict[str, Any], show_progress: bool = True) -> bool:
        """Enhanced decision making using statistical information and strict no-attribute control."""
        
        # Don't accept if venue is full
        if game_state.admitted_count >= 1000:
            return False
        
        # Handle people with no attributes using enhanced statistical approach
        if all(not person.attributes.get(attr, False) for attr in person.attributes):
            return self._decide_no_attributes_person(game_state.admitted_count, current_stats, show_progress)
        
        # If we haven't admitted anyone yet, accept to get started
        admitted_count = current_stats.get('admitted_people', [])
        if len(admitted_count) == 0:
            return True
        
        # Get constraints
        if not hasattr(self, '_constraints') or not self._constraints:
            constraints = getattr(game_state, 'constraints', [])
            if constraints:
                self._constraints = constraints
            else:
                return True
        else:
            constraints = self._constraints
        
        # Calculate current percentages among admitted people
        total_admitted = len(admitted_count)
        remaining_spots = 1000 - total_admitted
        
        # Calculate dynamic tolerance based on venue fullness
        current_tolerance = self._calculate_current_tolerance(total_admitted)
        
        # Show statistical information occasionally
        progress = total_admitted / 1000.0
        milestone_points = [0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9]
        if any(abs(progress - mp) < 0.005 for mp in milestone_points) and show_progress:
            print(f"  📊 Progress: {progress:.1%}, Tolerance: {current_tolerance:.1%}")
            if self._relative_frequencies:
                print(f"  📈 Frequencies: {self._relative_frequencies}")
        
        for constraint in constraints:
            attr = constraint.attribute
            required_count = constraint.min_count
            target_percentage = required_count / 1000.0
            
            # Current count and percentage
            current_count = current_stats.get('attribute_counts', {}).get(attr, 0)
            current_percentage = current_count / total_admitted if total_admitted > 0 else 0
            
            person_has_attr = person.attributes.get(attr, False)
            
            # Enhanced over-representation check using statistical expectations
            if person_has_attr and current_percentage > (target_percentage + current_tolerance):
                if show_progress:
                    print(f"  🚫 Rejecting: {attr} over-represented ({current_percentage:.1%} vs {target_percentage:.1%}, tol {current_tolerance:.1%})")
                return False
            
            # Enhanced under-representation check using expected yield
            if not person_has_attr and current_percentage < (target_percentage - 0.08):
                still_needed = required_count - current_count
                
                # Use statistical information to estimate if we can still meet the constraint
                if self._relative_frequencies and attr in self._relative_frequencies:
                    expected_yield = self._calculate_expected_attribute_yield(attr, remaining_spots)
                    
                    # If expected yield from remaining people is insufficient, be selective
                    if expected_yield < still_needed * 1.2:  # Need 20% buffer
                        if show_progress:
                            print(f"  🚫 Rejecting: Need more {attr} ({current_count}/{required_count}, "
                                  f"expected {expected_yield:.1f} from {remaining_spots} remaining)")
                        return False
                else:
                    # Fallback to original logic if no statistical data
                    if still_needed > remaining_spots * 0.7:  # Made slightly less strict
                        if show_progress:
                            print(f"  🚫 Rejecting: Need more {attr} ({current_count}/{required_count})")
                        return False
            
            # Bonus: if person has a highly correlated attribute combination, prefer them
            if person_has_attr and self._correlations:
                person_attrs = [a for a, v in person.attributes.items() if v]
                if len(person_attrs) > 1:
                    # Check if this person has positively correlated attributes
                    correlation_bonus = 0
                    for other_attr in person_attrs:
                        if other_attr != attr and other_attr in self._correlations.get(attr, {}):
                            corr = self._correlations[attr][other_attr]
                            if corr > 0.1:  # Positive correlation
                                correlation_bonus += corr
                    
                    if correlation_bonus > 0.2 and show_progress:
                        print(f"  ⭐ Person has correlated attributes ({attr} + others), correlation bonus: {correlation_bonus:.2f}")
        
        # Accept if no over-representation concerns
        return True
    
    def on_game_start(self, game_state: GameState) -> None:
        """Store constraints and statistical information when game starts."""
        self._constraints = getattr(game_state, 'constraints', [])
        
        # Extract statistical information from attribute_statistics
        attribute_statistics = getattr(game_state, 'attribute_statistics', None)
        if attribute_statistics:
            self._relative_frequencies = getattr(attribute_statistics, 'relative_frequencies', {})
            self._correlations = getattr(attribute_statistics, 'correlations', {})
            self._attribute_statistics = attribute_statistics
            
            print(f"  📊 Loaded statistical data:")
            print(f"      Relative frequencies: {self._relative_frequencies}")
            print(f"      Correlations available for: {list(self._correlations.keys())}")
            
            # Calculate and display the statistical no-attributes target
            if self._constraints:
                stat_target = self._calculate_no_attributes_target_with_statistics()
                basic_target = self._calculate_no_attributes_target_basic()
                print(f"      No-attr target: {stat_target:.1%} (statistical) vs {basic_target:.1%} (basic)")
        else:
            print(f"  ⚠️  No statistical data available, using fallback logic")
    
    def get_name(self) -> str:
        stat_info = "with_stats" if self._relative_frequencies else "no_stats"
        return f"Scenario1Strategy_Enhanced(tol:{self.initial_tolerance:.0%}->{self.final_tolerance:.0%}@{self.strictness_start:.0%},{stat_info})"
