#!/usr/bin/env python3
"""
Risk Model Wrapper Script.

This script provides a formal wrapper for the risk model that:
1. Reads input data from data files (JSON/CSV)
2. Reads configuration from config files (JSON)
3. Calculates composite risk
4. Performs normalization
5. Saves results to output files

Usage:
    python risk_model_wrapper.py --data data.json --config config.json --output results.json
"""

import sys
import os
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from risk_model.core import (
    Grid,
    SpeciesDensity,
    Season,
    Environment,
    VegetationType,
    TimeContext,
)
from risk_model.risk import (
    RiskModel,
    GridRiskResult,
)
from risk_model.config import (
    RiskWeights,
    WeightManager,
    ModelConfig,
)
from risk_model.risk import (
    HumanRiskWeights,
    EnvironmentalRiskWeights,
)


# ============================================================================
# Data File Format Definitions
# ============================================================================

@dataclass
class GridInputData:
    """Input data for a single grid cell."""
    grid_id: str
    x: float
    y: float
    distance_to_boundary: float
    distance_to_road: float
    distance_to_water: float
    fire_risk: float
    terrain_complexity: float
    vegetation_type: str  # "GRASSLAND", "FOREST", "SHRUB"
    species_densities: Dict[str, float]  # species_name -> density


@dataclass
class TimeInputData:
    """Input data for time context."""
    hour_of_day: int
    season: str  # "DRY", "RAINY"


@dataclass
class ModelInputData:
    """Complete input data for the model."""
    grids: List[GridInputData]
    time: TimeInputData


@dataclass
class ModelConfigData:
    """Configuration data for the model."""
    risk_weights: Optional[Dict[str, float]] = None
    human_risk_weights: Optional[Dict[str, float]] = None
    environmental_risk_weights: Optional[Dict[str, float]] = None


# ============================================================================
# Data Loading Functions
# ============================================================================

def load_data_from_json(filepath: str) -> ModelInputData:
    """
    Load input data from a JSON file.

    Expected JSON format:
    {
        "grids": [
            {
                "grid_id": "A01",
                "x": 0.0,
                "y": 0.0,
                "distance_to_boundary": 0.1,
                "distance_to_road": 0.2,
                "distance_to_water": 0.3,
                "fire_risk": 0.5,
                "terrain_complexity": 0.3,
                "vegetation_type": "GRASSLAND",
                "species_densities": {
                    "rhino": 0.7,
                    "elephant": 0.5,
                    "bird": 0.8
                }
            }
        ],
        "time": {
            "hour_of_day": 22,
            "season": "RAINY"
        }
    }

    Args:
        filepath: Path to JSON file

    Returns:
        ModelInputData object
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    grids_data = data.get("grids", [])
    time_data = data.get("time", {})

    grids = []
    for g in grids_data:
        grids.append(GridInputData(
            grid_id=g.get("grid_id", ""),
            x=g.get("x", 0.0),
            y=g.get("y", 0.0),
            distance_to_boundary=g.get("distance_to_boundary", 0.0),
            distance_to_road=g.get("distance_to_road", 0.0),
            distance_to_water=g.get("distance_to_water", 0.0),
            fire_risk=g.get("fire_risk", 0.0),
            terrain_complexity=g.get("terrain_complexity", 0.0),
            vegetation_type=g.get("vegetation_type", "GRASSLAND"),
            species_densities=g.get("species_densities", {})
        ))

    time = TimeInputData(
        hour_of_day=time_data.get("hour_of_day", 12),
        season=time_data.get("season", "DRY")
    )

    return ModelInputData(grids=grids, time=time)


def load_config_from_json(filepath: str) -> ModelConfigData:
    """
    Load configuration from a JSON file.

    Expected JSON format:
    {
        "risk_weights": {
            "human_weight": 0.4,
            "environmental_weight": 0.3,
            "density_weight": 0.3
        },
        "human_risk_weights": {
            "boundary_weight": 0.4,
            "road_weight": 0.35,
            "water_weight": 0.25
        },
        "environmental_risk_weights": {
            "fire_weight": 0.6,
            "terrain_weight": 0.4
        }
    }

    All fields are optional - defaults will be used for missing fields.

    Args:
        filepath: Path to JSON file

    Returns:
        ModelConfigData object
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return ModelConfigData(
        risk_weights=data.get("risk_weights"),
        human_risk_weights=data.get("human_risk_weights"),
        environmental_risk_weights=data.get("environmental_risk_weights")
    )


