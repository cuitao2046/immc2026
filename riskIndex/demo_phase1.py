#!/usr/bin/env python3
"""
Phase 1 Demo: Core Model Implementation

This script demonstrates the core data structures and risk calculators.
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
from risk_model.risk import (
    HumanRiskCalculator,
    HumanRiskWeights,
    EnvironmentalRiskCalculator,
    EnvironmentalRiskWeights,
    DensityRiskCalculator,
    DiurnalFactorCalculator,
    DiurnalMode,
    SeasonalFactorCalculator,
    TemporalFactorCalculator,
)


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_grid():
    """Demonstrate Grid data structure."""
    print_separator("1. Grid Data Structure")

    # Create a grid cell near boundary and road
    grid = Grid(
        grid_id="A12",
        x=10.5,
        y=25.3,
        distance_to_boundary=0.1,  # Very close to boundary
        distance_to_road=0.2,     # Close to road
        distance_to_water=0.7       # Far from water
    )

    print(f"Grid ID: {grid.grid_id}")
    print(f"Position: ({grid.x}, {grid.y})")
    print(f"Distances - Boundary: {grid.distance_to_boundary}, "
          f"Road: {grid.distance_to_road}, "
          f"Water: {grid.distance_to_water}")

    boundary_prox, road_prox, water_prox = grid.proximity_score
    print(f"Proximity Scores - Boundary: {boundary_prox:.3f}, "
          f"Road: {road_prox:.3f}, "
          f"Water: {water_prox:.3f}")

    return grid


def demo_human_risk():
    """Demonstrate Human Risk Calculator."""
    print_separator("2. Human Risk Calculator")

    # Create grid with various distances
    grid_high_risk = Grid(
        grid_id="HOTSPOT",
        x=5.0,
        y=5.0,
        distance_to_boundary=0.05,
        distance_to_road=0.05,
        distance_to_water=0.1
    )

    grid_low_risk = Grid(
        grid_id="SAFE",
        x=50.0,
        y=50.0,
        distance_to_boundary=0.9,
        distance_to_road=0.95,
        distance_to_water=0.8
    )

    # Use default weights
    calculator = HumanRiskCalculator()

    print("High risk area (near boundary and road):")
    risk = calculator.calculate(grid_high_risk, poaching_probability=1.0)
    print(f"  Risk: {risk:.3f}")

    breakdown = calculator.calculate_component_breakdown(grid_high_risk)
    print(f"  Breakdown - Boundary: {breakdown[0]:.3f}, "
          f"Road: {breakdown[1]:.3f}, "
          f"Water: {breakdown[2]:.3f}")

    print("\nLow risk area (deep inside protected area):")
    risk = calculator.calculate(grid_low_risk, poaching_probability=1.0)
    print(f"  Risk: {risk:.3f}")

    print("\nWith reduced poaching probability (0.5):")
    risk = calculator.calculate(grid_high_risk, poaching_probability=0.5)
    print(f"  Risk: {risk:.3f}")


def demo_environmental_risk():
    """Demonstrate Environmental Risk Calculator."""
    print_separator("3. Environmental Risk Calculator")

    # High fire risk area
    env_high = Environment(
        fire_risk=0.9,
        terrain_complexity=0.7,
        vegetation_type=VegetationType.FOREST
    )

    # Low risk area
    env_low = Environment(
        fire_risk=0.1,
        terrain_complexity=0.2,
        vegetation_type=VegetationType.GRASSLAND
    )

    calculator = EnvironmentalRiskCalculator()

    print("High environmental risk (fire-prone forest with complex terrain):")
    risk = calculator.calculate(env_high)
    print(f"  Risk: {risk:.3f}")
    breakdown = calculator.calculate_component_breakdown(env_high)
    print(f"  Breakdown - Fire: {breakdown[0]:.3f}, "
          f"Terrain: {breakdown[1]:.3f}")

    print("\nLow environmental risk:")
    risk = calculator.calculate(env_low)
    print(f"  Risk: {risk:.3f}")


def demo_species_density():
    """Demonstrate Species Density Calculator."""
    print_separator("4. Species Density Calculator")

    calculator = DensityRiskCalculator()

    # Area with high rhino density
    density_rhino = SpeciesDensity({
        "rhino": 0.9,
        "elephant": 0.3,
        "bird": 0.5
    })

    # Area with high elephant density
    density_elephant = SpeciesDensity({
        "rhino": 0.2,
        "elephant": 0.9,
        "bird": 0.4
    })

    print("Rhino hotspot (dry season):")
    score = calculator.calculate(density_rhino, Season.DRY)
    print(f"  Conservation Value: {score:.3f}")
    breakdown = calculator.calculate_species_breakdown(density_rhino, Season.DRY)
    print(f"  Breakdown: {breakdown}")

    print("\nRhino hotspot (rainy season):")
    score = calculator.calculate(density_rhino, Season.RAINY)
    print(f"  Conservation Value: {score:.3f}")

    print("\nElephant area (rainy season):")
    score = calculator.calculate(density_elephant, Season.RAINY)
    print(f"  Conservation Value: {score:.3f}")


def demo_temporal_factors():
    """Demonstrate Temporal Factor Calculators."""
    print_separator("5. Temporal Factors")

    # Diurnal factors
    print("Diurnal Factors (Discrete Mode):")
    diurnal_discrete = DiurnalFactorCalculator(mode=DiurnalMode.DISCRETE)
    for hour in [8, 12, 20, 0]:
        factor = diurnal_discrete.calculate(hour)
        print(f"  {hour:02d}:00 -> {factor:.2f}x")

    print("\nDiurnal Factors (Continuous Mode):")
    diurnal_continuous = DiurnalFactorCalculator(mode=DiurnalMode.CONTINUOUS)
    for hour in [8, 12, 20, 0]:
        factor = diurnal_continuous.calculate(hour)
        print(f"  {hour:02d}:00 -> {factor:.2f}x")

    # Seasonal factors
    print("\nSeasonal Factors:")
    seasonal = SeasonalFactorCalculator()
    print(f"  Dry Season: {seasonal.calculate(Season.DRY):.2f}x")
    print(f"  Rainy Season: {seasonal.calculate(Season.RAINY):.2f}x")

    # Combined
    print("\nCombined Temporal Factors:")
    temporal = TemporalFactorCalculator()

    print("  Daytime, Dry Season:")
    ctx_day_dry = TimeContext(hour_of_day=10, season=Season.DRY)
    print(f"    Factor: {temporal.calculate(ctx_day_dry):.2f}x")

    print("  Nighttime, Rainy Season:")
    ctx_night_rain = TimeContext(hour_of_day=22, season=Season.RAINY)
    print(f"    Factor: {temporal.calculate(ctx_night_rain):.2f}x")


def main():
    """Run all Phase 1 demos."""
    print("\n" + "="*60)
    print("  PROTECTED AREA RISK MODEL - PHASE 1 DEMO")
    print("  Core Model Implementation")
    print("="*60)

    demo_grid()
    demo_human_risk()
    demo_environmental_risk()
    demo_species_density()
    demo_temporal_factors()

    print_separator("✓ PHASE 1 COMPLETE")
    print("All core data structures and risk calculators are working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
