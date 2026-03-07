# Protected Area Grid Risk Index Model

A comprehensive mathematical model for calculating risk coefficients in wildlife protected areas to guide optimal allocation of patrol and monitoring resources.

## Features

- **Core Risk Model**: Human risk, Environmental risk, Species density calculations
- **Temporal Factors**: Diurnal and seasonal risk variations
- **Automatic Distance Calculation**: Auto-calculate distances from grid coordinates
- **Spatial-Temporal Risk Field**: Continuous interpolation across space and time
- **DSSA Algorithm**: Drone Swarm Scheduling Algorithm for patrol optimization
- **Visualization**: Risk heatmaps, component analysis, and temporal comparisons
- **Data Generation**: Synthetic data for testing and validation
- **Wrapper Script**: JSON-based configuration and data file I/O

## Project Structure

```
riskIndex/
├── src/risk_model/
│   ├── core/              # Core data structures
│   ├── risk/              # Risk calculators
│   ├── data/              # Data generation and I/O
│   ├── config/            # Configuration management
│   ├── visualization/     # Plotting and visualization
│   └── advanced/          # IMMC enhancements
├── tests/                 # Unit tests
├── examples/              # Example scripts
├── plots/                 # Generated plots
├── demo_phase*.py         # Phase demonstration scripts
├── risk_model_wrapper.py   # Wrapper script for JSON file I/O
├── example_data.json     # Example input data
├── example_config.json   # Example configuration
└── example_results.json  # Example output results
```

## Quick Start

### Using the Wrapper Script

```bash
# Run with example data
python3 risk_model_wrapper.py --data example_data.json --config example_config.json --output results.json
```

### Run All Demos

```bash
# Phase 1: Core Model Implementation
python3 demo_phase1.py

# Phase 2: Risk Integration & Normalization
python3 demo_phase2.py

# Phase 3: Data Generation & Input/Output
python3 demo_phase3.py

# Phase 4: Visualization
python3 demo_phase4.py

# Phase 5: Testing & Validation
python3 demo_phase5.py

# Phase 6: Advanced Features (IMMC Enhancements)
python3 demo_phase6.py
```

## Coordinate System

The model uses a grid-based coordinate system:
- **Origin**: Bottom-left grid cell center
- **X-axis**: Increases to the right (column index)
- **Y-axis**: Increases upward (row index)
- **Distance Calculation**: Euclidean distance used for automatic distance computation

## Wrapper Script Usage

### Input Data Format (`data.json`)

```json
{
  "map_config": {
    "map_width": 10,
    "map_height": 6,
    "boundary_type": "RECTANGLE",
    "road_locations": [[2, 3], [5, 7]],
    "water_locations": [[1, 1], [8, 5]]
  },
  "grids": [
    {
      "grid_id": "A01",
      "x": 0,
      "y": 0,
      "fire_risk": 0.8,
      "terrain_complexity": 0.7,
      "vegetation_type": "FOREST",
      "species_densities": {
        "rhino": 0.9,
        "elephant": 0.7,
        "bird": 0.5
      }
    }
  ],
  "time": {
    "hour_of_day": 22,
    "season": "RAINY"
  }
}
```

### Configuration Format (`config.json`)

```json
{
  "risk_weights": {
    "human_weight": 0.4,
    "environmental_weight": 0.3,
    "density_weight": 0.3
  },
  "human_risk_weights": {
    "boundary_weight": 0.4,
    "road_weight": 0.35,
    "water_weight": 0.25
  },
  "environmental_risk_weights": {
    "fire_weight": 0.6,
    "terrain_weight": 0.4
  }
}
```

## Model Overview

### Risk Formula

```
R'_{i,t} = (ω₁·H_{i,t} + ω₂·E_i + ω₃·Σ_s w_s·D_{s,i,t}) × T_t × S_t

R_i = (R'_{i,t} - R_min) / (R_max - R_min)
```

### Components

| Component | Description |
|-----------|-------------|
| H_{i,t} | Human risk (boundary/road/water proximity) |
| E_i | Environmental risk (fire + terrain complexity) |
| D_{s,i,t} | Weighted species density |
| T_t | Diurnal factor (day/night) |
| S_t | Seasonal factor (dry/rainy) |

## IMMC Competition Enhancements

### 1. Spatio-Temporal Risk Field

Continuous risk interpolation using Gaussian or IDW kernels:

```python
from risk_model.advanced import SpatioTemporalRiskField

risk_field = SpatioTemporalRiskField(grids, risk_results)
risk = risk_field.get_risk_at(x=50, y=50, t=2, season=Season.RAINY)
```

### 2. DSSA Algorithm (Drone Swarm Scheduling)

Pseudo-code and implementation for optimal patrol scheduling. See `risk_model/advanced/dssa.py` for the complete IMMC-formatted algorithm.

### 3. Complete Workflow

```
Generate Data → Calculate Risks → Build Risk Field → Optimize Patrols → Visualize
```

## Requirements

- Python 3.8+
- numpy
- matplotlib

## Development Phases

| Phase | Status | Demo |
|-------|--------|------|
| 1. Core Model Implementation | ✅ | `demo_phase1.py` |
| 2. Risk Integration & Normalization | ✅ | `demo_phase2.py` |
| 3. Data Generation & I/O | ✅ | `demo_phase3.py` |
| 4. Visualization | ✅ | `demo_phase4.py` |
| 5. Testing & Validation | ✅ | `demo_phase5.py` |
| 6. IMMC Advanced Features | ✅ | `demo_phase6.py` |

## License

For IMMC competition use.
