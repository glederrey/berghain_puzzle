"""Utility functions for the Berghain puzzle."""

from typing import Dict, List, Any
import json
import os
from datetime import datetime


def save_results(results: Dict[str, Any], filename: str = None) -> str:
    """Save game results to a JSON file.
    
    Args:
        results: Results dictionary from GameRunner
        filename: Optional filename, if not provided will use timestamp
        
    Returns:
        Path to saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_name = results.get('strategy', 'unknown').replace(' ', '_')
        scenario = results.get('scenario', 'unknown')
        filename = f"results_{strategy_name}_scenario{scenario}_{timestamp}.json"
    
    # Create results directory if it doesn't exist
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    filepath = os.path.join(results_dir, filename)
    
    # Convert any non-serializable objects to strings
    serializable_results = make_serializable(results)
    
    with open(filepath, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    return filepath


def load_results(filepath: str) -> Dict[str, Any]:
    """Load game results from a JSON file.
    
    Args:
        filepath: Path to the results file
        
    Returns:
        Results dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def make_serializable(obj: Any) -> Any:
    """Convert objects to JSON-serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        Serializable version of the object
    """
    if hasattr(obj, '__dict__'):
        # Convert dataclass or custom objects to dict
        return {k: make_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    else:
        # Convert other types to string
        return str(obj)


def calculate_strategy_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate performance metrics for a strategy.
    
    Args:
        results: Results from GameRunner.run_game()
        
    Returns:
        Dictionary of performance metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics['rejected_count'] = results['rejected_count']
    metrics['admitted_count'] = results['admitted_count']
    metrics['success'] = 1.0 if results['success'] else 0.0
    metrics['completion_rate'] = results['admitted_count'] / 1000.0
    
    # Efficiency metrics
    total_seen = results['admitted_count'] + results['rejected_count']
    if total_seen > 0:
        metrics['acceptance_rate'] = results['admitted_count'] / total_seen
        metrics['rejection_rate'] = results['rejected_count'] / total_seen
    else:
        metrics['acceptance_rate'] = 0.0
        metrics['rejection_rate'] = 0.0
    
    # Constraint satisfaction metrics
    constraints = results.get('constraints', [])
    if constraints:
        current_stats = results['current_stats']
        attribute_counts = current_stats['attribute_counts']
        
        constraint_scores = []
        for constraint in constraints:
            attr = constraint.attribute
            required = constraint.min_count
            actual = attribute_counts.get(attr, 0)
            score = min(actual / required, 1.0) if required > 0 else 1.0
            constraint_scores.append(score)
        
        metrics['avg_constraint_satisfaction'] = sum(constraint_scores) / len(constraint_scores)
        metrics['min_constraint_satisfaction'] = min(constraint_scores)
        metrics['constraints_met'] = sum(1 for score in constraint_scores if score >= 1.0)
        metrics['total_constraints'] = len(constraints)
    
    return metrics


def compare_strategies(results_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare multiple strategy results.
    
    Args:
        results_list: List of results from different strategies
        
    Returns:
        Comparison analysis
    """
    if not results_list:
        return {}
    
    comparison = {
        'strategies': [],
        'metrics': {},
        'rankings': {},
        'best_strategy': None
    }
    
    # Calculate metrics for each strategy
    all_metrics = []
    for results in results_list:
        strategy_name = results['strategy']
        metrics = calculate_strategy_metrics(results)
        metrics['strategy'] = strategy_name
        all_metrics.append(metrics)
        comparison['strategies'].append(strategy_name)
    
    # Aggregate metrics
    metric_names = [k for k in all_metrics[0].keys() if k != 'strategy']
    for metric in metric_names:
        values = [m[metric] for m in all_metrics]
        comparison['metrics'][metric] = {
            'values': values,
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'strategies': comparison['strategies']
        }
    
    # Rankings (lower is better for rejected_count, higher is better for others)
    for metric in metric_names:
        if metric == 'rejected_count':
            # Lower is better
            sorted_metrics = sorted(all_metrics, key=lambda x: x[metric])
        else:
            # Higher is better (assuming all other metrics)
            sorted_metrics = sorted(all_metrics, key=lambda x: x[metric], reverse=True)
        
        comparison['rankings'][metric] = [m['strategy'] for m in sorted_metrics]
    
    # Determine best overall strategy (lowest rejected count among successful strategies)
    successful_strategies = [m for m in all_metrics if m['success'] > 0.5]
    if successful_strategies:
        best = min(successful_strategies, key=lambda x: x['rejected_count'])
        comparison['best_strategy'] = best['strategy']
    else:
        # If no successful strategies, pick the one with highest completion rate
        best = max(all_metrics, key=lambda x: x['completion_rate'])
        comparison['best_strategy'] = best['strategy']
    
    return comparison


def print_strategy_comparison(comparison: Dict[str, Any]) -> None:
    """Print a formatted comparison of strategies.
    
    Args:
        comparison: Output from compare_strategies()
    """
    print("🏆 Strategy Comparison Summary")
    print("=" * 50)
    
    if comparison.get('best_strategy'):
        print(f"Best Strategy: {comparison['best_strategy']}")
        print()
    
    # Print key metrics
    key_metrics = ['rejected_count', 'success', 'completion_rate', 'acceptance_rate']
    
    for metric in key_metrics:
        if metric in comparison['metrics']:
            data = comparison['metrics'][metric]
            print(f"{metric.replace('_', ' ').title()}:")
            for strategy, value in zip(data['strategies'], data['values']):
                if metric == 'success':
                    status = "✅" if value > 0.5 else "❌"
                    print(f"  {status} {strategy}: {value}")
                else:
                    print(f"  {strategy}: {value:.3f}")
            print()
    
    # Print rankings
    print("Rankings (best to worst):")
    for metric in ['rejected_count', 'success', 'completion_rate']:
        if metric in comparison['rankings']:
            print(f"  {metric.replace('_', ' ').title()}: {' > '.join(comparison['rankings'][metric])}")
    print()
