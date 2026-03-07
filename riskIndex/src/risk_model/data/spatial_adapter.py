"""
Adapter to convert spatial generator data to main risk model format.

This module provides conversion utilities between SpatialMaps (from
spatial_generator.py) and the core risk model data structures (Grid,
Environment, SpeciesDensity, TimeContext).

NOTE: The spatial generator's built-in risk calculation now uses the SAME
logic as the main risk model for consistency.
"""

from typing import List, Tuple, Dict, Any
import numpy as np

from ..core import Grid, Environment, SpeciesDensity, TimeContext, Season, VegetationType
from .spatial_generator import SpatialMaps, SpatialConfig


def normalize_distance(distance: float, max_distance: float) -> float:
    """
    Normalize distance value to [0, 1] range.

    Uses the SAME normalization as the spatial generator's risk calculation.

    Args:
        distance: Distance value
        max_distance: Maximum distance for normalization

    Returns:
        Normalized distance value
    """
    normalized = distance / max_distance
    return float(np.clip(normalized, 0.0, 1.0))


def convert_vegetation_type(vegetation_value: int) -> VegetationType:
    """
    Convert spatial generator vegetation value to VegetationType enum.

    Spatial vegetation values:
    0 = none, 1 = grass, 2 = shrub, 3 = forest, 4 = wetland

    Args:
        vegetation_value: Vegetation value from spatial generator

    Returns:
        VegetationType enum
    """
    if vegetation_value == 3:
        return VegetationType.FOREST
    elif vegetation_value == 2:
        return VegetationType.SHRUB
    else:
        # grass, wetland, or none -> default to grassland
        return VegetationType.GRASSLAND


def convert_season(season_str: str) -> Season:
    """
    Convert season string to Season enum.

    Args:
        season_str: "rainy" or "dry"

    Returns:
        Season enum
    """
    if season_str.lower() == "rainy":
        return Season.RAINY
    return Season.DRY


class SpatialToRiskModelAdapter:
    """
    Adapter to convert SpatialMaps to risk model input format.

    This adapter ensures that distance values are normalized EXACTLY the same
    way as in the spatial generator's internal risk calculation for
    perfect consistency.
    """

    def __init__(self, spatial_maps: SpatialMaps):
        """
        Initialize the adapter with spatial maps.

        Args:
            spatial_maps: SpatialMaps object from spatial generator
        """
        self.maps = spatial_maps
        self.size = spatial_maps.config.size
        # Max distances matching spatial_generator.py
        self._max_boundary_dist = self.size / 2
        self._max_road_dist = self.size
        self._max_water_dist = self.size

    def get_grid_id(self, i: int, j: int) -> str:
        """
        Generate a grid ID from coordinates.

        Args:
            i: Row index
            j: Column index

        Returns:
            Grid ID string (e.g., "A01", "B12")
        """
        letter = chr(ord('A') + (i // 26))
        if i >= 26:
            letter = chr(ord('A') + (i // 26) - 1) + chr(ord('A') + (i % 26))
        return f"{letter}{j:02d}"

    def convert_grid(self, i: int, j: int) -> Grid:
        """
        Convert a single grid cell to Grid object.

        Uses EXACTLY the same distance normalization as spatial_generator.py.

        Args:
            i: Row index
            j: Column index

        Returns:
            Grid object
        """
        # Normalize distances to [0, 1] - SAME as spatial_generator.py
        d_boundary = normalize_distance(
            self.maps.distance_to_boundary[i, j],
            self._max_boundary_dist
        )
        d_road = normalize_distance(
            self.maps.distance_to_road[i, j],
            self._max_road_dist
        )
        d_water = normalize_distance(
            self.maps.distance_to_water[i, j],
            self._max_water_dist
        )

        return Grid(
            grid_id=self.get_grid_id(i, j),
            x=float(j),
            y=float(i),
            distance_to_boundary=d_boundary,
            distance_to_road=d_road,
            distance_to_water=d_water
        )

    def convert_environment(self, i: int, j: int) -> Environment:
        """
        Convert a single grid cell to Environment object.

        Args:
            i: Row index
            j: Column index

        Returns:
            Environment object
        """
        vegetation_value = self.maps.vegetation[i, j]
        terrain_value = self.maps.terrain[i, j]

        return Environment(
            fire_risk=float(self.maps.fire_risk[i, j]),
            terrain_complexity=float(terrain_value / 3.0),  # Normalize to [0, 1]
            vegetation_type=convert_vegetation_type(vegetation_value)
        )

    def convert_species_density(self, i: int, j: int) -> SpeciesDensity:
        """
        Convert a single grid cell to SpeciesDensity object.

        Args:
            i: Row index
            j: Column index

        Returns:
            SpeciesDensity object
        """
        densities = {
            "rhino": float(self.maps.rhino[i, j]),
            "elephant": float(self.maps.elephant[i, j]),
            "bird": float(self.maps.bird[i, j])
        }
        return SpeciesDensity(densities=densities)

    def convert_time_context(self) -> TimeContext:
        """
        Convert spatial config to TimeContext object.

        Returns:
            TimeContext object
        """
        return TimeContext(
            hour_of_day=self.maps.config.hour,
            season=convert_season(self.maps.config.season)
        )

    def get_all_grid_data(self) -> List[Tuple[Grid, Environment, SpeciesDensity]]:
        """
        Get all grid cells converted to risk model format.

        Returns:
            List of (Grid, Environment, SpeciesDensity) tuples for all cells
        """
        grid_data = []
        for i in range(self.size):
            for j in range(self.size):
                grid = self.convert_grid(i, j)
                env = self.convert_environment(i, j)
                density = self.convert_species_density(i, j)
                grid_data.append((grid, env, density))
        return grid_data

    def get_risk_map_array(self, results: List[Any]) -> np.ndarray:
        """
        Convert risk model results back to a 2D numpy array.

        Args:
            results: List of GridRiskResult objects

        Returns:
            2D numpy array of normalized risk values
        """
        risk_map = np.zeros((self.size, self.size))

        # Create a dictionary for quick lookup
        result_dict = {r.grid_id: r for r in results}

        for i in range(self.size):
            for j in range(self.size):
                grid_id = self.get_grid_id(i, j)
                if grid_id in result_dict:
                    risk = result_dict[grid_id].normalized_risk
                    risk_map[i, j] = risk if risk is not None else 0.0

        return risk_map


def create_risk_model_input(
    spatial_maps: SpatialMaps
) -> Tuple[List[Tuple[Grid, Environment, SpeciesDensity]], TimeContext]:
    """
    Convenience function to create complete risk model input from spatial maps.

    Args:
        spatial_maps: SpatialMaps object from spatial generator

    Returns:
        Tuple of (grid_data_list, time_context)
    """
    adapter = SpatialToRiskModelAdapter(spatial_maps)
    grid_data = adapter.get_all_grid_data()
    time_context = adapter.convert_time_context()
    return grid_data, time_context
