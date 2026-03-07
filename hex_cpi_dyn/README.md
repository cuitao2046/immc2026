# Wildlife Reserve Protection Optimization (DSSA)

A Python implementation of the Dynamic Sparrow Search Algorithm (DSSA) for optimizing wildlife protection resource allocation in a reserve using hexagonal honeycomb grids.

## Features

- **Hexagonal Grid System**: Uses axial coordinate system for accurate distance calculations
- **Terrain-Based Deployment Constraints**: Resources can only be deployed in suitable terrain types
- **Multi-Resource Optimization**: Optimizes placement of patrols, cameras, drones, and fences
- **DSSA Algorithm**: Efficient metaheuristic optimization with producers, followers, and scouts
- **Comprehensive Visualization**: Risk heatmaps, deployment maps, convergence curves, and terrain maps

## Project Structure

```
CPI/
├── data_loader.py          # Data loading and configuration management
├── grid_model.py           # Hexagonal grid model and distance calculations
├── coverage_model.py       # Protection coverage and benefit calculations
├── dssa_optimizer.py       # Dynamic Sparrow Search Algorithm implementation
├── visualization.py        # Plotting and visualization functions
├── main.py                 # Main program entry point
├── config.json             # Configuration file
├── risk_calculator.py      # Risk calculation utilities
└── README.md              # This file
```

## Installation

### Requirements

- Python 3.7+
- numpy
- matplotlib
- pandas (optional)

### Install Dependencies

```bash
pip install numpy matplotlib pandas
```

## Usage

### Quick Start

Run the default scenario:

```bash
python main.py
```

This will:
1. Generate a hexagonal grid with random terrain and risk values
2. Run DSSA optimization for 100 iterations
3. Generate all visualizations in the `output/` directory
4. Save results to `output/results.json`

### Custom Configuration

Edit `config.json` to customize:

```json
{
  "grid_radius": 5,
  "constraints": {
    "total_patrol": 20,
    "total_camps": 5,
    "max_rangers_per_camp": 5,
    "total_cameras": 10,
    "total_drones": 3,
    "total_fence_length": 50.0
  },
  "coverage_params": {
    "patrol_radius": 5.0,
    "drone_radius": 8.0,
    "camera_radius": 3.0,
    "fence_protection": 0.5,
    "wp": 0.3,
    "wd": 0.3,
    "wc": 0.2,
    "wf": 0.2
  }
}
```

### Programmatic Usage

```python
from main import WildlifeProtectionOptimizer
from dssa_optimizer import DSSAConfig

# Initialize optimizer
optimizer = WildlifeProtectionOptimizer()

# Setup scenario
optimizer.setup_default_scenario()

# Configure DSSA
dssa_config = DSSAConfig(
    population_size=50,
    max_iterations=100,
    producer_ratio=0.2,
    scout_ratio=0.2
)

# Run optimization
solution, fitness, history = optimizer.run_optimization(dssa_config)

# Print results
optimizer.print_solution_summary()

# Generate visualizations
optimizer.generate_all_visualizations(output_dir='./output')

# Save results
optimizer.save_results(output_path='./output/results.json')
```

## Model Components

### 1. Hexagonal Grid System

- Uses axial coordinates (q, r) for grid representation
- Calculates distances using hexagonal distance formula
- Supports terrain classification (5 types)

### 2. Terrain Types

| Terrain | Patrol | Camp | Drone | Camera | Fence |
|---------|--------|------|-------|--------|-------|
| Salt Marsh | 0 | 0 | 1 | 0 | 0 |
| Sparse Grass | 1 | 1 | 1 | 1 | 1 |
| Dense Grass | 1 | 1 | 1 | 0 | 1 |
| Water Hole | 0 | 0 | 1 | 0 | 0 |
| Road | 1 | 1 | 1 | 1 | 1 |

### 3. Coverage Models

- **Patrol Coverage**: Exponential decay with distance
- **Drone Coverage**: Terrain-dependent visibility
- **Camera Coverage**: Terrain-dependent visibility
- **Fence Protection**: Reduces intrusion probability

### 4. DSSA Algorithm

- **Producers**: Explore new solutions around best solution
- **Followers**: Move toward best solution or producers
- **Scouts**: Random exploration to avoid local optima
- **Feasibility Repair**: Ensures all solutions respect constraints

## Output Files

After running the program, the following files are generated in `output/`:

1. **risk_heatmap.png**: Visualizes poaching risk across the reserve
2. **deployment_map.png**: Shows optimal resource placement
3. **convergence_curve.png**: DSSA fitness over iterations
4. **terrain_map.png**: Terrain distribution across the reserve
5. **results.json**: Detailed optimization results in JSON format

## Mathematical Model

### Objective Function

Maximize total protection benefit:

```
F = Σ R_i × (1 - exp(-E_i))
```

Where:
- R_i = Risk at grid i
- E_i = Combined protection effect at grid i

### Protection Effect

```
E_i = w_p × Patrol_i + w_d × Drone_i + w_c × Camera_i + w_f × Fence_i
```

### Constraints

- Resource quantity limits
- Terrain-based deployment feasibility
- Maximum rangers per camp

## Parameters

### DSSA Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| population_size | 50 | Number of sparrows in population |
| max_iterations | 100 | Maximum optimization iterations |
| producer_ratio | 0.2 | Proportion of producers |
| scout_ratio | 0.2 | Proportion of scouts |
| ST | 0.8 | Safety threshold |
| R2 | 0.5 | Warning value |

### Coverage Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| patrol_radius | 5.0 | Patrol effective radius |
| drone_radius | 8.0 | Drone effective radius |
| camera_radius | 3.0 | Camera effective radius |
| fence_protection | 0.5 | Fence protection coefficient |
| wp | 0.3 | Patrol weight |
| wd | 0.3 | Drone weight |
| wc | 0.2 | Camera weight |
| wf | 0.2 | Fence weight |

## Performance

- **Grid Size**: 91 hexagonal cells (radius=5)
- **Optimization Time**: ~30-60 seconds (100 iterations)
- **Memory Usage**: ~50-100 MB

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is for educational and research purposes.

## References

- Sparrow Search Algorithm (SSA) for optimization
- Hexagonal grid systems for spatial modeling
- Wildlife protection resource allocation models
