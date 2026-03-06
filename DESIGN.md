# CPI (Conservation Priority Index) Module Design Document

## Overview

This module calculates Conservation Priority Index (CPI) for wildlife monitoring device placement in protected areas. It combines ecological factors, fire risk, travel time, and species importance to prioritize monitoring locations.

## Architecture

```
cpi.py
├── Geometry Utilities
├── Minimum Enclosing Circle
├── Fire Risk Model
├── Shortest Path (Dijkstra)
├── CPI Calculation
└── Example Pipeline
```

## Module Breakdown

### 1. Basic Geometry Utilities (`dms_to_decimal`, `point_in_polygon`, `dist2`)

**Purpose**: Handle coordinate conversions and spatial queries.

| Function | Description |
|----------|-------------|
| `dms_to_decimal()` | Convert DMS (degrees-minutes-seconds) format (e.g., `19°26'55.93"S`) to decimal degrees |
| `point_in_polygon()` | Ray casting algorithm to test if a point lies inside a polygon |
| `dist2()` | Squared Euclidean distance between two points (for efficiency) |

### 2. Minimum Enclosing Circle (`minimum_enclosing_circle`)

**Purpose**: Compute the smallest circle enclosing a set of points (used for fire quadrilaterals).

| Function | Description |
|----------|-------------|
| `_circle_from_2_points()` | Circle from diameter endpoints |
| `_circle_from_3_points()` | Circumcircle of triangle (returns None if colinear) |
| `_is_in_circle()` | Test point inclusion in circle |
| `minimum_enclosing_circle()` | Welzl's randomized algorithm (expected O(n) time) |

### 3. Fire Risk Model (`build_fire_risk_function`)

**Purpose**: Create a spatial fire risk function from fire quadrilaterals.

**Configuration**:
- `combine`: `"max"` (take maximum risk) or `"sum"` (sum risks)
- `radial_mode`: `"linear"` (1 at center, 0 at edge) or `"gaussian"` (exponential decay)
- `gaussian_alpha`: Controls Gaussian spread (smaller = steeper)

**Returns**: A function `fire_risk(lon, lat) → [0,1]`

### 4. Shortest Path Travel Time (`dijkstra_multi_source`)

**Purpose**: Compute shortest travel time from multiple source nodes (camps) through terrain.

| Parameter | Type | Description |
|-----------|------|-------------|
| `nodes` | `List[int]` | All cell IDs |
| `neighbors` | `Dict[int, List[int]]` | Adjacency list |
| `terrain_cost` | `Dict[int, float]` | Cost to enter each node |
| `sources` | `List[int]` | Source node IDs (camps) |
| `blocked` | `Callable[[int], bool]` | Optional impassable node test |

**Returns**: `Dict[int, float]` - travel time from nearest source to each node

### 5. CPI Calculation (`compute_cpi_for_cell`)

**Purpose**: Core CPI formula for a single cell, species, and device type.

**Formula**:
```
CPI = (D + (1 - D) * η * S) * W_i - Φ - γ_fire
```

| Symbol | Meaning | Source |
|--------|---------|--------|
| D | Deterrence effect | `params["D_device"]` (0 if no device) |
| η | Verification effectiveness | `eta_camera` or `eta_uav` |
| S | Survival probability | `exp(-λ * T_c)` |
| λ | Survival decay rate | `params["lambda"]` |
| T_c | Travel time to cell | `precomp["T_c"][cell_id]` |
| W_i | Species weight | `params["W"][species_id]` |
| Φ | Ecological penalty | `eco_penalty` if sensitive + device |
| γ_fire | Fire penalty | `gamma_max * fire_risk` |

### 6. End-to-End Pipeline (`build_and_compute_example`)

**Purpose**: Demonstration of the complete workflow.

Steps:
1. Define park boundary (DMS → decimal)
2. Define fire quadrilaterals
3. Build fire risk function
4. Define cell grid, adjacency, terrain costs
5. Compute travel times from camps
6. Assemble precomputed maps
7. Set parameters
8. Compute CPI for all cell-species-device combinations

## Data Flow

```
Park Boundary ──┐
                ├──> Fire Risk Function ──> Fire Penalty
Fire Quads ─────┘

Cells ──┐
        ├──> Dijkstra ──> Travel Time (T_c) ──> Survival (S)
Terrain ─┘
Camps ───┘

Species Weights ──┐
Ecological Sens. ──├──> CPI Calculation
Fire Penalty ──────┘
Travel Time ───────┘
Device Type ───────┘
```

## Parameters

| Parameter | Type | Typical Value | Description |
|-----------|------|---------------|-------------|
| `lambda` | float | 0.4 | Survival decay rate |
| `D_device` | float | 0.8 | Deterrence when device present |
| `eta_camera` | float | 0.5 | Verification effectiveness (camera) |
| `eta_uav` | float | 1.0 | Verification effectiveness (UAV) |
| `eco_penalty` | float | 50.0 | Penalty for placing device in sensitive area |
| `W` | dict | `{"rhino": 10.0, "elephant": 2.0}` | Species importance weights |
| `W_base` | float | 0.5 | Baseline weight for non-habitat cells |
| `gamma_max` | float | 20.0 | Maximum fire penalty |

## Extension Points

1. **Alternative Risk Models**: Replace `build_fire_risk_function()` with custom implementation
2. **Different Pathfinding**: Swap `dijkstra_multi_source()` for A* or other algorithms
3. **Additional Penalties**: Extend CPI formula with more terms in `compute_cpi_for_cell()`
4. **Optimization**: Precompute more values in `precomp` dict for repeated CPI calculations

## Dependencies

- Python standard library only: `math`, `random`, `heapq`, `typing`
