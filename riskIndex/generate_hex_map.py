#!/usr/bin/env python3
"""
Generate a hexagon grid map with rectangular boundary and risk heatmap.
"""

import sys
import os
import json
import random
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Set

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon, Patch
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap

from risk_model.core import Grid, SpeciesDensity, Season, Environment, VegetationType, TimeContext
from risk_model.risk import RiskModel, CompositeRiskCalculator, HumanRiskCalculator, EnvironmentalRiskCalculator
from risk_model.config import WeightManager


# ============================================================================
# Hexagon Grid System (Offset Coordinates for Rectangular Grid)
# ============================================================================

@dataclass
class HexCoord:
    """
    Offset coordinates for hexagon grid with rectangular boundary.
    Uses "even-q" offset coordinates for pointy-topped hexagons.
    """
    col: int  # column (x)
    row: int  # row (y)

    def to_tuple(self) -> Tuple[int, int]:
        return (self.col, self.row)

    def __eq__(self, other):
        return isinstance(other, HexCoord) and self.col == other.col and self.row == other.row

    def __hash__(self):
        return hash((self.col, self.row))


def hex_to_pixel_offset(hex_coord: HexCoord, size: float = 1.0) -> Tuple[float, float]:
    """
    Convert offset hex coordinates to pixel coordinates.
    Uses "even-q" offset coordinates for pointy-topped hexagons in rectangular grid.
    """
    col, row = hex_coord.col, hex_coord.row

    # Even-q offset coordinates to pixel
    x = size * (3/2 * col)
    y = size * (math.sqrt(3) * (row + 0.5 * (col % 2)))

    return (x, y)


def generate_rectangular_hex_grid(num_cols: int = 20, num_rows: int = 15) -> List[HexCoord]:
    """
    Generate a rectangular hexagon grid using even-q offset coordinates.

    Args:
        num_cols: Number of columns
        num_rows: Number of rows

    Returns:
        List of HexCoord in offset coordinates
    """
    hexes = []
    for col in range(num_cols):
        for row in range(num_rows):
            hexes.append(HexCoord(col=col, row=row))
    return hexes


def get_hex_neighbors_offset(hex_coord: HexCoord, num_cols: int, num_rows: int) -> List[HexCoord]:
    """
    Get all neighbors of a hexagon in even-q offset coordinates.
    """
    col, row = hex_coord.col, hex_coord.row

    # Neighbor patterns depend on whether column is even or odd
    if col % 2 == 0:
        # Even column
        neighbors = [
            HexCoord(col + 1, row),      # East
            HexCoord(col + 1, row - 1),  # Northeast
            HexCoord(col, row - 1),      # Northwest
            HexCoord(col - 1, row),      # West
            HexCoord(col, row + 1),      # Southwest
            HexCoord(col + 1, row + 1),  # Southeast
        ]
    else:
        # Odd column
        neighbors = [
            HexCoord(col + 1, row + 1),  # East
            HexCoord(col + 1, row),      # Northeast
            HexCoord(col, row - 1),      # Northwest
            HexCoord(col - 1, row),      # West
            HexCoord(col - 1, row + 1),  # Southwest
            HexCoord(col, row + 1),      # Southeast
        ]

    # Filter out neighbors outside the grid
    valid_neighbors = []
    for n in neighbors:
        if 0 <= n.col < num_cols and 0 <= n.row < num_rows:
            valid_neighbors.append(n)

    return valid_neighbors


def hex_distance_offset(a: HexCoord, b: HexCoord) -> float:
    """
    Calculate approximate distance between two hexagons in offset coordinates.
    Uses pixel distance for accuracy.
    """
    xa, ya = hex_to_pixel_offset(a, 1.0)
    xb, yb = hex_to_pixel_offset(b, 1.0)
    return math.sqrt((xa - xb) ** 2 + (ya - yb) ** 2)


# ============================================================================
# Curved Road Generation
# ============================================================================

