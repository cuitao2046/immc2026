"""
Spatial data generator with continuous field maps (based on data.py).

This module generates realistic continuous spatial data using Gaussian smoothing
for terrain, water bodies, vegetation, roads, and animal distributions.
"""

from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
import os
import json

import numpy as np

# Try to import scipy for Gaussian filtering, but provide fallback
try:
    from scipy.ndimage import gaussian_filter
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    # Simple fallback for Gaussian filter
    def gaussian_filter(arr: np.ndarray, sigma: float) -> np.ndarray:
        """Fallback Gaussian filter using convolution."""
        size = int(sigma * 3) * 2 + 1
        if size <= 1:
            return arr

        x = np.linspace(-size // 2, size // 2, size)
        kernel = np.exp(-x ** 2 / (2 * sigma ** 2))
        kernel = kernel / np.sum(kernel)

        result = np.zeros_like(arr)
        for i in range(arr.shape[0]):
            result[i, :] = np.convolve(arr[i, :], kernel, mode='same')
        for j in range(arr.shape[1]):
            result[:, j] = np.convolve(result[:, j], kernel, mode='same')

        return result


# Try to import matplotlib for plotting, but make it optional
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


@dataclass
class SpatialConfig:
    """Configuration for spatial data generation."""
    # Basic settings
    size: int = 120
    season: str = "rainy"
    hour: int = 22
    output_dir: str = "maps"
    save_maps: bool = True
    save_data: bool = True
    map_format: str = "jpg"  # "jpg", "png", or "both"

    # Smoothing scales
    terrain_smooth_scale: float = 10.0
    water_smooth_scale: float = 8.0
    animal_smooth_scale: float = 6.0

    # Terrain thresholds (for terrain classification)
    terrain_threshold_lowland: float = 0.3
    terrain_threshold_plain: float = 0.55
    terrain_threshold_hill: float = 0.75

    # Water settings
    water_threshold: float = 0.65  # Threshold for water body generation

    # Road settings
    num_roads: int = 4  # Number of roads to generate

    # Waterhole settings
    waterhole_probability: float = 0.02  # Probability of waterhole near water
    waterhole_search_range: int = 2  # Search range for nearby water (pixels)

    # Species density weights
    rhino_weight: float = 0.5
    elephant_weight: float = 0.3
    bird_weight: float = 0.2

    # Species seasonal multipliers (rainy, dry)
    rhino_season_multipliers: tuple = (1.2, 1.0)
    elephant_season_multipliers: tuple = (1.3, 0.9)
    bird_season_multipliers: tuple = (1.5, 0.8)

    # Fire risk by vegetation type (grass, shrub, forest, wetland)
    fire_risk_by_vegetation: tuple = (0.8, 0.6, 0.5, 0.2)

    # Risk weights
    risk_weight_human: float = 0.4
    risk_weight_environmental: float = 0.3
    risk_weight_density: float = 0.3

    # Human risk weights
    human_risk_weight_boundary: float = 0.4
    human_risk_weight_road: float = 0.35
    human_risk_weight_water: float = 0.25

    # Environmental risk weights
    env_risk_weight_fire: float = 0.6
    env_risk_weight_terrain: float = 0.4

    # Temporal factors
    temporal_factor_night: float = 1.3
    temporal_factor_day: float = 1.0
    temporal_factor_rainy: float = 1.2
    temporal_factor_dry: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Returns:
            Dictionary containing all configuration values
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """
        Convert configuration to a JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str) -> None:
        """
        Save configuration to a JSON file.

        Args:
            filepath: Path to save the configuration file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpatialConfig':
        """
        Create configuration from a dictionary.

        Args:
            data: Dictionary containing configuration values

        Returns:
            SpatialConfig object
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SpatialConfig':
        """
        Create configuration from a JSON string.

        Args:
            json_str: JSON string

        Returns:
            SpatialConfig object
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load(cls, filepath: str) -> 'SpatialConfig':
        """
        Load configuration from a JSON file.

        Args:
            filepath: Path to the configuration file

        Returns:
            SpatialConfig object
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    @classmethod
    def default(cls) -> 'SpatialConfig':
        """
        Create a configuration with default values.

        Returns:
            SpatialConfig object with default values
        """
        return cls()


@dataclass
class SpatialMaps:
    """Container for all generated spatial maps."""
    terrain: np.ndarray
    water: np.ndarray
    vegetation: np.ndarray
    roads: np.ndarray
    waterholes: np.ndarray
    rhino: np.ndarray
    elephant: np.ndarray
    bird: np.ndarray
    animal_density: np.ndarray
    fire_risk: np.ndarray
    distance_to_road: np.ndarray
    distance_to_water: np.ndarray
    distance_to_boundary: np.ndarray
    risk_map: np.ndarray
    config: SpatialConfig


def normalize(x: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1] range."""
    x_min = x.min()
    x_max = x.max()
    if x_max == x_min:
        return np.zeros_like(x)
    return (x - x_min) / (x_max - x_min)


def smooth_random(size: int, scale: float = 6.0) -> np.ndarray:
    """Generate smooth random noise using Gaussian filtering."""
    noise = np.random.rand(size, size)
    return normalize(gaussian_filter(noise, sigma=scale))


class SpatialDataGenerator:
    """
    Generates realistic continuous spatial data for the risk model.

    Based on the data.py script with Gaussian smoothing for realistic
    continuous fields of terrain, water, vegetation, roads, and animals.
    """

    def __init__(self, config: Optional[SpatialConfig] = None, seed: Optional[int] = None):
        """
        Initialize the spatial data generator.

        Args:
            config: Spatial generation configuration
            seed: Random seed for reproducibility
        """
        self.config = config or SpatialConfig()
        if seed is not None:
            np.random.seed(seed)

    def generate_terrain(self) -> np.ndarray:
        """
        Generate terrain map.

        Returns:
            Terrain map with values:
            0 = lowland, 1 = plain, 2 = hill, 3 = mountain
        """
        terrain_noise = smooth_random(self.config.size, self.config.terrain_smooth_scale)
        terrain = np.zeros((self.config.size, self.config.size), dtype=int)
        terrain[terrain_noise < self.config.terrain_threshold_lowland] = 0
        terrain[(terrain_noise >= self.config.terrain_threshold_lowland) &
                (terrain_noise < self.config.terrain_threshold_plain)] = 1
        terrain[(terrain_noise >= self.config.terrain_threshold_plain) &
                (terrain_noise < self.config.terrain_threshold_hill)] = 2
        terrain[terrain_noise >= self.config.terrain_threshold_hill] = 3
        return terrain

    def generate_water(self, terrain: np.ndarray) -> np.ndarray:
        """
        Generate water bodies map.

        Args:
            terrain: Terrain map

        Returns:
            Water map (1 = water, 0 = land)
        """
        water_noise = smooth_random(self.config.size, self.config.water_smooth_scale)
        water = np.zeros((self.config.size, self.config.size), dtype=int)
        water[(water_noise > self.config.water_threshold) & (terrain == 0)] = 1
        return water

    def generate_vegetation(self, terrain: np.ndarray, water: np.ndarray) -> np.ndarray:
        """
        Generate vegetation map.

        Args:
            terrain: Terrain map
            water: Water map

        Returns:
            Vegetation map with values:
            0 = none, 1 = grass, 2 = shrub, 3 = forest, 4 = wetland
        """
        vegetation = np.zeros((self.config.size, self.config.size), dtype=int)
        for i in range(self.config.size):
            for j in range(self.config.size):
                if water[i, j] == 1:
                    vegetation[i, j] = 4
                elif terrain[i, j] == 1:
                    vegetation[i, j] = 1
                elif terrain[i, j] == 2:
                    vegetation[i, j] = 2
                elif terrain[i, j] == 3:
                    vegetation[i, j] = 3
        return vegetation

    def generate_roads(self, water: np.ndarray) -> np.ndarray:
        """
        Generate road network.

        Args:
            water: Water map (roads avoid water)

        Returns:
            Road map (1 = road, 0 = no road)
        """
        roads = np.zeros((self.config.size, self.config.size), dtype=int)

        for _ in range(self.config.num_roads):
            x = np.random.randint(0, self.config.size)
            y = 0

            for _ in range(self.config.size):
                if water[x, y] == 0:
                    roads[x, y] = 1

                move = np.random.choice([-1, 0, 1])
                x = np.clip(x + move, 0, self.config.size - 1)
                y += 1
                if y >= self.config.size:
                    break

        return roads

    def generate_waterholes(self, water: np.ndarray) -> np.ndarray:
        """
        Generate waterholes near water bodies.

        Args:
            water: Water map

        Returns:
            Waterholes map (1 = waterhole, 0 = no waterhole)
        """
        waterholes = np.zeros((self.config.size, self.config.size), dtype=int)
        search_range = self.config.waterhole_search_range

        for i in range(self.config.size):
            for j in range(self.config.size):
                if water[i, j] == 0:
                    near_water = False
                    for dx in range(-search_range, search_range + 1):
                        for dy in range(-search_range, search_range + 1):
                            xi = i + dx
                            yj = j + dy
                            if 0 <= xi < self.config.size and 0 <= yj < self.config.size:
                                if water[xi, yj] == 1:
                                    near_water = True
                                    break
                        if near_water:
                            break

                    if near_water and np.random.random() < self.config.waterhole_probability:
                        waterholes[i, j] = 1

        return waterholes

    def generate_animal_distributions(
        self,
        vegetation: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate animal density maps.

        Args:
            vegetation: Vegetation map

        Returns:
            Tuple of (rhino, elephant, bird, total_animal_density)
        """
        rhino = smooth_random(self.config.size, self.config.animal_smooth_scale)
        elephant = smooth_random(self.config.size, self.config.animal_smooth_scale)
        bird = smooth_random(self.config.size, self.config.animal_smooth_scale)

        # Constrain animal distributions by vegetation
        rhino = rhino * (vegetation == 1)
        elephant = elephant * ((vegetation == 1) | (vegetation == 3))
        bird = bird * (vegetation == 4)

        animal_density = rhino + elephant + bird

        return rhino, elephant, bird, animal_density

    def generate_fire_risk(self, vegetation: np.ndarray) -> np.ndarray:
        """
        Generate fire risk map.

        Args:
            vegetation: Vegetation map

        Returns:
            Fire risk map [0, 1]
        """
        fire_risk = np.zeros((self.config.size, self.config.size))
        fire_risk[vegetation == 1] = self.config.fire_risk_by_vegetation[0]  # grass
        fire_risk[vegetation == 2] = self.config.fire_risk_by_vegetation[1]  # shrub
        fire_risk[vegetation == 3] = self.config.fire_risk_by_vegetation[2]  # forest
        fire_risk[vegetation == 4] = self.config.fire_risk_by_vegetation[3]  # wetland
        return fire_risk

    def calculate_distances(
        self,
        roads: np.ndarray,
        waterholes: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate distance maps to roads, waterholes, and boundary.

        Args:
            roads: Road map
            waterholes: Waterholes map

        Returns:
            Tuple of (distance_to_road, distance_to_water, distance_to_boundary)
        """
        def distance_to_feature(feature: np.ndarray) -> np.ndarray:
            """Calculate distance to nearest feature."""
            coords = np.argwhere(feature == 1)
            dist = np.full((self.config.size, self.config.size), self.config.size, dtype=float)

            if len(coords) > 0:
                for i in range(self.config.size):
                    for j in range(self.config.size):
                        d = np.sqrt((coords[:, 0] - i) ** 2 + (coords[:, 1] - j) ** 2)
                        dist[i, j] = np.min(d)

            return dist

        d_road = distance_to_feature(roads)
        d_water = distance_to_feature(waterholes)

        d_boundary = np.zeros((self.config.size, self.config.size))
        for i in range(self.config.size):
            for j in range(self.config.size):
                d_boundary[i, j] = min(i, j, self.config.size - i, self.config.size - j)

        return d_road, d_water, d_boundary

    def calculate_risk(
        self,
        d_boundary: np.ndarray,
        d_road: np.ndarray,
        d_water: np.ndarray,
        terrain: np.ndarray,
        fire_risk: np.ndarray,
        rhino: np.ndarray,
        elephant: np.ndarray,
        bird: np.ndarray
    ) -> np.ndarray:
        """
        Calculate the final risk map.

        Uses the SAME calculation logic as the main risk model for consistency.

        Args:
            d_boundary: Distance to boundary map
            d_road: Distance to road map
            d_water: Distance to water map
            terrain: Terrain map
            fire_risk: Fire risk map
            rhino: Rhino density map
            elephant: Elephant density map
            bird: Bird density map

        Returns:
            Normalized risk map [0, 1]
        """
        risk = np.zeros((self.config.size, self.config.size))

        # Time factors from configuration
        is_night = self.config.hour < 6 or self.config.hour > 18
        t_factor = self.config.temporal_factor_night if is_night else self.config.temporal_factor_day
        s_factor = self.config.temporal_factor_rainy if self.config.season == "rainy" else self.config.temporal_factor_dry

        # Seasonal multipliers for species from configuration
        if self.config.season == "rainy":
            rhino_mult = self.config.rhino_season_multipliers[0]
            elephant_mult = self.config.elephant_season_multipliers[0]
            bird_mult = self.config.bird_season_multipliers[0]
        else:
            rhino_mult = self.config.rhino_season_multipliers[1]
            elephant_mult = self.config.elephant_season_multipliers[1]
            bird_mult = self.config.bird_season_multipliers[1]

        # Max distances for normalization - same as adapter
        max_boundary_dist = self.config.size / 2
        max_road_dist = self.config.size
        max_water_dist = self.config.size

        for i in range(self.config.size):
            for j in range(self.config.size):
                # Human risk - using configured weights
                d_boundary_norm = min(d_boundary[i, j] / max_boundary_dist, 1.0)
                d_road_norm = min(d_road[i, j] / max_road_dist, 1.0)
                d_water_norm = min(d_water[i, j] / max_water_dist, 1.0)

                # Proximity = 1 - normalized_distance
                h = (self.config.human_risk_weight_boundary * (1.0 - d_boundary_norm) +
                     self.config.human_risk_weight_road * (1.0 - d_road_norm) +
                     self.config.human_risk_weight_water * (1.0 - d_water_norm))

                # Environmental risk - using configured weights
                terrain_diff = terrain[i, j] / 3
                e = (self.config.env_risk_weight_fire * fire_risk[i, j] +
                     self.config.env_risk_weight_terrain * terrain_diff)

                # Density value with seasonal multipliers - using configured species weights
                d = (self.config.rhino_weight * rhino[i, j] * rhino_mult +
                     self.config.elephant_weight * elephant[i, j] * elephant_mult +
                     self.config.bird_weight * bird[i, j] * bird_mult)

                # Combine with risk weights
                risk[i, j] = (self.config.risk_weight_human * h +
                              self.config.risk_weight_environmental * e +
                              self.config.risk_weight_density * d) * t_factor * s_factor

        return normalize(risk)

    def generate(self) -> SpatialMaps:
        """
        Generate complete set of spatial maps.

        Returns:
            SpatialMaps object containing all generated maps
        """
        # Create output directory
        if self.config.save_maps or self.config.save_data:
            os.makedirs(self.config.output_dir, exist_ok=True)

        # Generate all maps
        terrain = self.generate_terrain()
        water = self.generate_water(terrain)
        vegetation = self.generate_vegetation(terrain, water)
        roads = self.generate_roads(water)
        waterholes = self.generate_waterholes(water)
        rhino, elephant, bird, animal_density = self.generate_animal_distributions(vegetation)
        fire_risk = self.generate_fire_risk(vegetation)
        d_road, d_water, d_boundary = self.calculate_distances(roads, waterholes)
        risk_map = self.calculate_risk(
            d_boundary, d_road, d_water,
            terrain, fire_risk,
            rhino, elephant, bird
        )

        maps = SpatialMaps(
            terrain=terrain,
            water=water,
            vegetation=vegetation,
            roads=roads,
            waterholes=waterholes,
            rhino=rhino,
            elephant=elephant,
            bird=bird,
            animal_density=animal_density,
            fire_risk=fire_risk,
            distance_to_road=d_road,
            distance_to_water=d_water,
            distance_to_boundary=d_boundary,
            risk_map=risk_map,
            config=self.config
        )

        # Save maps if requested
        if self.config.save_maps and HAS_MATPLOTLIB:
            self._save_maps(
                terrain, water, vegetation, roads, waterholes,
                animal_density, risk_map,
                rhino, elephant, bird, fire_risk
            )
            self._save_readme(maps)

        # Save raw data if requested
        if self.config.save_data:
            self._save_data(maps)

        return maps

    def _save_map(
        self,
        data: np.ndarray,
        filename: str,
        title: str,
        cmap: str = "viridis",
        colorbar: bool = False,
        is_discrete: bool = False
    ) -> None:
        """
        Save a single map in configured format(s).

        Args:
            data: Map data array
            filename: Base filename (without extension)
            title: Plot title
            cmap: Colormap name
            colorbar: Whether to add colorbar
            is_discrete: Whether data is discrete (for better tick display)
        """
        formats = []
        if self.config.map_format in ["jpg", "both"]:
            formats.append("jpg")
        if self.config.map_format in ["png", "both"]:
            formats.append("png")

        for fmt in formats:
            plt.figure(figsize=(10, 8), dpi=150)
            im = plt.imshow(data, cmap=cmap)
            plt.title(title, fontsize=14, fontweight='bold')
            plt.xlabel('X Coordinate', fontsize=10)
            plt.ylabel('Y Coordinate', fontsize=10)

            if colorbar:
                cbar = plt.colorbar(im, fraction=0.046, pad=0.04)
                cbar.ax.tick_params(labelsize=9)

            if is_discrete:
                # For discrete data, adjust ticks
                unique_vals = np.unique(data)
                if len(unique_vals) <= 10:
                    im.set_clim(vmin=np.min(data) - 0.5, vmax=np.max(data) + 0.5)

            plt.tight_layout()

            ext = ".jpg" if fmt == "jpg" else ".png"
            filepath = os.path.join(self.config.output_dir, filename + ext)
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()

    def _save_maps(
        self,
        terrain: np.ndarray,
        water: np.ndarray,
        vegetation: np.ndarray,
        roads: np.ndarray,
        waterholes: np.ndarray,
        animal_density: np.ndarray,
        risk_map: np.ndarray,
        rhino: np.ndarray,
        elephant: np.ndarray,
        bird: np.ndarray,
        fire_risk: np.ndarray
    ) -> None:
        """
        Save all maps in configured format(s).

        Generates comprehensive visualizations for each spatial element.
        """
        # Create a masked array for forest only
        forest_only = np.ma.masked_where(vegetation != 3, vegetation)
        # Create a masked array for water only (permanent water bodies)
        water_only = np.ma.masked_where(water != 1, water)
        # Create a masked array for grassland only
        grass_only = np.ma.masked_where(vegetation != 1, vegetation)
        # Create a masked array for shrub only
        shrub_only = np.ma.masked_where(vegetation != 2, vegetation)
        # Create a masked array for wetland only
        wetland_only = np.ma.masked_where(vegetation != 4, vegetation)
        # Create lowland mask
        lowland_only = np.ma.masked_where(terrain != 0, terrain)
        # Create plain mask
        plain_only = np.ma.masked_where(terrain != 1, terrain)
        # Create hill mask
        hill_only = np.ma.masked_where(terrain != 2, terrain)
        # Create mountain mask
        mountain_only = np.ma.masked_where(terrain != 3, terrain)

        # Terrain maps
        self._save_map(terrain, "01_terrain", "Terrain Map", cmap="terrain", colorbar=True, is_discrete=True)
        self._save_map(lowland_only, "01a_lowland", "Lowland Distribution", cmap="Blues", colorbar=False)
        self._save_map(plain_only, "01b_plain", "Plain Distribution", cmap="YlGn", colorbar=False)
        self._save_map(hill_only, "01c_hill", "Hill Distribution", cmap="BrBG", colorbar=False)
        self._save_map(mountain_only, "01d_mountain", "Mountain Distribution", cmap="terrain", colorbar=False)

        # Water maps
        self._save_map(water, "02_water_bodies", "Permanent Water Bodies", cmap="Blues", colorbar=True)
        self._save_map(water_only, "02a_water_only", "Water Body Distribution", cmap="Blues", colorbar=False)
        self._save_map(waterholes, "03_waterholes", "Waterhole Locations", cmap="Blues", colorbar=False)

        # Vegetation maps
        self._save_map(vegetation, "04_vegetation", "Vegetation Map", cmap="Greens", colorbar=True, is_discrete=True)
        self._save_map(grass_only, "04a_grassland", "Grassland Distribution", cmap="YlGn", colorbar=False)
        self._save_map(shrub_only, "04b_shrubland", "Shrubland Distribution", cmap="Greens", colorbar=False)
        self._save_map(forest_only, "04c_forest", "Forest Distribution", cmap="viridis", colorbar=False)
        self._save_map(wetland_only, "04d_wetland", "Wetland Distribution", cmap="Blues", colorbar=False)

        # Road map
        self._save_map(roads, "05_roads", "Road Network", cmap="gray", colorbar=False)

        # Fire risk map
        self._save_map(fire_risk, "06_fire_risk", "Fire Risk Index", cmap="YlOrRd", colorbar=True)

        # Animal density maps
        self._save_map(rhino, "07a_rhino_density", "Rhinoceros Density Distribution", cmap="YlGn", colorbar=True)
        self._save_map(elephant, "07b_elephant_density", "Elephant Density Distribution", cmap="YlGn", colorbar=True)
        self._save_map(bird, "07c_bird_density", "Bird Density Distribution", cmap="YlGnBu", colorbar=True)
        self._save_map(animal_density, "07_total_animal_density", "Total Animal Density", cmap="YlGn", colorbar=True)

        # Risk map - heatmap
        self._save_map(risk_map, "08_risk_index", "Risk Index Heat Map", cmap="hot", colorbar=True)

    def _save_data(self, maps: SpatialMaps) -> None:
        """
        Save raw data as numpy arrays for later use.

        Args:
            maps: SpatialMaps object containing all generated data
        """
        data_dir = os.path.join(self.config.output_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Save each map as numpy array
        np.save(os.path.join(data_dir, "terrain.npy"), maps.terrain)
        np.save(os.path.join(data_dir, "water.npy"), maps.water)
        np.save(os.path.join(data_dir, "vegetation.npy"), maps.vegetation)
        np.save(os.path.join(data_dir, "roads.npy"), maps.roads)
        np.save(os.path.join(data_dir, "waterholes.npy"), maps.waterholes)
        np.save(os.path.join(data_dir, "rhino.npy"), maps.rhino)
        np.save(os.path.join(data_dir, "elephant.npy"), maps.elephant)
        np.save(os.path.join(data_dir, "bird.npy"), maps.bird)
        np.save(os.path.join(data_dir, "animal_density.npy"), maps.animal_density)
        np.save(os.path.join(data_dir, "fire_risk.npy"), maps.fire_risk)
        np.save(os.path.join(data_dir, "distance_to_road.npy"), maps.distance_to_road)
        np.save(os.path.join(data_dir, "distance_to_water.npy"), maps.distance_to_water)
        np.save(os.path.join(data_dir, "distance_to_boundary.npy"), maps.distance_to_boundary)
        np.save(os.path.join(data_dir, "risk_map.npy"), maps.risk_map)

        # Also save as CSV for easier viewing
        import csv
        csv_dir = os.path.join(self.config.output_dir, "csv")
        os.makedirs(csv_dir, exist_ok=True)

        np.savetxt(os.path.join(csv_dir, "risk_map.csv"), maps.risk_map, delimiter=",")
        np.savetxt(os.path.join(csv_dir, "terrain.csv"), maps.terrain, delimiter=",", fmt="%d")
        np.savetxt(os.path.join(csv_dir, "water.csv"), maps.water, delimiter=",", fmt="%d")
        np.savetxt(os.path.join(csv_dir, "vegetation.csv"), maps.vegetation, delimiter=",", fmt="%d")

        # Save full configuration
        import json
        with open(os.path.join(data_dir, "config.json"), "w") as f:
            f.write(maps.config.to_json())

    def _save_readme(self, maps: SpatialMaps) -> None:
        """
        Save a README file explaining the generated data.

        Args:
            maps: SpatialMaps object
        """
        readme_path = os.path.join(self.config.output_dir, "README.txt")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("="*70 + "\n")
            f.write("  PROTECTED AREA SPATIAL DATA - GENERATED MAPS\n")
            f.write("="*70 + "\n\n")

            f.write(f"Configuration:\n")
            f.write(f"  Map size: {maps.config.size}x{maps.config.size}\n")
            f.write(f"  Season: {maps.config.season}\n")
            f.write(f"  Hour: {maps.config.hour:02d}:00\n\n")

            f.write("Map Legend:\n")
            f.write("-"*70 + "\n")
            f.write("\nTerrain Values:\n")
            f.write("  0 = Lowland\n")
            f.write("  1 = Plain\n")
            f.write("  2 = Hill\n")
            f.write("  3 = Mountain\n\n")

            f.write("Vegetation Values:\n")
            f.write("  0 = None\n")
            f.write("  1 = Grassland\n")
            f.write("  2 = Shrubland\n")
            f.write("  3 = Forest\n")
            f.write("  4 = Wetland\n\n")

            f.write("Generated Files:\n")
            f.write("-"*70 + "\n")
            f.write("\nImage Maps (JPG/PNG):\n")
            f.write("  01_terrain.* - Full terrain classification map\n")
            f.write("  01a_lowland.* - Lowland distribution\n")
            f.write("  01b_plain.* - Plain distribution\n")
            f.write("  01c_hill.* - Hill distribution\n")
            f.write("  01d_mountain.* - Mountain distribution\n")
            f.write("  02_water_bodies.* - Permanent water bodies\n")
            f.write("  02a_water_only.* - Water body distribution mask\n")
            f.write("  03_waterholes.* - Waterhole locations\n")
            f.write("  04_vegetation.* - Full vegetation classification map\n")
            f.write("  04a_grassland.* - Grassland distribution\n")
            f.write("  04b_shrubland.* - Shrubland distribution\n")
            f.write("  04c_forest.* - Forest distribution\n")
            f.write("  04d_wetland.* - Wetland distribution\n")
            f.write("  05_roads.* - Road network\n")
            f.write("  06_fire_risk.* - Fire risk index\n")
            f.write("  07a_rhino_density.* - Rhinoceros density distribution\n")
            f.write("  07b_elephant_density.* - Elephant density distribution\n")
            f.write("  07c_bird_density.* - Bird density distribution\n")
            f.write("  07_total_animal_density.* - Combined animal density\n")
            f.write("  08_risk_index.* - Risk index heat map\n\n")

            f.write("Raw Data (data/ directory):\n")
            f.write("  *.npy - NumPy array files for each map\n")
            f.write("  config.json - Generation configuration\n\n")

            f.write("CSV Data (csv/ directory):\n")
            f.write("  risk_map.csv - Risk index values\n")
            f.write("  terrain.csv - Terrain classification\n")
            f.write("  water.csv - Water bodies\n")
            f.write("  vegetation.csv - Vegetation classification\n\n")

            f.write("="*70 + "\n")
