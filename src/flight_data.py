"""
Core FlightData class - the central data model for flight simulation data.
"""

import warnings
import numpy as np
import scipy.io as sio
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any, Union

from .utils.conversions import UnitConverter


# Default variable mappings - FALLBACK ONLY
# This is used when config/data_mapping.yaml is not found.
# Users should edit config/data_mapping.yaml for their own data format.
DEFAULT_MAPPING = {
    'position': {'north': 'N', 'east': 'E', 'down': 'D'},
    'attitude': {'roll': 'phi', 'pitch': 'theta', 'yaw': 'psi'},
    'controls': {'aileron': 'delta_a', 'elevator': 'delta_e', 'rudder': 'delta_r'},
    'propulsion': {
        'rpm_left': 'RPM_Cl', 'rpm_right': 'RPM_Cr',
        'tilt_left': 'theta_Cl', 'tilt_right': 'theta_Cr'
    },
    'metadata': {'sample_rate': 'output_hz', 'duration': 'Time'},
    'units': {
        'position': 'meters', 'attitude': 'radians',
        'controls': 'radians', 'propulsion_tilt': 'radians'
    }
}


def load_mapping_config(config_path: Optional[Union[str, Path]] = None) -> Dict:
    """
    Load data mapping configuration from YAML file.

    Args:
        config_path: Path to data_mapping.yaml. If None, searches default locations.

    Returns:
        Dictionary with variable mappings
    """
    if config_path is None:
        # Search default locations
        search_paths = [
            Path(__file__).parent.parent / 'config' / 'data_mapping.yaml',
            Path.cwd() / 'config' / 'data_mapping.yaml',
            Path.cwd() / 'data_mapping.yaml',
        ]
        for path in search_paths:
            if path.exists():
                config_path = path
                break

    if config_path is None or not Path(config_path).exists():
        return DEFAULT_MAPPING.copy()

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Merge with defaults for any missing keys
    merged = DEFAULT_MAPPING.copy()
    for category in merged:
        if category in config:
            if isinstance(merged[category], dict):
                merged[category].update(config[category])
            else:
                merged[category] = config[category]

    return merged


