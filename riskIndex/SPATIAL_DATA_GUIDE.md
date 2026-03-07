# Spatial Data Generator Guide

## Overview

The Spatial Data Generator creates realistic continuous spatial maps for wildlife reserve risk modeling using Gaussian smoothing techniques. This guide describes the generated data structures, formats, and usage patterns.

## Data Generation Process

### Core Concept

The generator uses **Gaussian smoothing** to create realistic continuous spatial patterns instead of discrete grid cells. This produces natural-looking transitions between different terrain types, vegetation zones, and animal distributions.

### Random Seed

For reproducibility, you can specify a random seed:

```python
generator = SpatialDataGenerator(config=config, seed=42)
```

## Configuration

### SpatialConfig Dataclass

#### Basic Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | int | 120 | Size of the square map (pixels) |
| `season` | str | "rainy" | Season: "rainy" or "dry" |
| `hour` | int | 22 | Hour of day (0-23) |
| `output_dir` | str | "maps" | Directory for saved maps |
| `save_maps` | bool | True | Whether to save image maps |
| `save_data` | bool | True | Whether to save raw data (NumPy/CSV) |
| `map_format` | str | "jpg" | Image format: "jpg", "png", or "both" |

#### Smoothing Scales

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `terrain_smooth_scale` | float | 10.0 | Gaussian sigma for terrain |
| `water_smooth_scale` | float | 8.0 | Gaussian sigma for water bodies |
| `animal_smooth_scale` | float | 6.0 | Gaussian sigma for animal distributions |

#### Terrain Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `terrain_threshold_lowland` | float | 0.3 | Threshold for lowland classification |
| `terrain_threshold_plain` | float | 0.55 | Threshold for plain classification |
| `terrain_threshold_hill` | float | 0.75 | Threshold for hill classification |

- Values below `terrain_threshold_lowland` = Lowland (0)
- Values between thresholds = Plain (1), Hill (2)
- Values above `terrain_threshold_hill` = Mountain (3)

#### Water Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `water_threshold` | float | 0.65 | Threshold for water body generation |

- Lower values create larger water bodies
- Water only appears in lowland areas

#### Road Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `num_roads` | int | 4 | Number of roads to generate |

#### Waterhole Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `waterhole_probability` | float | 0.02 | Probability of waterhole near water |
| `waterhole_search_range` | int | 2 | Search range for nearby water (pixels) |

#### Species Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rhino_weight` | float | 0.5 | Weight for rhino in density calculation |
| `elephant_weight` | float | 0.3 | Weight for elephant in density calculation |
| `bird_weight` | float | 0.2 | Weight for bird in density calculation |
| `rhino_season_multipliers` | tuple | (1.2, 1.0) | Seasonal multipliers (rainy, dry) |
| `elephant_season_multipliers` | tuple | (1.3, 0.9) | Seasonal multipliers (rainy, dry) |
| `bird_season_multipliers` | tuple | (1.5, 0.8) | Seasonal multipliers (rainy, dry) |

Weights must sum to 1.0.

#### Fire Risk Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fire_risk_by_vegetation` | tuple | (0.8, 0.6, 0.5, 0.2) | Fire risk by vegetation type |

Tuple order: (grass, shrub, forest, wetland)

#### Risk Calculation Weights

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `risk_weight_human` | float | 0.4 | Weight for human risk component |
| `risk_weight_environmental` | float | 0.3 | Weight for environmental risk component |
| `risk_weight_density` | float | 0.3 | Weight for animal density component |

Weights must sum to 1.0.

#### Human Risk Sub-weights

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `human_risk_weight_boundary` | float | 0.4 | Weight for boundary proximity |
| `human_risk_weight_road` | float | 0.35 | Weight for road proximity |
| `human_risk_weight_water` | float | 0.25 | Weight for water proximity |

Weights must sum to 1.0.

