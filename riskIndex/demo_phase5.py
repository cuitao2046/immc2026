#!/usr/bin/env python3
"""
Phase 5 Demo: Testing & Validation

This script demonstrates the test suite and validation.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from risk_model.core import (
    Grid,
    Species,
    SpeciesDensity,
    Season,
    Environment,
    VegetationType,
    TimeContext,
)
from risk_model.risk import RiskModel
from risk_model.data import (
    SyntheticDataGenerator,
    GridLayoutConfig,
    DataValidator,
)


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_data_validation():
    """Demonstrate data validation."""
    print_separator("1. Data Validation")

    # Create validator
    validator = DataValidator()

    # Generate valid data
    generator = SyntheticDataGenerator(seed=42)
    config = GridLayoutConfig(grid_width=4, grid_height=4)
    grids, environments, densities = generator.generate_full_dataset(config, seed=42)

    print("Validating synthetic data...")
    is_valid = validator.validate_batch(grids, environments, densities)
    validator.print_summary()

    # Test with invalid data
    print("\n\nTesting validation with invalid data...")
    invalid_grids = []
    try:
        invalid_grid = Grid("BAD", 0, 0, 1.5, 0.5, 0.5)  # Invalid distance
        invalid_grids.append(invalid_grid)
    except ValueError as e:
        print(f"✓ Grid validation caught invalid distance: {e}")

    validator.clear_errors()


def demo_edge_cases():
    """Demonstrate edge case handling."""
    print_separator("2. Edge Case Handling")

    model = RiskModel()

    # All grids same risk
    print("Test: All grids with identical characteristics")
    grids = []
    envs = []
    densities = []

    for i in range(5):
        grid = Grid(f"G{i:02d}", i, i, 0.5, 0.5, 0.5)
        env = Environment(0.5, 0.5, VegetationType.GRASSLAND)
        density = SpeciesDensity({"rhino": 0.5, "elephant": 0.5, "bird": 0.5})
        grids.append(grid)
        envs.append(env)
        densities.append(density)

    grid_data = list(zip(grids, envs, densities))
    ctx = TimeContext(hour_of_day=12, season=Season.DRY)
    results = model.calculate_batch(grid_data, ctx)

    print(f"  All normalized risks should be ~0.5")
    for r in results:
        print(f"    {r.grid_id}: {r.normalized_risk:.6f}")

    # Single grid
    print("\nTest: Single grid cell")
    model2 = RiskModel()
    grid = Grid("SINGLE", 0, 0, 0.5, 0.5, 0.5)
    env = Environment(0.5, 0.5, VegetationType.GRASSLAND)
    density = SpeciesDensity({"rhino": 0.5, "elephant": 0.5, "bird": 0.5})

    result = model2.calculate_grid(grid, env, density, ctx, fit_normalizer=True)
    print(f"  Single grid normalized risk: {result.normalized_risk}")


def demo_model_stability():
    """Demonstrate model stability and reproducibility."""
    print_separator("3. Model Stability & Reproducibility")

    # Test with same seed gives same results
    print("Test: Reproducibility with fixed seed")
    generator1 = SyntheticDataGenerator(seed=123)
    generator2 = SyntheticDataGenerator(seed=123)

    config = GridLayoutConfig(grid_width=3, grid_height=3)
    grids1, envs1, dens1 = generator1.generate_full_dataset(config, seed=123)
    grids2, envs2, dens2 = generator2.generate_full_dataset(config, seed=123)

    # Compare
    match = True
    for i in range(len(grids1)):
        if grids1[i].distance_to_boundary != grids2[i].distance_to_boundary:
            match = False
            break

    print(f"  Same seed produces same results: {'✓' if match else '✗'}")

    # Test risk calculation consistency
    print("\nTest: Risk calculation consistency")
    model = RiskModel()
    ctx = TimeContext(hour_of_day=18, season=Season.RAINY)
    grid_data1 = list(zip(grids1, envs1, dens1))
    grid_data2 = list(zip(grids2, envs2, dens2))

    results1 = model.calculate_batch(grid_data1, ctx)
    results2 = model.calculate_batch(grid_data2, ctx)

    risk_match = True
    for r1, r2 in zip(results1, results2):
        if abs(r1.normalized_risk - r2.normalized_risk) > 1e-9:
            risk_match = False
            break

    print(f"  Same inputs produce same risk values: {'✓' if risk_match else '✗'}")


def demo_validation_summary():
    """Demonstrate validation summary report."""
    print_separator("4. Validation Summary Report")

    # Generate and validate a complete dataset
    generator = SyntheticDataGenerator(seed=456)
    config = GridLayoutConfig(grid_width=6, grid_height=6)
    grids, environments, densities = generator.generate_full_dataset(config, seed=456)

    # Calculate risks
    model = RiskModel()
    ctx = TimeContext(hour_of_day=2, season=Season.RAINY)
    grid_data = list(zip(grids, environments, densities))
    results = model.calculate_batch(grid_data, ctx)

    # Summary statistics
    risks = [r.normalized_risk for r in results]

    print("Dataset Summary:")
    print(f"  Total grid cells: {len(grids)}")
    print(f"  Grid layout: {config.grid_width}x{config.grid_height}")
    print(f"\nRisk Statistics:")
    print(f"  Min: {min(risks):.4f}")
    print(f"  Max: {max(risks):.4f}")
    print(f"  Mean: {sum(risks)/len(risks):.4f}")

    # Risk categories
    high = sum(1 for r in risks if r > 0.7)
    medium = sum(1 for r in risks if 0.3 <= r <= 0.7)
    low = sum(1 for r in risks if r < 0.3)

    print(f"\nRisk Distribution:")
    print(f"  High Risk (>0.7):   {high:2d} ({high/len(risks)*100:.0f}%)")
    print(f"  Medium Risk (0.3-0.7): {medium:2d} ({medium/len(risks)*100:.0f}%)")
    print(f"  Low Risk (<0.3):    {low:2d} ({low/len(risks)*100:.0f}%)")

    # Top 5 high-risk grids
    sorted_results = sorted(results, key=lambda x: x.normalized_risk, reverse=True)
    print(f"\nTop 5 High-Risk Grids:")
    for i, r in enumerate(sorted_results[:5]):
        print(f"  {i+1}. {r.grid_id}: {r.normalized_risk:.4f}")


def main():
    """Run all Phase 5 demos."""
    print("\n" + "="*60)
    print("  PROTECTED AREA RISK MODEL - PHASE 5 DEMO")
    print("  Testing & Validation")
    print("="*60)

    demo_data_validation()
    demo_edge_cases()
    demo_model_stability()
    demo_validation_summary()

    print_separator("✓ PHASE 5 COMPLETE")
    print("Testing and validation modules are working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
