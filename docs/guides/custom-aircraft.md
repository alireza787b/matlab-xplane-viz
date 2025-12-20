# Custom Aircraft and Data Mapping Guide

This guide explains how to use ANY MATLAB/Simulink simulation data with ANY X-Plane aircraft model. The system is fully configurable through two YAML files.

## The Mapping Chain

```
Your .mat file → data_mapping.yaml → Internal Variables → xplane.yaml → X-Plane Datarefs
```

1. **Your .mat file**: Contains your simulation data with your variable names
2. **data_mapping.yaml**: Maps your variable names to internal names
3. **Internal Variables**: Standard names used by the system (N, E, D, phi, theta, psi, etc.)
4. **xplane.yaml**: Maps internal variables to X-Plane datarefs
5. **X-Plane Datarefs**: The actual X-Plane parameters being controlled

## Step 1: Map Your MAT File Variables

Edit `config/data_mapping.yaml` to match YOUR .mat file's variable names.

### Example: Custom Position Variable Names

If your .mat file uses `pos_x`, `pos_y`, `pos_z` instead of `N`, `E`, `D`:

```yaml
position:
  north: "pos_x"    # Your variable name for North position
  east: "pos_y"     # Your variable name for East position
  down: "pos_z"     # Your variable name for Down position

units:
  position: "meters"  # or "feet"
```

### Example: Attitude in Degrees

If your simulation outputs attitude in degrees:

```yaml
attitude:
  roll: "roll_angle"    # Your variable name
  pitch: "pitch_angle"
  yaw: "heading"

units:
  attitude: "degrees"   # System will convert to radians internally
```

### Example: Different Propulsion Variables

```yaml
propulsion:
  rpm_left: "motor1_rpm"
  rpm_right: "motor2_rpm"
  tilt_left: "nacelle1_angle"
  tilt_right: "nacelle2_angle"

units:
  propulsion_tilt: "degrees"  # or "radians"
```

## Step 2: Map to X-Plane Datarefs

Edit `config/xplane.yaml` to target YOUR X-Plane aircraft's datarefs.

### Control Surfaces

Different X-Plane aircraft use different datarefs. Find yours in Plane Maker or using DataRefTool.

```yaml
variable_mapping:
  controls:
    aileron:
      source_unit: "radians"
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"  # Default
      target_unit: "degrees"
      max_deflection: 30.0
      inverted: false

    elevator:
      source_unit: "radians"
      target_dref: "sim/flightmodel/controls/hstab1_elv1def"
      target_unit: "degrees"
      max_deflection: 25.0
      inverted: false

    rudder:
      source_unit: "radians"
      target_dref: "sim/flightmodel/controls/vstab1_rud1def"
      target_unit: "degrees"
      max_deflection: 30.0
      inverted: false
```

### Propulsion System

For different aircraft types, map to appropriate datarefs:

```yaml
  propulsion:
    # For conventional aircraft
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 10000      # Your simulation's max RPM
      scale: 0.01           # RPM to N1 percentage

    # For tilt-rotor/VTOL
    tilt_left:
      source_unit: "radians"
      target_dref: "sim/flightmodel/engine/POINT_pitch[0]"
      target_unit: "degrees"
```

## Common Aircraft Type Configurations

### Fixed-Wing Aircraft

```yaml
variable_mapping:
  controls:
    aileron:
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"
      max_deflection: 20.0
    elevator:
      target_dref: "sim/flightmodel/controls/hstab1_elv1def"
      max_deflection: 25.0
    rudder:
      target_dref: "sim/flightmodel/controls/vstab1_rud1def"
      max_deflection: 30.0

  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 2700
      scale: 0.037  # RPM to percentage
```

### Tilt-Rotor VTOL

```yaml
variable_mapping:
  controls:
    aileron:
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"
    elevator:
      target_dref: "sim/flightmodel/controls/hstab1_elv1def"
    rudder:
      target_dref: "sim/flightmodel/controls/vstab1_rud1def"

  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 10000
      scale: 0.01
    rpm_right:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[1]"
      max_value: 10000
      scale: 0.01
    tilt_left:
      target_dref: "sim/flightmodel/engine/POINT_pitch[0]"
      source_unit: "radians"
      target_unit: "degrees"
    tilt_right:
      target_dref: "sim/flightmodel/engine/POINT_pitch[1]"
      source_unit: "radians"
      target_unit: "degrees"
```

### Quadcopter/Multirotor

```yaml
variable_mapping:
  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 8000
      scale: 0.0125
    rpm_right:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[1]"
      max_value: 8000
      scale: 0.0125
    # Add more motors as needed for engines [2], [3], etc.
```

## Finding X-Plane Datarefs

### Using DataRefTool Plugin

