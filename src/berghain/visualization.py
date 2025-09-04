"""Visualization utilities for the Berghain puzzle."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
import numpy as np


class BerghainVisualizer:
    """Visualization utilities for analyzing game results."""
    
    def __init__(self):
        """Initialize the visualizer."""
        pass
    
    def plot_live_progress(self, game_runner) -> go.Figure:
        """Plot live progress from a GameRunner.
        
        Args:
            game_runner: GameRunner instance
            
        Returns:
            Plotly figure showing current progress
        """
        people_history = game_runner.get_people_seen()
        
        if not people_history:
            return go.Figure().add_annotation(text="No game progress yet")
        
        # Create progress data
        person_indices = [record.person_index for record in people_history]
        admits = [record.admitted_count_after for record in people_history]
        rejects = [record.rejected_count_after for record in people_history]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=person_indices,
            y=admits,
            mode='lines+markers',
            name='Admitted',
            line=dict(color='green', width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=person_indices,
            y=rejects,
            mode='lines+markers',
            name='Rejected',
            line=dict(color='red', width=3),
            marker=dict(size=6)
        ))
        
        # Add target line
        fig.add_hline(y=1000, line_dash="dash", line_color="blue", 
                     annotation_text="Target (1000)")
        
        # Add constraint progress if available
        game_summary = game_runner.get_game_summary()
        if game_summary.get('constraints'):
            for constraint in game_summary['constraints']:
                required = constraint['required']
                fig.add_hline(y=required, line_dash="dot", line_color="orange",
                             annotation_text=f"{constraint['attribute']}: {required}")
        
        fig.update_layout(
            title=f"Live Game Progress - {game_runner.strategy.get_name()}",
            xaxis_title="Person Index",
            yaxis_title="Count",
            hovermode='x unified',
            height=500
        )
        
        return fig
    
    def plot_live_constraints(self, game_runner) -> go.Figure:
        """Plot live constraint satisfaction progress.
        
        Args:
            game_runner: GameRunner instance
            
        Returns:
            Plotly figure showing constraint progress
        """
        game_summary = game_runner.get_game_summary()
        constraints = game_summary.get('constraints', [])
        
        if not constraints:
            return go.Figure().add_annotation(text="No constraints in this scenario")
        
        constraint_names = []
        current_counts = []
        required_counts = []
        percentages = []
        colors = []
        
        for constraint in constraints:
            constraint_names.append(constraint['attribute'])
            current_counts.append(constraint['actual'])
            required_counts.append(constraint['required'])
            
            percentage = (constraint['actual'] / constraint['required'] * 100) if constraint['required'] > 0 else 100
            percentages.append(percentage)
            
            # Color based on satisfaction
            if constraint['satisfied']:
                colors.append('green')
            elif percentage >= 80:
                colors.append('orange')
            else:
                colors.append('red')
        
        fig = go.Figure()
        
        # Current progress bars
        fig.add_trace(go.Bar(
            x=constraint_names,
            y=current_counts,
            name='Current Count',
            marker_color=colors,
            text=[f"{p:.1f}%" for p in percentages],
            textposition='outside'
        ))
        
        # Required target bars (outline)
        fig.add_trace(go.Bar(
            x=constraint_names,
            y=required_counts,
            name='Required Count',
            marker=dict(color='rgba(0,0,0,0)', line=dict(color='black', width=2)),
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Live Constraint Progress",
            xaxis_title="Constraint Attributes",
            yaxis_title="Count",
            barmode='overlay',
            height=400
        )
        
        return fig
    
    def plot_constraint_percentages_over_time(self, game_runner) -> go.Figure:
        """Plot constraint percentages among accepted people over time.
        
        Args:
            game_runner: GameRunner instance
            
        Returns:
            Plotly figure showing constraint percentages over time
        """
        people_history = game_runner.get_people_seen()
        
        if not people_history:
            return go.Figure().add_annotation(text="No game progress yet")
        
        # Get constraint information
        game_summary = game_runner.get_game_summary()
        constraints = game_summary.get('constraints', [])
        
        if not constraints:
            return go.Figure().add_annotation(text="No constraints in this scenario")
        
        # Calculate cumulative constraint percentages over time
        admitted_people = [record for record in people_history if record.decision]
        
        if not admitted_people:
            return go.Figure().add_annotation(text="No people admitted yet")
        
        # Track percentages over time for each constraint
        constraint_data = {}
        person_indices = []
        
        for constraint in constraints:
            constraint_data[constraint['attribute']] = {
                'percentages': [],
                'target': constraint['required'] / 1000.0 * 100  # Target percentage
            }
        
        # Calculate running percentages
        running_counts = {constraint['attribute']: 0 for constraint in constraints}
        
        for i, person in enumerate(admitted_people):
            # Update counts
            for attr in running_counts:
                if person.attributes.get(attr, False):
                    running_counts[attr] += 1
            
            # Calculate percentages
            total_admitted = i + 1
            for attr in running_counts:
                percentage = (running_counts[attr] / total_admitted) * 100
                constraint_data[attr]['percentages'].append(percentage)
            
            person_indices.append(person.person_index)
        
        # Create the plot
        fig = go.Figure()
        
        # Define colors for different constraints
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink']
        
        for i, (attr, data) in enumerate(constraint_data.items()):
            color = colors[i % len(colors)]
            
            # Add the percentage line
            fig.add_trace(go.Scatter(
                x=person_indices,
                y=data['percentages'],
                mode='lines+markers',
                name=f'{attr} %',
                line=dict(color=color, width=3),
                marker=dict(size=4)
            ))
            
            # Add target line
            fig.add_hline(
                y=data['target'],
                line_dash="dash",
                line_color=color,
                annotation_text=f"{attr} target ({data['target']:.0f}%)",
                annotation_position="top right"
            )
        
        # Add overall layout
        fig.update_layout(
            title="Constraint Percentages Among Accepted People Over Time",
            xaxis_title="Person Index",
            yaxis_title="Percentage (%)",
            hovermode='x unified',
            height=500,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def plot_game_progress(self, results: Dict[str, Any]) -> go.Figure:
        """Plot the progress of admits/rejects over time.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure
        """
        history = results['history']
        if not history:
            return go.Figure().add_annotation(text="No game history available")
        
        # Create cumulative counts
        admits = []
        rejects = []
        person_indices = []
        
        for record in history:
            person_indices.append(record['person_index'])
            admits.append(record['admitted_count'] + (1 if record['decision'] else 0))
            rejects.append(record['rejected_count'] + (0 if record['decision'] else 1))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=person_indices,
            y=admits,
            mode='lines',
            name='Admitted',
            line=dict(color='green')
        ))
        
        fig.add_trace(go.Scatter(
            x=person_indices,
            y=rejects,
            mode='lines',
            name='Rejected',
            line=dict(color='red')
        ))
        
        # Add target line
        fig.add_hline(y=1000, line_dash="dash", line_color="blue", 
                     annotation_text="Target (1000)")
        
        fig.update_layout(
            title=f"Game Progress - {results['strategy']} (Scenario {results['scenario']})",
            xaxis_title="Person Index",
            yaxis_title="Count",
            hovermode='x unified'
        )
        
        return fig
    
    def plot_attribute_distribution(self, results: Dict[str, Any]) -> go.Figure:
        """Plot the distribution of attributes in admitted vs rejected people.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure
        """
        current_stats = results['current_stats']
        admitted = current_stats['admitted_people']
        rejected = current_stats['rejected_people']
        
        if not admitted and not rejected:
            return go.Figure().add_annotation(text="No people data available")
        
        # Get all unique attributes
        all_attributes = set()
        for person in admitted + rejected:
            all_attributes.update(person.keys())
        
        all_attributes = sorted(list(all_attributes))
        
        # Calculate percentages
        admitted_counts = {}
        rejected_counts = {}
        
        for attr in all_attributes:
            admitted_counts[attr] = sum(1 for p in admitted if p.get(attr, False))
            rejected_counts[attr] = sum(1 for p in rejected if p.get(attr, False))
        
        admitted_pcts = {attr: (count / len(admitted) * 100) if admitted else 0 
                        for attr, count in admitted_counts.items()}
        rejected_pcts = {attr: (count / len(rejected) * 100) if rejected else 0 
                        for attr, count in rejected_counts.items()}
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=all_attributes,
            y=[admitted_pcts[attr] for attr in all_attributes],
            name='Admitted',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=all_attributes,
            y=[rejected_pcts[attr] for attr in all_attributes],
            name='Rejected',
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Attribute Distribution: Admitted vs Rejected",
            xaxis_title="Attributes",
            yaxis_title="Percentage (%)",
            barmode='group'
        )
        
        return fig
    
    def plot_constraint_progress(self, results: Dict[str, Any]) -> go.Figure:
        """Plot progress towards meeting constraints.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure
        """
        constraints = results['constraints']
        if not constraints:
            return go.Figure().add_annotation(text="No constraints in this scenario")
        
        current_stats = results['current_stats']
        attribute_counts = current_stats['attribute_counts']
        
        constraint_names = []
        current_counts = []
        required_counts = []
        percentages = []
        
        for constraint in constraints:
            attr = constraint.attribute
            required = constraint.min_count
            current = attribute_counts.get(attr, 0)
            
            constraint_names.append(attr)
            current_counts.append(current)
            required_counts.append(required)
            percentages.append((current / required * 100) if required > 0 else 100)
        
        fig = go.Figure()
        
        # Current progress bars
        fig.add_trace(go.Bar(
            x=constraint_names,
            y=current_counts,
            name='Current Count',
            marker_color='lightblue'
        ))
        
        # Required target bars
        fig.add_trace(go.Bar(
            x=constraint_names,
            y=required_counts,
            name='Required Count',
            marker_color='navy',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Constraint Progress",
            xaxis_title="Constraint Attributes",
            yaxis_title="Count",
            barmode='overlay'
        )
        
        return fig
    
    def plot_decision_timeline(self, results: Dict[str, Any]) -> go.Figure:
        """Plot accept/reject decisions over time.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure
        """
        history = results['history']
        if not history:
            return go.Figure().add_annotation(text="No game history available")
        
        # Create timeline data
        person_indices = [r['person_index'] for r in history]
        decisions = [1 if r['decision'] else 0 for r in history]
        
        # Create color mapping
        colors = ['red' if d == 0 else 'green' for d in decisions]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=person_indices,
            y=decisions,
            mode='markers',
            marker=dict(
                color=colors,
                size=8,
                line=dict(width=1, color='black')
            ),
            name='Decisions',
            hovertemplate='Person %{x}<br>Decision: %{customdata}<extra></extra>',
            customdata=['Accepted' if d else 'Rejected' for d in decisions]
        ))
        
        fig.update_layout(
            title="Decision Timeline",
            xaxis_title="Person Index",
            yaxis_title="Decision (0=Reject, 1=Accept)",
            yaxis=dict(tickvals=[0, 1], ticktext=['Reject', 'Accept']),
            height=400
        )
        
        return fig
    
    def plot_attribute_correlations(self, results: Dict[str, Any]) -> go.Figure:
        """Plot correlation matrix of attributes.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure
        """
        attr_stats = results['attribute_statistics']
        correlations = attr_stats.correlations
        
        if not correlations:
            return go.Figure().add_annotation(text="No correlation data available")
        
        # Create correlation matrix
        attributes = list(correlations.keys())
        matrix = []
        
        for attr1 in attributes:
            row = []
            for attr2 in attributes:
                corr = correlations.get(attr1, {}).get(attr2, 0)
                row.append(corr)
            matrix.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=attributes,
            y=attributes,
            colorscale='RdBu',
            zmid=0,
            text=np.round(matrix, 2),
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Attribute Correlations",
            xaxis_title="Attributes",
            yaxis_title="Attributes"
        )
        
        return fig
    
    def create_live_dashboard(self, game_runner) -> go.Figure:
        """Create a comprehensive live dashboard for GameRunner.
        
        Args:
            game_runner: GameRunner instance
            
        Returns:
            Plotly figure with subplots showing live game state
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Game Progress (Admitted vs Rejected)",
                "Constraint Percentages Over Time", 
                "Current Constraint Status",
                "Decision Timeline"
            ],
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}]
            ]
        )
        
        # 1. Game Progress (top left)
        progress_fig = self.plot_live_progress(game_runner)
        for trace in progress_fig.data:
            trace.showlegend = False  # Avoid duplicate legends
            fig.add_trace(trace, row=1, col=1)
        
        # 2. Constraint Percentages Over Time (top right)
        constraint_pct_fig = self.plot_constraint_percentages_over_time(game_runner)
        for trace in constraint_pct_fig.data:
            trace.showlegend = True
            fig.add_trace(trace, row=1, col=2)
        
        # 3. Current Constraint Status (bottom left)
        constraint_status_fig = self.plot_live_constraints(game_runner)
        for trace in constraint_status_fig.data:
            trace.showlegend = False
            fig.add_trace(trace, row=2, col=1)
        
        # 4. Recent Decision Timeline (bottom right)
        people_history = game_runner.get_people_seen()
        if people_history:
            # Show last 50 decisions for timeline
            recent_history = people_history[-50:] if len(people_history) > 50 else people_history
            person_indices = [r.person_index for r in recent_history]
            decisions = [1 if r.decision else 0 for r in recent_history]
            colors = ['green' if d == 1 else 'red' for d in decisions]
            
            fig.add_trace(go.Scatter(
                x=person_indices,
                y=decisions,
                mode='markers',
                marker=dict(color=colors, size=6),
                name='Recent Decisions',
                showlegend=False
            ), row=2, col=2)
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text=f"Live Game Dashboard - {game_runner.strategy.get_name()}",
            showlegend=True
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Person Index", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=1)
        
        fig.update_xaxes(title_text="Person Index", row=1, col=2)
        fig.update_yaxes(title_text="Percentage (%)", row=1, col=2)
        
        fig.update_xaxes(title_text="Constraint", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        
        fig.update_xaxes(title_text="Person Index", row=2, col=2)
        fig.update_yaxes(title_text="Decision", row=2, col=2)
        
        return fig
    
    def create_summary_dashboard(self, results: Dict[str, Any]) -> go.Figure:
        """Create a comprehensive dashboard of all visualizations.
        
        Args:
            results: Results from GameRunner.run_game()
            
        Returns:
            Plotly figure with subplots
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                "Game Progress",
                "Attribute Distribution", 
                "Constraint Progress",
                "Decision Timeline"
            ],
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}]
            ]
        )
        
        # Game progress
        progress_fig = self.plot_game_progress(results)
        for trace in progress_fig.data:
            fig.add_trace(trace, row=1, col=1)
        
        # Attribute distribution
        attr_fig = self.plot_attribute_distribution(results)
        for trace in attr_fig.data:
            fig.add_trace(trace, row=1, col=2)
        
        # Constraint progress
        constraint_fig = self.plot_constraint_progress(results)
        for trace in constraint_fig.data:
            fig.add_trace(trace, row=2, col=1)
        
        # Decision timeline
        timeline_fig = self.plot_decision_timeline(results)
        for trace in timeline_fig.data:
            fig.add_trace(trace, row=2, col=2)
        
        fig.update_layout(
            height=800,
            title_text=f"Berghain Game Analysis - {results['strategy']} (Scenario {results['scenario']})",
            showlegend=True
        )
        
        return fig
    
    def compare_strategies(self, multiple_results: List[Dict[str, Any]]) -> go.Figure:
        """Compare results from multiple strategies.
        
        Args:
            multiple_results: List of results from different strategies
            
        Returns:
            Plotly figure comparing strategies
        """
        if not multiple_results:
            return go.Figure().add_annotation(text="No results to compare")
        
        strategies = [r['strategy'] for r in multiple_results]
        rejected_counts = [r['rejected_count'] for r in multiple_results]
        success_status = [r['success'] for r in multiple_results]
        
        colors = ['green' if success else 'red' for success in success_status]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=strategies,
            y=rejected_counts,
            marker_color=colors,
            text=[f"{'✓' if s else '✗'}" for s in success_status],
            textposition='outside'
        ))
        
        fig.update_layout(
            title="Strategy Comparison: Rejected Count (Lower is Better)",
            xaxis_title="Strategy",
            yaxis_title="Number of Rejected People",
            xaxis_tickangle=-45
        )
        
        return fig
