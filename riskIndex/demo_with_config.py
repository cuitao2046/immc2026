#!/usr/bin/env python3
"""
Demo: Use Configuration File for Spatial Data Generator.

This script demonstrates:
1. Loading configuration from a JSON file
2. Saving configuration to a JSON file
3. Generating maps using the configuration
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np

from risk_model.data import SpatialDataGenerator, SpatialConfig


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def main():
    """Run the configuration file demo."""
    print_header("SPATIAL DATA GENERATOR - CONFIG FILE DEMO")

    # ========================================================================
    # Step 1: Create and save a default configuration
    # ========================================================================
    print_header("STEP 1: Create and Save Default Configuration")

    # Create a default configuration
    config = SpatialConfig.default()
    print("Default configuration:")
    print(f"  size: {config.size}")
    print(f"  season: {config.season}")
    print(f"  hour: {config.hour}")
    print(f"  terrain_smooth_scale: {config.terrain_smooth_scale}")
    print(f"  water_smooth_scale: {config.water_smooth_scale}")
    print(f"  animal_smooth_scale: {config.animal_smooth_scale}")
    print(f"  output_dir: {config.output_dir}")
    print(f"  save_maps: {config.save_maps}")
    print(f"  save_data: {config.save_data}")
    print(f"  map_format: {config.map_format}")

    # Save to JSON file
    config_file = "my_config.json"
    config.save(config_file)
    print(f"\n✓ Configuration saved to: {config_file}")

    # Show the JSON content
    print("\nJSON content:")
    print("-" * 70)
    print(config.to_json())
    print("-" * 70)

    # ========================================================================
    # Step 2: Load configuration from file
    # ========================================================================
    print_header("STEP 2: Load Configuration from File")

    loaded_config = SpatialConfig.load(config_file)
    print("✓ Configuration loaded from file!")
    print(f"  size: {loaded_config.size}")
    print(f"  season: {loaded_config.season}")
    print(f"  hour: {loaded_config.hour}")

    # ========================================================================
    # Step 3: Create a custom configuration
    # ========================================================================
    print_header("STEP 3: Create Custom Configuration")

    custom_config = SpatialConfig(
        size=100,
        season="dry",
        hour=10,
        terrain_smooth_scale=12.0,
        water_smooth_scale=10.0,
        animal_smooth_scale=8.0,
        output_dir="custom_maps",
        save_maps=True,
        save_data=True,
        map_format="png"
    )

    print("Custom configuration created:")
    print(f"  size: {custom_config.size}")
    print(f"  season: {custom_config.season}")
    print(f"  hour: {custom_config.hour}")
    print(f"  output_dir: {custom_config.output_dir}")
    print(f"  map_format: {custom_config.map_format}")

    custom_config.save("custom_config.json")
    print("\n✓ Custom configuration saved to: custom_config.json")

    # ========================================================================
    # Step 4: Use example config file
    # ========================================================================
    print_header("STEP 4: Use Example Config File")

    example_config_file = "config_example.json"
    if os.path.exists(example_config_file):
        example_config = SpatialConfig.load(example_config_file)
        print(f"✓ Loaded example config from: {example_config_file}")
        print(f"  size: {example_config.size}")
        print(f"  season: {example_config.season}")
        print(f"  hour: {example_config.hour}")

        # Update a few parameters
        example_config.output_dir = "example_maps"
        example_config.hour = 2  # Change to early morning

        print("\nUpdated configuration:")
        print(f"  output_dir: {example_config.output_dir}")
        print(f"  hour: {example_config.hour}")

        # Generate with the example config
        print("\nGenerating maps with example config... (this may take a moment)")
        generator = SpatialDataGenerator(config=example_config, seed=42)
        maps = generator.generate()

        print("✓ Generation complete!")
        print(f"\nSummary:")
        print(f"  Risk map mean: {maps.risk_map.mean():.4f}")
        print(f"  Risk map max: {maps.risk_map.max():.4f}")
        high_risk = np.sum(maps.risk_map > 0.7)
        total_pixels = maps.risk_map.size
        print(f"  High risk pixels (>0.7): {high_risk} ({high_risk/total_pixels*100:.1f}%)")
    else:
        print(f"Example config file not found: {example_config_file}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("✓ DEMO COMPLETE")

    print("\nConfiguration file features:")
    print("  ✓ Save configuration to JSON file")
    print("  ✓ Load configuration from JSON file")
    print("  ✓ Create custom configurations programmatically")
    print("  ✓ Modify configurations after loading")
    print("  ✓ Use config_example.json as a template")

    print("\nUsage in your code:")
    print("""
    from risk_model.data import SpatialDataGenerator, SpatialConfig

    # Option 1: Load from config file
    config = SpatialConfig.load("my_config.json")

    # Option 2: Create programmatically
    config = SpatialConfig(
        size=120,
        season="rainy",
        hour=22,
        output_dir="my_maps",
        save_maps=True,
        save_data=True,
        map_format="jpg"
    )

    # Save config for later use
    config.save("my_config.json")

    # Generate maps
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()
    """)

    print("\nGenerated config files:")
    print("  - my_config.json (default config)")
    print("  - custom_config.json (custom config)")
    print("  - config_example.json (example template)")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
