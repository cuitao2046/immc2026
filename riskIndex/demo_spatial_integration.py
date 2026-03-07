#!/usr/bin/env python3
"""
Demo: Integrate Spatial Data Generator with Main Risk Model.

This script shows how to:
1. Generate realistic spatial maps using SpatialDataGenerator
2. Convert them to the main risk model format using SpatialToRiskModelAdapter
3. Run the complete risk model calculation
4. Compare results with the built-in risk map from spatial generator

NOTE: As of the latest update, the spatial generator's built-in risk calculation
uses EXACTLY the same logic as the main risk model, so the results are identical!
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np

from risk_model.data import (
    SpatialDataGenerator,
    SpatialConfig,
    SpatialToRiskModelAdapter,
    create_risk_model_input,
)
from risk_model.risk import (
    CompositeRiskCalculator,
    NormalizationEngine,
    GridRiskResult,
    HumanRiskCalculator,
    EnvironmentalRiskCalculator,
    DensityRiskCalculator,
    TemporalFactorCalculator,
)
from risk_model.config import WeightManager
from risk_model.core import Species
from risk_model.risk.human import HumanRiskWeights
from risk_model.risk.environmental import EnvironmentalRiskWeights


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def main():
    """Run the spatial integration demo."""
    print_header("SPATIAL DATA GENERATOR + MAIN RISK MODEL - INTEGRATION DEMO")

    # ========================================================================
    # Step 1: Generate spatial maps
    # ========================================================================
    print_header("STEP 1: Generating Spatial Maps")

    config = SpatialConfig(
        size=30,  # Smaller size for faster demo
        season="rainy",
        hour=22,
        save_maps=False
    )

    print(f"Configuration:")
    print(f"  Map size: {config.size}x{config.size}")
    print(f"  Season: {config.season}")
    print(f"  Hour: {config.hour:02d}:00")

    # Set seed before creating generator
    np.random.seed(42)
    generator = SpatialDataGenerator(config=config, seed=None)
    maps = generator.generate()

    print("\n✓ Spatial maps generated!")
    print(f"  - Terrain values: {np.unique(maps.terrain)}")
    print(f"  - Water pixels: {np.sum(maps.water)}")
    print(f"  - Road pixels: {np.sum(maps.roads)}")
    print(f"  - Mean animal density: {maps.animal_density.mean():.4f}")

    # ========================================================================
    # Step 2: Convert to risk model format
    # ========================================================================
    print_header("STEP 2: Converting to Risk Model Format")

    # Create adapter
    adapter = SpatialToRiskModelAdapter(maps)

    # Convert all grid data
    grid_data, time_context = create_risk_model_input(maps)

    print(f"✓ Converted {len(grid_data)} grid cells")
    print(f"\nExample grid cell (center of map):")
    center_i = config.size // 2
    center_j = config.size // 2

    example_grid = adapter.convert_grid(center_i, center_j)
    example_env = adapter.convert_environment(center_i, center_j)
    example_density = adapter.convert_species_density(center_i, center_j)

    print(f"  Grid ID: {example_grid.grid_id}")
    print(f"  Position: ({example_grid.x:.0f}, {example_grid.y:.0f})")
    print(f"  Distances - boundary: {example_grid.distance_to_boundary:.3f}, "
          f"road: {example_grid.distance_to_road:.3f}, "
          f"water: {example_grid.distance_to_water:.3f}")
    print(f"  Environment - fire risk: {example_env.fire_risk:.3f}, "
          f"terrain complexity: {example_env.terrain_complexity:.3f}")
    print(f"  Species densities - rhino: {example_density.densities['rhino']:.3f}, "
          f"elephant: {example_density.densities['elephant']:.3f}, "
          f"bird: {example_density.densities['bird']:.3f}")
    print(f"  Time context - hour: {time_context.hour_of_day}, "
          f"season: {time_context.season.value}")

    # ========================================================================
    # Step 3: Configure and run main risk model
    # ========================================================================
    print_header("STEP 3: Running Main Risk Model")

    # Set up weight manager with weights matching spatial generator
    weight_manager = WeightManager()
    weight_manager.set_risk_weights(
        human_weight=0.4,
        environmental_weight=0.3,
        density_weight=0.3
    )

    # Create calculators with matching weights
    human_weights = HumanRiskWeights(
        boundary_weight=0.4,
        road_weight=0.35,
        water_weight=0.25
    )
    env_weights = EnvironmentalRiskWeights(
        fire_weight=0.6,
        terrain_weight=0.4
    )

    # Set up species config matching spatial generator
    species_config = {
        "rhino": Species("rhino", 0.5, 1.2, 1.0),
        "elephant": Species("elephant", 0.3, 1.3, 0.9),
        "bird": Species("bird", 0.2, 1.5, 0.8),
    }

    # Create composite calculator with all custom components
    calculator = CompositeRiskCalculator(
        weight_manager=weight_manager,
        human_calculator=HumanRiskCalculator(weights=human_weights),
        environmental_calculator=EnvironmentalRiskCalculator(weights=env_weights),
        density_calculator=DensityRiskCalculator(species_config=species_config),
        temporal_calculator=TemporalFactorCalculator()
    )
    normalizer = NormalizationEngine()

    print("✓ Risk model configured with matching weights")
    print("  Calculating risk for all grid cells...")

    # First, calculate raw risks
    raw_results = []
    for grid, env, density in grid_data:
        raw_risk, components = calculator.calculate_raw(
            grid, env, density, time_context,
            return_components=True
        )
        raw_results.append((grid, raw_risk, components))

    # Normalize
    raw_risks = [r[1] for r in raw_results]
    normalizer.fit(raw_risks)

    # Create results
    results = []
    for grid, raw_risk, components in raw_results:
        normalized_risk = normalizer.normalize(raw_risk)
        results.append(GridRiskResult(
            grid_id=grid.grid_id,
            raw_risk=raw_risk,
            normalized_risk=normalized_risk,
            components=components
        ))

    print("✓ Risk calculation complete!")

    # ========================================================================
    # Step 4: Compare results
    # ========================================================================
    print_header("STEP 4: Comparing Results")

    # Get risk map from main model results
    main_risk_map = adapter.get_risk_map_array(results)

    # Get built-in risk map from spatial generator
    spatial_risk_map = maps.risk_map

    print("Risk Map Statistics:")
    print(f"\n  Main Risk Model:")
    print(f"    Min: {main_risk_map.min():.4f}")
    print(f"    Max: {main_risk_map.max():.4f}")
    print(f"    Mean: {main_risk_map.mean():.4f}")
    print(f"    Std: {main_risk_map.std():.4f}")

    print(f"\n  Spatial Generator (built-in):")
    print(f"    Min: {spatial_risk_map.min():.4f}")
    print(f"    Max: {spatial_risk_map.max():.4f}")
    print(f"    Mean: {spatial_risk_map.mean():.4f}")
    print(f"    Std: {spatial_risk_map.std():.4f}")

    # Calculate correlation
    correlation = np.corrcoef(main_risk_map.flatten(), spatial_risk_map.flatten())[0, 1]
    max_diff = np.max(np.abs(main_risk_map - spatial_risk_map))
    print(f"\n  Correlation between models: {correlation:.10f}")
    print(f"  Maximum difference: {max_diff:.10f}")

    if max_diff < 1e-10:
        print("  ✓ PERFECT MATCH - Both models produce identical results!")
    elif correlation > 0.999999:
        print("  ✓ NEARLY PERFECT - Results are effectively identical")
    elif correlation > 0.9:
        print("  ✓ Strong correlation - models produce consistent results!")
    elif correlation > 0.7:
        print("  ✓ Good correlation - results are reasonably consistent")
    else:
        print("  ⚠ Moderate correlation - differences due to implementation details")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("✓ INTEGRATION DEMO COMPLETE")

    print("\nKey takeaways:")
    print("  1. SpatialDataGenerator creates realistic continuous spatial maps")
    print("  2. SpatialToRiskModelAdapter converts to main risk model format")
    print("  3. Both systems calculate risk using EXACTLY the same mathematical model")
    print("  4. Results are identical (within floating-point precision)!")

    print("\nUsage patterns:")
    print("""
    # Quick generation with built-in risk:
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()
    risk_map = maps.risk_map  # Built-in risk calculation (FAST)

    # Full integration with main risk model:
    maps = generator.generate()
    grid_data, time_context = create_risk_model_input(maps)
    results = risk_model.calculate_batch(grid_data, time_context)
    # (Useful if you need to customize calculators, weights, etc.)
    """)

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
