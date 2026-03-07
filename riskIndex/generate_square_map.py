#!/usr/bin/env python3
"""
Generate a square grid map with curved roads and water features.
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
from matplotlib.patches import Rectangle, Patch
from matplotlib.collections import PatchCollection


@dataclass
class SquareCoord:
    """Coordinates for square grid."""
    x: int  # column
    y: int  # row

    def to_tuple(self) -> Tuple[int, int]:
        return (self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, SquareCoord) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))


def square_to_pixel(coord: SquareCoord, size: float = 1.0) -> Tuple[float, float]:
    """Convert square grid coordinates to pixel coordinates."""
    return (coord.x * size, coord.y * size)


def generate_square_grid(num_cols: int = 20, num_rows: int = 15) -> List[SquareCoord]:
    """Generate a square grid."""
    squares = []
    for y in range(num_rows):
        for x in range(num_cols):
            squares.append(SquareCoord(x=x, y=y))
    return squares


def get_square_neighbors(coord: SquareCoord, num_cols: int, num_rows: int) -> List[SquareCoord]:
    """Get 8 neighbors of a square (including diagonals)."""
    x, y = coord.x, coord.y
    neighbors = []

    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < num_cols and 0 <= ny < num_rows:
                neighbors.append(SquareCoord(x=nx, y=ny))

    return neighbors


def get_square_neighbors_4way(coord: SquareCoord, num_cols: int, num_rows: int) -> List[SquareCoord]:
    """Get 4 neighbors of a square (up/down/left/right only)."""
    x, y = coord.x, coord.y
    neighbors = []

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # up, right, down, left

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < num_cols and 0 <= ny < num_rows:
            neighbors.append(SquareCoord(x=nx, y=ny))

    return neighbors


def square_distance(a: SquareCoord, b: SquareCoord) -> float:
    """Calculate Euclidean distance between two squares."""
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)


def generate_curved_road_square(
    start_coord: SquareCoord,
    num_cols: int,
    num_rows: int,
    length: int,
    curvature: float = 0.3,
    branch_prob: float = 0.15
) -> List[List[SquareCoord]]:
    """Generate a curved road on square grid."""
    roads = []
    main_road = [start_coord]
    current = start_coord

    # Directions: 0=up, 1=right, 2=down, 3=left
    current_dir = 1  # Start going right

    for _ in range(length):
        # Get 4-way neighbors
        neighbors = get_square_neighbors_4way(current, num_cols, num_rows)

        if not neighbors:
            break

        # Randomly change direction with some probability
        if random.random() < curvature and len(main_road) > 2:
            prev_coord = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_coord]
            if possible_next:
                next_coord = random.choice(possible_next)
            else:
                next_coord = random.choice(neighbors)
        else:
            # Continue in similar direction
            prev_coord = main_road[-2] if len(main_road) >= 2 else None
            possible_next = [n for n in neighbors if n != prev_coord]

            if possible_next and random.random() < 0.7:
                # Prefer direction that continues general trend
                if len(main_road) >= 3:
                    dx_trend = current.x - main_road[-3].x
                    dy_trend = current.y - main_road[-3].y

                    best = None
                    best_score = -float('inf')
                    for n in possible_next:
                        dx = n.x - current.x
                        dy = n.y - current.y
                        score = dx * dx_trend + dy * dy_trend
                        if score > best_score:
                            best_score = score
                            best = n
                    if best:
                        next_coord = best
                    else:
                        next_coord = random.choice(possible_next)
                else:
                    next_coord = random.choice(possible_next)
            elif possible_next:
                next_coord = random.choice(possible_next)
            else:
                next_coord = random.choice(neighbors)

        main_road.append(next_coord)
        current = next_coord

    roads.append(main_road)

    # Generate branches
    for i in range(3, len(main_road) - 3):
        if random.random() < branch_prob:
            branch_point = main_road[i]
            neighbors = get_square_neighbors_4way(branch_point, num_cols, num_rows)

            main_road_set = set(main_road)
            possible_starts = [n for n in neighbors if n not in main_road_set]

            if possible_starts:
                branch_start = random.choice(possible_starts)
                branch_length = random.randint(4, 10)
                branch_road = [branch_point, branch_start]
                current_branch = branch_start

                for _ in range(branch_length):
                    branch_neighbors = get_square_neighbors_4way(current_branch, num_cols, num_rows)
                    branch_road_set = set(branch_road)
                    possible_next = [n for n in branch_neighbors if n not in branch_road_set]

                    if possible_next:
                        # Avoid going back to main road too quickly
                        not_main = [n for n in possible_next if n not in main_road_set]
                        if not_main and random.random() < 0.8:
                            next_branch = random.choice(not_main)
                        else:
                            next_branch = random.choice(possible_next)

                        branch_road.append(next_branch)
                        current_branch = next_branch
                    else:
                        break

                roads.append(branch_road)

    return roads


def generate_square_map_data(
    num_cols: int = 30,
    num_rows: int = 20,
    output_json: str = "square_map_data.json"
):
    """Generate square grid map data."""
    print(f"Generating square grid: {num_cols} cols × {num_rows} rows...")
    coords = generate_square_grid(num_cols, num_rows)
    coord_set = set(coords)
    print(f"  Total squares: {len(coords)}")

    # Generate main roads
    print("Generating curved roads...")
    all_road_coords = set()
    road_paths = []

    # Main road 1: starts from left, goes towards right
    start1 = SquareCoord(x=0, y=num_rows // 2)
    roads1 = generate_curved_road_square(start1, num_cols, num_rows, length=num_cols * 2, curvature=0.35, branch_prob=0.12)
    for road in roads1:
        road_paths.append(road)
        for c in road:
            if c in coord_set:
                all_road_coords.add(c)

    # Main road 2: starts from bottom-left, goes towards top-right
    start2 = SquareCoord(x=2, y=2)
    roads2 = generate_curved_road_square(start2, num_cols, num_rows, length=int(num_cols * 1.5), curvature=0.32, branch_prob=0.15)
    for road in roads2:
        road_paths.append(road)
        for c in road:
            if c in coord_set:
                all_road_coords.add(c)

    # Main road 3: starts from top, goes towards bottom
    start3 = SquareCoord(x=num_cols // 2, y=0)
    roads3 = generate_curved_road_square(start3, num_cols, num_rows, length=num_rows * 2, curvature=0.38, branch_prob=0.1)
    for road in roads3:
        road_paths.append(road)
        for c in road:
            if c in coord_set:
                all_road_coords.add(c)

    print(f"  Road squares: {len(all_road_coords)}")

    # Generate water sources (ponds and lakes)
    print("Generating water sources...")
    all_water_coords = set()

    # Pond 1
    pond1_center = SquareCoord(x=num_cols // 4, y=num_rows // 3)
    pond1_radius = 3
    for c in coords:
        if square_distance(c, pond1_center) <= pond1_radius:
            all_water_coords.add(c)

    # Pond 2
    pond2_center = SquareCoord(x=num_cols * 3 // 4, y=num_rows * 2 // 3)
    pond2_radius = 3.5
    for c in coords:
        if square_distance(c, pond2_center) <= pond2_radius:
            all_water_coords.add(c)

    # Pond 3
    pond3_center = SquareCoord(x=num_cols // 2, y=num_rows // 2)
    pond3_radius = 2.5
    for c in coords:
        if square_distance(c, pond3_center) <= pond3_radius:
            all_water_coords.add(c)

    # River - winding path from right to left
    river_coords = []
    river_current = SquareCoord(x=num_cols - 1, y=num_rows - 2)
    river_coords.append(river_current)
    all_water_coords.add(river_current)

    for _ in range(num_cols * 2):
        neighbors = get_square_neighbors_4way(river_current, num_cols, num_rows)
        river_so_far = set(river_coords)

        # Prefer left-moving neighbors
        leftish = [n for n in neighbors if n.x < river_current.x and n not in river_so_far]
        other = [n for n in neighbors if n not in river_so_far and n not in leftish]

        if leftish and random.random() < 0.7:
            next_river = random.choice(leftish)
        elif other:
            next_river = random.choice(other)
        else:
            break

        river_coords.append(next_river)
        all_water_coords.add(next_river)
        river_current = next_river

    print(f"  Water squares: {len(all_water_coords)}")

    # Generate grid data for each square
    print("Generating grid data...")
    grids = []

    for idx, coord in enumerate(coords):
        # Grid ID
        grid_id = f"S{idx:04d}"

        # Fire risk: higher away from water, near top-right
        dist_to_water = float('inf')
        for water_coord in all_water_coords:
            dist = square_distance(coord, water_coord)
            if dist < dist_to_water:
                dist_to_water = dist

        water_factor = min(1.0, dist_to_water / 10.0)
        pos_factor = (coord.x / num_cols) * 0.5 + ((num_rows - coord.y) / num_rows) * 0.5
        fire_risk = 0.1 + 0.7 * water_factor * pos_factor + random.uniform(-0.1, 0.1)
        fire_risk = min(1.0, max(0.0, fire_risk))

        # Terrain complexity: more complex near center
        center_dist = square_distance(coord, SquareCoord(x=num_cols//2, y=num_rows//2))
        max_center_dist = math.sqrt((num_cols/2)**2 + (num_rows/2)**2)
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
            "x": coord.x,
            "y": coord.y,
            "fire_risk": fire_risk,
            "terrain_complexity": terrain_complexity,
            "vegetation_type": vegetation_type,
            "species_densities": species_densities
        })

    # Create map_config
    road_locations = [[c.x, c.y] for c in all_road_coords]
    water_locations = [[c.x, c.y] for c in all_water_coords]

    data = {
        "map_config": {
            "num_cols": num_cols,
            "num_rows": num_rows,
            "boundary_type": "SQUARE",
            "road_locations": road_locations,
            "water_locations": water_locations
        },
        "square_coords": [[c.x, c.y] for c in coords],
        "grids": grids,
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(data, f)

    print(f"Generated square map data saved to: {output_json}")
    print(f"  Grid size: {num_cols} cols × {num_rows} rows")
    print(f"  Total squares: {len(coords)}")
    print(f"  Road squares: {len(road_locations)}")
    print(f"  Water squares: {len(water_locations)}")

    return data, coords, all_road_coords, all_water_coords


def visualize_square_map(
    data: dict,
    coords: List[SquareCoord],
    road_coords: Set[SquareCoord],
    water_coords: Set[SquareCoord],
    output_path: str = "square_map_features.jpg"
):
    """Visualize square grid map features."""
    square_size = 1.0
    num_cols = data["map_config"]["num_cols"]
    num_rows = data["map_config"]["num_rows"]

    fig, ax = plt.subplots(figsize=(16, 12), dpi=100)

    patches = []

    for coord in coords:
        x, y = square_to_pixel(coord, square_size)

        # Determine color
        if coord in water_coords:
            color = [0.3, 0.6, 1.0]  # Blue - water
        elif coord in road_coords:
            if coord in water_coords:
                color = [0.5, 0.35, 0.2]  # Dark brown - bridge
            else:
                color = [0.7, 0.55, 0.4]  # Brown - road
        else:
            color = [0.92, 0.95, 0.90]  # Light background

        # Create square patch
        square_patch = Rectangle(
            (x - square_size/2, y - square_size/2),
            square_size,
            square_size,
            facecolor=color,
            edgecolor=[0.7, 0.7, 0.7],
            linewidth=0
        )
        patches.append(square_patch)

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
    all_x, all_y = zip(*[square_to_pixel(c, square_size) for c in coords])
    ax.set_xlim(min(all_x) - 1, max(all_x) + 1)
    ax.set_ylim(min(all_y) - 1, max(all_y) + 1)

    ax.set_title(f"Square Grid\n{num_cols} cols × {num_rows} rows = {len(coords)} squares", fontsize=16, pad=20)
    ax.set_xlabel("X (Column)", fontsize=12)
    ax.set_ylabel("Y (Row)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Square map features saved to: {output_path}")
    plt.close(fig)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Square Grid Map Generator - Generate square grid maps with curved roads"
    )
    parser.add_argument(
        "--cols", "-c",
        type=int,
        default=30,
        help="Number of columns in square grid (default: 30)"
    )
    parser.add_argument(
        "--rows", "-r",
        type=int,
        default=20,
        help="Number of rows in square grid (default: 20)"
    )
    parser.add_argument(
        "--data", "-d",
        type=str,
        default="square_map_data.json",
        help="Output JSON data file path (default: square_map_data.json)"
    )
    parser.add_argument(
        "--map-image", "-m",
        type=str,
        default="square_map_features.jpg",
        help="Output map features image path (default: square_map_features.jpg)"
    )

    args = parser.parse_args()

    print("="*70)
    print("  SQUARE GRID MAP GENERATOR")
    print("="*70)

    # Generate data
    print(f"\n[1/2] Generating square grid data: {args.cols} cols × {args.rows} rows...")
    data, coords, road_coords, water_coords = generate_square_map_data(
        num_cols=args.cols,
        num_rows=args.rows,
        output_json=args.data
    )

    # Visualize map features
    print(f"\n[2/2] Visualizing square map to: {args.map_image}")
    visualize_square_map(data, coords, road_coords, water_coords, args.map_image)

    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"  Grid size: {args.cols} cols × {args.rows} rows")
    print(f"  Total squares: {len(coords)}")
    print(f"  Road squares: {len(road_coords)}")
    print(f"  Water squares: {len(water_coords)}")
    print("="*70)
    print("\nGenerated files:")
    print(f"  - {args.data} (square map data)")
    print(f"  - {args.map_image} (map visualization)")


if __name__ == "__main__":
    main()