# ============================================================================
# Data Conversion Functions
# ============================================================================

def convert_grid_input(grid_data: GridInputData) -> Tuple[Grid, Environment, SpeciesDensity]:
    """
    Convert GridInputData to model input objects.

    Args:
        grid_data: Grid input data

    Returns:
        Tuple of (Grid, Environment, SpeciesDensity)
    """
    # Create Grid object
    grid = Grid(
        grid_id=grid_data.grid_id,
        x=grid_data.x,
        y=grid_data.y,
        distance_to_boundary=grid_data.distance_to_boundary,
        distance_to_road=grid_data.distance_to_road,
        distance_to_water=grid_data.distance_to_water
    )

    # Create Environment object
    veg_type_map = {
        "GRASSLAND": VegetationType.GRASSLAND,
        "FOREST": VegetationType.FOREST,
        "SHRUB": VegetationType.SHRUB
    }
    veg_type = veg_type_map.get(grid_data.vegetation_type, VegetationType.GRASSLAND)

    environment = Environment(
        fire_risk=grid_data.fire_risk,
        terrain_complexity=grid_data.terrain_complexity,
        vegetation_type=veg_type
    )

    # Create SpeciesDensity object
    density = SpeciesDensity(densities=grid_data.species_densities)

    return grid, environment, density


def convert_time_input(time_data: TimeInputData) -> TimeContext:
    """
    Convert TimeInputData to TimeContext.

    Args:
        time_data: Time input data

    Returns:
        TimeContext object
    """
    season_map = {
        "DRY": Season.DRY,
        "RAINY": Season.RAINY
    }
    season = season_map.get(time_data.season, Season.DRY)

    return TimeContext(
        hour_of_day=time_data.hour_of_day,
        season=season
    )


def create_model_from_config(config_data: ModelConfigData) -> RiskModel:
    """
    Create RiskModel from configuration data.

    Args:
        config_data: Model configuration data

    Returns:
        RiskModel instance
    """
    from risk_model.risk import (
        CompositeRiskCalculator,
        HumanRiskCalculator,
        EnvironmentalRiskCalculator,
    )

    # Create weight manager with custom config if provided
    weight_manager = WeightManager()

    # Update risk weights if provided
    if config_data.risk_weights:
        weight_manager.set_risk_weights(
            human_weight=config_data.risk_weights.get("human_weight"),
            environmental_weight=config_data.risk_weights.get("environmental_weight"),
            density_weight=config_data.risk_weights.get("density_weight")
        )

    # Create human risk calculator with custom weights if provided
    human_weights = None
    if config_data.human_risk_weights:
        human_weights = HumanRiskWeights(
            boundary_weight=config_data.human_risk_weights.get("boundary_weight", 0.4),
            road_weight=config_data.human_risk_weights.get("road_weight", 0.35),
            water_weight=config_data.human_risk_weights.get("water_weight", 0.25)
        )
    human_calc = HumanRiskCalculator(weights=human_weights)

    # Create environmental risk calculator with custom weights if provided
    env_weights = None
    if config_data.environmental_risk_weights:
        env_weights = EnvironmentalRiskWeights(
            fire_weight=config_data.environmental_risk_weights.get("fire_weight", 0.6),
            terrain_weight=config_data.environmental_risk_weights.get("terrain_weight", 0.4)
        )
    env_calc = EnvironmentalRiskCalculator(weights=env_weights)

    # Create composite calculator
    composite_calc = CompositeRiskCalculator(
        weight_manager=weight_manager,
        human_calculator=human_calc,
        environmental_calculator=env_calc
    )

    # Create risk model
    return RiskModel(composite_calculator=composite_calc)


# ============================================================================
# Result Saving Functions
# ============================================================================

def save_results_to_json(
    results: List[GridRiskResult],
    output_filepath: str
) -> None:
    """
    Save risk calculation results to a JSON file.

    Args:
        results: List of GridRiskResult objects
        output_filepath: Path to output JSON file
    """
    output_data = {
        "results": []
    }

    for result in results:
        result_dict = {
            "grid_id": result.grid_id,
            "raw_risk": result.raw_risk,
            "normalized_risk": result.normalized_risk
        }

        if result.components:
            result_dict["components"] = {
                "human_risk": result.components.human_risk,
                "environmental_risk": result.components.environmental_risk,
                "density_value": result.components.density_value,
                "diurnal_factor": result.components.diurnal_factor,
                "seasonal_factor": result.components.seasonal_factor,
                "temporal_factor": result.components.temporal_factor
            }

        output_data["results"].append(result_dict)

    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)


