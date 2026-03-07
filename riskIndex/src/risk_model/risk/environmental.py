"""
Environmental risk calculator module.
"""

from typing import Optional

from ..core.environment import Environment
from ..config import EnvironmentalRiskWeights


class EnvironmentalRiskCalculator:
    """
    Calculates environmental risk based on fire risk and terrain complexity.
    """

    def __init__(self, weights: Optional[EnvironmentalRiskWeights] = None):
        """
        Initialize the environmental risk calculator.

        Args:
            weights: Weight configuration for environmental risk factors
        """
        self.weights = weights or EnvironmentalRiskWeights()

    def calculate(self, environment: Environment) -> float:
        """
        Calculate environmental risk for a grid cell.

        Args:
            environment: Environmental conditions for the grid cell

        Returns:
            Environmental risk value [0, 1]
        """
        fire_risk = environment.get_fire_risk_factor()
        terrain_risk = environment.get_terrain_risk_factor()

        return (
            self.weights.fire_weight * fire_risk +
            self.weights.terrain_weight * terrain_risk
        )

    def calculate_component_breakdown(
        self,
        environment: Environment
    ) -> tuple[float, float]:
        """
        Calculate the individual components of environmental risk.

        Args:
            environment: Environmental conditions for the grid cell

        Returns:
            Tuple of (fire_risk_component, terrain_risk_component)
        """
        fire_risk = environment.get_fire_risk_factor()
        terrain_risk = environment.get_terrain_risk_factor()

        return (
            self.weights.fire_weight * fire_risk,
            self.weights.terrain_weight * terrain_risk
        )
