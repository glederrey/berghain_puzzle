# Berghain Puzzle - ListenLabs Challenge

A Python project for solving the Berghain bouncer puzzle challenge by ListenLabs.

## Problem Description

You're the bouncer at a night club. Your goal is to fill the venue with N=1000 people while satisfying constraints like "at least 40% Berlin locals", or "at least 80% wearing all black". People arrive one by one, and you must immediately decide whether to let them in or turn them away. Your challenge is to fill the venue with as few rejections as possible while meeting all minimum requirements.

### Rules
- People arrive sequentially with binary attributes (e.g., female/male, young/old, regular/new)
- You must make immediate accept/reject decisions
- The game ends when either:
  - (a) venue is full (1000 people)
  - (b) you rejected 20,000 people
- There are 3 different scenarios with different constraints and attribute distributions

## Project Structure

```
berghain_puzzle/
├── src/berghain/           # Main package
│   ├── __init__.py
│   ├── api.py             # API client for game interactions
│   ├── strategies.py      # Decision strategies (random, constraint-aware, etc.)
│   ├── visualization.py   # Plotly visualizations
│   └── utils.py          # Utility functions
├── notebooks/              # Jupyter notebooks
│   └── berghain_experiment.ipynb  # Main experimentation notebook
├── .env                   # Environment variables (Player ID)
├── pyproject.toml        # UV project configuration
└── README.md             # This file
```

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd berghain_puzzle
   ```

2. **Activate the UV environment:**
   ```bash
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Ready to use:**
   The API endpoint is already configured for the ListenLabs challenge (`https://berghain.challenges.listenlabs.ai`).

## Usage

### Jupyter Notebook (Recommended)

Start the notebook for interactive experimentation:

```bash
jupyter notebook notebooks/berghain_experiment.ipynb
```

The notebook includes:
- Setup and imports
- Strategy definition and testing
- Single game experiments
- Visualization of results
- Multiple strategy comparison
- Custom strategy development space

### Python Scripts

You can also use the package directly in Python:

```python
from berghain.api import BerghainAPI
from berghain.strategies import RandomStrategy, ConstraintAwareStrategy, GameRunner
from berghain.visualization import BerghainVisualizer

# Initialize API client
api = BerghainAPI()  # Uses default ListenLabs endpoint

# Create and run a strategy
strategy = ConstraintAwareStrategy(safety_margin=0.1)
runner = GameRunner(api, strategy)
results = runner.run_game(scenario=1)

# Visualize results
visualizer = BerghainVisualizer()
dashboard = visualizer.create_summary_dashboard(results)
dashboard.show()
```

## Strategies Included

1. **RandomStrategy**: Makes random accept/reject decisions
2. **AlwaysAcceptStrategy**: Accepts everyone until venue is full
3. **ConstraintAwareStrategy**: Makes decisions based on constraint progress and safety margins

## Key Features

- **Modular Design**: Easy to add new strategies by inheriting from `DecisionStrategy`
- **Comprehensive Visualization**: Multiple plot types for analyzing game performance
- **Strategy Comparison**: Tools for comparing multiple strategies side-by-side
- **Data Analysis**: Utilities for understanding attribute distributions and correlations
- **Result Persistence**: Save and load game results for later analysis

## API Integration

The project includes a complete API client that handles:
- Game creation for different scenarios
- Person evaluation and decision submission
- Game state tracking
- Error handling and retries

## Visualization

Multiple visualization types are available:
- Game progress over time
- Attribute distribution comparisons
- Constraint satisfaction progress
- Decision timelines
- Strategy performance comparisons
- Correlation matrices

## Strategy Development Tips

1. **Analyze attribute frequencies** to understand how often you'll see each attribute
2. **Consider correlations** between attributes - some might appear together frequently
3. **Build in safety margins** since you don't know exact distributions
4. **Monitor constraint progress** as the game progresses
5. **Balance acceptance rate** vs constraint satisfaction

## Development

To add a new strategy:

1. Create a class inheriting from `DecisionStrategy`
2. Implement the `decide()` method
3. Implement the `get_name()` method
4. Test it using the notebook or scripts

Example:
```python
class MyStrategy(DecisionStrategy):
    def decide(self, person, game_state, current_stats):
        # Your decision logic here
        return True  # or False
    
    def get_name(self):
        return "MyStrategy"
```

## Results and Analysis

The project provides tools for:
- Tracking game history and decisions
- Calculating performance metrics
- Comparing strategies across scenarios
- Saving results for later analysis
- Generating comprehensive reports

## Environment Variables

- `PLAYER_ID`: Your player ID for the ListenLabs challenge (stored in `.env`)

## Dependencies

- `requests`: HTTP client for API calls
- `plotly`: Interactive visualizations
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `jupyter`: Interactive notebook environment
- `python-dotenv`: Environment variable management

## Next Steps

1. Run experiments on all three scenarios
2. Analyze attribute statistics and correlations
3. Develop sophisticated strategies based on the data
4. Optimize for minimum rejections while meeting constraints
5. Submit your best strategy to the ListenLabs challenge!