@dataclass
class FlightData:
    """
    Core data container for flight simulation data.

    Handles loading from .mat files, data validation, and derived quantity computation.
    All angles are stored internally in radians, with degree conversions available.
    """

    # Metadata
    source_file: str = ""
    sample_rate: float = 10.0  # Hz
    duration: float = 0.0  # seconds
    n_samples: int = 0

    # Time vector
    time: np.ndarray = field(default_factory=lambda: np.array([]))

    # Position (NED frame, meters)
    N: np.ndarray = field(default_factory=lambda: np.array([]))
    E: np.ndarray = field(default_factory=lambda: np.array([]))
    D: np.ndarray = field(default_factory=lambda: np.array([]))

    # Attitude (Euler angles, radians)
    phi: np.ndarray = field(default_factory=lambda: np.array([]))    # Roll
    theta: np.ndarray = field(default_factory=lambda: np.array([]))  # Pitch
    psi: np.ndarray = field(default_factory=lambda: np.array([]))    # Yaw/Heading

    # Control surfaces (radians)
    delta_a: np.ndarray = field(default_factory=lambda: np.array([]))  # Aileron
    delta_e: np.ndarray = field(default_factory=lambda: np.array([]))  # Elevator
    delta_r: np.ndarray = field(default_factory=lambda: np.array([]))  # Rudder

    # Propulsion
    RPM_Cl: np.ndarray = field(default_factory=lambda: np.array([]))   # Left cruise RPM
    RPM_Cr: np.ndarray = field(default_factory=lambda: np.array([]))   # Right cruise RPM
    theta_Cl: np.ndarray = field(default_factory=lambda: np.array([]))  # Left tilt angle
    theta_Cr: np.ndarray = field(default_factory=lambda: np.array([]))  # Right tilt angle

    # Derived quantities (computed after loading)
    Vn: np.ndarray = field(default_factory=lambda: np.array([]))  # North velocity
    Ve: np.ndarray = field(default_factory=lambda: np.array([]))  # East velocity
    Vd: np.ndarray = field(default_factory=lambda: np.array([]))  # Down velocity
    V_ground: np.ndarray = field(default_factory=lambda: np.array([]))  # Ground speed
    V_total: np.ndarray = field(default_factory=lambda: np.array([]))   # Total velocity
    altitude: np.ndarray = field(default_factory=lambda: np.array([]))  # Altitude (=-D)

    # Raw data storage for any extra variables
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mat_file(cls, filepath: str,
                      mapping_config: Optional[Union[str, Path, Dict]] = None) -> 'FlightData':
        """
        Load flight data from a MATLAB .mat file.

        Args:
            filepath: Path to the .mat file
            mapping_config: Either a path to data_mapping.yaml, a dict with mappings,
                           or None to use default/auto-detected config

        Returns:
            FlightData instance with loaded and processed data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"MAT file not found: {filepath}")

        # Load mapping configuration
        if isinstance(mapping_config, dict):
            mapping = mapping_config
        else:
            mapping = load_mapping_config(mapping_config)

        # Load raw data
        mat_data = sio.loadmat(str(path))

        # Create instance
        flight_data = cls()
        flight_data.source_file = str(path)

        # Helper to safely extract array using mapping
        def get_array(mat_key: str) -> np.ndarray:
            if mat_key in mat_data:
                return mat_data[mat_key].flatten().astype(np.float64)
            return np.array([])

        def get_scalar(mat_key: str, default: float = 0.0) -> float:
            if mat_key in mat_data:
                return float(mat_data[mat_key].flatten()[0])
            return default

        # Extract metadata using mapping
        meta = mapping.get('metadata', {})
        flight_data.sample_rate = get_scalar(meta.get('sample_rate', 'output_hz'), 10.0)
        flight_data.duration = get_scalar(meta.get('duration', 'Time'), 0.0)

        # Extract position using mapping
        pos = mapping.get('position', {})
        flight_data.N = get_array(pos.get('north', 'N'))
        flight_data.E = get_array(pos.get('east', 'E'))
        flight_data.D = get_array(pos.get('down', 'D'))

        # Extract attitude using mapping
        att = mapping.get('attitude', {})
        flight_data.phi = get_array(att.get('roll', 'phi'))
        flight_data.theta = get_array(att.get('pitch', 'theta'))
        flight_data.psi = get_array(att.get('yaw', 'psi'))

        # Convert attitude to radians if needed
        units = mapping.get('units', {})
        if units.get('attitude', 'radians') == 'degrees':
            flight_data.phi = np.radians(flight_data.phi)
            flight_data.theta = np.radians(flight_data.theta)
            flight_data.psi = np.radians(flight_data.psi)

        # Extract control surfaces using mapping
        ctrl = mapping.get('controls', {})
        flight_data.delta_a = get_array(ctrl.get('aileron', 'delta_a'))
        flight_data.delta_e = get_array(ctrl.get('elevator', 'delta_e'))
        flight_data.delta_r = get_array(ctrl.get('rudder', 'delta_r'))

        # Convert controls to radians if needed
        if units.get('controls', 'radians') == 'degrees':
            flight_data.delta_a = np.radians(flight_data.delta_a)
            flight_data.delta_e = np.radians(flight_data.delta_e)
            flight_data.delta_r = np.radians(flight_data.delta_r)

        # Extract propulsion using mapping
        prop = mapping.get('propulsion', {})
        flight_data.RPM_Cl = get_array(prop.get('rpm_left', 'RPM_Cl'))
        flight_data.RPM_Cr = get_array(prop.get('rpm_right', 'RPM_Cr'))
        flight_data.theta_Cl = get_array(prop.get('tilt_left', 'theta_Cl'))
        flight_data.theta_Cr = get_array(prop.get('tilt_right', 'theta_Cr'))

        # Convert propulsion tilt to radians if needed
        if units.get('propulsion_tilt', 'radians') == 'degrees':
            flight_data.theta_Cl = np.radians(flight_data.theta_Cl)
            flight_data.theta_Cr = np.radians(flight_data.theta_Cr)

        # Set sample count
        flight_data.n_samples = len(flight_data.N)

        # Generate time vector
        dt = 1.0 / flight_data.sample_rate
        flight_data.time = np.arange(flight_data.n_samples) * dt

        # Store raw data for reference
        flight_data.raw_data = {
            k: v for k, v in mat_data.items()
            if not k.startswith('__')
        }

        # Validate loaded data
        flight_data._validate_data()

        # Compute derived quantities
        flight_data._compute_derived_quantities()

        return flight_data

    def _compute_derived_quantities(self) -> None:
        """Compute velocities and other derived quantities from position data."""
        if len(self.N) == 0:
            return

        dt = 1.0 / self.sample_rate

        # Compute velocities using central differences
        self.Vn = np.gradient(self.N, dt)
        self.Ve = np.gradient(self.E, dt)
        self.Vd = np.gradient(self.D, dt)

        # Ground speed and total velocity
        self.V_ground = np.sqrt(self.Vn**2 + self.Ve**2)
        self.V_total = np.sqrt(self.Vn**2 + self.Ve**2 + self.Vd**2)

        # Altitude (negative of Down)
        self.altitude = -self.D

    def _validate_data(self) -> None:
        """
        Validate loaded data for NaN/Inf values and consistency.

        Raises:
            ValueError: If NaN or Inf values are found in critical arrays.
        """
        # Define arrays to validate
        arrays_to_check = [
            (self.N, 'N (North position)'),
            (self.E, 'E (East position)'),
            (self.D, 'D (Down position)'),
            (self.phi, 'phi (Roll angle)'),
            (self.theta, 'theta (Pitch angle)'),
            (self.psi, 'psi (Yaw angle)'),
        ]

        for arr, name in arrays_to_check:
            if len(arr) == 0:
                continue
            if np.any(np.isnan(arr)):
                raise ValueError(f"NaN values found in {name}. Check data source.")
            if np.any(np.isinf(arr)):
                raise ValueError(f"Infinite values found in {name}. Check data source.")

        # Check array length consistency
        arrays_with_data = [(arr, name) for arr, name in arrays_to_check if len(arr) > 0]
        if len(arrays_with_data) > 1:
            lengths = [len(arr) for arr, _ in arrays_with_data]
            if len(set(lengths)) > 1:
                details = [f"{name}: {len(arr)}" for arr, name in arrays_with_data]
                raise ValueError(
                    f"Inconsistent array lengths: {', '.join(details)}. "
                    "All arrays must have the same number of samples."
                )

        # Warn about potential unit issues
        if len(self.phi) > 0:
            if np.any(np.abs(self.phi) > 2 * np.pi):
                warnings.warn(
                    "Roll angles (phi) exceed 2π radians. "
                    "If your data is in degrees, set 'attitude: degrees' in data_mapping.yaml",
                    UserWarning
                )
        if len(self.theta) > 0:
            if np.any(np.abs(self.theta) > np.pi / 2 + 0.1):  # Allow small margin
                warnings.warn(
                    "Pitch angles (theta) exceed ±90°. "
                    "If your data is in degrees, set 'attitude: degrees' in data_mapping.yaml",
                    UserWarning
                )

    # Convenience properties for degree conversions
    @property
    def phi_deg(self) -> np.ndarray:
        """Roll angle in degrees."""
        return UnitConverter.rad_to_deg(self.phi)

    @property
    def theta_deg(self) -> np.ndarray:
        """Pitch angle in degrees."""
        return UnitConverter.rad_to_deg(self.theta)

    @property
    def psi_deg(self) -> np.ndarray:
        """Yaw/heading in degrees."""
        return UnitConverter.rad_to_deg(self.psi)

    @property
    def delta_a_deg(self) -> np.ndarray:
        """Aileron deflection in degrees."""
        return UnitConverter.rad_to_deg(self.delta_a)

    @property
    def delta_e_deg(self) -> np.ndarray:
        """Elevator deflection in degrees."""
        return UnitConverter.rad_to_deg(self.delta_e)

    @property
    def delta_r_deg(self) -> np.ndarray:
        """Rudder deflection in degrees."""
        return UnitConverter.rad_to_deg(self.delta_r)

    @property
    def V_ground_knots(self) -> np.ndarray:
        """Ground speed in knots."""
        return UnitConverter.ms_to_knots(self.V_ground)

    @property
    def V_ground_kmh(self) -> np.ndarray:
        """Ground speed in km/h."""
        return UnitConverter.ms_to_kmh(self.V_ground)

    @property
    def climb_rate(self) -> np.ndarray:
        """Climb rate in m/s (positive = climbing)."""
        return -self.Vd

    @property
    def climb_rate_fpm(self) -> np.ndarray:
        """Climb rate in feet per minute."""
        return UnitConverter.ms_to_fpm(self.climb_rate)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the flight data."""
        return {
            'duration_s': self.duration,
            'n_samples': self.n_samples,
            'sample_rate_hz': self.sample_rate,
            'distance_traveled_m': self.N[-1] - self.N[0] if len(self.N) > 0 else 0,
            'altitude_range_m': (self.altitude.min(), self.altitude.max()) if len(self.altitude) > 0 else (0, 0),
            'speed_range_ms': (self.V_ground.min(), self.V_ground.max()) if len(self.V_ground) > 0 else (0, 0),
            'mean_speed_ms': self.V_ground.mean() if len(self.V_ground) > 0 else 0,
            'mean_speed_knots': self.V_ground_knots.mean() if len(self.V_ground) > 0 else 0,
        }

    def __repr__(self) -> str:
        return (
            f"FlightData(source='{Path(self.source_file).name}', "
            f"duration={self.duration}s, samples={self.n_samples}, "
            f"rate={self.sample_rate}Hz)"
        )
