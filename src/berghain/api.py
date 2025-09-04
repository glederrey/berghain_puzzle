"""API client for the Berghain puzzle game."""

import os
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Person:
    """Represents a person with attributes."""
    person_index: int
    attributes: Dict[str, bool]


@dataclass
class Constraint:
    """Represents a game constraint."""
    attribute: str
    min_count: int


@dataclass
class AttributeStatistics:
    """Represents attribute statistics for the game."""
    relative_frequencies: Dict[str, float]
    correlations: Dict[str, Dict[str, float]]


@dataclass
class GameState:
    """Represents the current state of the game."""
    game_id: str
    status: str
    admitted_count: int
    rejected_count: int
    next_person: Optional[Person]
    constraints: List[Constraint]
    attribute_statistics: AttributeStatistics


class BerghainAPI:
    """API client for interacting with the Berghain puzzle game."""
    
    def __init__(self, base_url: str = "https://berghain.challenges.listenlabs.ai", player_id: Optional[str] = None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            player_id: Player ID, if not provided will try to load from environment
        """
        self.base_url = base_url.rstrip('/')
        self.player_id = player_id or os.getenv('PLAYER_ID')
        self.session = requests.Session()
        
        if not self.player_id:
            raise ValueError("Player ID must be provided or set in PLAYER_ID environment variable")
    
    def new_game(self, scenario: int) -> GameState:
        """Create a new game.
        
        Args:
            scenario: Scenario number (1, 2, or 3)
            
        Returns:
            GameState object with initial game information
        """
        if scenario not in [1, 2, 3]:
            raise ValueError("Scenario must be 1, 2, or 3")
            
        url = f"{self.base_url}/new-game"
        params = {
            'scenario': scenario,
            'playerId': self.player_id
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse constraints
        constraints = [
            Constraint(attribute=c['attribute'], min_count=c['minCount'])
            for c in data['constraints']
        ]
        
        # Parse attribute statistics
        attr_stats = AttributeStatistics(
            relative_frequencies=data['attributeStatistics']['relativeFrequencies'],
            correlations=data['attributeStatistics']['correlations']
        )
        
        return GameState(
            game_id=data['gameId'],
            status='running',
            admitted_count=0,
            rejected_count=0,
            next_person=None,
            constraints=constraints,
            attribute_statistics=attr_stats
        )
    
    def decide_and_next(self, game_id: str, person_index: int, accept: Optional[bool] = None) -> GameState:
        """Make a decision on a person and get the next person.
        
        Args:
            game_id: The game ID
            person_index: Index of the current person
            accept: Whether to accept the person (None for first person)
            
        Returns:
            Updated GameState
        """
        url = f"{self.base_url}/decide-and-next"
        params = {
            'gameId': game_id,
            'personIndex': person_index
        }
        
        if accept is not None:
            params['accept'] = str(accept).lower()
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse next person if present
        next_person = None
        if data.get('nextPerson'):
            next_person = Person(
                person_index=data['nextPerson']['personIndex'],
                attributes=data['nextPerson']['attributes']
            )
        
        return GameState(
            game_id=game_id,
            status=data['status'],
            admitted_count=data.get('admittedCount', 0),
            rejected_count=data.get('rejectedCount', 0),
            next_person=next_person,
            constraints=[],  # Constraints are only provided at game start
            attribute_statistics=AttributeStatistics({}, {})  # Stats are only provided at game start
        )
    
    def get_game_info(self, game_state: GameState) -> Dict[str, Any]:
        """Get formatted game information for display.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary with formatted game information
        """
        return {
            'game_id': game_state.game_id,
            'status': game_state.status,
            'admitted': game_state.admitted_count,
            'rejected': game_state.rejected_count,
            'total_seen': game_state.admitted_count + game_state.rejected_count,
            'next_person': {
                'index': game_state.next_person.person_index if game_state.next_person else None,
                'attributes': game_state.next_person.attributes if game_state.next_person else None
            } if game_state.next_person else None,
            'constraints': [
                {'attribute': c.attribute, 'min_count': c.min_count}
                for c in game_state.constraints
            ],
            'attribute_frequencies': game_state.attribute_statistics.relative_frequencies,
            'correlations': game_state.attribute_statistics.correlations
        }
