#!/usr/bin/env python3
"""
Generate a large 100x50 map and visualize it.
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
from matplotlib.patches import Rectangle, Circle, Patch

from risk_model.core import Grid, SpeciesDensity, Season, Environment, VegetationType, TimeContext
from risk_model.risk import RiskModel, CompositeRiskCalculator, HumanRiskCalculator, EnvironmentalRiskCalculator
from risk_model.config import WeightManager


# ============================================================================
# Distance Calculator (copied from wrapper to avoid import issues)
# ============================================================================

@dataclass
class MapConfig:
    """Map configuration for automatic distance calculation."""
    map_width: int  # Number of columns
    map_height: int  # Number of rows
    boundary_type: str  # "RECTANGLE"
    road_locations: List[Tuple[int, int]]  # List of (x, y) grid coordinates
    water_locations: List[Tuple[int, int]]  # List of (x, y) grid coordinates


class DistanceCalculator:
    """Calculate distances using grid coordinates."""

    def __init__(self, map_config: MapConfig):
        self.map_width = map_config.map_width
        self.map_height = map_config.map_height
        self.boundary_type = map_config.boundary_type
        self.road_locations = map_config.road_locations
        self.water_locations = map_config.water_locations

    def euclidean_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Calculate Euclidean distance between two grid cells."""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def calculate_distance_to_boundary(self, x: int, y: int) -> float:
        """
        Calculate distance to nearest boundary.
        Coordinate system: origin at bottom-left, x increases right, y increases up.
        """
        if self.boundary_type == "RECTANGLE":
            # Distance to each edge (in grid units)
            dist_left = x
            dist_right = (self.map_width - 1) - x
            dist_bottom = y
            dist_top = (self.map_height - 1) - y

            min_dist_grid = min(dist_left, dist_right, dist_bottom, dist_top)

            # Normalize to [0, 1]
            max_possible_dist = max(self.map_width, self.map_height) / 2
            normalized_dist = min_dist_grid / max_possible_dist if max_possible_dist > 0 else 0.0

            # Invert: closer to boundary = higher risk (0 = far, 1 = at boundary)
            return 1.0 - min(normalized_dist, 1.0)
        else:
            return 0.5

    def calculate_distance_to_feature(self, x: int, y: int, feature_locations: List[Tuple[int, int]]) -> float:
        """Calculate normalized distance to nearest feature (road or water)."""
        if not feature_locations:
            return 0.5

        min_dist = float('inf')
        for (fx, fy) in feature_locations:
            dist = self.euclidean_distance(x, y, fx, fy)
            if dist < min_dist:
                min_dist = dist

        # Normalize to [0, 1]
        max_possible_dist = math.sqrt(self.map_width ** 2 + self.map_height ** 2)
        normalized_dist = min_dist / max_possible_dist if max_possible_dist > 0 else 0.0

        # Invert: closer to feature = higher risk (0 = far, 1 = at feature)
        return 1.0 - min(normalized_dist, 1.0)

    def calculate_distances(self, x: int, y: int) -> Tuple[float, float, float]:
        """Calculate all three distances for a grid cell."""
        dist_boundary = self.calculate_distance_to_boundary(x, y)
        dist_road = self.calculate_distance_to_feature(x, y, self.road_locations)
        dist_water = self.calculate_distance_to_feature(x, y, self.water_locations)
        return dist_boundary, dist_road, dist_water


# ============================================================================
# Data Generation
# ============================================================================