#### Environmental Risk Sub-weights

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `env_risk_weight_fire` | float | 0.6 | Weight for fire risk |
| `env_risk_weight_terrain` | float | 0.4 | Weight for terrain complexity |

Weights must sum to 1.0.

#### Temporal Factors

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temporal_factor_night` | float | 1.3 | Risk multiplier at night |
| `temporal_factor_day` | float | 1.0 | Risk multiplier during day |
| `temporal_factor_rainy` | float | 1.2 | Risk multiplier in rainy season |
| `temporal_factor_dry` | float | 1.0 | Risk multiplier in dry season |

### Configuration File Usage

Configurations can be saved and loaded from JSON files:

```python
from risk_model.data import SpatialConfig

# Create and save a configuration
config = SpatialConfig(
    size=120,
    season="rainy",
    hour=22,
    num_roads=6,
    waterhole_probability=0.05
)
config.save("my_config.json")

# Load from file
loaded_config = SpatialConfig.load("my_config.json")
```

See `config_example.json` for a complete template.

## Generated Maps

All maps are NumPy arrays of shape `(size, size)`.

### 1. Terrain Map (`terrain`)

Discrete terrain classification with natural boundaries.

| Value | Type | Description |
|-------|------|-------------|
| 0 | Lowland | Flat areas, ideal for water bodies |
| 1 | Plain | Grassland areas |
| 2 | Hill | Sloped terrain |
| 3 | Mountain | High elevation, forested |

**Generation Method:**
- Smooth random noise with Gaussian filter (σ=10.0 by default)
- Threshold classification using `terrain_threshold_*` config values

### 2. Water Bodies Map (`water`)

Binary map indicating permanent water bodies.

| Value | Description |
|-------|-------------|
| 0 | Land |
| 1 | Water |

**Generation Constraints:**
- Only appears in lowland areas (terrain == 0)
- Smooth noise with σ=8.0 by default
- Threshold using `water_threshold` config

### 3. Vegetation Map (`vegetation`)

Vegetation types derived from terrain and water.

| Value | Type | Associated Terrain |
|-------|------|-------------------|
| 0 | None | (unused) |
| 1 | Grass | Plain (terrain == 1) |
| 2 | Shrub | Hill (terrain == 2) |
| 3 | Forest | Mountain (terrain == 3) |
| 4 | Wetland | Water (water == 1) |

### 4. Roads Map (`roads`)

Road network with natural-looking paths.

| Value | Description |
|-------|-------------|
| 0 | No road |
| 1 | Road |

**Generation Algorithm:**
- Creates `num_roads` roads from top to bottom
- Random walk with ±1 or 0 lateral movement
- Avoids water bodies
- Natural, meandering path appearance

### 5. Waterholes Map (`waterholes`)

Small water sources near larger water bodies.

| Value | Description |
|-------|-------------|
| 0 | No waterhole |
| 1 | Waterhole |

**Placement Rules:**
- Must be within `waterhole_search_range` pixels of water
- `waterhole_probability` chance per eligible location
- Not in water

### 6. Animal Density Maps

Continuous density values in range [0, 1].

#### Rhino Density (`rhino`)
- Prefers grassland (vegetation == 1)
- Smooth noise with σ=6.0 by default
- Zero in non-grass areas

#### Elephant Density (`elephant`)
- Prefers grassland and forest (vegetation == 1 or 3)
- Smooth noise with σ=6.0 by default
- Zero elsewhere

#### Bird Density (`bird`)
- Prefers wetlands (vegetation == 4)
- Smooth noise with σ=6.0 by default
- Zero in non-wetland areas

#### Total Animal Density (`animal_density`)
- Weighted sum using `rhino_weight`, `elephant_weight`, `bird_weight`
- Applied with seasonal multipliers
- Not normalized to preserve relative abundances

### 7. Fire Risk Map (`fire_risk`)

Fire risk based on vegetation type.

| Vegetation | Default Fire Risk |
|------------|-----------|
| Grass (1) | 0.8 |
| Shrub (2) | 0.6 |
| Forest (3) | 0.5 |
| Wetland (4) | 0.2 |

Configurable via `fire_risk_by_vegetation`.

### 8. Distance Maps

Continuous distance measurements in pixel units.

#### Distance to Road (`distance_to_road`)
- Euclidean distance to nearest road pixel
- Maximum value = map size where no roads exist

#### Distance to Water (`distance_to_water`)
- Euclidean distance to nearest waterhole
- Note: This measures distance to waterholes, not permanent water bodies

#### Distance to Boundary (`distance_to_boundary`)
- Manhattan distance to nearest edge
- `min(i, j, size-i, size-j)`

### 9. Risk Map (`risk_map`)

Final normalized risk index in range [0, 1].

**Calculation Formula (configurable weights):**

```
Human Risk (H) = human_risk_weight_boundary * (1 - normalized_boundary_dist)
               + human_risk_weight_road * (1 - normalized_road_dist)
               + human_risk_weight_water * (1 - normalized_water_dist)

