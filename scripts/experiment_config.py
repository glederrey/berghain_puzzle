"""
Experiment Configuration

Default configurations for different types of experiments.
"""

# Default experiment configurations
EXPERIMENT_CONFIGS = {
    "quick": {
        "steps_per_save": 50,
        "max_steps": 100000,
        "strategy_params": {
            "initial_tolerance": 0.20,
            "final_tolerance": 0.02,
            "strictness_start": 0.10
        }
    },
    
    "standard": {
        "steps_per_save": 100,
        "max_steps": 100000,
        "strategy_params": {
            "initial_tolerance": 0.20,
            "final_tolerance": 0.02,
            "strictness_start": 0.10
        }
    },
    
    "full": {
        "steps_per_save": 200,
        "max_steps": 100000,
        "strategy_params": {
            "initial_tolerance": 0.20,
            "final_tolerance": 0.02,
            "strictness_start": 0.10
        }
    },
    
    "aggressive": {
        "steps_per_save": 100,
        "max_steps": 100000,
        "strategy_params": {
            "initial_tolerance": 0.15,
            "final_tolerance": 0.01,
            "strictness_start": 0.05
        }
    },
    
    "conservative": {
        "steps_per_save": 100,
        "max_steps": 100000,
        "strategy_params": {
            "initial_tolerance": 0.30,
            "final_tolerance": 0.05,
            "strictness_start": 0.20
        }
    }
}

def get_config(config_name):
    """Get experiment configuration by name.
    
    Args:
        config_name: Name of the configuration
        
    Returns:
        Configuration dictionary
    """
    if config_name not in EXPERIMENT_CONFIGS:
        print(f"Available configurations: {list(EXPERIMENT_CONFIGS.keys())}")
        raise ValueError(f"Unknown configuration: {config_name}")
    
    return EXPERIMENT_CONFIGS[config_name].copy()

def list_configs():
    """List all available configurations."""
    print("Available experiment configurations:")
    for name, config in EXPERIMENT_CONFIGS.items():
        strategy = config["strategy_params"]
        print(f"  {name}:")
        print(f"    Steps per save: {config['steps_per_save']}")
        print(f"    Max steps: {config['max_steps']}")
        print(f"    Tolerance: {strategy['initial_tolerance']:.0%} → {strategy['final_tolerance']:.0%}")
        print(f"    Strictness start: {strategy['strictness_start']:.0%}")
        print()