def generate_large_map_data(
    map_width: int = 100,
    map_height: int = 50,
    output_json: str = "large_map_data.json"
):
    """
    Generate large map data for testing.

    Coordinate system:
    - Origin at bottom-left (0, 0)
    - x increases to the right
    - y increases upward
    """
    # Generate road locations (some linear features)
    road_locations = []
    # Horizontal roads
    for x in range(map_width):
        road_locations.append([x, 10])
        road_locations.append([x, 25])
        road_locations.append([x, 40])
    # Vertical roads
    for y in range(map_height):
        road_locations.append([25, y])
        road_locations.append([50, y])
        road_locations.append([75, y])

    # Generate water locations (ponds/lakes)
    water_locations = []
    # Pond 1
    center_x1, center_y1 = 20, 15
    radius1 = 5
    for x in range(map_width):
        for y in range(map_height):
            if (x - center_x1) ** 2 + (y - center_y1) ** 2 <= radius1 ** 2:
                water_locations.append([x, y])
    # Pond 2
    center_x2, center_y2 = 70, 35
    radius2 = 7
    for x in range(map_width):
        for y in range(map_height):
            if (x - center_x2) ** 2 + (y - center_y2) ** 2 <= radius2 ** 2:
                water_locations.append([x, y])
    # River
    for x in range(40, 60):
        y = int(20 + 5 * math.sin(x * 0.2))
        if 0 <= y < map_height:
            water_locations.append([x, y])
            if y + 1 < map_height:
                water_locations.append([x, y + 1])

    # Remove duplicates
    road_locations = list(set(tuple(loc) for loc in road_locations))
    water_locations = list(set(tuple(loc) for loc in water_locations))
    road_locations = [list(loc) for loc in road_locations]
    water_locations = [list(loc) for loc in water_locations]

    # Generate grids
    grids = []
    for y in range(map_height):
        for x in range(map_width):
            # Grid ID: row letter + column number
            row_letter = chr(ord('A') + (y % 26))
            col_num = x % 100
            grid_id = f"{row_letter}{col_num:02d}_{y}"

            # Fire risk: higher near top-right (drier area)
            fire_risk = 0.1 + 0.8 * (x / map_width) * (y / map_height)
            fire_risk = min(1.0, max(0.0, fire_risk + random.uniform(-0.1, 0.1)))

            # Terrain complexity: more complex in some regions
            terrain_complexity = 0.3 + 0.5 * abs(math.sin(x * 0.1) * math.cos(y * 0.15))
            terrain_complexity = min(1.0, max(0.0, terrain_complexity))

            # Vegetation type
            veg_random = random.random()
            if veg_random < 0.4:
                vegetation_type = "GRASSLAND"
            elif veg_random < 0.7:
                vegetation_type = "FOREST"
            else:
                vegetation_type = "SHRUB"

            # Species densities: higher near water
            dist_to_water = float('inf')
            for (wx, wy) in water_locations:
                dist = math.sqrt((x - wx) ** 2 + (y - wy) ** 2)
                if dist < dist_to_water:
                    dist_to_water = dist

            water_factor = max(0.0, 1.0 - dist_to_water / 20.0)
            rhino_density = 0.1 + 0.8 * water_factor * random.uniform(0.5, 1.0)
            elephant_density = 0.2 + 0.7 * water_factor * random.uniform(0.5, 1.0)
            bird_density = 0.3 + 0.6 * random.uniform(0.5, 1.0)

            species_densities = {
                "rhino": min(1.0, rhino_density),
                "elephant": min(1.0, elephant_density),
                "bird": min(1.0, bird_density)
            }

            grids.append({
                "grid_id": grid_id,
                "x": x,
                "y": y,
                "fire_risk": fire_risk,
                "terrain_complexity": terrain_complexity,
                "vegetation_type": vegetation_type,
                "species_densities": species_densities
            })

    # Create JSON structure
    data = {
        "map_config": {
            "map_width": map_width,
            "map_height": map_height,
            "boundary_type": "RECTANGLE",
            "road_locations": road_locations,
            "water_locations": water_locations
        },
        "grids": grids,
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    # Save to JSON
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated map data saved to: {output_json}")
    print(f"  Map size: {map_width} x {map_height}")
    print(f"  Grids: {len(grids)}")
    print(f"  Road locations: {len(road_locations)}")
    print(f"  Water locations: {len(water_locations)}")

    return data


def visualize_map_features(
    data: dict,
    output_path: str = "map_features.jpg"
):
    """Visualize map features (roads, water sources)."""
    map_width = data["map_config"]["map_width"]
    map_height = data["map_config"]["map_height"]
    road_locations = data["map_config"]["road_locations"]
    water_locations = data["map_config"]["water_locations"]

    # Create feature arrays
    road_array = np.zeros((map_height, map_width))
    water_array = np.zeros((map_height, map_width))

    for (x, y) in road_locations:
        if 0 <= x < map_width and 0 <= y < map_height:
            road_array[y, x] = 1

    for (x, y) in water_locations:
        if 0 <= x < map_width and 0 <= y < map_height:
            water_array[y, x] = 1

    # Create plot
    fig, ax = plt.subplots(figsize=(16, 10), dpi=100)

    # Create RGB image
    rgb = np.ones((map_height, map_width, 3)) * 0.95  # Light background

    # Water in blue
    for y in range(map_height):
        for x in range(map_width):
            if water_array[y, x] == 1:
                rgb[y, x] = [0.3, 0.6, 1.0]  # Blue

    # Roads in brown
    for y in range(map_height):
        for x in range(map_width):
            if road_array[y, x] == 1:
                if water_array[y, x] == 1:
                    rgb[y, x] = [0.5, 0.35, 0.2]  # Darker brown for bridges
                else:
                    rgb[y, x] = [0.7, 0.55, 0.4]  # Brown

    ax.imshow(rgb, origin='lower', aspect='equal')

    # Add legend patches
    legend_elements = [
        Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'),
        Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    ax.set_title(f"Map Features (100x50)\nOrigin at Bottom-Left", fontsize=16, pad=20)
    ax.set_xlabel("X (Column Index)", fontsize=12)
    ax.set_ylabel("Y (Row Index)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='-')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Map features visualization saved to: {output_path}")
    plt.close(fig)


def calculate_and_visualize_risk(
    data: dict,
    output_path: str = "risk_heatmap.jpg"
):
    """Calculate risk and visualize heatmap."""
    map_config = MapConfig(
        map_width=data["map_config"]["map_width"],
        map_height=data["map_config"]["map_height"],
        boundary_type=data["map_config"]["boundary_type"],
        road_locations=[tuple(loc) for loc in data["map_config"]["road_locations"]],
        water_locations=[tuple(loc) for loc in data["map_config"]["water_locations"]]
    )

    distance_calculator = DistanceCalculator(map_config)

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
        # Calculate distances
        dist_boundary, dist_road, dist_water = distance_calculator.calculate_distances(
            g_data["x"], g_data["y"]
        )

        # Create objects
        grid = Grid(
            grid_id=g_data["grid_id"],
            x=float(g_data["x"]),
            y=float(g_data["y"]),
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
    print("Calculating risk for all grids...")
    results = model.calculate_batch(grid_data_list, time_context)
    print("Risk calculation complete.")

    # Create risk grid for visualization
    map_width = data["map_config"]["map_width"]
    map_height = data["map_config"]["map_height"]
    risk_grid = np.zeros((map_height, map_width))

    for idx, result in enumerate(results):
        g_data = data["grids"][idx]
        x = g_data["x"]
        y = g_data["y"]
        if 0 <= x < map_width and 0 <= y < map_height:
            risk_grid[y, x] = result.normalized_risk if result.normalized_risk is not None else 0.0

    # Create visualization
    fig, ax = plt.subplots(figsize=(16, 10), dpi=100)

    # Custom colormap
    from matplotlib.colors import LinearSegmentedColormap
    colors = [
        (0.0, '#00aa00'),   # Green - low risk
        (0.3, '#88cc00'),
        (0.5, '#ffff00'),   # Yellow - medium risk
        (0.7, '#ff8800'),
        (1.0, '#ff0000')    # Red - high risk
    ]
    cmap = LinearSegmentedColormap.from_list('risk_gradient', colors)

    im = ax.imshow(risk_grid, cmap=cmap, vmin=0, vmax=1, origin='lower', aspect='equal')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Normalized Risk', rotation=270, labelpad=20, fontsize=12)

    ax.set_title(f"Risk Heatmap (100x50)\nOrigin at Bottom-Left", fontsize=16, pad=20)
    ax.set_xlabel("X (Column Index)", fontsize=12)
    ax.set_ylabel("Y (Row Index)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='-')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Risk heatmap saved to: {output_path}")
    plt.close(fig)

    return results


def main():
    """Main function."""
    print("="*70)
    print("  LARGE MAP GENERATOR (100x50)")
    print("="*70)

    # Step 1: Generate data
    print("\n[1/3] Generating map data...")
    data = generate_large_map_data(100, 50, "large_map_data.json")

    # Step 2: Visualize features
    print("\n[2/3] Visualizing map features...")
    visualize_map_features(data, "map_features.jpg")

    # Step 3: Calculate and visualize risk
    print("\n[3/3] Calculating risk and generating heatmap...")
    results = calculate_and_visualize_risk(data, "risk_heatmap.jpg")

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
    print("  - large_map_data.json (input data)")
    print("  - map_features.jpg (roads and water)")
    print("  - risk_heatmap.jpg (risk heatmap)")


if __name__ == "__main__":
    main()
