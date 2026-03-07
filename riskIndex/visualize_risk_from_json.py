#!/usr/bin/env python3
"""
Visualize risk heatmap from wrapper script output JSON.
"""

import sys
import os
import json
import argparse
from typing import List, Dict, Any, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.collections import PatchCollection
from matplotlib.colors import LinearSegmentedColormap


def load_results_from_json(filepath: str) -> Dict[str, Any]:
    """Load risk calculation results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def visualize_risk_heatmap_square(
    results_data: Dict[str, Any],
    input_data: Optional[Dict[str, Any]] = None,
    output_path: str = "risk_heatmap_from_json.jpg",
    show_labels: bool = True,
    show_features: bool = True
):
    """
    Visualize risk heatmap from results.

    Args:
        results_data: Output from risk_model_wrapper.py
        input_data: Optional input data with road/water locations
        output_path: Output image path
        show_labels: Whether to show risk value labels
        show_features: Whether to overlay road/water features
    """
    results = results_data.get("results", [])

    if not results:
        print("No results found in JSON file!")
        return

    # Try to determine grid size
    # First check if input data is provided
    num_cols = None
    num_rows = None
    road_coords = set()
    water_coords = set()

    if input_data:
        map_config = input_data.get("map_config", {})
        num_cols = map_config.get("num_cols") or map_config.get("map_width")
        num_rows = map_config.get("num_rows") or map_config.get("map_height")

        if show_features:
            road_locations = map_config.get("road_locations", [])
            water_locations = map_config.get("water_locations", [])
            road_coords = set((loc[0], loc[1]) for loc in road_locations)
            water_coords = set((loc[0], loc[1]) for loc in water_locations)

    # If grid size not found, try to infer from data coordinates
    if num_cols is None or num_rows is None:
        xs = []
        ys = []
        for result in results:
            x = result.get("x")
            y = result.get("y")
            if x is not None:
                xs.append(x)
            if y is not None:
                ys.append(y)

        if xs and ys:
            num_cols = max(xs) + 1
            num_rows = max(ys) + 1
            print(f"Inferred grid size from coordinates: {num_cols} cols × {num_rows} rows")
        else:
            # Fallback: assume results are in order, create a reasonable grid
            n = len(results)
            num_cols = int(np.ceil(np.sqrt(n * 1.5)))
            num_rows = int(np.ceil(n / num_cols))
            print(f"Warning: Grid size not specified. Using {num_cols} cols × {num_rows} rows.")

    # Create risk grid
    risk_grid = np.full((num_rows, num_cols), np.nan)
    grid_data = {}

    for idx, result in enumerate(results):
        grid_id = result.get("grid_id", f"G{idx:04d}")
        norm_risk = result.get("normalized_risk", 0.0)

        # Try to find coordinates
        x, y = None, None

        # First try: look for x/y directly in result
        x = result.get("x")
        y = result.get("y")

        # Second try: look for x/y in input data if available
        if (x is None or y is None) and input_data:
            grids = input_data.get("grids", [])
            if idx < len(grids):
                g = grids[idx]
                x = g.get("hex_col") or g.get("x")
                y = g.get("hex_row") or g.get("y")

        # Fallback: use index
        if x is None or y is None:
            x = idx % num_cols
            y = idx // num_cols

        if 0 <= x < num_cols and 0 <= y < num_rows:
            risk_grid[y, x] = norm_risk
            grid_data[(x, y)] = {
                "grid_id": grid_id,
                "risk": norm_risk
            }

    # Create visualization
    square_size = 1.0
    fig, ax = plt.subplots(figsize=(18, 14), dpi=100)

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

    for y in range(num_rows):
        for x in range(num_cols):
            risk = risk_grid[y, x]

            if np.isnan(risk):
                continue

            # Get feature info
            is_road = (x, y) in road_coords
            is_water = (x, y) in water_coords

            # Determine color
            base_color = cmap(risk)

            if show_features and is_water:
                # Mix blue with risk color
                water_color = (0.3, 0.6, 1.0, 1.0)
                facecolor = tuple(0.4 * water_color[i] + 0.6 * base_color[i] for i in range(3))
            elif show_features and is_road:
                # Mix brown with risk color
                road_color = (0.7, 0.55, 0.4, 1.0)
                facecolor = tuple(0.4 * road_color[i] + 0.6 * base_color[i] for i in range(3))
            else:
                facecolor = base_color

            # Create square patch
            square_patch = Rectangle(
                (x * square_size - square_size/2, y * square_size - square_size/2),
                square_size,
                square_size,
                facecolor=facecolor,
                edgecolor=[0.5, 0.5, 0.5],
                linewidth=0
            )
            patches.append(square_patch)

    # Add all patches
    collection = PatchCollection(patches, match_original=True)
    ax.add_collection(collection)

    # Add risk value labels
    if show_labels:
        for (x, y), data in grid_data.items():
            risk = data["risk"]

            # Choose text color for contrast
            if risk < 0.3 or risk > 0.7:
                text_color = 'white'
            else:
                text_color = 'black'

            ax.text(
                x * square_size,
                y * square_size,
                f"{risk:.2f}",
                ha='center',
                va='center',
                color=text_color,
                fontsize=7,
                fontweight='bold'
            )

    # Add colorbar
    from matplotlib.cm import ScalarMappable
    sm = ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Normalized Risk', rotation=270, labelpad=20, fontsize=12)

    # Add legend for features
    if show_features and (road_coords or water_coords):
        legend_elements = []
        if road_coords:
            legend_elements.append(Patch(facecolor=[0.7, 0.55, 0.4], edgecolor='black', label='Road'))
        if water_coords:
            legend_elements.append(Patch(facecolor=[0.3, 0.6, 1.0], edgecolor='black', label='Water'))
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', fontsize=12)

    # Set limits and aspect
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, num_cols * square_size - 0.5)
    ax.set_ylim(-0.5, num_rows * square_size - 0.5)

    ax.set_title(f"Risk Heatmap\n{num_cols} cols × {num_rows} rows, {len(results)} grids", fontsize=16, pad=20)
    ax.set_xlabel("X (Column)", fontsize=12)
    ax.set_ylabel("Y (Row)", fontsize=12)
    ax.grid(alpha=0.2, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Risk heatmap saved to: {output_path}")
    plt.close(fig)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Visualize Risk Heatmap from JSON - Generate risk heatmap from wrapper script output"
    )
    parser.add_argument(
        "--results", "-r",
        type=str,
        required=True,
        help="Path to risk results JSON file (from risk_model_wrapper.py)"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Optional path to input data JSON (for road/water overlay)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="risk_heatmap_from_json.jpg",
        help="Output heatmap image path (default: risk_heatmap_from_json.jpg)"
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Hide risk value labels on heatmap"
    )
    parser.add_argument(
        "--no-features",
        action="store_true",
        help="Hide road/water feature overlays"
    )

    args = parser.parse_args()

    print("="*70)
    print("  RISK HEATMAP VISUALIZER")
    print("="*70)

    # Load results
    print(f"\n[1/3] Loading risk results from: {args.results}")
    results_data = load_results_from_json(args.results)
    print(f"  Loaded {len(results_data.get('results', []))} grid results")

    # Load input data if provided
    input_data = None
    if args.input:
        print(f"\n[2/3] Loading input data from: {args.input}")
        input_data = load_results_from_json(args.input)
        print("  Input data loaded")
    else:
        print("\n[2/3] No input data provided (no road/water overlay)")

    # Generate heatmap
    print(f"\n[3/3] Generating heatmap to: {args.output}")
    visualize_risk_heatmap_square(
        results_data,
        input_data=input_data,
        output_path=args.output,
        show_labels=not args.no_labels,
        show_features=not args.no_features
    )

    print("\n" + "="*70)
    print("  COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
