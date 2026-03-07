"""
Spatial data generator with continuous field maps (based on data.py).

This module generates realistic continuous spatial data using Gaussian smoothing
for terrain, water bodies, vegetation, roads, and animal distributions.
"""

from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
import os

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
    size: int = 120
    season: str = "rainy"
    hour: int = 22
    terrain_smooth_scale: float = 10.0
    water_smooth_scale: float = 8.0
    animal_smooth_scale: float = 6.0
    output_dir: str = "maps"
    save_maps: bool = True


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
        terrain[terrain_noise < 0.3] = 0
        terrain[(terrain_noise >= 0.3) & (terrain_noise < 0.55)] = 1
        terrain[(terrain_noise >= 0.55) & (terrain_noise < 0.75)] = 2
        terrain[terrain_noise >= 0.75] = 3
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
        water[(water_noise > 0.65) & (terrain == 0)] = 1
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

    def generate_roads(self, water: np.ndarray, num_roads: int = 4) -> np.ndarray:
        """
        Generate road network.

        Args:
            water: Water map (roads avoid water)
            num_roads: Number of roads to generate

        Returns:
            Road map (1 = road, 0 = no road)
        """
        roads = np.zeros((self.config.size, self.config.size), dtype=int)

        for _ in range(num_roads):
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

    def generate_waterholes(self, water: np.ndarray, probability: float = 0.02) -> np.ndarray:
        """
        Generate waterholes near water bodies.

        Args:
            water: Water map
            probability: Probability of waterhole near water

        Returns:
            Waterholes map (1 = waterhole, 0 = no waterhole)
        """
        waterholes = np.zeros((self.config.size, self.config.size), dtype=int)

        for i in range(self.config.size):
            for j in range(self.config.size):
                if water[i, j] == 0:
                    near_water = False
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            xi = i + dx
                            yj = j + dy
                            if 0 <= xi < self.config.size and 0 <= yj < self.config.size:
                                if water[xi, yj] == 1:
                                    near_water = True
                                    break
                        if near_water:
                            break

                    if near_water and np.random.random() < probability:
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
        fire_risk[vegetation == 1] = 0.8
        fire_risk[vegetation == 2] = 0.6
        fire_risk[vegetation == 3] = 0.5
        fire_risk[vegetation == 4] = 0.2
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

        # Time factors
        t_factor = 1.3 if (self.config.hour < 6 or self.config.hour > 18) else 1.0
        s_factor = 1.2 if self.config.season == "rainy" else 1.0

        for i in range(self.config.size):
            for j in range(self.config.size):
                # Human risk
                h = 0.4 * (1 / (d_boundary[i, j] + 1)) + \
                    0.35 * (1 / (d_road[i, j] + 1)) + \
                    0.25 * (1 / (d_water[i, j] + 1))

                # Environmental risk
                terrain_diff = terrain[i, j] / 3
                e = 0.6 * fire_risk[i, j] + 0.4 * terrain_diff

                # Density value
                d = 0.5 * rhino[i, j] + 0.3 * elephant[i, j] + 0.2 * bird[i, j]

                risk[i, j] = (0.4 * h + 0.3 * e + 0.3 * d) * t_factor * s_factor

        return normalize(risk)

    def generate(self) -> SpatialMaps:
        """
        Generate complete set of spatial maps.

        Returns:
            SpatialMaps object containing all generated maps
        """
        # Create output directory
        if self.config.save_maps:
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

        # Save maps if requested
        if self.config.save_maps and HAS_MATPLOTLIB:
            self._save_maps(terrain, water, vegetation, roads, waterholes,
                           animal_density, risk_map)

        return SpatialMaps(
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

    def _save_maps(
        self,
        terrain: np.ndarray,
        water: np.ndarray,
        vegetation: np.ndarray,
        roads: np.ndarray,
        waterholes: np.ndarray,
        animal_density: np.ndarray,
        risk_map: np.ndarray
    ) -> None:
        """Save maps to files using matplotlib."""
        plt.figure()
        plt.imshow(terrain, cmap="terrain")
        plt.title("Terrain")
        plt.colorbar()
        plt.savefig(os.path.join(self.config.output_dir, "terrain_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(water, cmap="Blues")
        plt.title("Water Bodies")
        plt.savefig(os.path.join(self.config.output_dir, "water_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(vegetation, cmap="Greens")
        plt.title("Vegetation")
        plt.savefig(os.path.join(self.config.output_dir, "vegetation_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(roads, cmap="gray")
        plt.title("Roads")
        plt.savefig(os.path.join(self.config.output_dir, "roads_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(waterholes, cmap="Blues")
        plt.title("Waterholes")
        plt.savefig(os.path.join(self.config.output_dir, "waterholes_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(animal_density, cmap="YlGn")
        plt.title("Animal Density")
        plt.savefig(os.path.join(self.config.output_dir, "animal_density_map.png"))
        plt.close()

        plt.figure()
        plt.imshow(risk_map, cmap="hot")
        plt.colorbar()
        plt.title("Risk Map")
        plt.savefig(os.path.join(self.config.output_dir, "risk_map.png"))
        plt.close()
