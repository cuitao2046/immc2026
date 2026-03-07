"""
Weight management system for the risk model.
"""

from typing import Dict, Any, Optional
import json

from .defaults import (
    RiskWeights,
    HumanRiskWeights,
    EnvironmentalRiskWeights,
    SpeciesConfig,
    DiurnalConfig,
    SeasonalConfig,
    FullModelConfig,
    DEFAULT_RISK_WEIGHTS
)


class WeightManager:
    """
    Manages weight configurations for the risk model.
    """

    def __init__(self, config: Optional[FullModelConfig] = None):
        """
        Initialize the weight manager.

        Args:
            config: Full model configuration, uses default if None
        """
        self.config = config or FullModelConfig.default()

    @classmethod
    def from_file(cls, filepath: Optional[str] = None) -> 'WeightManager':
        """
        Create a WeightManager from a configuration file.

        Args:
            filepath: Path to JSON configuration file, or None for default

        Returns:
            WeightManager instance
        """
        config = FullModelConfig.load_or_default(filepath)
        return cls(config)

    def get_risk_weights(self) -> RiskWeights:
        """Get the composite risk weights."""
        return self.config.risk_weights

    def get_human_risk_weights(self) -> HumanRiskWeights:
        """Get the human risk weights."""
        return self.config.human_risk_weights

    def get_environmental_risk_weights(self) -> EnvironmentalRiskWeights:
        """Get the environmental risk weights."""
        return self.config.environmental_risk_weights

    def get_species_configs(self) -> Dict[str, SpeciesConfig]:
        """Get the species configurations."""
        return self.config.species_configs

    def get_diurnal_config(self) -> DiurnalConfig:
        """Get the diurnal configuration."""
        return self.config.diurnal_config

    def get_seasonal_config(self) -> SeasonalConfig:
        """Get the seasonal configuration."""
        return self.config.seasonal_config

    def set_risk_weights(
        self,
        human_weight: Optional[float] = None,
        environmental_weight: Optional[float] = None,
        density_weight: Optional[float] = None
    ) -> None:
        """
        Update composite risk weights.

        Args:
            human_weight: New human risk weight (optional)
            environmental_weight: New environmental risk weight (optional)
            density_weight: New density weight (optional)
        """
        current = self.config.risk_weights
        self.config.risk_weights = RiskWeights(
            human_weight=human_weight if human_weight is not None else current.human_weight,
            environmental_weight=environmental_weight if environmental_weight is not None else current.environmental_weight,
            density_weight=density_weight if density_weight is not None else current.density_weight
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return self.config.to_dict()

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return self.config.to_json(indent=indent)

    def save(self, filepath: str) -> None:
        """Save configuration to a JSON file."""
        self.config.save(filepath)

    @classmethod
    def load(cls, filepath: str) -> 'WeightManager':
        """Load configuration from a JSON file."""
        config = FullModelConfig.load(filepath)
        return cls(config)


# Backward compatibility
class ModelConfig:
    """
    Legacy model configuration (backward compatibility).

    Note: Use FullModelConfig for new code.
    """

    def __init__(
        self,
        risk_weights: RiskWeights,
        human_risk_weights: HumanRiskWeights,
        environmental_risk_weights: EnvironmentalRiskWeights
    ):
        self.risk_weights = risk_weights
        self.human_risk_weights = human_risk_weights
        self.environmental_risk_weights = environmental_risk_weights

    @classmethod
    def default(cls) -> 'ModelConfig':
        """Create a model configuration with default values."""
        full_config = FullModelConfig.default()
        return cls(
            risk_weights=full_config.risk_weights,
            human_risk_weights=full_config.human_risk_weights,
            environmental_risk_weights=full_config.environmental_risk_weights
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            'risk_weights': {
                'human_weight': self.risk_weights.human_weight,
                'environmental_weight': self.risk_weights.environmental_weight,
                'density_weight': self.risk_weights.density_weight
            },
            'human_risk_weights': {
                'boundary_weight': self.human_risk_weights.boundary_weight,
                'road_weight': self.human_risk_weights.road_weight,
                'water_weight': self.human_risk_weights.water_weight
            },
            'environmental_risk_weights': {
                'fire_weight': self.environmental_risk_weights.fire_weight,
                'terrain_weight': self.environmental_risk_weights.terrain_weight
            }
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Load configuration from a dictionary."""
        return cls(
            risk_weights=RiskWeights(**data['risk_weights']),
            human_risk_weights=HumanRiskWeights(**data['human_risk_weights']),
            environmental_risk_weights=EnvironmentalRiskWeights(**data['environmental_risk_weights'])
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelConfig':
        """Load configuration from JSON string."""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def load(cls, filepath: str) -> 'ModelConfig':
        """Load configuration from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