Environmental Risk (E) = env_risk_weight_fire * fire_risk
                       + env_risk_weight_terrain * (terrain/3)

Density Value (D) = rhino_weight * rhino * rhino_season_mult
                  + elephant_weight * elephant * elephant_season_mult
                  + bird_weight * bird * bird_season_mult

Time Factor (T) = temporal_factor_night if hour < 6 or hour > 18
                else temporal_factor_day

Season Factor (S) = temporal_factor_rainy if season == "rainy"
                  else temporal_factor_dry

Raw Risk = (risk_weight_human * H
          + risk_weight_environmental * E
          + risk_weight_density * D) * T * S

Risk Map = normalize(Raw Risk) to [0, 1]
```

## Usage Examples

### Basic Usage

```python
from risk_model.data import SpatialDataGenerator, SpatialConfig

# Create configuration
config = SpatialConfig(
    size=120,
    season="rainy",
    hour=22,
    output_dir="my_maps",
    save_maps=True
)

# Create generator and generate maps
generator = SpatialDataGenerator(config=config, seed=42)
maps = generator.generate()

# Access individual maps
print(f"Risk map shape: {maps.risk_map.shape}")
print(f"Max risk: {maps.risk_map.max()}")
print(f"Min risk: {maps.risk_map.min()}")
```

### Custom Configuration Example

```python
# Configuration focused on bird conservation with many waterholes
config = SpatialConfig(
    size=100,
    season="rainy",
    hour=6,
    num_roads=3,
    waterhole_probability=0.08,
    waterhole_search_range=3,
    rhino_weight=0.2,
    elephant_weight=0.2,
    bird_weight=0.6,
    bird_season_multipliers=(2.0, 1.0),
    temporal_factor_night=1.5
)

generator = SpatialDataGenerator(config=config, seed=42)
maps = generator.generate()
```

### Accessing Specific Data

```python
# Get high-risk areas
high_risk_mask = maps.risk_map > 0.7
high_risk_count = np.sum(high_risk_mask)
print(f"High risk pixels: {high_risk_count}")

# Get animal density in specific region
region = maps.animal_density[20:40, 20:40]
print(f"Regional animal density mean: {region.mean()}")

# Find all water locations
water_coords = np.argwhere(maps.water == 1)
print(f"Water body pixels: {len(water_coords)}")
```

### Batch Generation for Different Times

```python
# Generate maps for different times of day
for hour in [0, 6, 12, 18]:
    config = SpatialConfig(
        season="rainy",
        hour=hour,
        output_dir=f"maps_{hour:02d}",
        save_maps=True
    )
    generator = SpatialDataGenerator(config=config, seed=42)
    maps = generator.generate()
    print(f"Hour {hour}: mean risk = {maps.risk_map.mean():.4f}")
