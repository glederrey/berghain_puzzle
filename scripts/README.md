# Berghain Puzzle Experiment Scripts

This folder contains Python scripts to run automated experiments for the Berghain puzzle, replicating the notebook functionality but with automatic dashboard saving.

## Scripts Overview

### 1. `run_experiment.py` - Full-featured Experiment Runner

The main experiment script with comprehensive features and configuration options.

**Features:**
- Automatic dashboard saving every N steps
- Configurable strategy parameters
- Progress tracking and reporting
- Error handling and recovery
- Detailed final summary

**Usage:**
```bash
# Basic usage
python scripts/run_experiment.py

# Custom configuration
python scripts/run_experiment.py --scenario 2 --steps-per-save 200 --max-steps 1500

# Strategy tuning
python scripts/run_experiment.py --initial-tolerance 0.25 --final-tolerance 0.01 --strictness-start 0.05
```

**Arguments:**
- `--scenario`: Scenario number (1, 2, or 3) [default: 1]
- `--steps-per-save`: Steps between dashboard saves [default: 100]
- `--max-steps`: Maximum steps to run [default: 2000]
- `--output-dir`: Output directory [default: "experiment_outputs"]
- `--initial-tolerance`: Strategy initial tolerance [default: 0.20]
- `--final-tolerance`: Strategy final tolerance [default: 0.02]
- `--strictness-start`: When to start reducing tolerance [default: 0.10]

### 2. `quick_experiment.py` - Simple Quick Runner

A simplified script for quick experiments with minimal configuration.

**Usage:**
```bash
# Quick 500-step experiment
python scripts/quick_experiment.py

# Custom quick experiment
python scripts/quick_experiment.py --scenario 3 --steps 300 --interval 50
```

### 3. `batch_experiment.py` - Parallel Multiple Experiment Runner

Run multiple experiments with different configurations in parallel and compare results.

**Features:**
- **Parallel execution** using ThreadPoolExecutor
- **Dashboard override mode** - continuously updates the same dashboard file
- **Thread-safe progress reporting**
- **Configurable worker count**

**Usage:**
```bash
# List available configurations
python scripts/batch_experiment.py --list-configs

# Run batch with multiple scenarios and configs (parallel)
python scripts/batch_experiment.py --scenarios 1 2 3 --configs standard aggressive conservative

# Quick batch test with limited workers
python scripts/batch_experiment.py --scenarios 1 --configs quick standard --max-workers 2

# Run without dashboard override (save all intermediate versions)
python scripts/batch_experiment.py --scenarios 1 2 --configs standard --no-override
```

**Arguments:**
- `--scenarios`: Scenario numbers to test [default: 1]
- `--configs`: Configuration names to test [default: standard]
- `--max-workers`: Maximum parallel workers [default: auto]
- `--no-override`: Don't override dashboard files (save all versions)
- `--output-dir`: Output directory [default: "batch_experiments"]

### 4. `experiment_config.py` - Configuration Management

Predefined configurations for different experiment types.

**Available Configurations:**
- `quick`: 50 steps/save, 300 max steps, standard strategy
- `standard`: 100 steps/save, 1000 max steps, balanced strategy
- `full`: 200 steps/save, 3000 max steps, comprehensive run
- `aggressive`: Quick strict strategy (low tolerance)
- `conservative`: Lenient strategy (high tolerance)

## Output Structure

### Individual Experiments
```
experiment_outputs/
├── game_id_0100steps_123456.html      # Dashboard at 100 steps
├── game_id_0100steps_constraints_123456.html  # Constraint chart
├── game_id_0200steps_123456.html      # Dashboard at 200 steps
└── ...
```

### Batch Experiments
```
batch_experiments/
├── exp_001_standard_s1_game_id/
│   ├── game_id_dashboard.html        # Main dashboard (overridden)
│   ├── dashboard_0100.html           # Step-specific saves
│   ├── dashboard_0200.html
│   ├── final_dashboard.html
│   └── experiment_metadata.json
├── exp_002_aggressive_s1_game_id/
│   └── ...
└── batch_results.json
```

**Dashboard Override Mode:**
- `game_id_dashboard.html`: Always contains the latest state (continuously overwritten)
- `dashboard_XXXX.html`: Step-specific versions for historical tracking
- `final_dashboard.html`: Final state snapshot

## Dashboard Files

Each saved dashboard includes:
- **Top Left**: Game progress (admitted vs rejected counts)
- **Top Right**: Constraint percentages over time
- **Bottom Left**: Current constraint status bars
- **Bottom Right**: Recent decision timeline

## Requirements

- Python 3.8+
- All dependencies from the main project (installed via `uv`)
- `.env` file with `PLAYER_ID` in the project root
- Internet connection for API calls

## Examples

### Run a Standard Experiment
```bash
cd /path/to/berghain_puzzle
python scripts/run_experiment.py --scenario 1 --steps-per-save 100
```

### Test Multiple Strategies (Parallel)
```bash
# Run multiple experiments in parallel
python scripts/batch_experiment.py --scenarios 1 2 --configs aggressive standard conservative

# Limit parallel workers (useful for resource management)
python scripts/batch_experiment.py --scenarios 1 2 --configs aggressive standard --max-workers 3
```

### Quick Test
```bash
python scripts/quick_experiment.py --steps 200
```

## Tips

1. **Dashboard Frequency**: Lower `steps-per-save` for more detailed tracking, higher for faster execution
2. **Strategy Tuning**: Use `aggressive` config for strict constraint adherence, `conservative` for higher admission rates
3. **Parallel Execution**: Batch experiments run in parallel by default for faster completion
4. **Resource Management**: Use `--max-workers` to limit parallel execution on resource-constrained systems
5. **Dashboard Override**: Default behavior continuously updates the main dashboard file for live monitoring
6. **Output Management**: Each experiment creates unique files using game_id, so multiple runs won't overwrite
7. **Interruption**: Scripts handle Ctrl+C gracefully and save current progress

## Monitoring Progress

All scripts provide real-time progress updates:
- Step completion status
- Current admitted/rejected counts
- Constraint satisfaction progress
- File save confirmations
- Final summary with success metrics

The saved HTML dashboards can be opened in any web browser to visualize the results interactively.
