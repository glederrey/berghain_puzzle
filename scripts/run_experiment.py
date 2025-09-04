#!/usr/bin/env python3
"""
Berghain Puzzle Experiment Runner

This script replicates the notebook experiment but runs automatically and saves
dashboard visualizations at regular intervals with the game_id as filename.
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from berghain import BerghainAPI, GameRunner, BerghainVisualizer
from berghain.strategies import Scenario1Strategy
from dotenv import load_dotenv
import plotly.io as pio


class ExperimentRunner:
    """Automated experiment runner for the Berghain puzzle."""
    
    def __init__(self, scenario=1, steps_per_save=100, max_steps=2000, 
                 output_dir="experiment_outputs", strategy_params=None):
        """Initialize the experiment runner.
        
        Args:
            scenario: Scenario number (1, 2, or 3)
            steps_per_save: Number of steps between dashboard saves
            max_steps: Maximum number of steps to run
            output_dir: Directory to save outputs
            strategy_params: Dictionary of strategy parameters
        """
        self.scenario = scenario
        self.steps_per_save = steps_per_save
        self.max_steps = max_steps
        self.output_dir = Path(output_dir)
        self.strategy_params = strategy_params or {}
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self._setup_components()
    
    def _setup_components(self):
        """Set up API client, strategy, and visualizer."""
        print("🔧 Setting up experiment components...")
        
        # Initialize API client
        try:
            self.api = BerghainAPI()
            print(f"✅ API client initialized with Player ID: {self.api.player_id}")
        except Exception as e:
            print(f"❌ API client initialization failed: {e}")
            raise
        
        # Initialize strategy
        self.strategy = Scenario1Strategy(**self.strategy_params)
        print(f"✅ Strategy created: {self.strategy.get_name()}")
        
        # Initialize visualizer
        self.visualizer = BerghainVisualizer()
        print("✅ Visualizer initialized")
        
        # Initialize game runner
        self.runner = GameRunner(self.api, self.strategy)
        print("✅ Game runner initialized")
    
    def start_experiment(self):
        """Start the experiment and display initial information."""
        print(f"\n🎮 Starting experiment - Scenario {self.scenario}")
        print("=" * 60)
        
        # Start the game
        try:
            game_state = self.runner.start_game(self.scenario)
            self.game_id = game_state.game_id
            print(f"✅ Game started successfully!")
            print(f"🎯 Game ID: {self.game_id}")
            
            # Display constraints
            print("\n📋 CONSTRAINTS:")
            self.runner.display_constraints_only()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting game: {e}")
            return False
    
    def save_dashboard(self, step_count):
        """Save the current dashboard to file.
        
        Args:
            step_count: Current step count for filename
        """
        try:
            # Create dashboard
            dashboard = self.visualizer.create_live_dashboard(self.runner)
            
            # Create filename
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.game_id}_{step_count:04d}steps_{timestamp}.html"
            filepath = self.output_dir / filename
            
            # Save dashboard
            dashboard.write_html(str(filepath))
            print(f"💾 Dashboard saved: {filename}")
            
            # Also save constraint percentage chart separately
            constraint_fig = self.visualizer.plot_constraint_percentages_over_time(self.runner)
            constraint_filename = f"{self.game_id}_{step_count:04d}steps_constraints_{timestamp}.html"
            constraint_filepath = self.output_dir / constraint_filename
            constraint_fig.write_html(str(constraint_filepath))
            print(f"📊 Constraint chart saved: {constraint_filename}")
            
        except Exception as e:
            print(f"❌ Error saving dashboard: {e}")
    
    def run_experiment(self):
        """Run the complete experiment."""
        if not self.start_experiment():
            return False
        
        print(f"\n🚀 Running experiment...")
        print(f"📈 Will save dashboards every {self.steps_per_save} steps")
        print(f"🎯 Maximum steps: {self.max_steps}")
        print("=" * 60)
        
        total_steps = 0
        save_count = 0
        
        # Save initial state
        self.save_dashboard(0)
        save_count += 1
        
        try:
            while total_steps < self.max_steps and not self.runner.game_completed:
                # Calculate steps to run (either steps_per_save or remaining)
                remaining_steps = self.max_steps - total_steps
                steps_to_run = min(self.steps_per_save, remaining_steps)
                
                print(f"\n📊 Running steps {total_steps + 1} to {total_steps + steps_to_run}...")
                
                # Run steps with reduced verbosity
                step_records = self.runner.step(steps_to_run, show_progress=False)
                total_steps += len(step_records)
                
                # Display progress summary
                game_summary = self.runner.get_game_summary()
                print(f"   Steps completed: {len(step_records)}")
                print(f"   Total admitted: {game_summary['admitted_count']}")
                print(f"   Total rejected: {game_summary['rejected_count']}")
                print(f"   Game status: {game_summary['status']}")
                
                # Check constraint progress
                for constraint in game_summary['constraints']:
                    attr = constraint['attribute']
                    actual = constraint['actual']
                    required = constraint['required']
                    percentage = (actual / required * 100) if required > 0 else 100
                    status = "✅" if constraint['satisfied'] else "⚠️"
                    print(f"   {status} {attr}: {actual}/{required} ({percentage:.1f}%)")
                
                # Save dashboard
                self.save_dashboard(total_steps)
                save_count += 1
                
                # Check if game is complete
                if self.runner.game_completed:
                    print(f"\n🏁 Game completed after {total_steps} steps!")
                    break
            
            # Final summary
            self._print_final_summary(total_steps, save_count)
            return True
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Experiment interrupted by user after {total_steps} steps")
            self._print_final_summary(total_steps, save_count)
            return False
        except Exception as e:
            print(f"\n❌ Error during experiment: {e}")
            return False
    
    def _print_final_summary(self, total_steps, save_count):
        """Print final experiment summary."""
        print("\n" + "=" * 60)
        print("📊 EXPERIMENT SUMMARY")
        print("=" * 60)
        
        game_summary = self.runner.get_game_summary()
        
        print(f"🎮 Game ID: {self.game_id}")
        print(f"🎯 Strategy: {game_summary['strategy']}")
        print(f"📈 Total steps: {total_steps}")
        print(f"✅ Admitted: {game_summary['admitted_count']}/1000")
        print(f"❌ Rejected: {game_summary['rejected_count']}")
        print(f"🎯 Success: {game_summary['success']}")
        print(f"💾 Dashboards saved: {save_count}")
        print(f"📁 Output directory: {self.output_dir}")
        
        print(f"\n🎯 Final Constraint Status:")
        for constraint in game_summary['constraints']:
            attr = constraint['attribute']
            actual = constraint['actual']
            required = constraint['required']
            percentage = (actual / required * 100) if required > 0 else 100
            status = "✅" if constraint['satisfied'] else "❌"
            print(f"  {status} {attr}: {actual}/{required} ({percentage:.1f}%)")
        
        # List saved files
        print(f"\n📄 Files saved:")
        for file in sorted(self.output_dir.glob(f"{self.game_id}*")):
            print(f"  - {file.name}")


def main():
    """Main function to run the experiment."""
    parser = argparse.ArgumentParser(description="Run Berghain puzzle experiment")
    parser.add_argument("--scenario", type=int, default=1, choices=[1, 2, 3],
                       help="Scenario number (1, 2, or 3)")
    parser.add_argument("--steps-per-save", type=int, default=100,
                       help="Number of steps between dashboard saves")
    parser.add_argument("--max-steps", type=int, default=2000,
                       help="Maximum number of steps to run")
    parser.add_argument("--output-dir", type=str, default="experiment_outputs",
                       help="Directory to save outputs")
    
    # Strategy parameters
    parser.add_argument("--initial-tolerance", type=float, default=0.20,
                       help="Initial tolerance for strategy")
    parser.add_argument("--final-tolerance", type=float, default=0.02,
                       help="Final tolerance for strategy")
    parser.add_argument("--strictness-start", type=float, default=0.10,
                       help="When to start reducing tolerance")
    
    args = parser.parse_args()
    
    # Prepare strategy parameters
    strategy_params = {
        'initial_tolerance': args.initial_tolerance,
        'final_tolerance': args.final_tolerance,
        'strictness_start': args.strictness_start
    }
    
    print("🧪 Berghain Puzzle Experiment Runner")
    print("=" * 60)
    print(f"📋 Configuration:")
    print(f"   Scenario: {args.scenario}")
    print(f"   Steps per save: {args.steps_per_save}")
    print(f"   Max steps: {args.max_steps}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Strategy params: {strategy_params}")
    
    # Create and run experiment
    try:
        experiment = ExperimentRunner(
            scenario=args.scenario,
            steps_per_save=args.steps_per_save,
            max_steps=args.max_steps,
            output_dir=args.output_dir,
            strategy_params=strategy_params
        )
        
        success = experiment.run_experiment()
        
        if success:
            print("\n🎉 Experiment completed successfully!")
            return 0
        else:
            print("\n⚠️  Experiment completed with issues")
            return 1
            
    except Exception as e:
        print(f"\n💥 Experiment failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
