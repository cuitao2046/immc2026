import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GridData:
    grid_id: int
    center_lat: float
    center_lon: float
    season: int = 1


@dataclass
class GeoFeature:
    name: str
    coordinates: List[Tuple[float, float]]


@dataclass
class RiskCoefficients:
    alpha_1: float = 0.4
    alpha_2: float = 0.4
    alpha_3: float = 0.2
    beta_1: float = 0.5
    beta_2: float = 0.5
    omega_1: float = 0.6
    omega_2: float = 0.4
    w_rhino: float = 0.5
    w_ele: float = 0.3
    w_bird: float = 0.2


class RiskCalculator:
    def __init__(self, coefficients: Optional[RiskCoefficients] = None):
        self.coeffs = coefficients or RiskCoefficients()
        self._validate_coefficients()
        
    def _validate_coefficients(self):
        if not np.isclose(self.coeffs.alpha_1 + self.coeffs.alpha_2 + self.coeffs.alpha_3, 1.0, atol=0.01):
            raise ValueError("alpha coefficients must sum to 1.0")
        if not np.isclose(self.coeffs.omega_1 + self.coeffs.omega_2, 1.0, atol=0.01):
            raise ValueError("omega coefficients must sum to 1.0")
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c
    
    def calculate_distance_to_feature(self, grid: GridData, feature: GeoFeature) -> float:
        min_dist = float('inf')
        for coord in feature.coordinates:
            dist = self.haversine_distance(grid.center_lat, grid.center_lon, coord[0], coord[1])
            min_dist = min(min_dist, dist)
        return min_dist
    
    def normalize_distance(self, distance: float, max_distance: float = 100.0) -> float:
        return 1.0 - min(distance / max_distance, 1.0)
    
    def calculate_human_risk(self, grid: GridData, boundary: GeoFeature, 
                            roads: List[GeoFeature], water_holes: List[GeoFeature]) -> float:
        d_boundary = self.calculate_distance_to_feature(grid, boundary)
        d_boundary_norm = self.normalize_distance(d_boundary, max_distance=50.0)
        
        min_road_dist = float('inf')
        for road in roads:
            dist = self.calculate_distance_to_feature(grid, road)
            min_road_dist = min(min_road_dist, dist)
        d_road_norm = self.normalize_distance(min_road_dist, max_distance=20.0)
        
        min_water_dist = float('inf')
        for water in water_holes:
            dist = self.calculate_distance_to_feature(grid, water)
            min_water_dist = min(min_water_dist, dist)
        d_water_norm = self.normalize_distance(min_water_dist, max_distance=15.0)
        
        H_i = (self.coeffs.alpha_1 * d_boundary_norm + 
               self.coeffs.alpha_2 * d_road_norm + 
               self.coeffs.alpha_3 * d_water_norm)
        return H_i
    
    def get_terrain_score(self, grid: GridData, savanna: GeoFeature, 
                         jungle: GeoFeature, salt_marsh: GeoFeature) -> float:
        dist_savanna = self.calculate_distance_to_feature(grid, savanna)
        dist_jungle = self.calculate_distance_to_feature(grid, jungle)
        dist_marsh = self.calculate_distance_to_feature(grid, salt_marsh)
        
        min_dist = min(dist_savanna, dist_jungle, dist_marsh)
        
        if min_dist == dist_marsh:
            return 0.8
        elif min_dist == dist_jungle:
            return 0.6
        else:
            return 0.4
    
    def calculate_environmental_risk(self, grid: GridData, fire_areas: List[GeoFeature],
                                    savanna: GeoFeature, jungle: GeoFeature, 
                                    salt_marsh: GeoFeature, fire_frequency: float = 0.5) -> float:
        V_fire = fire_frequency
        C_terrain = self.get_terrain_score(grid, savanna, jungle, salt_marsh)
        
        E_i = self.coeffs.beta_1 * V_fire + self.coeffs.beta_2 * C_terrain
        return E_i
    
    def get_species_density(self, grid: GridData, species: str, season: int,
                           rhino_areas: List[GeoFeature], ele_areas: List[GeoFeature],
                           bird_areas: List[GeoFeature]) -> float:
        season_factor = 1.0
        if season == 1:
            season_factor = 1.2
        elif season == 2:
            season_factor = 0.8
        
        if species == 'rhino':
            areas = rhino_areas
            base_density = 0.7
        elif species == 'elephant':
            areas = ele_areas
            base_density = 0.5
        elif species == 'bird':
            areas = bird_areas
            base_density = 0.3
        else:
            return 0.0
        
        max_density = 0.0
        for area in areas:
            dist = self.calculate_distance_to_feature(grid, area)
            if dist < 5.0:
                density = base_density * (1 - dist / 5.0)
                max_density = max(max_density, density)
        
        return max_density * season_factor
    
    def calculate_species_risk(self, grid: GridData, season: int,
                             rhino_areas: List[GeoFeature], ele_areas: List[GeoFeature],
                             bird_areas: List[GeoFeature]) -> float:
        D_rhino = self.get_species_density(grid, 'rhino', season, rhino_areas, ele_areas, bird_areas)
        D_ele = self.get_species_density(grid, 'elephant', season, rhino_areas, ele_areas, bird_areas)
        D_bird = self.get_species_density(grid, 'bird', season, rhino_areas, ele_areas, bird_areas)
        
        species_risk = (self.coeffs.w_rhino * D_rhino + 
                       self.coeffs.w_ele * D_ele + 
                       self.coeffs.w_bird * D_bird)
        return species_risk
    
    def calculate_risk_score(self, grid: GridData, boundary: GeoFeature,
                           roads: List[GeoFeature], water_holes: List[GeoFeature],
                           fire_areas: List[GeoFeature], savanna: GeoFeature,
                           jungle: GeoFeature, salt_marsh: GeoFeature,
                           rhino_areas: List[GeoFeature], ele_areas: List[GeoFeature],
                           bird_areas: List[GeoFeature], fire_frequency: float = 0.5) -> float:
        H_i = self.calculate_human_risk(grid, boundary, roads, water_holes)
        E_i = self.calculate_environmental_risk(grid, fire_areas, savanna, jungle, salt_marsh, fire_frequency)
        species_risk = self.calculate_species_risk(grid, grid.season, rhino_areas, ele_areas, bird_areas)
        
        R_prime = (self.coeffs.omega_1 * H_i + self.coeffs.omega_2 * E_i) * species_risk
        return R_prime
    
    def normalize_to_0_100(self, risk_scores: List[float]) -> List[float]:
        if not risk_scores:
            return []
        
        min_score = min(risk_scores)
        max_score = max(risk_scores)
        
        if max_score == min_score:
            return [50.0] * len(risk_scores)
        
        normalized = [(score - min_score) / (max_score - min_score) * 100 for score in risk_scores]
        return normalized
    
    def calculate_all_grids(self, grids: List[GridData], boundary: GeoFeature,
                          roads: List[GeoFeature], water_holes: List[GeoFeature],
                          fire_areas: List[GeoFeature], savanna: GeoFeature,
                          jungle: GeoFeature, salt_marsh: GeoFeature,
                          rhino_areas: List[GeoFeature], ele_areas: List[GeoFeature],
                          bird_areas: List[GeoFeature], fire_frequency: float = 0.5) -> Dict[int, float]:
        risk_scores = {}
        
        for grid in grids:
            R_prime = self.calculate_risk_score(grid, boundary, roads, water_holes,
                                               fire_areas, savanna, jungle, salt_marsh,
                                               rhino_areas, ele_areas, bird_areas, fire_frequency)
            risk_scores[grid.grid_id] = R_prime
        
        scores_list = list(risk_scores.values())
        normalized_scores = self.normalize_to_0_100(scores_list)
        
        result = {}
        for grid_id, norm_score in zip(risk_scores.keys(), normalized_scores):
            result[grid_id] = norm_score
        
        return result
