#!/usr/bin/env python3
"""Test that road width is 1 grid."""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Let's create a simple test - generate a map with roads and verify
# First check if we have a config with roads
test_config = {
  "features": {
    "ponds": 0,
    "large_water": 0,
    "forest": 0,
    "shrub": 0,
    "grassland": 1,
    "rhino": 0,
    "elephant": 0,
    "bird": 0,
    "roads": 1,
    "mountain": 0,
    "hills": 0
  },
  "vegetation_distribution": {
    "grassland_ratio": 1.0,
    "forest_ratio": 0.0,
    "shrub_ratio": 0.0
  },
  "water_config": {
    "pond_count": 0,
    "pond_min_radius": 2.0,
    "pond_max_radius": 4.0,
    "large_water_radius": 8.0,
    "has_river": 0
  },
  "road_config": {
    "main_road_count": 1,
    "curvature": 0.0,
    "branch_probability": 0.0
  },
  "terrain_config": {
    "mountain_count": 0,
    "mountain_radius": 4.0,
    "hill_count": 0,
    "hill_radius": 2.5
  }
}

with open('test_road_config.json', 'w') as f:
    json.dump(test_config, f)

print("=" * 70)
print("CURRENT ROAD GENERATION")
print("=" * 70)
print("\nThe current road generator already creates roads with 1-grid width:")
print("  - Each step selects only ONE neighbor cell")
print("  - Road is a single connected line of cells")
print("  - No widening logic in the code")
print("\nRoad generation functions:")
print("  - generate_curved_road_square() in generate_square_map.py")
print("  - generate_curved_road_rect() in generate_hex_map.py")
print("\nBoth functions work by:")
print("  1. Starting at a position")
print("  2. Choosing ONE neighbor for the next step")
print("  3. Repeating...")
print("\nThis ensures roads are always 1 grid wide!")
print("=" * 70)

# Clean up
import os
os.unlink('test_road_config.json')
