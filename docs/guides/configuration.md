# Configuration Guide

Complete reference for all configuration files and options.

## Configuration Files

| File | Purpose |
|------|---------|
| `config/data_mapping.yaml` | MAT file variable name mappings |
| `config/xplane.yaml` | X-Plane connection and playback settings |
| `config/default.yaml` | Plot styling, colors, and visualization settings |
| `config/aircraft/vtol_default.yaml` | Aircraft geometry for 3D visualization |

## Data Mapping (`config/data_mapping.yaml`)

Maps your `.mat` file variable names to internal names. Edit this to match YOUR data format.

### Position Variables

```yaml
position:
  north: "N"    # Your .mat variable for North position (meters, NED frame)
  east: "E"     # Your .mat variable for East position (meters)
  down: "D"     # Your .mat variable for Down position (meters, positive = below origin)
```

**Example:** If your simulation uses `x_pos`, `y_pos`, `z_pos`:
```yaml
position:
  north: "x_pos"
  east: "y_pos"
  down: "z_pos"
```

### Attitude Variables

```yaml
attitude:
  roll: "phi"      # Roll angle (bank)
  pitch: "theta"   # Pitch angle
  yaw: "psi"       # Yaw/Heading angle
```

### Control Surfaces

```yaml
controls:
  aileron: "delta_a"   # Aileron deflection
  elevator: "delta_e"  # Elevator deflection
  rudder: "delta_r"    # Rudder deflection
```

### Propulsion

```yaml
propulsion:
  rpm_left: "RPM_Cl"     # Left motor/propeller RPM
  rpm_right: "RPM_Cr"    # Right motor/propeller RPM
  tilt_left: "theta_Cl"  # Left tilt angle (for tilt-rotor)
  tilt_right: "theta_Cr" # Right tilt angle
```

### Metadata

```yaml
metadata:
  sample_rate: "output_hz"  # Data sample rate (Hz)
  duration: "Time"          # Total simulation duration (seconds)
```

### Units

Specify the units used in your `.mat` file:

```yaml
units:
  position: "meters"        # meters or feet
  attitude: "radians"       # radians or degrees
  controls: "radians"       # radians or degrees
  propulsion_rpm: "rpm"     # RPM
  propulsion_tilt: "radians"  # radians or degrees
```

**Important:** The system will automatically convert to internal units (radians) if you specify `degrees`.

---

## X-Plane Configuration (`config/xplane.yaml`)

### Connection Settings

```yaml
connection:
  host: localhost     # X-Plane host (IP for remote)
  port: 49009         # XPlaneConnect plugin port
  native_port: 49000  # Native X-Plane UDP port
  backend: auto       # auto | xpc | native
  timeout: 1000       # Timeout in milliseconds
```

**Backend Options:**
- `auto` - Try XPC first, fall back to native UDP
- `xpc` - Use NASA XPlaneConnect (requires plugin)
- `native` - Use built-in X-Plane UDP (no plugin needed)

### Playback Settings

```yaml
playback:
  default_speed: 1.0  # 1.0 = real-time, 2.0 = double speed
  loop: false         # Repeat when finished
  show_status: true   # Display status in X-Plane
```

### Origin Point

```yaml
origin:
  auto_detect: true   # Use current X-Plane aircraft position

  # Manual override (when auto_detect: false)
  latitude: 37.5242
  longitude: -122.0690
  altitude: 100       # Meters MSL
```

### Control Normalization

```yaml
controls:
  aileron_max_deg: 30.0   # Max deflection for normalization
  elevator_max_deg: 30.0
  rudder_max_deg: 30.0
```

### Feature Toggles

```yaml
features:
  position: true    # Send position data
  attitude: true    # Send attitude data
  controls: true    # Send control surfaces
  propulsion: true  # Send RPM/tilt data
```

### Variable Mapping

Maps simulation variables to X-Plane datarefs:

```yaml
variable_mapping:
  controls:
    aileron:
      source_unit: "radians"
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"
      target_unit: "degrees"
      max_deflection: 30.0
      inverted: false

  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 10000
      scale: 0.01
```

---

## Plot Styling (`config/default.yaml`)

### General Plot Settings

```yaml
plot:
  dpi: 300           # Output resolution
  format: "png"      # png, svg, pdf
  figure_size: [12, 8]
  font_family: "DejaVu Sans"
  title_size: 14
  label_size: 12
  tick_size: 10
  legend_size: 10
```

### Colors

```yaml
colors:
  # Position plots
  position:
    N: "#1f77b4"      # Blue
    E: "#2ca02c"      # Green
    D: "#d62728"      # Red

  # Attitude plots
  attitude:
    phi: "#ff7f0e"    # Orange (roll)
    theta: "#9467bd"  # Purple (pitch)
    psi: "#8c564b"    # Brown (yaw)

  # Control surfaces
  controls:
    aileron: "#17becf"
    elevator: "#bcbd22"
    rudder: "#e377c2"
```

### Grid and Lines

```yaml
grid:
  show: true
  alpha: 0.3
  linestyle: "--"

lines:
  width: 1.5
  marker_size: 6
```

### Animation Settings

```yaml
animation:
  fps: 30
  duration_factor: 1.0
  trail_length: 100
  output_format: "gif"  # gif or mp4
```

---

## Aircraft Geometry (`config/aircraft/vtol_default.yaml`)

Defines 3D aircraft model for visualization.

### Basic Dimensions

```yaml
type: "vtol"
name: "VTOL Default"

geometry:
  fuselage:
    length: 8.0   # meters
    width: 1.2
    height: 1.0

  wing:
    span: 10.0
    chord: 1.5

  horizontal_tail:
    span: 3.0
    chord: 0.8

  vertical_tail:
    height: 1.2
    chord: 0.8
```

### Propeller Configuration

```yaml
  propellers:
    cruise:
      count: 2
      positions:
        - [0, -2.5, 0]   # Left [x, y, z]
        - [0, 2.5, 0]    # Right
      diameter: 1.5
      tiltable: true
```

### Aerodynamic Limits

```yaml
limits:
  control_surfaces:
    aileron_max: 30    # degrees
    elevator_max: 30
    rudder_max: 30

  attitude:
    roll_max: 60
    pitch_max: 30

  propulsion:
    rpm_max: 10000
    tilt_max: 90
```

---

## Custom Configurations

### Per-Session Config

Place a `config.yaml` in your session folder to override defaults:

```
sessions/
  session_001/
    config.yaml      # Session-specific overrides
    raw_data/
    plots/
```

### Environment Variables

```bash
export XPLANE_HOST="192.168.1.100"
export XPLANE_BACKEND="native"
```

### Command Line Overrides

Most settings can be overridden via CLI:

```bash
python run_analysis.py --session session_001 \
  --xplane-play \
  --xplane-host 192.168.1.100 \
  --xplane-backend native \
  --xplane-speed 2.0
```

---

## Next Steps

- [Data Format Guide](data-format.md) - MAT file requirements
- [X-Plane Setup](xplane-setup.md) - X-Plane integration
- [Getting Started](getting-started.md) - Basic usage