```

## Output Files

### Image Maps

When `save_maps=True`, the following image files are generated:

| Filename | Colormap | Description |
|----------|----------|-------------|
| `01_terrain.*` | terrain | 4-level terrain classification |
| `01a_lowland.*` | Blues | Lowland distribution mask |
| `01b_plain.*` | YlGn | Plain distribution mask |
| `01c_hill.*` | BrBG | Hill distribution mask |
| `01d_mountain.*` | terrain | Mountain distribution mask |
| `02_water_bodies.*` | Blues | Permanent water bodies |
| `02a_water_only.*` | Blues | Water body distribution mask |
| `03_waterholes.*` | Blues | Waterhole locations |
| `04_vegetation.*` | Greens | Vegetation types |
| `04a_grassland.*` | YlGn | Grassland distribution mask |
| `04b_shrubland.*` | Greens | Shrubland distribution mask |
| `04c_forest.*` | viridis | Forest distribution mask |
| `04d_wetland.*` | Blues | Wetland distribution mask |
| `05_roads.*` | gray | Road network |
| `06_fire_risk.*` | YlOrRd | Fire risk index |
| `07a_rhino_density.*` | YlGn | Rhinoceros density distribution |
| `07b_elephant_density.*` | YlGn | Elephant density distribution |
| `07c_bird_density.*` | YlGnBu | Bird density distribution |
| `07_total_animal_density.*` | YlGn | Combined animal density |
| `08_risk_index.*` | hot | Final risk heatmap with colorbar |

### Raw Data Files

When `save_data=True`, the following files are saved in the `data/` directory:

| File | Description |
|------|-------------|
| `terrain.npy` | Terrain classification map |
| `water.npy` | Water bodies map |
| `vegetation.npy` | Vegetation map |
| `roads.npy` | Roads map |
| `waterholes.npy` | Waterholes map |
| `rhino.npy` | Rhino density map |
| `elephant.npy` | Elephant density map |
| `bird.npy` | Bird density map |
| `animal_density.npy` | Total animal density |
| `fire_risk.npy` | Fire risk map |
| `distance_to_road.npy` | Distance to roads map |
| `distance_to_water.npy` | Distance to waterholes map |
| `distance_to_boundary.npy` | Distance to boundary map |
| `risk_map.npy` | Risk index map |
| `config.json` | Full generation configuration |

### CSV Files

CSV versions are also saved in the `csv/` directory for easy viewing.

## Dependencies

### Required
- `numpy` - Array operations

### Optional (with fallbacks)
- `scipy` - Gaussian filtering (falls back to convolution implementation)
- `matplotlib` - Map visualization (skips saving if unavailable)

## Data Validation

All maps are validated implicitly through their generation:
- Terrain values: {0, 1, 2, 3}
- Binary maps (water, roads, waterholes): {0, 1}
- Vegetation values: {0, 1, 2, 3, 4}
- Continuous maps: [0, 1] normalized
- Distance maps: ≥ 0

## Notes on Realism

1. **Gaussian Smoothing Scale**: Larger sigma values create broader, more realistic patterns
2. **Ecological Constraints**: Animals are constrained to suitable vegetation types
3. **Hydrological Logic**: Water only appears in lowlands, waterholes near water
4. **Temporal Variation**: Risk varies by time of day and season
5. **Configurable Weights**: All aspects of the model can be customized via configuration

## Extension Points

To customize the generator:

1. Subclass `SpatialDataGenerator`
2. Override specific `generate_*` methods
3. Add new map types to `SpatialMaps` dataclass
4. Use configuration options to tweak behavior without code changes

Example:
```python
class CustomSpatialGenerator(SpatialDataGenerator):
    def generate_fire_risk(self, vegetation: np.ndarray) -> np.ndarray:
        # Custom fire risk logic
        fire_risk = np.zeros_like(vegetation, dtype=float)
        # ... your custom logic ...
        return fire_risk
```
