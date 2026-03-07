#!/usr/bin/env python3
"""
Demo script for the Spatial Data Generator.

Generates realistic continuous spatial maps using Gaussian smoothing.
Based on data.py script.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from risk_model.data import SpatialDataGenerator, SpatialConfig


def print_separator(title: str):
    """Print a separator with title."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    """Run the spatial data generator demo."""
    print("\n" + "="*60)
    print("  SPATIAL DATA GENERATOR DEMO")
    print("  Based on data.py with Gaussian smoothing")
    print("="*60)

    # Configure and create generator
    config = SpatialConfig(
        size=120,
        season="rainy",
        hour=22,
        output_dir="spatial_maps",
        save_maps=True
    )

    print(f"\nConfiguration:")
    print(f"  Map size: {config.size}x{config.size}")
    print(f"  Season: {config.season}")
    print(f"  Hour: {config.hour:02d}:00")
    print(f"  Output directory: {config.output_dir}")

    print_separator("Generating spatial maps...")

    # Create generator with seed for reproducibility
    generator = SpatialDataGenerator(config=config, seed=42)

    # Generate all maps
    maps = generator.generate()

    print("✓ All maps generated!")

    # Print summary statistics
    print_separator("Map Statistics")

    print(f"Terrain:")
    print(f"  Lowland: {np.sum(maps.terrain == 0)}")
    print(f"  Plain: {np.sum(maps.terrain == 1)}")
    print(f"  Hill: {np.sum(maps.terrain == 2)}")
    print(f"  Mountain: {np.sum(maps.terrain == 3)}")

    print(f"\nWater:")
    print(f"  Water area: {np.sum(maps.water == 1)}")

    print(f"\nVegetation:")
    print(f"  Grass: {np.sum(maps.vegetation == 1)}")
    print(f"  Shrub: {np.sum(maps.vegetation == 2)}")
    print(f"  Forest: {np.sum(maps.vegetation == 3)}")
    print(f"  Wetland: {np.sum(maps.vegetation == 4)}")

    print(f"\nRoads:")
    print(f"  Road pixels: {np.sum(maps.roads == 1)}")

    print(f"\nWaterholes:")
    print(f"  Waterhole pixels: {np.sum(maps.waterholes == 1)}")

    print(f"\nRisk Map:")
    print(f"  Min risk: {maps.risk_map.min():.4f}")
    print(f"  Max risk: {maps.risk_map.max():.4f}")
    print(f"  Mean risk: {maps.risk_map.mean():.4f}")

    high_risk = np.sum(maps.risk_map > 0.7)
    total_pixels = maps.risk_map.size
    print(f"  High risk pixels (>0.7): {high_risk} ({high_risk/total_pixels*100:.1f}%)")

    if config.save_maps:
        print_separator("Saved Maps")
        output_dir = config.output_dir
        if os.path.exists(output_dir):
            for filename in sorted(os.listdir(output_dir)):
                filepath = os.path.join(output_dir, filename)
                size = os.path.getsize(filepath)
                print(f"  {filename:<30} ({size:,} bytes)")

    print_separator("✓ SPATIAL DATA GENERATOR DEMO COMPLETE")
    print("\nUsage examples:")
    print("""
    from risk_model.data import SpatialDataGenerator, SpatialConfig

    # Create configuration
    config = SpatialConfig(
        size=120,
        season="rainy",
        hour=22,
        output_dir="maps",
        save_maps=True
    )

    # Create generator and generate maps
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    # Access individual maps
    print(maps.risk_map)           # Risk heatmap
    print(maps.terrain)             # Terrain map
    print(maps.animal_density)      # Animal density
    """)
    print("="*60 + "\n")


# Import numpy for statistics
import numpy as np

if __name__ == "__main__":
    main()
