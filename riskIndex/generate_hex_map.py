#!/usr/bin/env python3
"""
Generate a hexagon grid map with curved roads.
"""

import sys
import os
import json
import random
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon, Patch
from matplotlib.collections import PatchCollection


# ============================================================================
# Hexagon Grid System
# ============================================================================

@dataclass
class HexCoord:
    """Axial coordinates for hexagon grid."""
    q: int  # column
    r: int  # row

    def to_tuple(self) -> Tuple[int, int]:
        return (self.q, self.r)

    def __eq__(self, other):
        return isinstance(other, HexCoord) and self.q == other.q and self.r == other.r

    def __hash__(self):
        return hash((self.q, self.r))

    def __add__(self, other):
        return HexCoord(self.q + other.q, self.r + other.r)


# Hexagon directions (axial coordinates)
HEX_DIRECTIONS = [
    HexCoord(1, 0),   # Right
    HexCoord(1, -1),  # Upper Right
    HexCoord(0, -1),  # Upper Left
    HexCoord(-1, 0),  # Left
    HexCoord(-1, 1),  # Lower Left
    HexCoord(0, 1),   # Lower Right
]


def hex_to_pixel(hex_coord: HexCoord, size: float = 1.0) -> Tuple[float, float]:
    """
    Convert axial hex coordinates to pixel coordinates.
    Uses "pointy-topped" hexagons.
    """
    q, r = hex_coord.q, hex_coord.r
    x = size * (3/2 * q)
    y = size * (math.sqrt(3)/2 * q + math.sqrt(3) * r)
    return (x, y)


def hex_neighbor(hex_coord: HexCoord, direction: int) -> HexCoord:
    """Get neighbor in given direction (0-5)."""
    return hex_coord + HEX_DIRECTIONS[direction % 6]


def hex_all_neighbors(hex_coord: HexCoord) -> List[HexCoord]:
    """Get all 6 neighbors of a hexagon."""
    return [hex_coord + d for d in HEX_DIRECTIONS]


def hex_distance(a: HexCoord, b: HexCoord) -> int:
    """Calculate distance between two hexagons in hex steps."""
    return (abs(a.q - b.q) + abs(a.q + a.r - b.q - b.r) + abs(a.r - b.r)) // 2


def generate_hex_grid(map_radius: int = 15) -> List[HexCoord]:
    """
    Generate a hexagon grid of given radius.
    Returns list of HexCoord in axial coordinates.
    """
    hexes = []
    for q in range(-map_radius, map_radius + 1):
        r1 = max(-map_radius, -q - map_radius)
        r2 = min(map_radius, -q + map_radius)
        for r in range(r1, r2 + 1):
            hexes.append(HexCoord(q, r))
    return hexes


# ============================================================================
# Curved Road Generation
# ============================================================================

def generate_curved_road(
    start_hex: HexCoord,
    direction: int,
    length: int,
    curvature: float = 0.3,
    branch_prob: float = 0.15
) -> List[List[HexCoord]]:
    """
    Generate a curved road starting from start_hex.
    Uses a random walk with momentum.
    Returns list of roads (main road + branches).
    """
    roads = []
    main_road = [start_hex]
    current_dir = direction
    current = start_hex

    for _ in range(length):
        # Randomly change direction with some probability
        if random.random() < curvature:
            turn = random.choice([-1, 1])  # left or right turn
            current_dir = (current_dir + turn) % 6
        elif random.random() < curvature * 0.3:
            # Occasionally turn more sharply
            turn = random.choice([-2, 2])
            current_dir = (current_dir + turn) % 6

        # Move to next hex
        next_hex = hex_neighbor(current, current_dir)
        main_road.append(next_hex)
        current = next_hex

    roads.append(main_road)

    # Generate branches
    for i in range(1, len(main_road) - 1):
        if random.random() < branch_prob:
            branch_point = main_road[i]
            # Choose a direction not along the main road
            main_dir_prev = None
            main_dir_next = None
            for d in range(6):
                if hex_neighbor(branch_point, d) == main_road[i-1]:
                    main_dir_prev = d
                if hex_neighbor(branch_point, d) == main_road[i+1]:
                    main_dir_next = d

            # Choose perpendicular direction
            possible_dirs = []
            for d in range(6):
                if d != main_dir_prev and d != main_dir_next:
                    possible_dirs.append(d)

            if possible_dirs:
                branch_dir = random.choice(possible_dirs)
                branch_length = random.randint(3, 10)
                branch_road = [branch_point]
                current_branch = branch_point
                current_branch_dir = branch_dir

                for _ in range(branch_length):
                    if random.random() < curvature * 0.5:
                        turn = random.choice([-1, 1])
                        current_branch_dir = (current_branch_dir + turn) % 6
                    next_branch = hex_neighbor(current_branch, current_branch_dir)
                    branch_road.append(next_branch)
                    current_branch = next_branch

                roads.append(branch_road)

    return roads


# ============================================================================
# Map Generation
# ============================================================================