1. Install [DataRefTool](https://github.com/leecbaker/datareftool) in X-Plane
2. Open the plugin window in X-Plane
3. Search for datarefs by keyword (e.g., "aileron", "engine")
4. Note the full dataref path

### Common Datarefs Reference

| Purpose | Dataref | Notes |
|---------|---------|-------|
| Left Aileron | `sim/flightmodel/controls/wing1l_ail1def` | Degrees |
| Right Aileron | `sim/flightmodel/controls/wing1r_ail1def` | Degrees |
| Left Elevator | `sim/flightmodel/controls/hstab1_elv1def` | Degrees |
| Right Elevator | `sim/flightmodel/controls/hstab2_elv1def` | Degrees |
| Rudder | `sim/flightmodel/controls/vstab1_rud1def` | Degrees |
| Throttle | `sim/flightmodel/engine/ENGN_thro[n]` | 0-1 |
| N1 Percentage | `sim/flightmodel/engine/ENGN_N1_[n]` | 0-100 |
| Engine Tilt | `sim/flightmodel/engine/POINT_pitch[n]` | Degrees |
| Flaps | `sim/flightmodel/controls/flaprqst` | 0-1 |
| Gear | `sim/cockpit/switches/gear_handle_status` | 0/1 |

Full dataref list: [X-Plane DataRefs](http://www.xsquawkbox.net/xpsdk/docs/DataRefs.html)

## Complete Example

### Your Simulation Data (example.mat)

```
Variables in your .mat file:
- x_pos, y_pos, z_pos (meters, NED frame)
- roll_deg, pitch_deg, heading_deg (degrees)
- ail_cmd, elev_cmd, rud_cmd (degrees)
- motor1_rpm, motor2_rpm (RPM)
- nacelle1_deg, nacelle2_deg (degrees)
- sim_time (seconds)
- sample_freq (Hz)
```

### config/data_mapping.yaml

```yaml
position:
  north: "x_pos"
  east: "y_pos"
  down: "z_pos"

attitude:
  roll: "roll_deg"
  pitch: "pitch_deg"
  yaw: "heading_deg"

controls:
  aileron: "ail_cmd"
  elevator: "elev_cmd"
  rudder: "rud_cmd"

propulsion:
  rpm_left: "motor1_rpm"
  rpm_right: "motor2_rpm"
  tilt_left: "nacelle1_deg"
  tilt_right: "nacelle2_deg"

metadata:
  sample_rate: "sample_freq"
  duration: "sim_time"

units:
  position: "meters"
  attitude: "degrees"
  controls: "degrees"
  propulsion_tilt: "degrees"
```

### config/xplane.yaml (variable_mapping section)

```yaml
variable_mapping:
  controls:
    aileron:
      source_unit: "degrees"  # Already converted from config
      target_dref: "sim/flightmodel/controls/wing1l_ail1def"
      target_unit: "degrees"
      max_deflection: 25.0
      inverted: false

    elevator:
      source_unit: "degrees"
      target_dref: "sim/flightmodel/controls/hstab1_elv1def"
      target_unit: "degrees"
      max_deflection: 20.0
      inverted: false

    rudder:
      source_unit: "degrees"
      target_dref: "sim/flightmodel/controls/vstab1_rud1def"
      target_unit: "degrees"
      max_deflection: 30.0
      inverted: false

  propulsion:
    rpm_left:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[0]"
      max_value: 8000
      scale: 0.0125

    rpm_right:
      target_dref: "sim/flightmodel/engine/ENGN_N1_[1]"
      max_value: 8000
      scale: 0.0125

    tilt_left:
      source_unit: "degrees"  # Already in degrees from simulation
      target_dref: "sim/flightmodel/engine/POINT_pitch[0]"
      target_unit: "degrees"

    tilt_right:
      source_unit: "degrees"
      target_dref: "sim/flightmodel/engine/POINT_pitch[1]"
      target_unit: "degrees"
```

### Run Playback

```bash
python run_analysis.py --session my_session --xplane-play
```

## Troubleshooting

### Control Surfaces Moving Wrong Direction

Set `inverted: true` in the control mapping:

```yaml
aileron:
  inverted: true
```

### RPM Values Too High/Low

Adjust `max_value` and `scale`:

```yaml
rpm_left:
  max_value: 5000    # Your simulation's max RPM
  scale: 0.02        # Adjust to get correct N1 percentage
```

### Aircraft Not Responding

1. Verify X-Plane is running and aircraft is loaded
2. Check dataref paths match your aircraft (use DataRefTool)
3. Try `--xplane-backend native` to bypass XPC plugin

### Data Format Issues

Run validation:

```python
from src.flight_data import FlightData

try:
    data = FlightData.from_mat_file("your_data.mat")
    print(data.get_summary())
except ValueError as e:
    print(f"Data validation failed: {e}")
```

## Next Steps

- [Configuration Guide](configuration.md) - Complete config reference
- [X-Plane Setup](xplane-setup.md) - X-Plane integration details
- [Data Format Guide](data-format.md) - MAT file requirements
