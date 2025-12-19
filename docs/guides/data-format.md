# Data Format Specification

This document describes the expected format for MATLAB `.mat` files used by the visualization system.

## Required Variables

The following variables must be present in your `.mat` file:

### Position Data (NED Frame)

| Variable | Type | Description | Units |
|----------|------|-------------|-------|
| `N` | float64 array | North position | meters |
| `E` | float64 array | East position | meters |
| `D` | float64 array | Down position (negative = altitude) | meters |

### Attitude Data (Euler Angles)

| Variable | Type | Description | Units |
|----------|------|-------------|-------|
| `phi` | float64 array | Roll angle | **radians** |
| `theta` | float64 array | Pitch angle | **radians** |
| `psi` | float64 array | Yaw/heading angle | **radians** |

**Important:** Angles must be in radians, not degrees.

### Control Surface Data

| Variable | Type | Description | Units |
|----------|------|-------------|-------|
| `delta_a` | float64 array | Aileron deflection | radians |
| `delta_e` | float64 array | Elevator deflection | radians |
| `delta_r` | float64 array | Rudder deflection | radians |

### Propulsion Data (VTOL-specific)

| Variable | Type | Description | Units |
|----------|------|-------------|-------|
| `RPM_Cl` | uint16/float array | Left cruise propeller RPM | RPM |
| `RPM_Cr` | uint16/float array | Right cruise propeller RPM | RPM |
| `theta_Cl` | uint8/float array | Left propeller tilt angle | degrees |
| `theta_Cr` | uint8/float array | Right propeller tilt angle | degrees |

### Metadata

| Variable | Type | Description |
|----------|------|-------------|
| `Time` | scalar | Total simulation duration in seconds |
| `output_hz` | scalar | Data output frequency in Hz |

## Coordinate System

The system uses the **NED (North-East-Down)** coordinate frame:

```
        North (+X)
           ^
           |
           |
    West --+-- East (+Y)
           |
           |
           v
        (Down +Z into page)
```

- **N (North)**: Positive northward
- **E (East)**: Positive eastward
- **D (Down)**: Positive downward (altitude = -D)

## Euler Angle Convention

Uses aerospace standard **ZYX (3-2-1)** rotation sequence:
1. Yaw (ψ) about Z-axis
2. Pitch (θ) about Y-axis
3. Roll (φ) about X-axis

```
     Z (Down)
      |
      |  / Y (East)
      | /
      |/_____ X (North)

Roll (φ):  Rotation about X (body longitudinal axis)
Pitch (θ): Rotation about Y (body lateral axis)
Yaw (ψ):   Rotation about Z (body vertical axis)
```

## Example MATLAB Export

Here's how to export your Simulink data properly:

```matlab
% Assuming 'out' is your Simulink output structure
% Resample to consistent rate if needed
dt = 0.1;  % 10 Hz
t = 0:dt:150;  % 150 seconds

% Position (from your navigation block)
N = interp1(out.tout, out.N.Data, t);
E = interp1(out.tout, out.E.Data, t);
D = interp1(out.tout, out.D.Data, t);

% Attitude (ensure radians!)
phi = interp1(out.tout, out.phi.Data, t);
theta = interp1(out.tout, out.theta.Data, t);
psi = interp1(out.tout, out.psi.Data, t);

% Control surfaces
delta_a = interp1(out.tout, out.delta_a.Data, t);
delta_e = interp1(out.tout, out.delta_e.Data, t);
delta_r = interp1(out.tout, out.delta_r.Data, t);

% Propulsion
RPM_Cl = interp1(out.tout, out.RPM_left.Data, t);
RPM_Cr = interp1(out.tout, out.RPM_right.Data, t);
theta_Cl = interp1(out.tout, out.tilt_left.Data, t);
theta_Cr = interp1(out.tout, out.tilt_right.Data, t);

% Metadata
Time = uint8(max(t));
output_hz = uint8(1/dt);

% Save
save('my_simulation.mat', 'N', 'E', 'D', 'phi', 'theta', 'psi', ...
     'delta_a', 'delta_e', 'delta_r', 'RPM_Cl', 'RPM_Cr', ...
     'theta_Cl', 'theta_Cr', 'Time', 'output_hz');
```

## Data Validation

The system automatically validates your data on load:

1. **NaN/Inf Check**: Flags any invalid values
2. **Range Check**: Warns about unusual attitude or control values
3. **Consistency Check**: Verifies sample count matches expected from Time and output_hz
4. **Kinematics Check**: Derives velocities and checks for physical reasonableness

## Derived Quantities

The following are automatically computed from your input data:

| Derived Variable | Description | Formula |
|------------------|-------------|---------|
| `Vn` | North velocity | dN/dt |
| `Ve` | East velocity | dE/dt |
| `Vd` | Down velocity | dD/dt |
| `V_ground` | Ground speed | √(Vn² + Ve²) |
| `V_total` | Total velocity | √(Vn² + Ve² + Vd²) |
| `altitude` | Altitude | -D |
| `climb_rate` | Climb rate | -Vd |

## Troubleshooting

### "Angles appear to be in degrees"
If your angles have values > 2π, the system will warn you. Convert to radians:
```matlab
phi_rad = deg2rad(phi_deg);
```

### Inconsistent array sizes
All time-series arrays must have the same length. Use `interp1` to resample if needed.

### Missing variables
Check the error message for which variable is missing. The system will still run with partial data but some plots may be skipped.
