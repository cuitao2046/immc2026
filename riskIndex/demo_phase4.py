#!/usr/bin/env python3
"""
Phase 4 Demo: Visualization

This script demonstrates risk visualization including heatmaps and analysis plots.
Note: This demo saves plots to files since matplotlib may not have a display.
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure matplotlib for non-interactive backend
import matplotlib
matplotlib.use('Agg')

from risk_model.core import TimeContext, Season
from risk_model.risk import RiskModel
from risk_model.data import (
    SyntheticDataGenerator,
    GridLayoutConfig,
)
from risk_model.visualization import (
    RiskHeatmap,
    TemporalVisualizer,
    AnalysisVisualizer,
)


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_heatmap(output_dir: str):
    """Demonstrate risk heatmap generation."""
    print_separator("1. Risk Heatmap")

    # Generate data
    generator = SyntheticDataGenerator(seed=42)
    config = GridLayoutConfig(grid_width=8, grid_height=6)
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    # Calculate risks
    model = RiskModel()
    time_context = TimeContext(hour_of_day=2, season=Season.RAINY)
    grid_data = list(zip(grids, environments, densities))
    results = model.calculate_batch(grid_data, time_context)

    risk_values = [r.normalized_risk for r in results]

    # Create heatmap
    heatmap = RiskHeatmap()
    output_path = os.path.join(output_dir, "risk_heatmap.png")

    print(f"Generating heatmap for {config.grid_width}x{config.grid_height} grid...")
    heatmap.plot_heatmap(
        grids, risk_values,
        grid_width=config.grid_width,
        grid_height=config.grid_height,
        title="Risk Heatmap - Night, Rainy Season",
        show_grid_labels=True,
        output_path=output_path
    )

    # Risk distribution
    dist_path = os.path.join(output_dir, "risk_distribution.png")
    heatmap.plot_risk_distribution(
        risk_values,
        title="Risk Value Distribution",
        output_path=dist_path
    )

    return grids, environments, densities, results


def demo_temporal_comparison(output_dir: str):
    """Demonstrate temporal comparison visualizations."""
    print_separator("2. Temporal Comparison")

    # Generate data
    generator = SyntheticDataGenerator(seed=123)
    config = GridLayoutConfig(grid_width=6, grid_height=4)
    grids, environments, densities = generator.generate_full_dataset(config, seed=123)

    model = RiskModel()
    visualizer = TemporalVisualizer()

    # Day/Night comparison
    print("Generating day/night comparison plot...")
    day_night_path = os.path.join(output_dir, "day_night_comparison.png")
    visualizer.compare_day_night(
        grids, environments, densities, model,
        season=Season.RAINY,
        title="Day vs Night Risk Comparison (Rainy Season)",
        output_path=day_night_path
    )

    # Season comparison
    print("Generating season comparison plot...")
    season_path = os.path.join(output_dir, "season_comparison.png")
    visualizer.compare_seasons(
        grids, environments, densities, model,
        hour=22,
        title="Dry vs Rainy Season Risk Comparison (Night)",
        output_path=season_path
    )


def demo_analysis_plots(output_dir: str):
    """Demonstrate analysis visualizations."""
    print_separator("3. Risk Component Analysis")

    # Generate data
    generator = SyntheticDataGenerator(seed=456)
    config = GridLayoutConfig(grid_width=8, grid_height=5)
    grids, environments, densities = generator.generate_full_dataset(config, seed=456)

    model = RiskModel()
    time_context = TimeContext(hour_of_day=23, season=Season.RAINY)
    grid_data = list(zip(grids, environments, densities))
    results = model.calculate_batch(grid_data, time_context)

    visualizer = AnalysisVisualizer()

    # Component breakdown
    print("Generating risk component breakdown...")
    breakdown_path = os.path.join(output_dir, "component_breakdown.png")
    visualizer.plot_component_breakdown(
        results,
        top_n=10,
        title="Risk Component Breakdown (Top 10 High-Risk Grids)",
        output_path=breakdown_path
    )

    # Scatter plots
    print("Generating risk component scatter plots...")
    scatter_path = os.path.join(output_dir, "component_scatter.png")
    visualizer.plot_risk_scatter(
        results,
        title="Risk Components Relationship Analysis",
        output_path=scatter_path
    )


def main():
    """Run all Phase 4 demos."""
    print("\n" + "="*60)
    print("  PROTECTED AREA RISK MODEL - PHASE 4 DEMO")
    print("  Visualization")
    print("="*60)
    print("\nNote: Plots will be saved to files (no display available)")

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "plots")
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nOutput directory: {output_dir}")

    demo_heatmap(output_dir)
    demo_temporal_comparison(output_dir)
    demo_analysis_plots(output_dir)

    # List generated files
    print_separator("Generated Plot Files")
    for filename in sorted(os.listdir(output_dir)):
        filepath = os.path.join(output_dir, filename)
        size = os.path.getsize(filepath)
        print(f"  {filename:<30} ({size:,} bytes)")

    print_separator("✓ PHASE 4 COMPLETE")
    print("All visualization modules are working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
