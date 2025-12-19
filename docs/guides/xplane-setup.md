# X-Plane Integration Guide

Play back your MATLAB/Simulink flight simulation data in X-Plane flight simulator for realistic visualization.

## Overview

The X-Plane integration allows you to:
- Replay flight data from `.mat` files in real-time
- Control aircraft position, attitude, and control surfaces
- Visualize propulsion state (RPM, tilt angles for VTOL)
- Use any X-Plane aircraft model for visualization

## Prerequisites

- X-Plane 11 or 12 installed and running
- Python environment with dependencies installed
- Flight simulation data in `.mat` format

## Quick Start

### 1. Basic Playback

```bash
# Play a session in X-Plane
python run_analysis.py --session session_001 --xplane-play

# Or use the standalone script
python scripts/xplane_playback.py sessions/session_001/raw_data/flight_data.mat
```

### 2. With Options

```bash
# Double speed playback
python run_analysis.py --session session_001 --xplane-play --xplane-speed 2.0

# Specific origin point
python run_analysis.py --session session_001 --xplane-play --xplane-origin 37.5,-122.0,100

# Loop continuously
python run_analysis.py --session session_001 --xplane-play --xplane-loop

# Remote X-Plane instance
python run_analysis.py --session session_001 --xplane-play --xplane-host 192.168.1.100
```

## Communication Backends

The system supports two communication methods:

### 1. NASA XPlaneConnect (Recommended)

**Pros:**
- High-level API
- Well-documented
- Control surface animation support

**Setup:**
1. Download plugin from [XPlaneConnect Releases](https://github.com/nasa/XPlaneConnect/releases)
2. Extract to `X-Plane/Resources/plugins/XPlaneConnect/`
3. Restart X-Plane

**Usage:**
```bash
python run_analysis.py --session session_001 --xplane-play --xplane-backend xpc
```

### 2. Native UDP (No Plugin)

**Pros:**
- No installation required
- Works with all X-Plane versions
- Automatically overrides physics

**Usage:**
```bash
python run_analysis.py --session session_001 --xplane-play --xplane-backend native
```

## Configuration

### Connection Settings

Edit `config/xplane.yaml`:

```yaml
connection:
  host: localhost     # X-Plane IP address
  port: 49009         # XPC plugin port
  native_port: 49000  # Native UDP port
  backend: auto       # auto, xpc, or native
  timeout: 1000       # Connection timeout (ms)
```

### Playback Settings

```yaml
playback:
  default_speed: 1.0  # 1.0 = real-time
  loop: false         # Loop continuously
  show_status: true   # Display status in X-Plane
```

### Origin Point

The playback uses your aircraft's current X-Plane position as the origin point for NED coordinates. Alternatively, specify manually:

```yaml
origin:
  auto_detect: false
  latitude: 37.5242
  longitude: -122.0690
  altitude: 100  # meters MSL
```

## Variable Mapping

### Control Surfaces

Map your simulation variables to X-Plane datarefs in `config/xplane.yaml`:

```yaml
variable_mapping:
  controls:
    aileron:
      source_unit: "radians"
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"
      target_unit: "degrees"
      max_deflection: 30.0
```

### Propulsion

For VTOL/tilt-rotor aircraft:

```yaml
  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 10000
      scale: 0.01  # RPM to percentage

    tilt_left:
      source_unit: "radians"
      target_dref: "sim/flightmodel/engine/POINT_pitch[0]"
      target_unit: "degrees"
```

## Python API

### Basic Usage

```python
from src.xplane import XPlanePlayer
from src.flight_data import FlightData

# Load data
flight_data = FlightData.from_mat_file("path/to/data.mat")

# Create player
player = XPlanePlayer()
player.connect()
player.load(flight_data)

# Play at 1.5x speed
player.play(speed=1.5)

# Wait for completion
while player.is_playing:
    time.sleep(0.1)

player.disconnect()
```

### Context Manager

```python
from src.xplane import XPlanePlayer

with XPlanePlayer() as player:
    player.load("path/to/data.mat")
    player.play()

    # Playback controls
    player.pause()
    player.resume()
    player.seek(30.0)  # Jump to 30 seconds
    player.set_speed(2.0)

    player.stop()
```

### Callbacks

```python
def on_frame(frame_idx, time_sec):
    print(f"Frame {frame_idx}: {time_sec:.2f}s")

def on_complete():
    print("Playback finished!")

player.on_frame(on_frame)
player.on_complete(on_complete)
player.play()
```

## Troubleshooting

### Connection Failed

1. **Check X-Plane is running** - Must be launched before playback
2. **Verify network settings** - For remote connections, check firewall
3. **Try native backend** - `--xplane-backend native` if XPC fails

### Aircraft Not Moving

1. **Check origin point** - Position aircraft where you want flight to start
2. **Verify data mapping** - Ensure `.mat` variables match config

### Physics Interfering

- Native UDP (VEHX command) automatically overrides physics
- For XPC, physics may need manual override via dataref

### Wrong Aircraft Model

The visualization uses whatever aircraft is loaded in X-Plane. For best results:
- Use an aircraft similar to your simulation model
- For VTOL, find a tilt-rotor model (or accept fixed-wing approximation)

## Common X-Plane Datarefs

| Variable | Dataref | Notes |
|----------|---------|-------|
| Aileron | `sim/flightmodel/controls/wing1l_ail1def` | Degrees |
| Elevator | `sim/flightmodel/controls/hstab1_elv1def` | Degrees |
| Rudder | `sim/flightmodel/controls/vstab1_rud1def` | Degrees |
| Throttle | `sim/flightmodel/engine/ENGN_thro[n]` | 0-1 |
| N1 RPM | `sim/flightmodel/engine/ENGN_N1_[n]` | Percentage |
| Engine Tilt | `sim/flightmodel/engine/POINT_pitch[n]` | Degrees |
| Flaps | `sim/flightmodel/controls/flaprqst` | 0-1 |
| Gear | `sim/cockpit/switches/gear_handle_status` | 0/1 |

Full dataref list: [X-Plane DataRefs](http://www.xsquawkbox.net/xpsdk/docs/DataRefs.html)

## Next Steps

- [Configuration Guide](configuration.md) - All configuration options
- [Data Format Guide](data-format.md) - MAT file requirements
- [Getting Started](getting-started.md) - Basic usage guide
