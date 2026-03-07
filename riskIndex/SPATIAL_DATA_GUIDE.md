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

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | int | 120 | Size of the square map (pixels) |
| `season` | str | "rainy" | Season: "rainy" or "dry" |
| `hour` | int | 22 | Hour of day (0-23) |
| `terrain_smooth_scale` | float | 10.0 | Gaussian sigma for terrain |
| `water_smooth_scale` | float | 8.0 | Gaussian sigma for water bodies |
| `animal_smooth_scale` | float | 6.0 | Gaussian sigma for animal distributions |
| `output_dir` | str | "maps" | Directory for saved maps |
| `save_maps` | bool | True | Whether to save PNG maps |

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
- Smooth random noise with Gaussian filter (σ=10.0)
- Threshold at 0.3, 0.55, 0.75 for classifications

### 2. Water Bodies Map (`water`)

Binary map indicating permanent water bodies.

| Value | Description |
|-------|-------------|
| 0 | Land |
| 1 | Water |

**Generation Constraints:**
- Only appears in lowland areas (terrain == 0)
- Smooth noise with σ=8.0
- Threshold at 0.65

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
- Creates 4 roads from top to bottom
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
- Must be within 2 pixels of water
- 2% probability per eligible location
- Not in water

### 6. Animal Density Maps

Continuous density values in range [0, 1].

#### Rhino Density (`rhino`)
- Prefers grassland (vegetation == 1)
- Smooth noise with σ=6.0
- Zero in non-grass areas

#### Elephant Density (`elephant`)
- Prefers grassland and forest (vegetation == 1 or 3)
- Smooth noise with σ=6.0
- Zero elsewhere

#### Bird Density (`bird`)
- Prefers wetlands (vegetation == 4)
- Smooth noise with σ=6.0
- Zero in non-wetland areas

#### Total Animal Density (`animal_density`)
- Sum: `rhino + elephant + bird`
- Not normalized to preserve relative abundances

### 7. Fire Risk Map (`fire_risk`)

Fire risk based on vegetation type.

| Vegetation | Fire Risk |
|------------|-----------|
| Grass (1) | 0.8 |
| Shrub (2) | 0.6 |
| Forest (3) | 0.5 |
| Wetland (4) | 0.2 |

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

**Calculation Formula:**

```
Human Risk (H) = 0.4 * (1/(d_boundary+1))
                + 0.35 * (1/(d_road+1))
                + 0.25 * (1/(d_water+1))

Environmental Risk (E) = 0.6 * fire_risk + 0.4 * (terrain/3)

Density Value (D) = 0.5 * rhino + 0.3 * elephant + 0.2 * bird

Time Factor (T) = 1.3 if hour < 6 or hour > 18 else 1.0
Season Factor (S) = 1.2 if season == "rainy" else 1.0

Raw Risk = (0.4*H + 0.3*E + 0.3*D) * T * S

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

When `save_maps=True`, the following PNG files are generated:

| Filename | Colormap | Description |
|----------|----------|-------------|
| `terrain_map.png` | terrain | 4-level terrain classification |
| `water_map.png` | Blues | Water bodies |
| `vegetation_map.png` | Greens | Vegetation types |
| `roads_map.png` | gray | Road network |
| `waterholes_map.png` | Blues | Waterhole locations |
| `animal_density_map.png` | YlGn | Combined animal density |
| `risk_map.png` | hot | Final risk heatmap with colorbar |

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

## Extension Points

To customize the generator:

1. Subclass `SpatialDataGenerator`
2. Override specific `generate_*` methods
3. Add new map types to `SpatialMaps` dataclass
4. Adjust weights in `calculate_risk()`

Example:
```python
class CustomSpatialGenerator(SpatialDataGenerator):
    def generate_fire_risk(self, vegetation: np.ndarray) -> np.ndarray:
        # Custom fire risk logic
        fire_risk = np.zeros_like(vegetation, dtype=float)
        # ... your custom logic ...
        return fire_risk
```
