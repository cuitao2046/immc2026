#!/usr/bin/env python3
"""
Demo: Risk Model with Configuration File Support.

This script demonstrates:
1. Loading risk model configuration from JSON file
2. Using default configuration when no file is specified
3. Comparing results with different configurations
4. Saving custom configurations
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np

from risk_model.config import FullModelConfig, WeightManager
from risk_model.risk import RiskModel
from risk_model.core import (
    Grid,
    Environment,
    SpeciesDensity,
    TimeContext,
    Season,
    VegetationType
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def create_sample_data():
    """Create sample input data for testing."""
    # Create a sample grid
    grid = Grid(
        grid_id="A12",
        x=15.0,
        y=20.0,
        distance_to_boundary=0.3,
        distance_to_road=0.5,
        distance_to_water=0.7
    )

    # Create sample environment
    environment = Environment(
        fire_risk=0.6,
        terrain_complexity=0.4,
        vegetation_type=VegetationType.GRASSLAND
    )

    # Create sample species density
    density = SpeciesDensity(
        densities={
            "rhino": 0.8,
            "elephant": 0.6,
            "bird": 0.9
        }
    )

    # Create time context
    time_context = TimeContext(
        hour_of_day=22,
        season=Season.RAINY
    )

    return grid, environment, density, time_context


def main():
    """Run the configuration file demo."""
    print_header("RISK MODEL - CONFIGURATION FILE DEMO")

    # ========================================================================
    # Step 1: Create and save default configuration
    # ========================================================================
    print_header("STEP 1: Default Configuration")

    default_config = FullModelConfig.default()
    print("Default configuration loaded!")
    print(f"  Risk weights - human: {default_config.risk_weights.human_weight}")
    print(f"                  environmental: {default_config.risk_weights.environmental_weight}")
    print(f"                  density: {default_config.risk_weights.density_weight}")
    print(f"  Human risk - boundary: {default_config.human_risk_weights.boundary_weight}")
    print(f"               road: {default_config.human_risk_weights.road_weight}")
    print(f"               water: {default_config.human_risk_weights.water_weight}")
    print(f"  Species: {list(default_config.species_configs.keys())}")
    print(f"  Diurnal mode: {default_config.diurnal_config.mode}")
    print(f"  Night factor: {default_config.diurnal_config.nighttime_factor}")
    print(f"  Rainy season factor: {default_config.seasonal_config.rainy_season_factor}")

    # Save default config
    default_config.save("risk_model_config_default.json")
    print(f"\n✓ Default configuration saved to: risk_model_config_default.json")

    # ========================================================================
    # Step 2: Load from configuration file
    # ========================================================================
    print_header("STEP 2: Load from Configuration File")

    # Load the custom config
    config_file = "risk_model_config_custom.json"
    if os.path.exists(config_file):
        loaded_config = FullModelConfig.load(config_file)
        print(f"✓ Loaded configuration from: {config_file}")
        print(f"  Risk weights - human: {loaded_config.risk_weights.human_weight}")
        print(f"                  environmental: {loaded_config.risk_weights.environmental_weight}")
        print(f"                  density: {loaded_config.risk_weights.density_weight}")
        print(f"  Night factor: {loaded_config.diurnal_config.nighttime_factor}")
        print(f"  Rainy season factor: {loaded_config.seasonal_config.rainy_season_factor}")
    else:
        print(f"Config file not found: {config_file}")
        loaded_config = FullModelConfig.default()

    # ========================================================================
    # Step 3: Create RiskModel from config
    # ========================================================================
    print_header("STEP 3: Create RiskModel from Configuration")

    # Create sample data
    grid, environment, density, time_context = create_sample_data()

    # Create model from default config
    print("\n--- Using Default Configuration ---")
    model_default = RiskModel.from_config_file()  # No file = use default
    result_default = model_default.calculate_grid(
        grid, environment, density, time_context, fit_normalizer=True
    )
    print(f"  Normalized risk: {result_default.normalized_risk:.4f}")
    print(f"  Raw risk: {result_default.raw_risk:.4f}")

    # Create model from custom config file
    print("\n--- Using Custom Configuration ---")
    model_custom = RiskModel.from_config_file("risk_model_config_custom.json")
    result_custom = model_custom.calculate_grid(
        grid, environment, density, time_context, fit_normalizer=True
    )
    print(f"  Normalized risk: {result_custom.normalized_risk:.4f}")
    print(f"  Raw risk: {result_custom.raw_risk:.4f}")

    # Compare
    diff = abs(result_default.raw_risk - result_custom.raw_risk)
    print(f"\nDifference: {diff:.4f}")

    # ========================================================================
    # Step 4: Using WeightManager
    # ========================================================================
    print_header("STEP 4: Using WeightManager")

    # Load with WeightManager
    manager = WeightManager.from_file("risk_model_config_custom.json")
    print(f"WeightManager loaded from file!")
    print(f"  Human risk weight: {manager.get_risk_weights().human_weight}")
    print(f"  Rhino species weight: {manager.get_species_configs()['rhino'].weight}")

    # Modify weights (all three must sum to 1.0)
    manager.set_risk_weights(human_weight=0.6, environmental_weight=0.2, density_weight=0.2)
    print(f"\nAfter modification:")
    print(f"  Human risk weight: {manager.get_risk_weights().human_weight}")
    print(f"  Environmental weight: {manager.get_risk_weights().environmental_weight}")
    print(f"  Density weight: {manager.get_risk_weights().density_weight}")

    # Save modified
    manager.save("risk_model_config_modified.json")
    print(f"\n✓ Modified configuration saved to: risk_model_config_modified.json")

    # ========================================================================
    # Step 5: Load or Default (safe loading)
    # ========================================================================
    print_header("STEP 5: Safe Loading with Load-or-Default")

    # Try to load a non-existent file - will use default
    non_existent = "non_existent_config.json"
    config_safe = FullModelConfig.load_or_default(non_existent)
    print(f"Tried to load: {non_existent}")
    print(f"Used default configuration instead")
    print(f"  Human weight: {config_safe.risk_weights.human_weight}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("✓ DEMO COMPLETE")

    print("\nConfiguration file features:")
    print("  ✓ Save default configuration to JSON")
    print("  ✓ Load configuration from JSON")
    print("  ✓ Load-or-default (safe loading)")
    print("  ✓ Modify configurations programmatically")
    print("  ✓ Save modified configurations")
    print("  ✓ Create RiskModel directly from config file")

    print("\nUsage examples:")
    print("""
    # Option 1: Use default configuration
    model = RiskModel.from_config_file()

    # Option 2: Load from configuration file
    model = RiskModel.from_config_file("my_config.json")

    # Option 3: Create from FullModelConfig
    config = FullModelConfig.load("my_config.json")
    model = RiskModel.from_config(config)

    # Option 4: Using WeightManager
    manager = WeightManager.from_file("my_config.json")
    manager.set_risk_weights(human_weight=0.5)
    manager.save("modified_config.json")
    """)

    print("\nGenerated configuration files:")
    print("  - risk_model_config.json (template with defaults)")
    print("  - risk_model_config_custom.json (custom example)")
    print("  - risk_model_config_default.json (saved default config)")
    print("  - risk_model_config_modified.json (modified via WeightManager)")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
