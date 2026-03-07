# Protected Area Grid Risk Index Model - Design Document

## 1. Model Objectives

In wildlife protected areas, resources such as patrol personnel, drones, fixed monitoring equipment, and rescue teams are limited. To maximize conservation effectiveness, the protected area needs to be modeled as a grid, with a **risk coefficient** calculated for each grid cell to guide optimal allocation of patrol and monitoring resources.

This model comprehensively considers:
- Human threat risk
- Environmental risk
- Animal distribution density
- Seasonal variations
- Diurnal variations

to calculate a **comprehensive risk value** for each grid cell.

Final output: risk values for each grid cell

```
R_i ∈ [0, 1]
```

Higher values indicate areas requiring more intensive monitoring.

---

## 2. Risk Calculation Formula

### 2.1 Comprehensive Risk (Non-Normalized)

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t
```

### 2.2 Normalization

```
R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

Result range:
```
R_i ∈ [0, 1]
```

Where:
- R_min = Minimum risk value across all grids
- R_max = Maximum risk value across all grids

### 2.3 Symbol Index

| Symbol | Meaning |
|--------|---------|
| i | Grid cell identifier |
| t | Time |
| s | Species |
| H_{i,t} | Human risk |
| E_i | Environmental risk |
| D_{s,i,t} | Species density |
| T_t | Diurnal influence factor |
| S_t | Seasonal influence factor |
| P_t | Poaching time probability |
| w_s | Species weight |
| ω₁, ω₂, ω₃ | Weight coefficients |

---

## 3. Human Risk Model

Human risk reflects the threat level of human activities such as poaching.

```
H_{i,t} = (α₁·d_boundary + α₂·d_road + α₃·d_water) × P_t
```

Note: Shorter distances result in higher human risk (distances should be normalized reciprocal values).

### 3.1 Parameters

| Parameter | Meaning |
|-----------|---------|
| d_boundary | Distance to protected area boundary |
| d_road | Distance to road |
| d_water | Distance to water source |
| P_t | Poaching time probability |

### 3.2 Weight Parameters

| Parameter | Meaning | Example Value |
|-----------|---------|---------------|
| α₁ | Boundary influence weight | 0.4 |
| α₂ | Road influence weight | 0.35 |
| α₃ | Water source influence weight | 0.25 |

Constraint:
```
α₁ + α₂ + α₃ = 1
```

---

## 4. Environmental Risk Model

Environmental risk reflects the impact of natural conditions on animal safety.

```
E_i = β₁·V_fire + β₂·C_terrain
```

### 4.1 Parameters

| Parameter | Meaning | Range |
|-----------|---------|-------|
| V_fire | Fire risk index | [0, 1] |
| C_terrain | Terrain complexity | [0, 1] |

### 4.2 Parameter Description

**Fire Risk (V_fire)**
- Range: 0 ≤ V_fire ≤ 1
- Sources:
  - Vegetation dryness
  - Temperature
  - Historical fire records

**Terrain Complexity (C_terrain)**
- Represents terrain influence on animal injury probability
- Examples:
  - Mountains
  - Canyons
  - Steep slopes
- Range: 0 ≤ C_terrain ≤ 1

---

## 5. Species Density Model

Animal density reflects conservation value.

```
D_{s,i,t}
```

Represents: Density of species (s) in grid (i) at time (t).

### 5.1 Weighted Species Density

```
Σ_s w_s·D_{s,i,t}
```

### 5.2 Species Weights (Example)

| Species | Weight |
|---------|--------|
| Rhino | 0.5 |
| Elephant | 0.3 |
| Bird | 0.2 |

Endangered animals have higher weights.

### 5.3 Seasonal Variation

```
D_{s,i,t} = D_{s,i} × M_season
```

**Seasonal Adjustment Coefficients (M_season)**

| Species | Rainy Season | Dry Season |
|---------|--------------|------------|
| Elephant | 1.3 | 0.9 |
| Rhino | 1.2 | 1.0 |
| Bird | 1.5 | 0.8 |

---

## 6. Seasonal Influence Model

Different seasons affect:
- Animal distribution
- Poaching activity
- Patrol difficulty

### 6.1 Seasonal Factor

```
S_t = {
    1.0   Dry Season
    1.2   Rainy Season
}
```

### 6.2 Seasonal Effects

| Season | Impact |
|--------|--------|
| Dry Season | Animals dispersed |
| Rainy Season | Animals concentrated at water sources |

Risk is typically higher during rainy season.

---

## 7. Diurnal Influence Model

Poaching activity is typically more frequent at night.

### 7.1 Diurnal Factor (Discrete)

```
T_t = {
    1.0   Daytime
    1.3   Nighttime
}
```

### 7.2 Diurnal Factor (Continuous)

```
T_t = 1 + γ·sin(2πt/24)
```

### 7.3 Risk Levels by Time

| Time | Risk |
|------|------|
| Daytime | Lower |
| Nighttime | Higher |

### 7.4 Example Time Factors

| Time | Factor |
|------|--------|
| 08:00 | 1.0 |
| 12:00 | 0.9 |
| 20:00 | 1.2 |
| 24:00 | 1.3 |

---

## 8. Model Weight Settings

Final risk weights:

```
ω₁ + ω₂ + ω₃ = 1
```

### 8.1 Example Weights

| Parameter | Meaning | Value |
|-----------|---------|-------|
| ω₁ | Human risk weight | 0.4 |
| ω₂ | Environmental risk weight | 0.3 |
| ω₃ | Animal density weight | 0.3 |

---

## 9. Input Data Structure

Model input data includes:

### 9.1 Grid Spatial Data

| Data | Description |
|------|-------------|
| Grid coordinates | Center position of each grid |
| Distance to boundary | GIS calculation |
| Distance to road | GIS calculation |
| Distance to water | GIS calculation |

### 9.2 Environmental Data

| Data | Description |
|------|-------------|
| Vegetation type | Grassland / Forest / Shrub |
| Fire risk | 0–1 |
| Terrain complexity | 0–1 |

### 9.3 Animal Data

| Data | Description |
|------|-------------|
| Species type | Rhino, Elephant, Bird |
| Density distribution | Per grid |

### 9.4 Time Data

| Data | Description |
|------|-------------|
| Time | 0–24 hours |
| Season | Rainy / Dry |

---

## 10. Model Output

Model output is the risk coefficient for all grids in the protected area:

```
R_i ∈ [0, 1]
```

### 10.1 Example Output

| Grid | Risk Value |
|------|------------|
| A12 | 0.82 |
| B07 | 0.65 |
| C14 | 0.33 |

---

## 11. Model Applications

The calculated risk map can be used for:

### 11.1 Patrol Route Optimization
Prioritize patrols in high-risk areas.

### 11.2 Drone Monitoring
Drone priority coverage:
- Nighttime
- High-risk areas

### 11.3 Station Site Selection
Select locations with:
- High-risk centers
- Maximum coverage area

### 11.4 Emergency Rescue
Deploy rescue personnel in areas with high animal injury probability.

---

## 12. Model Advantages

Compared to traditional static models, this model offers:

### 12.1 Dynamic Risk Assessment
Considers both:
- Spatial factors
- Temporal factors

### 12.2 Ecological Consistency
Animal behavior changes with seasons.

### 12.3 Scheduling Algorithm Ready
Can directly serve as **input variables for DSSA scheduling algorithms**.