def generate_curved_road_rect(
    start_hex: HexCoord,
    num_cols: int,
    num_rows: int,
    length: int,
    curvature: float = 0.3,
    branch_prob: float = 0.15
) -> List[List[HexCoord]]:
    """
    Generate a curved road on rectangular hex grid.
    """
    roads = []
    main_road = [start_hex]
    current = start_hex

    # Directions: 0=East, 1=Northeast, 2=Northwest, 3=West, 4=Southwest, 5=Southeast
    current_dir = 0  # Start going east

    for _ in range(length):
        # Get neighbors
        neighbors = get_hex_neighbors_offset(current, num_cols, num_rows)

        if not neighbors:
            break

        # Randomly change direction with some probability
        if random.random() < curvature and len(main_road) > 2:
            # Choose a random neighbor not backtracking
            prev_hex = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_hex]
            if possible_next:
                next_hex = random.choice(possible_next)
            else:
                next_hex = random.choice(neighbors)
        else:
            # Continue in similar direction - pick neighbor closest to current direction
            # For simplicity, just pick random neighbor with some momentum
            prev_hex = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_hex]
            if possible_next:
                # Prefer neighbors that move generally right/left
                if random.random() < 0.7:
                    # Prefer horizontal-ish movement
                    rightish = [n for n in possible_next if n.col > current.col]
                    leftish = [n for n in possible_next if n.col < current.col]
                    if rightish:
                        next_hex = random.choice(rightish)
                    elif leftish:
                        next_hex = random.choice(leftish)
                    else:
                        next_hex = random.choice(possible_next)
                else:
                    next_hex = random.choice(possible_next)
            else:
                next_hex = random.choice(neighbors)

        main_road.append(next_hex)
        current = next_hex

    roads.append(main_road)

    # Generate branches
    for i in range(3, len(main_road) - 3):
        if random.random() < branch_prob:
            branch_point = main_road[i]
            neighbors = get_hex_neighbors_offset(branch_point, num_cols, num_rows)

            # Find a direction not on the main road
            main_road_set = set(main_road)
            possible_starts = [n for n in neighbors if n not in main_road_set]

            if possible_starts:
                branch_start = random.choice(possible_starts)
                branch_length = random.randint(4, 10)
                branch_road = [branch_point, branch_start]
                current_branch = branch_start

                for _ in range(branch_length):
                    branch_neighbors = get_hex_neighbors_offset(current_branch, num_cols, num_cols)
                    # Avoid going back to main road too quickly
                    branch_road_set = set(branch_road)
                    possible_next = [n for n in branch_neighbors if n not in branch_road_set]
                    if possible_next:
                        next_branch = random.choice(possible_next)
                        branch_road.append(next_branch)
                        current_branch = next_branch
                    else:
                        break

                roads.append(branch_road)

    return roads


# ============================================================================
# Distance Calculator for Rectangular Hex Grid
# ============================================================================

@dataclass
class RectHexMapConfig:
    """Map configuration for rectangular hex grid."""
    num_cols: int
    num_rows: int
    hex_coords: List[HexCoord]
    road_hexes: Set[HexCoord]
    water_hexes: Set[HexCoord]


class RectHexDistanceCalculator:
    """Calculate distances using rectangular hex grid coordinates."""

    def __init__(self, map_config: RectHexMapConfig):
        self.num_cols = map_config.num_cols
        self.num_rows = map_config.num_rows
        self.hex_coords = map_config.hex_coords
        self.road_hexes = map_config.road_hexes
        self.water_hexes = map_config.water_hexes
        self.hex_set = set(map_config.hex_coords)

    def calculate_distance_to_boundary(self, hex_coord: HexCoord) -> float:
        """Calculate normalized distance to nearest rectangular boundary."""
        # Distance to each edge
        dist_left = hex_coord.col
        dist_right = (self.num_cols - 1) - hex_coord.col
        dist_bottom = hex_coord.row
        dist_top = (self.num_rows - 1) - hex_coord.row

        min_dist = min(dist_left, dist_right, dist_bottom, dist_top)
        max_possible = max(self.num_cols, self.num_rows) / 2
        normalized_dist = min_dist / max_possible if max_possible > 0 else 0.0

        # Invert: closer to boundary = higher risk
        return 1.0 - min(normalized_dist, 1.0)

    def calculate_distance_to_feature(self, hex_coord: HexCoord, feature_set: Set[HexCoord]) -> float:
        """Calculate normalized distance to nearest feature set."""
        if not feature_set:
            return 0.5

        min_dist = float('inf')
        for feature_hex in feature_set:
            dist = hex_distance_offset(hex_coord, feature_hex)
            if dist < min_dist:
                min_dist = dist
                if min_dist == 0:
                    break

        # Normalize to [0, 1]
        max_possible = math.sqrt(self.num_cols ** 2 + self.num_rows ** 2) * math.sqrt(3)
        normalized_dist = min_dist / max_possible if max_possible > 0 else 0.0

        # Invert: closer to feature = higher risk
        return 1.0 - min(normalized_dist, 1.0)

    def calculate_distances(self, hex_coord: HexCoord) -> Tuple[float, float, float]:
        """Calculate all three distances for a hex cell."""
        dist_boundary = self.calculate_distance_to_boundary(hex_coord)
        dist_road = self.calculate_distance_to_feature(hex_coord, self.road_hexes)
        dist_water = self.calculate_distance_to_feature(hex_coord, self.water_hexes)
        return dist_boundary, dist_road, dist_water