# ============================================================================
# Main Wrapper Function
# ============================================================================

def run_risk_model(
    data_file: str,
    config_file: Optional[str] = None,
    output_file: Optional[str] = None
) -> List[GridRiskResult]:
    """
    Run the risk model with data from files.

    Args:
        data_file: Path to input data JSON file
        config_file: Optional path to config JSON file
        output_file: Optional path to output JSON file

    Returns:
        List of GridRiskResult objects
    """
    print("="*70)
    print("  RISK MODEL WRAPPER")
    print("="*70)

    # Step 1: Load input data
    print(f"\n[1/5] Loading input data from: {data_file}")
    input_data = load_data_from_json(data_file)
    print(f"  Loaded {len(input_data.grids)} grid cells")
    print(f"  Time: {input_data.time.hour_of_day:02d}:00, {input_data.time.season} season")

    # Step 2: Load configuration
    model_config = ModelConfigData()
    if config_file:
        print(f"\n[2/5] Loading configuration from: {config_file}")
        model_config = load_config_from_json(config_file)
        print("  Configuration loaded")
    else:
        print(f"\n[2/5] Using default configuration")

    # Step 3: Create risk model
    print(f"\n[3/5] Creating risk model")
    model = create_model_from_config(model_config)
    print("  Model created")

    # Step 4: Convert input data
    print(f"\n[4/5] Converting input data")
    grid_data_list = []
    for grid_input in input_data.grids:
        grid, env, density = convert_grid_input(grid_input)
        grid_data_list.append((grid, env, density))
    time_context = convert_time_input(input_data.time)
    print(f"  Converted {len(grid_data_list)} grid cells")

    # Step 5: Calculate risk
    print(f"\n[5/5] Calculating risk")
    results = model.calculate_batch(grid_data_list, time_context)
    print(f"  Calculated risk for {len(results)} grid cells")

    # Save results if output file specified
    if output_file:
        print(f"\nSaving results to: {output_file}")
        save_results_to_json(results, output_file)
        print("  Results saved")

    # Print summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)

    if results:
        norm_risks = [r.normalized_risk for r in results if r.normalized_risk is not None]
        if norm_risks:
            print(f"  Min normalized risk: {min(norm_risks):.4f}")
            print(f"  Max normalized risk: {max(norm_risks):.4f}")
            print(f"  Avg normalized risk: {sum(norm_risks)/len(norm_risks):.4f}")

            high_risk = sum(1 for r in norm_risks if r > 0.7)
            print(f"  High risk cells (>0.7): {high_risk}/{len(norm_risks)}")

    print("="*70)

    return results


# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    """Main function for command line usage."""
    parser = argparse.ArgumentParser(
        description="Risk Model Wrapper - Calculate composite risk with normalization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example data.json format:
{
    "grids": [
        {
            "grid_id": "A01",
            "x": 0.0,
            "y": 0.0,
            "distance_to_boundary": 0.1,
            "distance_to_road": 0.2,
            "distance_to_water": 0.3,
            "fire_risk": 0.5,
            "terrain_complexity": 0.3,
            "vegetation_type": "GRASSLAND",
            "species_densities": {
                "rhino": 0.7,
                "elephant": 0.5,
                "bird": 0.8
            }
        }
    ],
    "time": {
        "hour_of_day": 22,
        "season": "RAINY"
    }
}

Example config.json format (all fields optional):
{
    "risk_weights": {
        "human_weight": 0.4,
        "environmental_weight": 0.3,
        "density_weight": 0.3
    },
    "human_risk_weights": {
        "boundary_weight": 0.4,
        "road_weight": 0.35,
        "water_weight": 0.25
    },
    "environmental_risk_weights": {
        "fire_weight": 0.6,
        "terrain_weight": 0.4
    }
}
        """
    )

    parser.add_argument(
        "--data", "-d",
        required=True,
        help="Path to input data JSON file"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration JSON file (optional, uses defaults if not provided)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Path to output results JSON file (optional)"
    )

    args = parser.parse_args()

    try:
        run_risk_model(
            data_file=args.data,
            config_file=args.config,
            output_file=args.output
        )
        return 0
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
