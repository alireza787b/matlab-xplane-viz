# Known Issues and Limitations

This document describes known limitations of the flight data visualization and X-Plane playback system, along with workarounds and possible future solutions.

## X-Plane Physics Override

### Problem

When playing back flight data in X-Plane, the tool uses **physics override mode** (`override_planepath`). This tells X-Plane to accept position and attitude values from the playback script instead of calculating them from the flight model.

**Side Effect**: When physics override is active, X-Plane ignores certain datarefs:

- `sim/flightmodel/engine/ENGN_thro[n]` - Throttle commands
- `sim/flightmodel/engine/ENGN_N1_[n]` - Engine N1 percentage

This means:
1. Cockpit throttle gauges may not respond during playback
2. Engine RPM indicators may not match the simulation data
3. Engine sounds may not correspond to actual RPM values

### Why This Happens

X-Plane's physics override is designed for external position control (like flight training devices). When active, X-Plane bypasses its internal flight model calculations - including engine response to throttle inputs.

The script sends throttle and N1 values, but X-Plane ignores them because it's not running the engine physics model.

### Current Workarounds

1. **Manual Prop Animation**: The playback script manually calculates and sets `prop_rotation_angle_deg` based on RPM data. This provides visual prop rotation even without physics.

2. **ACF Idle RPM**: Configure the aircraft's ACF file with idle RPM:
   ```
   acf/_RSC_idlespeed_ENGN = 500  # RPM at idle
   ```
   This ensures props rotate at idle even when the script isn't controlling them.

3. **Position/Attitude Work Correctly**: The main value of playback - seeing the aircraft fly the recorded trajectory - works perfectly.

4. **Control Surfaces Work**: Aileron, elevator, rudder animations work correctly.

### Possible Future Solutions

1. **Disable Physics Override**: Use only dataref control for position without physics override. This would require more complex dataref manipulation but might allow throttle response.

2. **Use Cockpit Actuator Datarefs**: Try `sim/cockpit2/engine/actuators/throttle_ratio` instead of `ENGN_thro`.

3. **XPC sendCTRL**: The XPlaneConnect plugin has a `sendCTRL` function that might handle throttle differently than `sendDREF`.

4. **Accept and Document**: The current workaround (manual prop animation + idle RPM) provides good visual results for demonstrations.

## Aircraft-Specific Considerations

### VTOL Tiltrotor Aircraft

For VTOL aircraft with tilting propellers:
- Prop tilt angles (`acf_vertcant`) work correctly
- Prop rotation is manually animated based on RPM data
- Aircraft should have `acf/_is_vtol = 1` in ACF file

### Fixed-Wing Aircraft

For conventional fixed-wing aircraft:
- Throttle/RPM limitations apply as described above
- No tilt angle configuration needed
- Single-engine or multi-engine configurations work via config

### Electric Aircraft

For electric motor aircraft:
- Ensure ACF has adequate battery capacity: `acf/_battery_watt_hr_max`
- Set appropriate idle speed: `acf/_RSC_idlespeed_ENGN`
- Fast spool time helps responsiveness: `acf/_spool_time_compressor_prop`

## Data Format Issues

### Missing Variables

If your .mat file is missing expected variables:
- Position (N, E, D) - Required for trajectory
- Attitude (phi, theta, psi) - Required for orientation
- Controls (delta_a, delta_e, delta_r) - Optional
- Propulsion (RPM, tilt) - Optional, configurable per aircraft type

The system gracefully handles missing optional variables by not plotting them.

### Unit Mismatches

Common issues:
- Position in feet instead of meters
- Angles in degrees instead of radians
- RPM as percentage instead of actual RPM

Solution: Configure unit conversion in `config/data_mapping.yaml`:
```yaml
units:
  position: "feet"  # Will convert to meters
  attitude: "degrees"  # Will convert to radians
```

## Reporting Issues

If you encounter issues not covered here:
1. Check the [GitHub Issues](https://github.com/alireza787b/matlab-xplane-viz/issues)
2. Include your configuration files and error messages
3. Describe the aircraft type and data format you're using
