# Getting Started Guide

This guide will walk you through setting up and using the VTOL Flight Simulation Visualization system.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/alireza787b/vtol-flight-viz.git
cd vtol-flight-viz
```

### 2. Create Virtual Environment

It's recommended to use a virtual environment to avoid conflicts with other Python packages.

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Your First Analysis

### Option 1: Using Sample Data

The repository includes sample session data. Run:

```bash
python run_analysis.py --session session_001
```

This will generate all plots in `sessions/session_001/plots/`.

### Option 2: Using Your Own Data

1. **Prepare your data**: Export your MATLAB/Simulink simulation as a `.mat` file with the required variables (see [Data Format](data-format.md)).

2. **Create a new session**:
```bash
mkdir -p sessions/my_flight/raw_data
cp your_simulation.mat sessions/my_flight/raw_data/
```

3. **Generate plots**:
```bash
python run_analysis.py --session my_flight
```

## Understanding the Output

After running the analysis, you'll find the following in your session's `plots/` folder:

```
plots/
├── time_histories/
│   ├── attitude.png          # Roll, pitch, yaw over time
│   ├── position.png          # N, E, D positions
│   ├── velocity.png          # Speed and climb rate
│   └── time_history_all.png  # Combined view
├── trajectory/
│   ├── ground_track.png      # Top-down 2D view
│   ├── trajectory_3d.png     # 3D flight path
│   ├── trajectory_combined.png
│   └── altitude_profile.png
├── controls/
│   ├── controls_all.png
│   ├── control_surfaces.png
│   └── propulsion.png
├── 3d_aircraft/
│   └── aircraft_3d_trajectory.png
├── summary/
│   └── dashboard.png         # Single-page overview
└── animations/
    └── flight_animation.gif  # (if --animate flag used)
```

## Generating Animations

Animations show the aircraft flying along the trajectory with attitude visualization:

```bash
python run_analysis.py --session session_001 --animate --fps 20
```

**Note:** Animation generation is computationally intensive. For long simulations, consider:
- Reducing FPS: `--fps 15`
- The animation uses automatic speed-up for long flights

## Customizing Output

### Using Custom Styles

Create a custom YAML configuration and use it:

```bash
python run_analysis.py --session session_001 --config my_style.yaml
```

### Modifying Plot Settings

Edit `config/default.yaml` to change:
- Color schemes
- Figure sizes
- DPI (resolution)
- Font sizes
- Grid styling

## Common Issues

### "No MAT files found"
Ensure your `.mat` file is in the `raw_data/` subfolder of your session.

### "Module not found" errors
Make sure you've activated the virtual environment:
```bash
source venv/bin/activate
```

### Plots not updating
By default, existing plots are cleaned before regenerating. If plots aren't updating, check file permissions.

## Next Steps

- Read the [Data Format Guide](data-format.md) to understand input requirements
- Check [Customization Guide](customization.md) for advanced styling
- See [API Reference](api-reference.md) for programmatic usage
