# VTOL Flight Simulation Visualization

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Professional-grade Python visualization system for VTOL (Vertical Take-Off and Landing) aircraft flight simulation data. Designed to process MATLAB/Simulink simulation outputs and generate publication-quality plots, 3D visualizations, and animations.

![Dashboard Example](docs/images/dashboard_preview.png)

## Features

- **Data Processing**: Load and validate MATLAB `.mat` simulation files
- **Time History Plots**: Attitude, position, velocity, and control surface histories
- **Trajectory Visualization**: 2D ground tracks and 3D flight paths
- **3D Aircraft Model**: Geometric aircraft representation with attitude visualization
- **Animated Flights**: Generate GIF/MP4 animations of flight trajectories
- **Dashboard View**: Single-page summary with all key flight metrics
- **Configurable Styling**: YAML-based themes for publication-quality output
- **Session Management**: Organize multiple simulation runs cleanly
- **X-Plane Ready**: Designed for future X-Plane UDP integration

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/alireza787b/vtol-flight-viz.git
cd vtol-flight-viz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Analyze a session (generates all plots)
python run_analysis.py --session session_001

# Generate plots with animation
python run_analysis.py --session session_001 --animate

# List available sessions
python run_analysis.py --list-sessions

# Analyze a specific MAT file
python run_analysis.py --mat-file path/to/data.mat --output-dir ./output
```

## Project Structure

```
vtol-flight-viz/
├── config/
│   ├── default.yaml              # Default plot styling and colors
│   └── aircraft/
│       └── vtol_default.yaml     # Aircraft geometry configuration
├── src/
│   ├── flight_data.py            # Core FlightData class
│   ├── utils/
│   │   ├── conversions.py        # Unit conversions (m/s→knots, rad→deg)
│   │   └── rotations.py          # Rotation matrices, 3D transforms
│   ├── styles/
│   │   └── themes.py             # Plot styling system
│   └── plotters/
│       ├── base.py               # Base plotter class
│       ├── time_history.py       # Time series plots
│       ├── trajectory.py         # 2D/3D trajectory plots
│       ├── controls.py           # Control surface plots
│       ├── aircraft_3d.py        # 3D aircraft visualization
│       └── dashboard.py          # Summary dashboard
├── sessions/                      # Simulation data organized by session
│   └── session_001/
│       ├── raw_data/             # Original .mat files
│       └── plots/                # Generated visualizations
├── docs/                          # Documentation
├── requirements.txt
└── run_analysis.py               # Main CLI entry point
```

## Input Data Format

The system expects MATLAB `.mat` files with the following variables:

| Variable | Description | Units |
|----------|-------------|-------|
| `N`, `E`, `D` | Position (NED frame) | meters |
| `phi`, `theta`, `psi` | Euler angles (roll, pitch, yaw) | radians |
| `delta_a`, `delta_e`, `delta_r` | Control surfaces (aileron, elevator, rudder) | radians |
| `RPM_Cl`, `RPM_Cr` | Cruise propeller RPM | RPM |
| `theta_Cl`, `theta_Cr` | Propeller tilt angles | degrees |
| `Time` | Simulation duration | seconds |
| `output_hz` | Sample rate | Hz |

## Generated Outputs

### Time History Plots
- `attitude.png` - Roll, pitch, yaw angles over time
- `position.png` - North, East, Down positions
- `velocity.png` - Ground speed and climb rate
- `time_history_all.png` - Combined view of all states

### Trajectory Plots
- `ground_track.png` - 2D top-down view
- `trajectory_3d.png` - 3D flight path
- `trajectory_combined.png` - Multiple views combined
- `altitude_profile.png` - Altitude vs time/distance

### Control & Propulsion
- `controls_all.png` - All control inputs
- `control_surfaces.png` - Aileron, elevator, rudder
- `propulsion.png` - RPM and tilt angles

### 3D Visualization
- `aircraft_3d_trajectory.png` - 3D path with aircraft attitude markers

### Summary
- `dashboard.png` - Single-page overview with all key data

### Animations
- `flight_animation.gif` - Animated flight visualization

## Configuration

### Plot Styling (`config/default.yaml`)

```yaml
plot:
  dpi: 300
  format: png
  figure_sizes:
    single: [10, 6]
    dashboard: [16, 12]

colors:
  attitude:
    phi: '#d62728'    # Roll - red
    theta: '#ff7f0e'  # Pitch - orange
    psi: '#9467bd'    # Yaw - purple
```

### Aircraft Geometry (`config/aircraft/vtol_default.yaml`)

```yaml
geometry:
  wing:
    span: 10.0
    chord: 1.5
  propellers:
    cruise:
      positions:
        left: [0.0, -2.5, 0.0]
        right: [0.0, 2.5, 0.0]
```

## CLI Reference

```
usage: run_analysis.py [-h] [--session SESSION] [--mat-file MAT_FILE]
                       [--output-dir OUTPUT_DIR] [--config CONFIG]
                       [--animate] [--fps FPS] [--list-sessions] [--no-clean]

Options:
  --session, -s       Session name (folder in sessions/)
  --mat-file, -m      Path to MAT file (alternative to --session)
  --output-dir, -o    Output directory (required with --mat-file)
  --config, -c        Path to custom style configuration YAML
  --animate, -a       Generate animated visualization (GIF)
  --fps               Animation frames per second (default: 30)
  --list-sessions     List available sessions and exit
  --no-clean          Keep existing plots (default: clean before regenerating)
```

## Adding New Sessions

1. Create a new session folder:
```bash
mkdir -p sessions/my_new_session/raw_data
```

2. Copy your `.mat` file:
```bash
cp my_simulation.mat sessions/my_new_session/raw_data/
```

3. Generate plots:
```bash
python run_analysis.py --session my_new_session
```

## Python API Usage

```python
from src.flight_data import FlightData
from src.plotters import TimeHistoryPlotter, TrajectoryPlotter
from src.styles.themes import load_style

# Load data
flight_data = FlightData.from_mat_file('path/to/data.mat')

# Print summary
print(flight_data.get_summary())

# Create individual plots
style = load_style()
plotter = TimeHistoryPlotter(flight_data, style, output_dir='./output')
fig = plotter.plot_attitude()
fig.savefig('attitude.png')
```

## Future Roadmap

- [ ] **X-Plane Integration**: Real-time visualization via UDP protocol
- [ ] **Flight Replay**: Animate simulation in X-Plane
- [ ] **Comparison Tools**: Overlay multiple flights for analysis
- [ ] **KML Export**: Google Earth visualization
- [ ] **Report Generation**: PDF reports with analysis
- [ ] **Real-time Streaming**: Live data visualization

## Requirements

- Python 3.8+
- NumPy, SciPy, Pandas
- Matplotlib, Plotly
- PyYAML
- ImageIO (for animations)

See `requirements.txt` for complete list.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**Alireza Ghaderi**
- GitHub: [@alireza787b](https://github.com/alireza787b)
- LinkedIn: [alireza787b](https://linkedin.com/in/alireza787b)

## Acknowledgments

- VTOL simulation data provided by flight dynamics research project
- Inspired by MATLAB/Simulink aerospace visualization tools
- Built for professional flight simulation analysis
