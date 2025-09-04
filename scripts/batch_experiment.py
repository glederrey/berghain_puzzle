#!/usr/bin/env python3
"""
Batch Experiment Runner

Run multiple experiments with different configurations and compare results.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import concurrent.futures
import threading
from typing import List, Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from berghain import BerghainAPI, GameRunner, BerghainVisualizer
from berghain.strategies import Scenario1Strategy
from dotenv import load_dotenv
from experiment_config import get_config, list_configs


class BatchExperimentRunner:
    """Run multiple experiments and compare results."""
    
    def __init__(self, output_dir="batch_experiments", max_workers=None, override_dashboards=True):
        """Initialize batch runner.
        
        Args:
            output_dir: Directory to save all outputs
            max_workers: Maximum number of parallel workers (None = auto)
            override_dashboards: Whether to overwrite existing dashboard files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        self.override_dashboards = override_dashboards
        
        # Load environment
        load_dotenv()
        
        # Results storage (thread-safe)
        self.results = []
        self.results_lock = threading.Lock()
    
    def run_single_experiment(self, scenario, config_name, experiment_id):
        """Run a single experiment with given configuration.
        
        Args:
            scenario: Scenario number
            config_name: Configuration name
            experiment_id: Unique experiment identifier
            
        Returns:
            Dictionary with experiment results
        """
        # Thread-safe printing
        with self.results_lock:
            print(f"\n🧪 Starting experiment {experiment_id}")
            print(f"   Scenario: {scenario}")
            print(f"   Config: {config_name}")
            print("-" * 40)
        
        # Get configuration
        config = get_config(config_name)
        
        # Create strategy (each thread needs its own instances)
        strategy = Scenario1Strategy(**config["strategy_params"])
        
        # Create API client and visualizer for this thread
        api = BerghainAPI()
        visualizer = BerghainVisualizer()
        
        # Create game runner
        runner = GameRunner(api, strategy)
        
        try:
            # Start game
            game_state = runner.start_game(scenario)
            game_id = game_state.game_id
            
            with self.results_lock:
                print(f"🎯 Game ID: {game_id}")
            
            # Create experiment-specific output directory
            exp_dir = self.output_dir / f"{experiment_id}_{game_id}"
            exp_dir.mkdir(exist_ok=True)
            
            # Run experiment
            total_steps = 0
            save_count = 0
            dashboard_filename = f"{game_id}_dashboard.html"  # Override same file
            
            while total_steps < config["max_steps"] and not runner.game_completed:
                # Run steps
                steps_to_run = min(config["steps_per_save"], 
                                 config["max_steps"] - total_steps)
                
                step_records = runner.step(steps_to_run, show_progress=False)
                total_steps += len(step_records)
                
                # Save dashboard (override previous)
                if self.override_dashboards:
                    dashboard = visualizer.create_live_dashboard(runner)
                    dashboard.write_html(str(exp_dir / dashboard_filename))
                
                else:
                    # Traditional separate files
                    dashboard = visualizer.create_live_dashboard(runner)
                    filename = f"dashboard_{total_steps:04d}.html"
                    dashboard.write_html(str(exp_dir / filename))
                
                save_count += 1
                
                with self.results_lock:
                    print(f"   {experiment_id}: Steps {total_steps}, "
                          f"Admitted: {runner.get_game_summary()['admitted_count']}")
                
                if runner.game_completed:
                    break
            
            # Get final results
            summary = runner.get_game_summary()
            
            # Save final dashboard
            final_dashboard = visualizer.create_live_dashboard(runner)
            if self.override_dashboards:
                # Overwrite the main dashboard file with final state
                final_dashboard.write_html(str(exp_dir / dashboard_filename))
            else:
                final_dashboard.write_html(str(exp_dir / "final_dashboard.html"))
            
            # Create result record
            result = {
                "experiment_id": experiment_id,
                "scenario": scenario,
                "config_name": config_name,
                "game_id": game_id,
                "strategy_name": summary["strategy"],
                "total_steps": total_steps,
                "admitted_count": summary["admitted_count"],
                "rejected_count": summary["rejected_count"],
                "success": summary["success"],
                "constraints": summary["constraints"],
                "config": config,
                "output_dir": str(exp_dir),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save experiment metadata
            with open(exp_dir / "experiment_metadata.json", "w") as f:
                json.dump(result, f, indent=2)
            
            with self.results_lock:
                print(f"✅ Experiment {experiment_id} completed")
                print(f"   Result: {'SUCCESS' if result['success'] else 'FAILED'}")
                print(f"   Admitted: {result['admitted_count']}/1000")
                print(f"   Rejected: {result['rejected_count']}")
            
            return result
            
        except Exception as e:
            with self.results_lock:
                print(f"❌ Experiment {experiment_id} failed: {e}")
            return {
                "experiment_id": experiment_id,
                "scenario": scenario,
                "config_name": config_name,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def run_batch(self, scenarios, configs):
        """Run batch of experiments in parallel.
        
        Args:
            scenarios: List of scenario numbers
            configs: List of configuration names
        """
        print("🚀 Starting batch experiments (parallel execution)")
        print("=" * 60)
        
        # Prepare experiment parameters
        experiments = []
        experiment_count = 0
        
        for scenario in scenarios:
            for config_name in configs:
                experiment_count += 1
                experiment_id = f"exp_{experiment_count:03d}_{config_name}_s{scenario}"
                experiments.append((scenario, config_name, experiment_id))
        
        print(f"📊 Total experiments: {len(experiments)}")
        print(f"🔧 Max workers: {self.max_workers or 'auto'}")
        print(f"📁 Override dashboards: {self.override_dashboards}")
        print("=" * 60)
        
        # Run experiments in parallel
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all experiments
            future_to_exp = {
                executor.submit(self.run_single_experiment, scenario, config_name, experiment_id): 
                (scenario, config_name, experiment_id)
                for scenario, config_name, experiment_id in experiments
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_exp):
                scenario, config_name, experiment_id = future_to_exp[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.results_lock:
                        print(f"🎯 Completed {len(results)}/{len(experiments)} experiments")
                        
                except Exception as exc:
                    with self.results_lock:
                        print(f"❌ Experiment {experiment_id} generated an exception: {exc}")
                    results.append({
                        "experiment_id": experiment_id,
                        "scenario": scenario,
                        "config_name": config_name,
                        "error": str(exc),
                        "success": False,
                        "timestamp": datetime.now().isoformat()
                    })
        
        # Store results
        self.results = results
        
        # Save batch results
        self._save_batch_results()
        self._print_batch_summary()
    
    def _save_batch_results(self):
        """Save batch results to file."""
        results_file = self.output_dir / "batch_results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"💾 Batch results saved to: {results_file}")
    
    def _print_batch_summary(self):
        """Print summary of batch results."""
        print("\n" + "=" * 60)
        print("📊 BATCH EXPERIMENT SUMMARY")
        print("=" * 60)
        
        successful = [r for r in self.results if r.get("success", False)]
        failed = [r for r in self.results if not r.get("success", False)]
        
        print(f"Total experiments: {len(self.results)}")
        print(f"Successful: {len(successful)}")
        print(f"Failed: {len(failed)}")
        print()
        
        if successful:
            print("🏆 SUCCESSFUL EXPERIMENTS:")
            for result in successful:
                print(f"  {result['experiment_id']}: "
                      f"{result['admitted_count']}/1000 admitted, "
                      f"{result['rejected_count']} rejected")
        
        if failed:
            print("\n❌ FAILED EXPERIMENTS:")
            for result in failed:
                error = result.get("error", "Unknown error")
                print(f"  {result['experiment_id']}: {error}")
        
        print(f"\n📁 All outputs saved to: {self.output_dir}")


def main():
    """Main function for batch experiments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run batch experiments in parallel")
    parser.add_argument("--scenarios", nargs="+", type=int, default=[1],
                       choices=[1, 2, 3], help="Scenarios to test")
    parser.add_argument("--configs", nargs="+", type=str, 
                       default=["standard"],
                       help="Configurations to test")
    parser.add_argument("--list-configs", action="store_true",
                       help="List available configurations")
    parser.add_argument("--output-dir", type=str, default="batch_experiments",
                       help="Output directory")
    parser.add_argument("--max-workers", type=int, default=None,
                       help="Maximum number of parallel workers (default: auto)")
    parser.add_argument("--no-override", action="store_true",
                       help="Don't override dashboard files (save all versions)")
    
    args = parser.parse_args()
    
    if args.list_configs:
        list_configs()
        return
    
    print("🧪 Parallel Batch Berghain Experiments")
    print("=" * 50)
    print(f"Scenarios: {args.scenarios}")
    print(f"Configurations: {args.configs}")
    print(f"Output directory: {args.output_dir}")
    print(f"Max workers: {args.max_workers or 'auto'}")
    print(f"Override dashboards: {not args.no_override}")
    
    # Create and run batch
    batch_runner = BatchExperimentRunner(
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        override_dashboards=not args.no_override
    )
    batch_runner.run_batch(args.scenarios, args.configs)


if __name__ == "__main__":
    main()
