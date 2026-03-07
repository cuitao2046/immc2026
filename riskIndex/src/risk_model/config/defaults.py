"""
Default configuration values for the risk model.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import math
import json


@dataclass
class RiskWeights:
    """
    Weights for combining different risk components.

    Attributes:
        human_weight: Weight for human risk component
        environmental_weight: Weight for environmental risk component
        density_weight: Weight for species density component
    """
    human_weight: float = 0.4
    environmental_weight: float = 0.3
    density_weight: float = 0.3

    def __post_init__(self):
        """Validate weights sum to 1."""
        total = self.human_weight + self.environmental_weight + self.density_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"Risk weights must sum to 1, got {total} "
                f"(human={self.human_weight}, "
                f"environmental={self.environmental_weight}, "
                f"density={self.density_weight})"
            )


@dataclass
class HumanRiskWeights:
    """
    Weights for human risk calculation.

    Attributes:
        boundary_weight: Weight for proximity to boundary
        road_weight: Weight for proximity to road
        water_weight: Weight for proximity to water source
    """
    boundary_weight: float = 0.4
    road_weight: float = 0.35
    water_weight: float = 0.25

    def __post_init__(self):
        """Validate weights sum to 1."""
        total = self.boundary_weight + self.road_weight + self.water_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"Weights must sum to 1, got {total} "
                f"(boundary={self.boundary_weight}, road={self.road_weight}, "
                f"water={self.water_weight})"
            )


@dataclass
class EnvironmentalRiskWeights:
    """
    Weights for environmental risk calculation.

    Attributes:
        fire_weight: Weight for fire risk
        terrain_weight: Weight for terrain complexity
    """
    fire_weight: float = 0.6
    terrain_weight: float = 0.4

    def __post_init__(self):
        """Validate weights sum to 1."""
        total = self.fire_weight + self.terrain_weight
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(
                f"Weights must sum to 1, got {total} "
                f"(fire={self.fire_weight}, terrain={self.terrain_weight})"
            )


@dataclass
class SpeciesConfig:
    """
    Configuration for a single species.
    """
    name: str
    weight: float
    rainy_season_multiplier: float = 1.0
    dry_season_multiplier: float = 1.0

    def __post_init__(self):
        """Validate weight is positive."""
        if self.weight <= 0:
            raise ValueError(f"Species weight must be positive, got {self.weight}")


@dataclass
class DiurnalConfig:
    """
    Configuration for diurnal (day/night) factors.
    """
    mode: str = "discrete"  # "discrete" or "continuous"
    daytime_factor: float = 1.0
    nighttime_factor: float = 1.3
    gamma: float = 0.3


@dataclass
class SeasonalConfig:
    """
    Configuration for seasonal factors.
    """
    dry_season_factor: float = 1.0
    rainy_season_factor: float = 1.2


@dataclass
class FullModelConfig:
    """
    Complete model configuration including all parameters.
    """
    # Risk weights
    risk_weights: RiskWeights
    human_risk_weights: HumanRiskWeights
    environmental_risk_weights: EnvironmentalRiskWeights

    # Species configuration (dict: name -> SpeciesConfig)
    species_configs: Dict[str, SpeciesConfig]

    # Temporal configuration
    diurnal_config: DiurnalConfig
    seasonal_config: SeasonalConfig

    @classmethod
    def default(cls) -> 'FullModelConfig':
        """Create a configuration with default values."""
        return cls(
            risk_weights=RiskWeights(),
            human_risk_weights=HumanRiskWeights(),
            environmental_risk_weights=EnvironmentalRiskWeights(),
            species_configs=cls._get_default_species_configs(),
            diurnal_config=DiurnalConfig(),
            seasonal_config=SeasonalConfig()
        )

    @staticmethod
    def _get_default_species_configs() -> Dict[str, SpeciesConfig]:
        """Get default species configuration."""
        return {
            "rhino": SpeciesConfig(
                name="rhino",
                weight=0.5,
                rainy_season_multiplier=1.2,
                dry_season_multiplier=1.0
            ),
            "elephant": SpeciesConfig(
                name="elephant",
                weight=0.3,
                rainy_season_multiplier=1.3,
                dry_season_multiplier=0.9
            ),
            "bird": SpeciesConfig(
                name="bird",
                weight=0.2,
                rainy_season_multiplier=1.5,
                dry_season_multiplier=0.8
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "risk_weights": {
                "human_weight": self.risk_weights.human_weight,
                "environmental_weight": self.risk_weights.environmental_weight,
                "density_weight": self.risk_weights.density_weight
            },
            "human_risk_weights": {
                "boundary_weight": self.human_risk_weights.boundary_weight,
                "road_weight": self.human_risk_weights.road_weight,
                "water_weight": self.human_risk_weights.water_weight
            },
            "environmental_risk_weights": {
                "fire_weight": self.environmental_risk_weights.fire_weight,
                "terrain_weight": self.environmental_risk_weights.terrain_weight
            },
            "species_configs": {
                name: {
                    "name": sp.name,
                    "weight": sp.weight,
                    "rainy_season_multiplier": sp.rainy_season_multiplier,
                    "dry_season_multiplier": sp.dry_season_multiplier
                }
                for name, sp in self.species_configs.items()
            },
            "diurnal_config": {
                "mode": self.diurnal_config.mode,
                "daytime_factor": self.diurnal_config.daytime_factor,
                "nighttime_factor": self.diurnal_config.nighttime_factor,
                "gamma": self.diurnal_config.gamma
            },
            "seasonal_config": {
                "dry_season_factor": self.seasonal_config.dry_season_factor,
                "rainy_season_factor": self.seasonal_config.rainy_season_factor
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FullModelConfig':
        """Load configuration from a dictionary."""
        return cls(
            risk_weights=RiskWeights(**data["risk_weights"]),
            human_risk_weights=HumanRiskWeights(**data["human_risk_weights"]),
            environmental_risk_weights=EnvironmentalRiskWeights(**data["environmental_risk_weights"]),
            species_configs={
                name: SpeciesConfig(**sp_data)
                for name, sp_data in data["species_configs"].items()
            },
            diurnal_config=DiurnalConfig(**data["diurnal_config"]),
            seasonal_config=SeasonalConfig(**data["seasonal_config"])
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'FullModelConfig':
        """Load configuration from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, filepath: str) -> 'FullModelConfig':
        """Load configuration from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())

    @classmethod
    def load_or_default(cls, filepath: Optional[str] = None) -> 'FullModelConfig':
        """
        Load configuration from file, or return default if no file specified.

        Args:
            filepath: Path to configuration file, or None for default

        Returns:
            FullModelConfig instance
        """
        if filepath and os.path.exists(filepath):
            return cls.load(filepath)
        return cls.default()


# Default configurations
DEFAULT_RISK_WEIGHTS = RiskWeights(
    human_weight=0.4,
    environmental_weight=0.3,
    density_weight=0.3
)

# Import os for path checking
import os