def generate_hex_map_data(
    map_radius: int = 15,
    output_json: str = "hex_map_data.json"
):
    """Generate hexagon map data."""
    print(f"Generating hex grid with radius {map_radius}...")
    hex_coords = generate_hex_grid(map_radius)
    hex_set = set(hex_coords)
    print(f"  Total hexagons: {len(hex_coords)}")

    # Find center hex
    center = HexCoord(0, 0)

    # Generate main roads
    print("Generating curved roads...")
    all_road_hexes = set()
    road_paths = []

    # Main road 1: starts from left, goes towards right with curve
    start1 = HexCoord(-map_radius + 2, 0)
    roads1 = generate_curved_road(start1, 0, length=map_radius * 2 - 4, curvature=0.25, branch_prob=0.12)
    for road in roads1:
        road_paths.append(road)
        for h in road:
            if h in hex_set:
                all_road_hexes.add(h)

    # Main road 2: starts from bottom-left, goes towards top-right
    start2 = HexCoord(-map_radius + 3, map_radius - 3)
    roads2 = generate_curved_road(start2, 2, length=map_radius * 2 - 6, curvature=0.3, branch_prob=0.15)
    for road in roads2:
        road_paths.append(road)
        for h in road:
            if h in hex_set:
                all_road_hexes.add(h)

    # Main road 3: starts from top, goes towards bottom
    start3 = HexCoord(0, -map_radius + 2)
    roads3 = generate_curved_road(start3, 5, length=map_radius * 2 - 4, curvature=0.28, branch_prob=0.1)
    for road in roads3:
        road_paths.append(road)
        for h in road:
            if h in hex_set:
                all_road_hexes.add(h)

    print(f"  Road hexagons: {len(all_road_hexes)}")

    # Generate water sources (ponds and lakes)
    print("Generating water sources...")
    all_water_hexes = set()

    # Pond 1
    pond1_center = HexCoord(-7, 5)
    pond1_radius = 3
    for h in hex_coords:
        if hex_distance(h, pond1_center) <= pond1_radius:
            all_water_hexes.add(h)

    # Pond 2
    pond2_center = HexCoord(8, -3)
    pond2_radius = 4
    for h in hex_coords:
        if hex_distance(h, pond2_center) <= pond2_radius:
            all_water_hexes.add(h)

    # Pond 3
    pond3_center = HexCoord(-2, -8)
    pond3_radius = 2
    for h in hex_coords:
        if hex_distance(h, pond3_center) <= pond3_radius:
            all_water_hexes.add(h)

    # River - winding path
    river_hexes = []
    river_current = HexCoord(map_radius - 2, -map_radius + 2)
    river_dir = 4  # lower left
    for _ in range(map_radius * 2 - 4):
        river_hexes.append(river_current)
        all_water_hexes.add(river_current)
        # Winding direction changes
        if random.random() < 0.35:
            river_dir = (river_dir + random.choice([-1, 0, 1])) % 6
        river_current = hex_neighbor(river_current, river_dir)
        if river_current not in hex_set:
            break

    print(f"  Water hexagons: {len(all_water_hexes)}")

    # Generate grid data for each hex
    print("Generating grid data...")
    grids = []
    hex_size = 1.0

    for idx, hex_coord in enumerate(hex_coords):
        # Grid ID
        grid_id = f"H{idx:04d}"

        # Calculate distances to features
        dist_to_road = float('inf')
        for road_hex in all_road_hexes:
            dist = hex_distance(hex_coord, road_hex)
            if dist < dist_to_road:
                dist_to_road = dist

        dist_to_water = float('inf')
        for water_hex in all_water_hexes:
            dist = hex_distance(hex_coord, water_hex)
            if dist < dist_to_water:
                dist_to_water = dist

        # Distance to boundary (edge of map)
        dist_to_boundary = map_radius - max(abs(hex_coord.q), abs(hex_coord.r), abs(hex_coord.q + hex_coord.r))

        # Fire risk: higher away from water, near top-right
        water_factor = min(1.0, dist_to_water / 8.0)
        pos_factor = (hex_coord.q + map_radius) / (2 * map_radius) * 0.5 + \
                     (-hex_coord.r + map_radius) / (2 * map_radius) * 0.5
        fire_risk = 0.1 + 0.7 * water_factor * pos_factor + random.uniform(-0.1, 0.1)
        fire_risk = min(1.0, max(0.0, fire_risk))

        # Terrain complexity: more complex near center
        center_dist = hex_distance(hex_coord, center)
        terrain_complexity = 0.2 + 0.6 * (1.0 - min(1.0, center_dist / (map_radius * 0.7)))
        terrain_complexity = min(1.0, max(0.0, terrain_complexity + random.uniform(-0.1, 0.1)))

        # Vegetation type
        veg_random = random.random()
        if veg_random < 0.35:
            vegetation_type = "GRASSLAND"
        elif veg_random < 0.75:
            vegetation_type = "FOREST"
        else:
            vegetation_type = "SHRUB"

        # Species densities: higher near water
        water_attraction = max(0.0, 1.0 - dist_to_water / 6.0)
        rhino_density = 0.05 + 0.85 * water_attraction * random.uniform(0.5, 1.0)
        elephant_density = 0.1 + 0.75 * water_attraction * random.uniform(0.5, 1.0)
        bird_density = 0.2 + 0.6 * random.uniform(0.5, 1.0)

        species_densities = {
            "rhino": min(1.0, rhino_density),
            "elephant": min(1.0, elephant_density),
            "bird": min(1.0, bird_density)
        }

        # Store axial coordinates as x=q, y=r for the wrapper
        grids.append({
            "grid_id": grid_id,
            "x": hex_coord.q,  # using q as x
            "y": hex_coord.r,  # using r as y
            "fire_risk": fire_risk,
            "terrain_complexity": terrain_complexity,
            "vegetation_type": vegetation_type,
            "species_densities": species_densities
        })

    # Create map_config with features
    # Note: For the wrapper, we'll use a rectangular grid representation
    # but the visualization will show hexagons
    road_locations = [[h.q, h.r] for h in all_road_hexes]
    water_locations = [[h.q, h.r] for h in all_water_hexes]

    # Calculate bounds for rectangular representation
    min_q = min(h.q for h in hex_coords)
    max_q = max(h.q for h in hex_coords)
    min_r = min(h.r for h in hex_coords)
    max_r = max(h.r for h in hex_coords)
    map_width = max_q - min_q + 1
    map_height = max_r - min_r + 1

    data = {
        "map_config": {
            "map_width": map_width,
            "map_height": map_height,
            "boundary_type": "HEXAGON",
            "hex_radius": map_radius,
            "road_locations": road_locations,
            "water_locations": water_locations
        },
        "hex_coords": [[h.q, h.r] for h in hex_coords],
        "grids": grids,
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated hex map data saved to: {output_json}")
    print(f"  Hexagon radius: {map_radius}")
    print(f"  Total hexagons: {len(hex_coords)}")
    print(f"  Road hexagons: {len(road_locations)}")
    print(f"  Water hexagons: {len(water_locations)}")

    return data, hex_coords, all_road_hexes, all_water_hexes


# ============================================================================
# Visualization
# ============================================================================

def visualize_hex_map(
    data: dict,
    hex_coords: List[HexCoord],
    road_hexes: set,
    water_hexes: set,
    output_path: str = "hex_map_features.jpg"
):
    """Visualize hexagon map features."""
    hex_size = 1.0

    fig, ax = plt.subplots(figsize=(16, 14), dpi=100)

    patches = []
    colors = []

    for hex_coord in hex_coords:
        x, y = hex_to_pixel(hex_coord, hex_size)

        # Determine color
        if hex_coord in water_hexes:
            color = [0.3, 0.6, 1.0]  # Blue - water
        elif hex_coord in road_hexes:
            if hex_coord in water_hexes:
                color = [0.5, 0.35, 0.2]  # Dark brown - bridge
            else:
                color = [0.7, 0.55, 0.4]  # Brown - road
        else:
            color = [0.92, 0.95, 0.90]  # Light background

        # Create hexagon patch
        hex_patch = RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_size * 0.95,
            orientation=math.pi/2,  # pointy-topped
            facecolor=color,
            edgecolor=[0.7, 0.7, 0.7],
            linewidth=0.5
        )
        patches.append(hex_patch)

    # Add all patches
    collection = PatchCollection(patches, match_original=True)
    ax.add_collection(collection)

    # Add legend
    legend_elements = [
        Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'),
        Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'),
        Patch(facecolor=[0.92, 0.95, 0.90], edgecolor='gray', label='Land'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    # Set limits and aspect
    ax.set_aspect('equal')
    all_x, all_y = zip(*[hex_to_pixel(h, hex_size) for h in hex_coords])
    ax.set_xlim(min(all_x) - 2, max(all_x) + 2)
    ax.set_ylim(min(all_y) - 2, max(all_y) + 2)

    ax.set_title(f"Hexagon Grid Map (Radius = {data['map_config']['hex_radius']})\n{len(hex_coords)} Hexagons", fontsize=16, pad=20)
    ax.set_xlabel("Axial Q Coordinate", fontsize=12)
    ax.set_ylabel("Axial R Coordinate", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Hex map features saved to: {output_path}")
    plt.close(fig)


def main():
    """Main function."""
    print("="*70)
    print("  HEXAGON MAP GENERATOR")
    print("="*70)

    # Generate data
    print("\n[1/2] Generating hex map data...")
    data, hex_coords, road_hexes, water_hexes = generate_hex_map_data(
        map_radius=15,
        output_json="hex_map_data.json"
    )

    # Visualize
    print("\n[2/2] Visualizing hex map...")
    visualize_hex_map(data, hex_coords, road_hexes, water_hexes, "hex_map_features.jpg")

    print("\n" + "="*70)
    print("  COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - hex_map_data.json (hexagon map data)")
    print("  - hex_map_features.jpg (hexagon map visualization)")


if __name__ == "__main__":
    main()
