#!/usr/bin/env python3
"""
Phase 2 Demo: Risk Integration & Normalization

This script demonstrates composite risk calculation and normalization.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from risk_model.core import (
    Grid,
    SpeciesDensity,
    Season,
    Environment,
    VegetationType,
    TimeContext,
)
from risk_model.risk import (
    CompositeRiskCalculator,
    NormalizationEngine,
    RiskModel,
    RiskComponents,
)
from risk_model.config import WeightManager, ModelConfig


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_weight_management():
    """Demonstrate weight management system."""
    print_separator("1. Weight Management")

    # Default weights
    print("Default configuration:")
    weight_manager = WeightManager()
    risk_weights = weight_manager.get_risk_weights()
    print(f"  Risk weights - Human: {risk_weights.human_weight:.2f}, "
          f"Environmental: {risk_weights.environmental_weight:.2f}, "
          f"Density: {risk_weights.density_weight:.2f}")

    # Custom weights
    print("\nCustom configuration:")
    weight_manager.set_risk_weights(
        human_weight=0.5,
        environmental_weight=0.25,
        density_weight=0.25
    )
    risk_weights = weight_manager.get_risk_weights()
    print(f"  Risk weights - Human: {risk_weights.human_weight:.2f}, "
          f"Environmental: {risk_weights.environmental_weight:.2f}, "
          f"Density: {risk_weights.density_weight:.2f}")

    # Save and load
    print("\nConfiguration save/load:")
    config_json = weight_manager.config.to_json()
    print(f"  Config JSON preview: {config_json[:80]}...")

    return weight_manager


def demo_composite_calculation():
    """Demonstrate composite risk calculation."""
    print_separator("2. Composite Risk Calculation")

    calculator = CompositeRiskCalculator()

    # Create test grid with high risk
    grid_high = Grid(
        grid_id="HOTSPOT",
        x=10.0,
        y=10.0,
        distance_to_boundary=0.05,
        distance_to_road=0.05,
        distance_to_water=0.1
    )
    env_high = Environment(
        fire_risk=0.8,
        terrain_complexity=0.7,
        vegetation_type=VegetationType.FOREST
    )
    density_high = SpeciesDensity({
        "rhino": 0.9,
        "elephant": 0.8,
        "bird": 0.6
    })
    time_context_night = TimeContext(hour_of_day=22, season=Season.RAINY)

    print("High risk scenario (night, rainy season, hotspot area):")
    raw_risk, components = calculator.calculate_raw(
        grid_high, env_high, density_high, time_context_night,
        return_components=True
    )
    print(f"  Raw risk: {raw_risk:.4f}")
    print(f"  Components:")
    print(f"    Human risk: {components.human_risk:.4f}")
    print(f"    Environmental risk: {components.environmental_risk:.4f}")
    print(f"    Density value: {components.density_value:.4f}")
    print(f"    Temporal factor: {components.temporal_factor:.4f} "
          f"(diurnal: {components.diurnal_factor:.2f}x, "
          f"seasonal: {components.seasonal_factor:.2f}x)")

    # Compare with low risk scenario
    grid_low = Grid(
        grid_id="SAFE",
        x=50.0,
        y=50.0,
        distance_to_boundary=0.95,
        distance_to_road=0.9,
        distance_to_water=0.8
    )
    env_low = Environment(
        fire_risk=0.1,
        terrain_complexity=0.2,
        vegetation_type=VegetationType.GRASSLAND
    )
    density_low = SpeciesDensity({
        "rhino": 0.1,
        "elephant": 0.2,
        "bird": 0.3
    })
    time_context_day = TimeContext(hour_of_day=10, season=Season.DRY)

    print("\nLow risk scenario (day, dry season, safe area):")
    raw_risk_low, components_low = calculator.calculate_raw(
        grid_low, env_low, density_low, time_context_day,
        return_components=True
    )
    print(f"  Raw risk: {raw_risk_low:.4f}")
    print(f"  Risk ratio (high/low): {raw_risk / raw_risk_low:.1f}x")


def demo_normalization():
    """Demonstrate risk normalization."""
    print_separator("3. Risk Normalization")

    normalizer = NormalizationEngine()

    # Sample raw risk values
    raw_risks = [0.2, 0.5, 0.3, 0.8, 0.1, 0.6, 0.4, 0.9]
    print(f"Raw risk values: {raw_risks}")

    normalizer.fit(raw_risks)
    print(f"Min risk: {normalizer.min_risk}")
    print(f"Max risk: {normalizer.max_risk}")

    normalized = normalizer.normalize_batch(raw_risks)
    print(f"Normalized values: {[f'{v:.3f}' for v in normalized]}")

    # Test single value normalization
    print("\nSingle value normalization:")
    test_values = [0.1, 0.5, 0.9]
    for val in test_values:
        norm = normalizer.normalize(val)
        print(f"  {val:.2f} -> {norm:.3f}")


def demo_complete_model():
    """Demonstrate the complete RiskModel."""
    print_separator("4. Complete Risk Model")

    model = RiskModel()

    # Create multiple grid cells
    grids_data = []

    # Grid 1: High risk
    grid1 = Grid("A01", 0, 0, 0.05, 0.1, 0.1)
    env1 = Environment(0.8, 0.7, VegetationType.FOREST)
    density1 = SpeciesDensity({"rhino": 0.9, "elephant": 0.7, "bird": 0.5})
    grids_data.append((grid1, env1, density1))

    # Grid 2: Medium-High risk
    grid2 = Grid("B03", 2, 1, 0.2, 0.3, 0.2)
    env2 = Environment(0.5, 0.4, VegetationType.SHRUB)
    density2 = SpeciesDensity({"rhino": 0.6, "elephant": 0.5, "bird": 0.7})
    grids_data.append((grid2, env2, density2))

    # Grid 3: Medium risk
    grid3 = Grid("C05", 4, 2, 0.4, 0.5, 0.4)
    env3 = Environment(0.3, 0.3, VegetationType.GRASSLAND)
    density3 = SpeciesDensity({"rhino": 0.4, "elephant": 0.4, "bird": 0.6})
    grids_data.append((grid3, env3, density3))

    # Grid 4: Low risk
    grid4 = Grid("D07", 6, 3, 0.7, 0.8, 0.6)
    env4 = Environment(0.2, 0.2, VegetationType.GRASSLAND)
    density4 = SpeciesDensity({"rhino": 0.2, "elephant": 0.3, "bird": 0.4})
    grids_data.append((grid4, env4, density4))

    # Grid 5: Very low risk
    grid5 = Grid("E09", 8, 4, 0.95, 0.9, 0.85)
    env5 = Environment(0.1, 0.1, VegetationType.GRASSLAND)
    density5 = SpeciesDensity({"rhino": 0.1, "elephant": 0.1, "bird": 0.2})
    grids_data.append((grid5, env5, density5))

    # Calculate for night/rainy season
    time_context = TimeContext(hour_of_day=23, season=Season.RAINY)
    results = model.calculate_batch(grids_data, time_context)

    print("Batch calculation - Night, Rainy Season:")
    print(f"  {'Grid':<8} {'Raw Risk':<12} {'Normalized':<12} {'Components'}")
    print("  " + "-"*65)
    for result in results:
        comp = result.components
        comp_str = f"H={comp.human_risk:.2f} E={comp.environmental_risk:.2f} D={comp.density_value:.2f} T={comp.temporal_factor:.2f}"
        print(f"  {result.grid_id:<8} {result.raw_risk:<12.4f} {result.normalized_risk:<12.4f} {comp_str}")

    # Compare with day/dry season
    print("\nNormalized risk comparison:")
    time_context_day = TimeContext(hour_of_day=10, season=Season.DRY)
    results_day = model.calculate_batch(grids_data, time_context_day)

    print(f"  {'Grid':<8} {'Night/Rainy':<12} {'Day/Dry':<12} {'Ratio':<10}")
    print("  " + "-"*45)
    for result_night, result_day in zip(results, results_day):
        ratio = result_night.normalized_risk / result_day.normalized_risk if result_day.normalized_risk > 0 else float('inf')
        print(f"  {result_night.grid_id:<8} {result_night.normalized_risk:<12.4f} {result_day.normalized_risk:<12.4f} {ratio:<10.1f}x")


def main():
    """Run all Phase 2 demos."""
    print("\n" + "="*60)
    print("  PROTECTED AREA RISK MODEL - PHASE 2 DEMO")
    print("  Risk Integration & Normalization")
    print("="*60)

    demo_weight_management()
    demo_composite_calculation()
    demo_normalization()
    demo_complete_model()

    print_separator("✓ PHASE 2 COMPLETE")
    print("Composite risk calculation and normalization are working!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
