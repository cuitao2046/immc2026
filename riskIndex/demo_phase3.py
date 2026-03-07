#!/usr/bin/env python3
"""
Phase 3 Demo: Data Generation & Input/Output

This script demonstrates synthetic data generation, validation, and I/O.
"""

import sys
import os
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from risk_model.core import TimeContext, Season
from risk_model.risk import RiskModel
from risk_model.data import (
    SyntheticDataGenerator,
    GridLayoutConfig,
    GridDataWriter,
    GridDataReader,
    DataValidator,
)


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_synthetic_data_generation():
    """Demonstrate synthetic data generation."""
    print_separator("1. Synthetic Data Generation")

    # Create generator with fixed seed for reproducibility
    generator = SyntheticDataGenerator(seed=42)

    # Small grid for demo
    config = GridLayoutConfig(
        grid_width=5,
        grid_height=5,
        area_width_km=50.0,
        area_height_km=50.0
    )

    print(f"Generating {config.grid_width}x{config.grid_height} grid...")
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    print(f"\nGenerated {len(grids)} grid cells")
    print("\nSample grid cells (first 5):")
    for i, grid in enumerate(grids[:5]):
        env = environments[i]
        dens = densities[i]
        print(f"\n  {grid.grid_id}:")
        print(f"    Position: ({grid.x:.1f}, {grid.y:.1f})")
        print(f"    Distances - Boundary: {grid.distance_to_boundary:.2f}, "
              f"Road: {grid.distance_to_road:.2f}, "
              f"Water: {grid.distance_to_water:.2f}")
        print(f"    Environment - Fire: {env.fire_risk:.2f}, "
              f"Terrain: {env.terrain_complexity:.2f}, "
              f"Veg: {env.vegetation_type.value}")
        print(f"    Densities - Rhino: {dens.densities['rhino']:.2f}, "
              f"Elephant: {dens.densities['elephant']:.2f}, "
              f"Bird: {dens.densities['bird']:.2f}")

    return grids, environments, densities


def demo_data_validation():
    """Demonstrate data validation."""
    print_separator("2. Data Validation")

    generator = SyntheticDataGenerator(seed=42)
    config = GridLayoutConfig(grid_width=3, grid_height=3)
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    validator = DataValidator()

    print("Validating synthetic data...")
    is_valid = validator.validate_batch(grids, environments, densities)

    validator.print_summary()

    # Show some statistics
    if is_valid:
        print(f"\nAll {len(grids)} grid cells validated successfully!")


def demo_risk_calculation_with_generated_data():
    """Demonstrate risk calculation with synthetic data."""
    print_separator("3. Risk Calculation with Generated Data")

    generator = SyntheticDataGenerator(seed=42)
    config = GridLayoutConfig(grid_width=6, grid_height=6)
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    model = RiskModel()
    time_context = TimeContext(hour_of_day=2, season=Season.RAINY)

    # Prepare grid data for batch calculation
    grid_data = list(zip(grids, environments, densities))

    results = model.calculate_batch(grid_data, time_context)

    print(f"Risk calculation for {len(results)} grids - Night, Rainy Season")
    print(f"\n  {'Grid':<8} {'Norm Risk':<10} {'Fire':<6} {'Rhino':<6} {'Road':<6}")
    print("  " + "-"*45)

    # Sort by risk
    sorted_results = sorted(results, key=lambda r: r.normalized_risk, reverse=True)

    for i, result in enumerate(sorted_results):
        grid_idx = next(i for i, g in enumerate(grids) if g.grid_id == result.grid_id)
        env = environments[grid_idx]
        dens = densities[grid_idx]
        grid = grids[grid_idx]

        print(f"  {result.grid_id:<8} {result.normalized_risk:<10.3f} "
              f"{env.fire_risk:<6.2f} {dens.densities['rhino']:<6.2f} {1-grid.distance_to_road:<6.2f}")

    # Summary
    high_risk = sum(1 for r in results if r.normalized_risk > 0.7)
    medium_risk = sum(1 for r in results if 0.3 <= r.normalized_risk <= 0.7)
    low_risk = sum(1 for r in results if r.normalized_risk < 0.3)

    print(f"\nRisk Summary:")
    print(f"  High Risk (>0.7):   {high_risk:2d} grids")
    print(f"  Medium Risk (0.3-0.7): {medium_risk:2d} grids")
    print(f"  Low Risk (<0.3):    {low_risk:2d} grids")

    return grids, environments, densities, results


def demo_data_io():
    """Demonstrate data input/output."""
    print_separator("4. Data Input/Output")

    generator = SyntheticDataGenerator(seed=42)
    config = GridLayoutConfig(grid_width=4, grid_height=4)
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    # Calculate risks for export
    model = RiskModel()
    time_context = TimeContext(hour_of_day=22, season=Season.RAINY)
    grid_data = list(zip(grids, environments, densities))
    results = model.calculate_batch(grid_data, time_context)

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "risk_data.csv")
        json_path = os.path.join(tmpdir, "risk_summary.json")

        print(f"Writing CSV to: {csv_path}")
        GridDataWriter.write_grids_to_csv(
            grids, csv_path, environments, densities, results
        )

        print(f"Writing JSON summary to: {json_path}")
        GridDataWriter.write_risk_summary_to_json(results, json_path)

        print("\nReading back CSV...")
        read_grids, read_envs, read_dens = GridDataReader.read_grids_from_csv(csv_path)

        print(f"  Successfully read {len(read_grids)} grids, "
              f"{len(read_envs)} environments, "
              f"{len(read_dens)} density entries")

        # Verify data
        if read_grids:
            print(f"  First grid: {read_grids[0].grid_id}")


def main():
    """Run all Phase 3 demos."""
    print("\n" + "="*60)
    print("  PROTECTED AREA RISK MODEL - PHASE 3 DEMO")
    print("  Data Generation & Input/Output")
    print("="*60)

    demo_synthetic_data_generation()
    demo_data_validation()
    demo_risk_calculation_with_generated_data()
    demo_data_io()

    print_separator("✓ PHASE 3 COMPLETE")
    print("Data generation, validation, and I/O are working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
