"""Enhanced game runner with step-by-step control and real-time feedback."""

from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass

# Import from parent package
from .api import BerghainAPI, Person, GameState, Constraint
from .strategies.base import DecisionStrategy


@dataclass
class PersonRecord:
    """Record of a person and the decision made."""
    person_index: int
    attributes: Dict[str, bool]
    decision: bool
    timestamp: float
    admitted_count_before: int
    rejected_count_before: int
    admitted_count_after: int
    rejected_count_after: int


class GameRunner:
    """Enhanced game runner with step-by-step control and comprehensive tracking."""
    
    def __init__(self, api_client: BerghainAPI, strategy: DecisionStrategy):
        """Initialize game runner.
        
        Args:
            api_client: BerghainAPI instance
            strategy: Decision strategy to use
        """
        self.api = api_client
        self.strategy = strategy
        self.reset()
    
    def reset(self):
        """Reset the game state."""
        self.game_state: Optional[GameState] = None
        self.initial_game_info: Optional[GameState] = None  # Store initial constraints and stats
        self.people_history: List[PersonRecord] = []
        self.current_stats = {
            'attribute_counts': {},
            'admitted_people': [],
            'rejected_people': [],
            'steps_taken': 0
        }
        self.game_started = False
        self.game_completed = False
    
    def start_game(self, scenario: int) -> GameState:
        """Start a new game and return initial state.
        
        Args:
            scenario: Scenario number (1, 2, or 3)
            
        Returns:
            Initial game state with constraints and statistics
        """
        print(f"🎮 Starting new game - Scenario {scenario}")
        
        # Start new game
        self.reset()
        self.initial_game_info = self.api.new_game(scenario)
        self.game_state = self.initial_game_info  # Start with the full initial state
        
        # Initialize attribute counts based on constraints
        for constraint in self.initial_game_info.constraints:
            self.current_stats['attribute_counts'][constraint.attribute] = 0
        
        # Let strategy know game is starting
        self.strategy.on_game_start(self.initial_game_info)
        
        # Get first person (this will update game_state but we keep initial_game_info)
        self.game_state = self.api.decide_and_next(self.initial_game_info.game_id, 0)
        self.game_started = True
        
        print("✅ Game started successfully!")
        self.display_game_info()
        
        return self.game_state
    
    def display_game_info(self):
        """Display current game information."""
        if not self.game_state:
            print("❌ No active game")
            return
        
        print("\n" + "="*60)
        print(f"🎯 GAME STATUS - {self.strategy.get_name()}")
        print("="*60)
        print(f"Game ID: {self.game_state.game_id}")
        print(f"Status: {self.game_state.status}")
        print(f"Admitted: {self.game_state.admitted_count}/1000")
        print(f"Rejected: {self.game_state.rejected_count}/20000")
        print(f"Steps taken: {self.current_stats['steps_taken']}")
        
        if self.initial_game_info and self.initial_game_info.constraints:
            print(f"\n🎯 CONSTRAINTS:")
            for constraint in self.initial_game_info.constraints:
                attr = constraint.attribute
                required = constraint.min_count
                current = self.current_stats['attribute_counts'].get(attr, 0)
                percentage = (current / required * 100) if required > 0 else 100
                status = "✅" if current >= required else "⚠️"
                print(f"  {status} {attr}: {current}/{required} ({percentage:.1f}%)")
        
        if self.initial_game_info and self.initial_game_info.attribute_statistics.relative_frequencies:
            print(f"\n📊 ATTRIBUTE FREQUENCIES:")
            for attr, freq in self.initial_game_info.attribute_statistics.relative_frequencies.items():
                print(f"  {attr}: {freq:.3f} ({freq*100:.1f}%)")
        
        if self.game_state.next_person:
            print(f"\n👤 NEXT PERSON (#{self.game_state.next_person.person_index}):")
            for attr, value in self.game_state.next_person.attributes.items():
                emoji = "✅" if value else "❌"
                print(f"  {emoji} {attr}: {value}")
        
        print("="*60)
    
    def display_constraints_only(self):
        """Display constraints and attribute statistics information."""
        if not self.initial_game_info or not self.initial_game_info.constraints:
            print("❌ No constraints available")
            return
        
        print("\n🎯 GAME CONSTRAINTS:")
        print("-" * 50)
        for constraint in self.initial_game_info.constraints:
            freq = self.initial_game_info.attribute_statistics.relative_frequencies.get(constraint.attribute, 0)
            expected_total = freq * 1000
            difficulty = constraint.min_count / expected_total if expected_total > 0 else float('inf')
            
            print(f"📋 {constraint.attribute}:")
            print(f"   Required: {constraint.min_count}/1000 ({constraint.min_count/10:.1f}%)")
            print(f"   Expected: ~{expected_total:.0f} ({freq*100:.1f}%)")
            print(f"   Difficulty: {difficulty:.2f}")
            print()
        
        # Display all attribute statistics
        print("📊 ATTRIBUTE STATISTICS:")
        print("-" * 50)
        print("Relative Frequencies:")
        for attr, freq in self.initial_game_info.attribute_statistics.relative_frequencies.items():
            print(f"  {attr}: {freq:.4f} ({freq*100:.1f}%)")
        
        print("\nCorrelations:")
        for attr1, correlations in self.initial_game_info.attribute_statistics.correlations.items():
            for attr2, corr in correlations.items():
                if attr1 != attr2:  # Skip self-correlations (always 1.0)
                    print(f"  {attr1} ↔ {attr2}: {corr:.4f}")
        print()
    
    def step(self, num_steps: int = 1, show_progress: bool = True) -> List[PersonRecord]:
        """Execute a number of game steps.
        
        Args:
            num_steps: Number of steps to execute
            show_progress: Whether to show progress during execution
            
        Returns:
            List of person records for the steps taken
        """
        if not self.game_started or self.game_completed:
            print("❌ Game not started or already completed")
            return []
        
        step_records = []
        
        for step in range(num_steps):

            if not show_progress:
                print(f"🔄 Step {step+1} of {num_steps}", end="\r")

            if not self.game_state.next_person or self.game_state.status != 'running':
                print(f"🏁 Game ended after {step} steps")
                self.game_completed = True
                break
            
            person = self.game_state.next_person
            
            # Make decision
            decision = self.strategy.decide(person, self.game_state, self.current_stats, show_progress)
            
            # Record state before decision
            admitted_before = self.game_state.admitted_count
            rejected_before = self.game_state.rejected_count
            
            # Create person record
            record = PersonRecord(
                person_index=person.person_index,
                attributes=person.attributes.copy(),
                decision=decision,
                timestamp=time.time(),
                admitted_count_before=admitted_before,
                rejected_count_before=rejected_before,
                admitted_count_after=admitted_before + (1 if decision else 0),
                rejected_count_after=rejected_before + (0 if decision else 1)
            )
            
            step_records.append(record)
            self.people_history.append(record)
            
            # Update statistics
            if decision:
                self.current_stats['admitted_people'].append(person.attributes.copy())
                for attr, value in person.attributes.items():
                    if value and attr in self.current_stats['attribute_counts']:
                        self.current_stats['attribute_counts'][attr] += 1
            else:
                self.current_stats['rejected_people'].append(person.attributes.copy())
            
            # Show progress
            if show_progress:
                action = "✅ ADMIT" if decision else "❌ REJECT"
                attrs_str = ", ".join([f"{k}:{v}" for k, v in person.attributes.items()])
                print(f"Step {self.current_stats['steps_taken']+1}: {action} Person #{person.person_index} [{attrs_str}]")
            
            # Send decision and get next person
            self.game_state = self.api.decide_and_next(
                self.game_state.game_id, 
                person.person_index, 
                decision
            )
            
            # Let strategy know about the decision
            self.strategy.on_decision_made(person, decision, self.game_state)
            
            self.current_stats['steps_taken'] += 1
            
            # Check if game is complete
            if self.game_state.status != 'running':
                print(f"🏁 Game completed! Final status: {self.game_state.status}")
                self.game_completed = True
                break
        
        return step_records
    
    def get_people_seen(self) -> List[PersonRecord]:
        """Get list of all people seen so far.
        
        Returns:
            List of PersonRecord objects
        """
        return self.people_history.copy()
    
    def get_admitted_people(self) -> List[PersonRecord]:
        """Get list of admitted people.
        
        Returns:
            List of PersonRecord objects for admitted people
        """
        return [record for record in self.people_history if record.decision]
    
    def get_rejected_people(self) -> List[PersonRecord]:
        """Get list of rejected people.
        
        Returns:
            List of PersonRecord objects for rejected people
        """
        return [record for record in self.people_history if not record.decision]
    
    def get_game_summary(self) -> Dict[str, Any]:
        """Get comprehensive game summary.
        
        Returns:
            Dictionary with game summary information
        """
        if not self.game_state:
            return {}
        
        admitted = self.get_admitted_people()
        rejected = self.get_rejected_people()
        
        return {
            'strategy': self.strategy.get_name(),
            'game_id': self.game_state.game_id,
            'status': self.game_state.status,
            'steps_taken': self.current_stats['steps_taken'],
            'admitted_count': len(admitted),
            'rejected_count': len(rejected),
            'total_seen': len(self.people_history),
            'success': self.game_state.status == 'completed' and len(admitted) == 1000,
            'constraints': [
                {
                    'attribute': c.attribute,
                    'required': c.min_count,
                    'actual': self.current_stats['attribute_counts'].get(c.attribute, 0),
                    'satisfied': self.current_stats['attribute_counts'].get(c.attribute, 0) >= c.min_count
                }
                for c in (self.initial_game_info.constraints if self.initial_game_info else [])
            ],
            'current_stats': self.current_stats,
            'people_history': self.people_history
        }
    
    def save_game_state(self, filename: str = None) -> str:
        """Save current game state to file.
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to saved file
        """
        from ..utils import save_results
        summary = self.get_game_summary()
        return save_results(summary, filename)
