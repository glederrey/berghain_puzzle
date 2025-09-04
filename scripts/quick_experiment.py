#!/usr/bin/env python3
"""
Quick Berghain Puzzle Experiment

A simplified script for running quick experiments with default settings.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from berghain import BerghainAPI, GameRunner, BerghainVisualizer
from berghain.strategies import Scenario1Strategy
from dotenv import load_dotenv


def run_quick_experiment(scenario=1, total_steps=10000, save_interval=100):
    """Run a quick experiment with default settings.
    
    Args:
        scenario: Scenario number (1, 2, or 3)
        total_steps: Total number of steps to run
        save_interval: Steps between saves
    """
    # Load environment
    load_dotenv()
    
    # Setup components
    print("🔧 Setting up experiment...")
    api = BerghainAPI()
    strategy = Scenario1Strategy()
    visualizer = BerghainVisualizer()
    runner = GameRunner(api, strategy)
    
    print(f"✅ Components ready - {strategy.get_name()}")
    
    # Start game
    print(f"\n🎮 Starting scenario {scenario}...")
    game_state = runner.start_game(scenario)
    game_id = game_state.game_id
    
    print(f"🎯 Game ID: {game_id}")
    runner.display_constraints_only()
    
    # Create output directory
    output_dir = Path("quick_experiment_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Run experiment in chunks
    steps_completed = 0
    save_count = 0
    
    print(f"\n🚀 Running {total_steps} steps in chunks of {save_interval}...")
    
    try:
        while steps_completed < total_steps and not runner.game_completed:
            # Run next chunk
            chunk_size = min(save_interval, total_steps - steps_completed)
            print(f"\n📊 Running steps {steps_completed + 1} to {steps_completed + chunk_size}...")
            
            step_records = runner.step(chunk_size, show_progress=False)
            steps_completed += len(step_records)
            
            # Show progress
            summary = runner.get_game_summary()
            print(f"   Admitted: {summary['admitted_count']}, Rejected: {summary['rejected_count']}")
            
            # Save dashboard
            dashboard = visualizer.create_live_dashboard(runner)
            filename = f"{game_id}_{steps_completed:04d}steps.html"
            filepath = output_dir / filename
            dashboard.write_html(str(filepath))
            print(f"💾 Saved: {filename}")
            save_count += 1
            
            if runner.game_completed:
                print("🏁 Game completed!")
                break
    
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    
    # Final summary
    summary = runner.get_game_summary()
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Steps: {steps_completed}")
    print(f"   Admitted: {summary['admitted_count']}/1000")
    print(f"   Rejected: {summary['rejected_count']}")
    print(f"   Success: {summary['success']}")
    print(f"   Files saved: {save_count}")
    print(f"   Output directory: {output_dir}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick Berghain experiment")
    parser.add_argument("--scenario", type=int, default=1, choices=[1, 2, 3])
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--interval", type=int, default=100)
    
    args = parser.parse_args()
    
    print("🧪 Quick Berghain Experiment")
    print("=" * 40)
    
    run_quick_experiment(args.scenario, args.steps, args.interval)