# ============================================================================
# Map Generation
# ============================================================================

def generate_rectangular_hex_map_data(
    num_cols: int = 25,
    num_rows: int = 18,
    output_json: str = "rect_hex_map_data.json"
):
    """Generate rectangular hexagon map data."""
    print(f"Generating rectangular hex grid: {num_cols} cols x {num_rows} rows...")
    hex_coords = generate_rectangular_hex_grid(num_cols, num_rows)
    hex_set = set(hex_coords)
    print(f"  Total hexagons: {len(hex_coords)}")

    # Generate main roads
    print("Generating curved roads...")
    all_road_hexes = set()
    road_paths = []

    # Main road 1: starts from left, goes towards right
    start1 = HexCoord(col=0, row=num_rows // 2)
    roads1 = generate_curved_road_rect(start1, num_cols, num_rows, length=num_cols * 2, curvature=0.35, branch_prob=0.12)
    for road in roads1:
        road_paths.append(road)
        for h in road:
            if h in hex_set:
                all_road_hexes.add(h)

    # Main road 2: starts from bottom-left, goes towards top-right
    start2 = HexCoord(col=2, row=2)
    roads2 = generate_curved_road_rect(start2, num_cols, num_rows, length=int(num_cols * 1.5), curvature=0.32, branch_prob=0.15)
    for road in roads2:
        road_paths.append(road)
        for h in road:
            if h in hex_set:
                all_road_hexes.add(h)

    # Main road 3: starts from top, goes towards bottom
    start3 = HexCoord(col=num_cols // 2, row=0)
    roads3 = generate_curved_road_rect(start3, num_cols, num_rows, length=num_rows * 2, curvature=0.38, branch_prob=0.1)
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
    pond1_center = HexCoord(col=num_cols // 4, row=num_rows // 3)
    pond1_radius_pix = 3.5
    for h in hex_coords:
        if hex_distance_offset(h, pond1_center) <= pond1_radius_pix:
            all_water_hexes.add(h)

    # Pond 2
    pond2_center = HexCoord(col=num_cols * 3 // 4, row=num_rows * 2 // 3)
    pond2_radius_pix = 4.0
    for h in hex_coords:
        if hex_distance_offset(h, pond2_center) <= pond2_radius_pix:
            all_water_hexes.add(h)

    # Pond 3
    pond3_center = HexCoord(col=num_cols // 2, row=num_rows // 2)
    pond3_radius_pix = 2.5
    for h in hex_coords:
        if hex_distance_offset(h, pond3_center) <= pond3_radius_pix:
            all_water_hexes.add(h)

    # River - winding path from right to left
    river_hexes = []
    river_current = HexCoord(col=num_cols - 1, row=num_rows - 2)
    river_hexes.append(river_current)
    all_water_hexes.add(river_current)

    for _ in range(num_cols * 2):
        # Move generally leftward with some randomness
        neighbors = get_hex_neighbors_offset(river_current, num_cols, num_rows)
        river_so_far = set(river_hexes)

        # Prefer left-moving neighbors
        leftish = [n for n in neighbors if n.col < river_current.col and n not in river_so_far]
        other = [n for n in neighbors if n not in river_so_far and n not in leftish]

        if leftish and random.random() < 0.7:
            next_river = random.choice(leftish)
        elif other:
            next_river = random.choice(other)
        else:
            break

        river_hexes.append(next_river)
        all_water_hexes.add(next_river)
        river_current = next_river

    print(f"  Water hexagons: {len(all_water_hexes)}")

    # Generate grid data for each hex
    print("Generating grid data...")
    grids = []

    for idx, hex_coord in enumerate(hex_coords):
        # Grid ID
        grid_id = f"H{idx:04d}"

        # Fire risk: higher away from water, near top-right
        dist_to_water = float('inf')
        for water_hex in all_water_hexes:
            dist = hex_distance_offset(hex_coord, water_hex)
            if dist < dist_to_water:
                dist_to_water = dist

        water_factor = min(1.0, dist_to_water / 10.0)
        pos_factor = (hex_coord.col / num_cols) * 0.5 + ((num_rows - hex_coord.row) / num_rows) * 0.5
        fire_risk = 0.1 + 0.7 * water_factor * pos_factor + random.uniform(-0.1, 0.1)
        fire_risk = min(1.0, max(0.0, fire_risk))

        # Terrain complexity: more complex near center
        center_dist = hex_distance_offset(hex_coord, HexCoord(col=num_cols//2, row=num_rows//2))
        max_center_dist = math.sqrt(num_cols**2 + num_rows**2) * math.sqrt(3) / 2
        terrain_complexity = 0.2 + 0.6 * (1.0 - min(1.0, center_dist / max_center_dist))
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
        water_attraction = max(0.0, 1.0 - dist_to_water / 8.0)
        rhino_density = 0.05 + 0.85 * water_attraction * random.uniform(0.5, 1.0)
        elephant_density = 0.1 + 0.75 * water_attraction * random.uniform(0.5, 1.0)
        bird_density = 0.2 + 0.6 * random.uniform(0.5, 1.0)

        species_densities = {
            "rhino": min(1.0, rhino_density),
            "elephant": min(1.0, elephant_density),
            "bird": min(1.0, bird_density)
        }

        grids.append({
            "grid_id": grid_id,
            "hex_col": hex_coord.col,
            "hex_row": hex_coord.row,
            "fire_risk": fire_risk,
            "terrain_complexity": terrain_complexity,
            "vegetation_type": vegetation_type,
            "species_densities": species_densities
        })

    # Create map_config
    road_locations = [[h.col, h.row] for h in all_road_hexes]
    water_locations = [[h.col, h.row] for h in all_water_hexes]

    data = {
        "map_config": {
            "num_cols": num_cols,
            "num_rows": num_rows,
            "boundary_type": "RECTANGULAR_HEX",
            "road_locations": road_locations,
            "water_locations": water_locations
        },
        "hex_coords": [[h.col, h.row] for h in hex_coords],
        "grids": grids,
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated rectangular hex map data saved to: {output_json}")
    print(f"  Grid size: {num_cols} cols x {num_rows} rows")
    print(f"  Total hexagons: {len(hex_coords)}")
    print(f"  Road hexagons: {len(road_locations)}")
    print(f"  Water hexagons: {len(water_locations)}")

    return data, hex_coords, all_road_hexes, all_water_hexes


# ============================================================================
# Visualization
# ============================================================================

def visualize_rect_hex_map(
    data: dict,
    hex_coords: List[HexCoord],
    road_hexes: Set[HexCoord],
    water_hexes: Set[HexCoord],
    output_path: str = "rect_hex_map_features.jpg"
):
    """Visualize rectangular hexagon map features."""
    hex_size = 1.0

    fig, ax = plt.subplots(figsize=(18, 14), dpi=100)

    patches = []

    for hex_coord in hex_coords:
        x, y = hex_to_pixel_offset(hex_coord, hex_size)

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

        # Create hexagon patch (pointy-topped)
        hex_patch = RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_size * 0.95,
            orientation=math.pi/2,  # pointy-topped
            facecolor=color,
            edgecolor=[0.7, 0.7, 0.7],
            linewidth=0
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
    all_x, all_y = zip(*[hex_to_pixel_offset(h, hex_size) for h in hex_coords])
    ax.set_xlim(min(all_x) - 2, max(all_x) + 2)
    ax.set_ylim(min(all_y) - 2, max(all_y) + 2)

    num_cols = data["map_config"]["num_cols"]
    num_rows = data["map_config"]["num_rows"]
    ax.set_title(f"Rectangular Hexagon Grid\n{num_cols} cols × {num_rows} rows = {len(hex_coords)} hexagons", fontsize=16, pad=20)
    ax.set_xlabel("Column", fontsize=12)
    ax.set_ylabel("Row", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Rectangular hex map features saved to: {output_path}")
    plt.close(fig)


def visualize_rect_risk_heatmap(
    data: dict,
    hex_coords: List[HexCoord],
    road_hexes: Set[HexCoord],
    water_hexes: Set[HexCoord],
    risk_results: List[Any],
    output_path: str = "rect_hex_risk_heatmap.jpg"
):
    """Visualize risk heatmap on rectangular hex grid."""
    hex_size = 1.0

    fig, ax = plt.subplots(figsize=(24, 18), dpi=100)

    # Create risk dictionary
    risk_dict = {}
    for idx, result in enumerate(risk_results):
        g_data = data["grids"][idx]
        hex_coord = HexCoord(col=g_data["hex_col"], row=g_data["hex_row"])
        risk_dict[hex_coord] = result.normalized_risk if result.normalized_risk is not None else 0.0

    # Custom colormap
    colors = [
        (0.0, '#00aa00'),   # Green - low risk
        (0.3, '#88cc00'),
        (0.5, '#ffff00'),   # Yellow - medium risk
        (0.7, '#ff8800'),
        (1.0, '#ff0000')    # Red - high risk
    ]
    cmap = LinearSegmentedColormap.from_list('risk_gradient', colors)

    patches = []
    text_items = []

    for hex_coord in hex_coords:
        x, y = hex_to_pixel_offset(hex_coord, hex_size)

        # Get risk value
        risk = risk_dict.get(hex_coord, 0.0)

        # Overlay with features
        if hex_coord in water_hexes:
            # Mix blue with risk color
            base_color = cmap(risk)
            water_color = (0.3, 0.6, 1.0, 1.0)
            facecolor = tuple(0.4 * water_color[i] + 0.6 * base_color[i] for i in range(3))
        elif hex_coord in road_hexes:
            # Mix brown with risk color
            base_color = cmap(risk)
            road_color = (0.7, 0.55, 0.4, 1.0)
            facecolor = tuple(0.4 * road_color[i] + 0.6 * base_color[i] for i in range(3))
        else:
            facecolor = cmap(risk)

        # Create hexagon patch
        hex_patch = RegularPolygon(
            (x, y),
            numVertices=6,
            radius=hex_size * 0.95,
            orientation=math.pi/2,
            facecolor=facecolor,
            edgecolor=[0.5, 0.5, 0.5],
            linewidth=0
        )
        patches.append(hex_patch)

        # Choose text color based on risk (black or white for contrast)
        if risk < 0.3 or risk > 0.7:
            text_color = 'white'
        else:
            text_color = 'black'

        # Add risk value text
        risk_text = f"{risk:.2f}"
        text_item = ax.text(
            x, y, risk_text,
            ha='center', va='center',
            color=text_color,
            fontsize=7,
            fontweight='bold'
        )
        text_items.append(text_item)

    # Add all patches
    collection = PatchCollection(patches, match_original=True)
    ax.add_collection(collection)

    # Add colorbar
    from matplotlib.cm import ScalarMappable
    sm = ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Normalized Risk', rotation=270, labelpad=20, fontsize=12)

    # Add legend for features
    legend_elements = [
        Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'),
        Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    # Set limits and aspect
    ax.set_aspect('equal')
    all_x, all_y = zip(*[hex_to_pixel_offset(h, hex_size) for h in hex_coords])
    ax.set_xlim(min(all_x) - 2, max(all_x) + 2)
    ax.set_ylim(min(all_y) - 2, max(all_y) + 2)

    num_cols = data["map_config"]["num_cols"]
    num_rows = data["map_config"]["num_rows"]
    ax.set_title(f"Risk Heatmap - Rectangular Hexagon Grid\n{num_cols} cols × {num_rows} rows = {len(hex_coords)} hexagons", fontsize=16, pad=20)
    ax.set_xlabel("Column", fontsize=12)
    ax.set_ylabel("Row", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Risk heatmap saved to: {output_path}")
    plt.close(fig)


# ============================================================================
# Risk Calculation
# ============================================================================

def calculate_risk_for_rect_hex_map(
    data: dict,
    hex_coords: List[HexCoord],
    road_hexes: Set[HexCoord],
    water_hexes: Set[HexCoord]
):
    """Calculate risk for rectangular hexagon map."""
    print("Calculating risk for rectangular hex grid...")

    map_config = RectHexMapConfig(
        num_cols=data["map_config"]["num_cols"],
        num_rows=data["map_config"]["num_rows"],
        hex_coords=hex_coords,
        road_hexes=road_hexes,
        water_hexes=water_hexes
    )

    distance_calculator = RectHexDistanceCalculator(map_config)

    # Create weight manager
    weight_manager = WeightManager()

    # Create calculators
    human_calc = HumanRiskCalculator()
    env_calc = EnvironmentalRiskCalculator()

    # Create composite calculator
    composite_calc = CompositeRiskCalculator(
        weight_manager=weight_manager,
        human_calculator=human_calc,
        environmental_calculator=env_calc
    )

    # Create risk model
    model = RiskModel(composite_calculator=composite_calc)

    # Convert data
    grid_data_list = []
    veg_type_map = {
        "GRASSLAND": VegetationType.GRASSLAND,
        "FOREST": VegetationType.FOREST,
        "SHRUB": VegetationType.SHRUB
    }

    for g_data in data["grids"]:
        hex_coord = HexCoord(col=g_data["hex_col"], row=g_data["hex_row"])

        # Calculate distances
        dist_boundary, dist_road, dist_water = distance_calculator.calculate_distances(hex_coord)

        # Create objects - use pixel coordinates for Grid
        x_pix, y_pix = hex_to_pixel_offset(hex_coord, 1.0)

        grid = Grid(
            grid_id=g_data["grid_id"],
            x=x_pix,
            y=y_pix,
            distance_to_boundary=dist_boundary,
            distance_to_road=dist_road,
            distance_to_water=dist_water
        )

        env = Environment(
            fire_risk=g_data["fire_risk"],
            terrain_complexity=g_data["terrain_complexity"],
            vegetation_type=veg_type_map.get(g_data["vegetation_type"], VegetationType.GRASSLAND)
        )

        density = SpeciesDensity(densities=g_data["species_densities"])

        grid_data_list.append((grid, env, density))

    # Time context
    time_data = data["time"]
    season_map = {"DRY": Season.DRY, "RAINY": Season.RAINY}
    time_context = TimeContext(
        hour_of_day=time_data["hour_of_day"],
        season=season_map.get(time_data["season"], Season.DRY)
    )

    # Calculate risk
    results = model.calculate_batch(grid_data_list, time_context)
    print("Risk calculation complete.")

    return results


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rectangular Hexagon Map Generator - Generate hex grid maps with risk heatmaps"
    )
    parser.add_argument(
        "--cols", "-c",
        type=int,
        default=15,
        help="Number of columns in hex grid (default: 15)"
    )
    parser.add_argument(
        "--rows", "-r",
        type=int,
        default=12,
        help="Number of rows in hex grid (default: 12)"
    )
    parser.add_argument(
        "--data", "-d",
        type=str,
        default="rect_hex_map_data.json",
        help="Output JSON data file path (default: rect_hex_map_data.json)"
    )
    parser.add_argument(
        "--map-image", "-m",
        type=str,
        default="rect_hex_map_features.jpg",
        help="Output map features image path (default: rect_hex_map_features.jpg)"
    )
    parser.add_argument(
        "--heatmap", "-t",
        type=str,
        default="rect_hex_risk_heatmap.jpg",
        help="Output risk heatmap image path (default: rect_hex_risk_heatmap.jpg)"
    )

    args = parser.parse_args()

    print("="*70)
    print("  RECTANGULAR HEXAGON MAP GENERATOR")
    print("="*70)

    # Generate data
    print(f"\n[1/4] Generating rectangular hex map data: {args.cols} cols × {args.rows} rows...")
    data, hex_coords, road_hexes, water_hexes = generate_rectangular_hex_map_data(
        num_cols=args.cols,
        num_rows=args.rows,
        output_json=args.data
    )

    # Visualize map features
    print(f"\n[2/4] Visualizing rectangular hex map to: {args.map_image}")
    visualize_rect_hex_map(data, hex_coords, road_hexes, water_hexes, args.map_image)

    # Calculate risk
    print("\n[3/4] Calculating risk...")
    results = calculate_risk_for_rect_hex_map(data, hex_coords, road_hexes, water_hexes)

    # Visualize risk heatmap
    print(f"\n[4/4] Visualizing risk heatmap to: {args.heatmap}")
    visualize_rect_risk_heatmap(data, hex_coords, road_hexes, water_hexes, results, args.heatmap)

    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    norm_risks = [r.normalized_risk for r in results if r.normalized_risk is not None]
    if norm_risks:
        print(f"  Min risk: {min(norm_risks):.4f}")
        print(f"  Max risk: {max(norm_risks):.4f}")
        print(f"  Avg risk: {sum(norm_risks)/len(norm_risks):.4f}")
        high_risk = sum(1 for r in norm_risks if r > 0.7)
        print(f"  High risk cells (>0.7): {high_risk}/{len(norm_risks)}")
    print("="*70)
    print("\nGenerated files:")
    print("  - rect_hex_map_data.json (rectangular hex map data)")
    print("  - rect_hex_map_features.jpg (map visualization)")
    print("  - rect_hex_risk_heatmap.jpg (risk heatmap)")


if __name__ == "__main__":
    main()
