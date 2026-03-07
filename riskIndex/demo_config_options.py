#!/usr/bin/env python3
"""
Demo: Test All Configuration Options.

This script demonstrates how to use the extended configuration options
to customize the generated maps:
- Terrain thresholds
- Water body size
- Road count
- Waterhole density
- Species weights
- Fire risk levels
- Risk calculation weights
- Temporal factors
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


def test_dense_waterholes():
    """Test configuration with more waterholes."""
    print_header("TEST 1: Dense Waterholes")

    config = SpatialConfig(
        size=80,
        season="dry",
        hour=10,
        waterhole_probability=0.08,  # More waterholes
        waterhole_search_range=3,      # Wider search range
        output_dir="test_dense_waterholes",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  waterhole_probability: {config.waterhole_probability}")
    print(f"  waterhole_search_range: {config.waterhole_search_range}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    wh_count = np.sum(maps.waterholes == 1)
    print(f"\nResult:")
    print(f"  Waterhole count: {wh_count}")
    print(f"  Waterhole density: {wh_count / (config.size * config.size):.4f}")


def test_more_roads():
    """Test configuration with more roads."""
    print_header("TEST 2: More Roads")

    config = SpatialConfig(
        size=80,
        season="dry",
        hour=10,
        num_roads=8,  # More roads
        output_dir="test_more_roads",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  num_roads: {config.num_roads}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    road_count = np.sum(maps.roads == 1)
    print(f"\nResult:")
    print(f"  Road pixels: {road_count}")


def test_large_water_bodies():
    """Test configuration with larger water bodies."""
    print_header("TEST 3: Large Water Bodies")

    config = SpatialConfig(
        size=80,
        season="dry",
        hour=10,
        water_threshold=0.50,  # Lower threshold = more water
        output_dir="test_large_water",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  water_threshold: {config.water_threshold}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    water_count = np.sum(maps.water == 1)
    print(f"\nResult:")
    print(f"  Water pixels: {water_count}")
    print(f"  Water coverage: {water_count / (config.size * config.size) * 100:.1f}%")


def test_mountainous_terrain():
    """Test configuration with more mountains."""
    print_header("TEST 4: Mountainous Terrain")

    config = SpatialConfig(
        size=80,
        season="dry",
        hour=10,
        terrain_threshold_lowland=0.2,   # Less lowland
        terrain_threshold_plain=0.35,     # Less plain
        terrain_threshold_hill=0.5,       # Less hill = more mountain
        output_dir="test_mountainous",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  terrain_threshold_lowland: {config.terrain_threshold_lowland}")
    print(f"  terrain_threshold_plain: {config.terrain_threshold_plain}")
    print(f"  terrain_threshold_hill: {config.terrain_threshold_hill}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    mountain_count = np.sum(maps.terrain == 3)
    print(f"\nResult:")
    print(f"  Mountain pixels: {mountain_count}")
    print(f"  Mountain coverage: {mountain_count / (config.size * config.size) * 100:.1f}%")


def test_high_fire_risk():
    """Test configuration with higher fire risk."""
    print_header("TEST 5: High Fire Risk")

    config = SpatialConfig(
        size=80,
        season="dry",
        hour=10,
        fire_risk_by_vegetation=(0.95, 0.85, 0.75, 0.4),  # Higher fire risk
        output_dir="test_high_fire",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  fire_risk_by_vegetation: {config.fire_risk_by_vegetation}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    print(f"\nResult:")
    print(f"  Fire risk mean: {maps.fire_risk.mean():.4f}")
    print(f"  Fire risk max: {maps.fire_risk.max():.4f}")


def test_bird_focused():
    """Test configuration focused on birds."""
    print_header("TEST 6: Bird-Focused Conservation")

    config = SpatialConfig(
        size=80,
        season="rainy",
        hour=6,
        rhino_weight=0.2,
        elephant_weight=0.2,
        bird_weight=0.6,  # Birds have higher weight
        bird_season_multipliers=(2.0, 1.0),  # Birds much more active in rainy
        output_dir="test_bird_focused",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  rhino_weight: {config.rhino_weight}")
    print(f"  elephant_weight: {config.elephant_weight}")
    print(f"  bird_weight: {config.bird_weight}")
    print(f"  bird_season_multipliers: {config.bird_season_multipliers}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    print(f"\nResult:")
    print(f"  Bird density mean: {maps.bird.mean():.4f}")
    print(f"  Risk map mean: {maps.risk_map.mean():.4f}")


def test_custom_risk_weights():
    """Test configuration with custom risk weights."""
    print_header("TEST 7: Custom Risk Weights")

    config = SpatialConfig(
        size=80,
        season="rainy",
        hour=2,
        risk_weight_human=0.6,       # Emphasize human risk
        risk_weight_environmental=0.2,
        risk_weight_density=0.2,
        human_risk_weight_boundary=0.5,
        human_risk_weight_road=0.4,
        human_risk_weight_water=0.1,
        temporal_factor_night=1.5,    # Extra risk at night
        temporal_factor_rainy=1.4,    # Extra risk in rainy
        output_dir="test_custom_risk",
        save_maps=True,
        save_data=True
    )

    print(f"Configuration:")
    print(f"  risk_weight_human: {config.risk_weight_human}")
    print(f"  risk_weight_environmental: {config.risk_weight_environmental}")
    print(f"  risk_weight_density: {config.risk_weight_density}")
    print(f"  temporal_factor_night: {config.temporal_factor_night}")
    print(f"  temporal_factor_rainy: {config.temporal_factor_rainy}")

    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()

    high_risk = np.sum(maps.risk_map > 0.7)
    total = maps.risk_map.size
    print(f"\nResult:")
    print(f"  Risk mean: {maps.risk_map.mean():.4f}")
    print(f"  Risk max: {maps.risk_map.max():.4f}")
    print(f"  High risk pixels (>0.7): {high_risk} ({high_risk/total*100:.1f}%)")


def main():
    """Run all configuration option tests."""
    print_header("CONFIGURATION OPTIONS DEMO")
    print("\nThis script demonstrates all the configurable options available.")
    print("Each test creates a custom configuration and generates maps.")

    # Run all tests
    test_dense_waterholes()
    test_more_roads()
    test_large_water_bodies()
    test_mountainous_terrain()
    test_high_fire_risk()
    test_bird_focused()
    test_custom_risk_weights()

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("✓ ALL TESTS COMPLETE")

    print("\nAvailable Configuration Options:")
    print("\nBasic Settings:")
    print("  size, season, hour, output_dir, save_maps, save_data, map_format")

    print("\nTerrain Configuration:")
    print("  terrain_smooth_scale, terrain_threshold_lowland,")
    print("  terrain_threshold_plain, terrain_threshold_hill")

    print("\nWater Configuration:")
    print("  water_smooth_scale, water_threshold")

    print("\nRoad Configuration:")
    print("  num_roads")

    print("\nWaterhole Configuration:")
    print("  waterhole_probability, waterhole_search_range")

    print("\nAnimal Configuration:")
    print("  animal_smooth_scale, rhino_weight, elephant_weight, bird_weight")
    print("  rhino_season_multipliers, elephant_season_multipliers, bird_season_multipliers")

    print("\nFire Risk Configuration:")
    print("  fire_risk_by_vegetation (grass, shrub, forest, wetland)")

    print("\nRisk Calculation Weights:")
    print("  risk_weight_human, risk_weight_environmental, risk_weight_density")
    print("  human_risk_weight_boundary, human_risk_weight_road, human_risk_weight_water")
    print("  env_risk_weight_fire, env_risk_weight_terrain")

    print("\nTemporal Factors:")
    print("  temporal_factor_night, temporal_factor_day")
    print("  temporal_factor_rainy, temporal_factor_dry")

    print("\n" + "="*70)
    print("See config_example.json for a complete template with default values.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
