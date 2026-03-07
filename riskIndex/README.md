# Protected Area Grid Risk Index Model

A comprehensive mathematical model for calculating risk coefficients in wildlife protected areas to guide optimal allocation of patrol and monitoring resources.

## Features

- **Core Risk Model**: Human risk, Environmental risk, Species density calculations
- **Temporal Factors**: Diurnal and seasonal risk variations
- **Spatial-Temporal Risk Field**: Continuous interpolation across space and time
- **DSSA Algorithm**: Drone Swarm Scheduling Algorithm for patrol optimization
- **Visualization**: Risk heatmaps, component analysis, and temporal comparisons
- **Data Generation**: Synthetic data for testing and validation

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
└── demo_phase*.py         # Phase demonstration scripts
```

## Quick Start

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
