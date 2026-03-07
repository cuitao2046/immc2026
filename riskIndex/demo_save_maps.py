#!/usr/bin/env python3
"""
Demo: Save Generated Maps and Data.

This script demonstrates:
1. Generating realistic spatial maps
2. Saving JPG/PNG maps for each element (water, forest, etc.)
3. Saving raw data as NumPy arrays and CSV files
4. Generating risk index heatmap
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
    """Run the save maps demo."""
    print_header("SPATIAL DATA GENERATOR - SAVE MAPS AND DATA DEMO")

    # ========================================================================
    # Step 1: Configure and generate
    # ========================================================================
    print_header("STEP 1: Configuring and Generating")

    config = SpatialConfig(
        size=120,          # Full size map
        season="rainy",    # Rainy season
        hour=22,           # Night time
        output_dir="generated_maps",
        save_maps=True,
        save_data=True,
        map_format="jpg"   # Save as JPG
    )

    print(f"Configuration:")
    print(f"  Map size: {config.size}x{config.size}")
    print(f"  Season: {config.season}")
    print(f"  Hour: {config.hour:02d}:00")
    print(f"  Output directory: {config.output_dir}")
    print(f"  Save maps: {config.save_maps}")
    print(f"  Save data: {config.save_data}")
    print(f"  Map format: {config.map_format}")

    print("\nGenerating maps... (this may take a moment)")
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    print("✓ Generation complete!")

    # ========================================================================
    # Step 2: Print summary statistics
    # ========================================================================
    print_header("STEP 2: Summary Statistics")

    print(f"Terrain:")
    print(f"  Lowland: {np.sum(maps.terrain == 0)}")
    print(f"  Plain: {np.sum(maps.terrain == 1)}")
    print(f"  Hill: {np.sum(maps.terrain == 2)}")
    print(f"  Mountain: {np.sum(maps.terrain == 3)}")

    print(f"\nWater:")
    print(f"  Permanent water: {np.sum(maps.water == 1)}")
    print(f"  Waterholes: {np.sum(maps.waterholes == 1)}")

    print(f"\nVegetation:")
    print(f"  Grassland: {np.sum(maps.vegetation == 1)}")
    print(f"  Shrubland: {np.sum(maps.vegetation == 2)}")
    print(f"  Forest: {np.sum(maps.vegetation == 3)}")
    print(f"  Wetland: {np.sum(maps.vegetation == 4)}")

    print(f"\nRoads:")
    print(f"  Road pixels: {np.sum(maps.roads == 1)}")

    print(f"\nAnimal Density:")
    print(f"  Rhino: {maps.rhino.mean():.4f} (max: {maps.rhino.max():.4f})")
    print(f"  Elephant: {maps.elephant.mean():.4f} (max: {maps.elephant.max():.4f})")
    print(f"  Bird: {maps.bird.mean():.4f} (max: {maps.bird.max():.4f})")
    print(f"  Total: {maps.animal_density.mean():.4f} (max: {maps.animal_density.max():.4f})")

    print(f"\nFire Risk:")
    print(f"  Mean: {maps.fire_risk.mean():.4f}")
    print(f"  Max: {maps.fire_risk.max():.4f}")

    print(f"\nRisk Map:")
    print(f"  Min: {maps.risk_map.min():.4f}")
    print(f"  Max: {maps.risk_map.max():.4f}")
    print(f"  Mean: {maps.risk_map.mean():.4f}")
    print(f"  Std: {maps.risk_map.std():.4f}")

    high_risk = np.sum(maps.risk_map > 0.7)
    total_pixels = maps.risk_map.size
    print(f"  High risk pixels (>0.7): {high_risk} ({high_risk/total_pixels*100:.1f}%)")

    # ========================================================================
    # Step 3: List saved files
    # ========================================================================
    print_header("STEP 3: Saved Files")

    output_dir = config.output_dir
    if os.path.exists(output_dir):
        image_files = [f for f in sorted(os.listdir(output_dir))
                      if f.endswith('.jpg') or f.endswith('.png')]
        print(f"\nImage maps ({len(image_files)} files):")
        for f in image_files[:10]:  # Show first 10
            filepath = os.path.join(output_dir, f)
            size = os.path.getsize(filepath)
            print(f"  {f:<30} ({size:,} bytes)")
        if len(image_files) > 10:
            print(f"  ... and {len(image_files) - 10} more")

        data_dir = os.path.join(output_dir, "data")
        if os.path.exists(data_dir):
            data_files = sorted(os.listdir(data_dir))
            print(f"\nRaw data ({len(data_files)} files in 'data/'):")
            for f in data_files:
                filepath = os.path.join(data_dir, f)
                size = os.path.getsize(filepath)
                print(f"  {f:<30} ({size:,} bytes)")

        csv_dir = os.path.join(output_dir, "csv")
        if os.path.exists(csv_dir):
            csv_files = sorted(os.listdir(csv_dir))
            print(f"\nCSV files ({len(csv_files)} files in 'csv/'):")
            for f in csv_files:
                filepath = os.path.join(csv_dir, f)
                size = os.path.getsize(filepath)
                print(f"  {f:<30} ({size:,} bytes)")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("✓ DEMO COMPLETE")

    print("\nGenerated files:")
    print("  ✓ JPG/PNG map files for each spatial element")
    print("  ✓ Separate maps for terrain types, vegetation types, etc.")
    print("  ✓ Raw NumPy arrays (.npy) for all data")
    print("  ✓ CSV files for easy viewing")
    print("  ✓ Risk index heatmap")
    print("  ✓ README.txt with full documentation")

    print("\nUsage in your code:")
    print("""
    from risk_model.data import SpatialDataGenerator, SpatialConfig

    # Configure
    config = SpatialConfig(
        size=120,
        season="rainy",
        hour=22,
        output_dir="my_maps",
        save_maps=True,    # Save JPG/PNG maps
        save_data=True,    # Save NumPy/CSV data
        map_format="jpg"   # Or "png" or "both"
    )

    # Generate and save
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    # Access data
    print(maps.risk_map)           # Risk index heatmap
    print(maps.terrain)             # Terrain map
    print(maps.vegetation)          # Vegetation map
    # ... and many more!
    """)

    print("="*70 + "\n")


if __name__ == "__main__":
    main()
