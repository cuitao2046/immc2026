# Input Data Guide

## Table of Contents
1. [Coordinate Formats](#coordinate-formats)
2. [Park Boundary](#park-boundary)
3. [Fire Quadrilaterals](#fire-quadrilaterals)
4. [Cell Grid Data](#cell-grid-data)
5. [Graph Structure](#graph-structure)
6. [Terrain Costs](#terrain-costs)
7. [Precomputed Maps](#precomputed-maps)
8. [Parameters](#parameters)
9. [Complete Input Example](#complete-input-example)

---

## Coordinate Formats

### DMS Format (Degrees-Minutes-Seconds)
Used for park boundary input.

**Type**: `str`

**Format**: `{deg}°{min}'{sec}"{direction}`

**Examples**:
```python
"19°26'55.93\"S"   # South latitude
"14°24'43.35\"E"   # East longitude
```

**Directions**:
- Latitude: `N` (positive), `S` (negative)
- Longitude: `E` (positive), `W` (negative)

### Decimal Degrees
Used internally and for fire quads.

**Type**: `Tuple[float, float]`

**Format**: `(longitude, latitude)`

**Examples**:
```python
(16.595, -18.834)   # (lon, lat)
(14.41204167, -19.44886944)  # Converted from DMS
```

---

## Park Boundary

**Function Parameter**: `park_boundary`

**Type**: `List[Tuple[float, float]]`

**Description**: Polygon defining the protected area boundary.

**Requirements**:
- Must be a simple (non-self-intersecting) polygon
- Vertices ordered clockwise or counter-clockwise
- Coordinates in decimal degrees (lon, lat)
- First/last point can be same or different (automatically closed)

**Example**:
```python
park_boundary = [
    (14.412042, -19.448869),   # Corner 1: 14°24'43.35"E, 19°26'55.93"S
    (14.262811, -18.616883),   # Corner 2: 14°15'46.12"E, 18°37'00.78"S
    (17.149883, -18.485992),   # Corner 3: 17°08'59.58"E, 18°29'09.57"S
    (17.109472, -19.325883),   # Corner 4: 17°06'34.10"E, 19°19'33.18"S
]
```

**Conversion from DMS**:
```python
from cpi import dms_to_decimal

park_boundary = [
    (dms_to_decimal("14°24'43.35\"E"), dms_to_decimal("19°26'55.93\"S")),
    (dms_to_decimal("14°15'46.12\"E"), dms_to_decimal("18°37'00.78\"S")),
    (dms_to_decimal("17°08'59.58\"E"), dms_to_decimal("18°29'09.57\"S")),
    (dms_to_decimal("17°06'34.10\"E"), dms_to_decimal("19°19'33.18\"S")),
]
```

---

## Fire Quadrilaterals

**Function Parameter**: `fire_quads`

**Type**: `List[List[Tuple[float, float]]]`

**Description**: List of quadrilaterals defining fire risk zones. Each quad is converted to its minimum enclosing circle.

**Requirements**:
- Each quadrilateral has exactly 4 vertices
- Coordinates in decimal degrees (lon, lat)
- Can be convex or concave

**Example**:
```python
fire_quads = [
    # Fire zone 1
    [
        (16.595, -18.834),
        (17.116, -18.832),
        (16.552, -19.084),
        (17.093, -19.145)
    ],
    # Fire zone 2
    [
        (15.482, -19.289),
        (15.875, -19.310),
        (15.879, -19.114),
        (15.515, -19.140)
    ]
]
```

**Note**: If you have only one fire zone, still wrap it in a list: `[quad1]`

---

## Cell Grid Data

### Cell Dictionary

**Type**: `Dict[int, Dict[str, Any]]`

**Description**: Maps cell IDs to their properties.

**Structure**:
```python
cells = {
    cell_id: {
        "lon": float,           # Longitude in decimal degrees
        "lat": float,           # Latitude in decimal degrees
        "terrain": str,         # Terrain type key (see Terrain Costs)
        # Optional additional fields:
        "habitat": Dict[str, bool],  # Species habitat presence
        "eco_sensitive": bool,       # Ecologically sensitive area flag
    },
    ...
}
```

**Example with 982 hex cells**:
```python
cells = {
    1: {"lon": 16.7, "lat": -18.95, "terrain": "road"},
    2: {"lon": 15.7, "lat": -19.2, "terrain": "grass"},
    3: {"lon": 16.2, "lat": -18.6, "terrain": "grass"},
    # ... up to cell_id 982
}
```

---

## Graph Structure

### Neighbors (Adjacency List)

**Type**: `Dict[int, List[int]]`

**Description**: Defines which cells are adjacent (can move between them).

**Example (hex grid)**:
```python
neighbors = {
    1: [2, 3, 7, 8, 9, 10],      # Cell 1 has 6 neighbors
    2: [1, 3, 4, 11, 12, 13],    # Cell 2 has 6 neighbors
    3: [1, 2, 4, 5, 6, 7],        # etc.
    # ...
}
```

**For grid with uniform structure**:
```python
# If your cells form a grid, you might generate neighbors programmatically
# neighbors = generate_hex_neighbors(num_cells=982)
```

---

## Terrain Costs

### Terrain Weight Dictionary

**Type**: `Dict[str, float]`

**Description**: Maps terrain type names to traversal cost (time units).

**Special Values**:
- `float("inf")` - Impassable terrain (cannot enter)
- `1.0` - Fastest (e.g., road)
- Higher values = slower

**Example**:
```python
terrain_weight = {
    "road": 1.0,           # Fast movement on roads
    "grass": 3.0,          # Slower through grass
    "forest": 5.0,         # Dense forest
    "swamp": float("inf"), # Impassable
    "river": float("inf"),
}
```

### Terrain Cost per Cell

**Type**: `Dict[int, float]`

**Description**: Maps cell IDs directly to terrain cost (derived from above).

**Example**:
```python
terrain_cost = {
    1: 1.0,     # road
    2: 3.0,     # grass
    3: 5.0,     # forest
    4: float("inf"),  # swamp
    # ...
}
```

**How to build**:
```python
terrain_cost = {
    cell_id: terrain_weight[cells[cell_id]["terrain"]]
    for cell_id in cells
}
```

---

## Precomputed Maps

**Type**: `Dict[str, Any]`

**Description**: Container for precomputed values used repeatedly in CPI calculations.

### Structure

```python
precomp = {
    # Required fields:
    "T_c": Dict[int, float],              # Travel time from nearest camp
    "eco_sensitive": Dict[int, bool],     # Is cell ecologically sensitive?
    "fire_penalty": Dict[int, float],     # Fire penalty value per cell
    "species_active": Dict[str, Dict[int, bool]],  # Species habitat per cell

    # Optional additions:
    "fire_risk": Dict[int, float],        # Raw fire risk [0,1]
    "cell_lon": Dict[int, float],         # Longitude per cell
    "cell_lat": Dict[int, float],         # Latitude per cell
}
```

### Field Details

#### 1. `T_c` - Travel Time
**Type**: `Dict[int, float]`

**Meaning**: Shortest travel time from nearest camp (source node) to each cell.

**How to compute**:
```python
from cpi import dijkstra_multi_source

T_c = dijkstra_multi_source(
    nodes=list(cells.keys()),
    neighbors=neighbors,
    terrain_cost=terrain_cost,
    sources=camp_cell_ids,        # List of camp cell IDs
    blocked=blocked_function       # Optional: cells blocked by fire
)
```

**Values**:
- `0.0` - At a camp
- Positive float - Travel time
- `float("inf")` - Unreachable

#### 2. `eco_sensitive` - Ecologically Sensitive Areas
**Type**: `Dict[int, bool]`

**Meaning**: `True` if placing a device here incurs ecological penalty.

**Example**:
```python
eco_sensitive = {
    1: False,
    2: True,     # Wetland, nesting area, etc.
    3: False,
    # ...
}
```

#### 3. `fire_penalty` - Fire Penalty
**Type**: `Dict[int, float]`

**Meaning**: Penalty subtracted from CPI due to fire risk.

**Calculation**:
```python
gamma_max = 20.0  # Maximum possible penalty

fire_penalty = {
    cell_id: gamma_max * fire_risk_fn(cells[cell_id]["lon"], cells[cell_id]["lat"])
    for cell_id in cells
}
```

**Range**: `0.0` to `gamma_max`

#### 4. `species_active` - Species Habitat Maps
**Type**: `Dict[str, Dict[int, bool]]`

**Meaning**: For each species, which cells are in its habitat.

**Example**:
```python
species_active = {
    "rhino": {
        1: True,    # Rhino habitat
        2: False,   # Not rhino habitat
        3: True,
        # ...
    },
    "elephant": {
        1: True,
        2: True,
        3: False,
        # ...
    },
    # Add more species...
}
```

---

## Parameters

**Type**: `Dict[str, Any]`

**Description**: Tunable constants for the CPI model.

### Full Parameter Dictionary

```python
params = {
    # Survival / Travel Time
    "lambda": 0.4,            # Survival decay rate (0-1 typical)

    # Device Effects
    "D_device": 0.8,          # Deterrence effect (0-1)
    "eta_camera": 0.5,        # Camera verification effectiveness (0-1)
    "eta_uav": 1.0,           # UAV verification effectiveness (0-1)

    # Penalties
    "eco_penalty": 50.0,      # Ecological penalty (can be large)
    "gamma_max": 20.0,        # Maximum fire penalty

    # Species Weights
    "W": {
        "rhino": 10.0,
        "elephant": 2.0,
        # Add more species...
    },
    "W_base": 0.5,            # Baseline weight for non-habitat cells
}
```

### Parameter Details

#### `lambda` - Survival Decay Rate
**Type**: `float`

**Typical Range**: `0.1` to `1.0`

**Meaning**: Controls how quickly survival probability decays with travel time.
- Smaller value = survival decays more slowly (far areas still viable)
- Larger value = survival decays rapidly (only near areas matter)

**Formula**: `S = exp(-λ * T_c)`

#### `D_device` - Deterrence Effect
**Type**: `float`

**Typical Range**: `0.0` to `1.0`

**Meaning**: Reduction in poaching probability due to device presence.
- `0.0` = No deterrence (device doesn't scare poachers)
- `1.0` = Perfect deterrence (poaching eliminated)

#### `eta_camera`, `eta_uav` - Verification Effectiveness
**Type**: `float`

**Typical Range**: `0.0` to `1.0`

**Meaning**: Probability that an incident is successfully verified/intercepted.
- `0.0` = Never catches poachers
- `1.0` = Always catches poachers (when deterrence fails)

#### `eco_penalty` - Ecological Penalty
**Type**: `float`

**Typical Range**: `10.0` to `100.0`

**Meaning**: Penalty subtracted from CPI when placing device in sensitive area.
- Set large to effectively prohibit devices in sensitive areas
- Set to 0 to disable ecological constraint

#### `gamma_max` - Maximum Fire Penalty
**Type**: `float`

**Typical Range**: `10.0` to `50.0`

**Meaning**: Penalty at maximum fire risk (center of fire zone).

#### `W` - Species Weights
**Type**: `Dict[str, float]`

**Meaning**: Importance weight for each species.
- Higher = higher priority for protecting that species
- Should reflect conservation status, economic value, cultural significance, etc.

#### `W_base` - Baseline Weight
**Type**: `float`

**Meaning**: Weight used when cell is not in species habitat.
- Set to 0 to ignore non-habitat cells
- Set to small positive value for general protection

---

## Complete Input Example

```python
from cpi import (
    dms_to_decimal,
    build_fire_risk_function,
    dijkstra_multi_source,
    compute_cpi_for_cell
)

# ==========================================================================
# 1. SPATIAL DATA
# ==========================================================================

# Park boundary (4 points)
park_boundary = [
    (dms_to_decimal("14°24'43.35\"E"), dms_to_decimal("19°26'55.93\"S")),
    (dms_to_decimal("14°15'46.12\"E"), dms_to_decimal("18°37'00.78\"S")),
    (dms_to_decimal("17°08'59.58\"E"), dms_to_decimal("18°29'09.57\"S")),
    (dms_to_decimal("17°06'34.10\"E"), dms_to_decimal("19°19'33.18\"S")),
]

# Fire quadrilaterals (2 zones)
fire_quads = [
    [(16.595, -18.834), (17.116, -18.832), (16.552, -19.084), (17.093, -19.145)],
    [(15.482, -19.289), (15.875, -19.310), (15.879, -19.114), (15.515, -19.140)],
]

# ==========================================================================
# 2. CELL GRID (replace with your 982 cells)
# ==========================================================================

cells = {
    1: {"lon": 16.7, "lat": -18.95, "terrain": "road"},
    2: {"lon": 15.7, "lat": -19.2, "terrain": "grass"},
    3: {"lon": 16.2, "lat": -18.6, "terrain": "forest"},
    # ... 979 more cells ...
}

# Cell adjacency
neighbors = {
    1: [2, 3],
    2: [1, 3],
    3: [1, 2],
    # ...
}

# ==========================================================================
# 3. TERRAIN AND TRAVEL
# ==========================================================================

terrain_weight = {"road": 1.0, "grass": 3.0, "forest": 5.0, "swamp": float("inf")}
terrain_cost = {cid: terrain_weight[cells[cid]["terrain"]] for cid in cells}

# Camps (source nodes)
camp_cell_ids = [1]

# ==========================================================================
# 4. FIRE RISK
# ==========================================================================

fire_risk_fn = build_fire_risk_function(
    park_boundary,
    fire_quads,
    combine="max",
    radial_mode="linear"
)

gamma_max = 20.0
fire_penalty = {}
fire_risk = {}
for cid, info in cells.items():
    r = fire_risk_fn(info["lon"], info["lat"])
    fire_risk[cid] = r
    fire_penalty[cid] = gamma_max * r

# Optional: Fire blocks travel
fire_blocks_travel = True
def blocked(cid):
    return fire_blocks_travel and fire_risk[cid] > 0.0

# ==========================================================================
# 5. PRECOMPUTE TRAVEL TIMES
# ==========================================================================

T_c = dijkstra_multi_source(
    nodes=list(cells.keys()),
    neighbors=neighbors,
    terrain_cost=terrain_cost,
    sources=camp_cell_ids,
    blocked=blocked
)

# ==========================================================================
# 6. PRECOMPUTED MAPS
# ==========================================================================

precomp = {
    "T_c": T_c,
    "eco_sensitive": {1: False, 2: True, 3: False},  # ... for all cells
    "fire_penalty": fire_penalty,
    "species_active": {
        "rhino": {1: True, 2: False, 3: True},
        "elephant": {1: True, 2: True, 3: False},
    }
}

# ==========================================================================
# 7. PARAMETERS
# ==========================================================================

params = {
    "lambda": 0.4,
    "D_device": 0.8,
    "eta_camera": 0.5,
    "eta_uav": 1.0,
    "eco_penalty": 50.0,
    "W": {"rhino": 10.0, "elephant": 2.0},
    "W_base": 0.5
}

# ==========================================================================
# 8. COMPUTE CPI
# ==========================================================================

# For one cell
cpi = compute_cpi_for_cell(
    cell_id=3,
    species_id="rhino",
    device_type="uav",
    params=params,
    precomp=precomp
)

# For all combinations
results = {}
for cid in cells:
    for sp in ["rhino", "elephant"]:
        for device in ["none", "camera", "uav"]:
            key = (cid, sp, device)
            results[key] = compute_cpi_for_cell(cid, sp, device, params, precomp)
```

---

## Data Preparation Checklist

Before running CPI calculations:

- [ ] Park boundary converted to decimal degrees
- [ ] Fire quadrilaterals defined
- [ ] All cells have lon, lat, terrain
- [ ] Neighbor adjacency list complete
- [ ] Terrain costs mapped
- [ ] Camp locations identified
- [ ] Ecologically sensitive areas marked
- [ ] Species habitat maps created
- [ ] Parameters set to reasonable values
