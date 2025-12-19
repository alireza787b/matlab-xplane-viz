"""
Core FlightData class - the central data model for flight simulation data.
"""

import numpy as np
import scipy.io as sio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Any

from .utils.conversions import UnitConverter


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
    def from_mat_file(cls, filepath: str) -> 'FlightData':
        """
        Load flight data from a MATLAB .mat file.

        Args:
            filepath: Path to the .mat file

        Returns:
            FlightData instance with loaded and processed data
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"MAT file not found: {filepath}")

        # Load raw data
        mat_data = sio.loadmat(str(path))

        # Create instance
        flight_data = cls()
        flight_data.source_file = str(path)

        # Extract metadata
        if 'output_hz' in mat_data:
            flight_data.sample_rate = float(mat_data['output_hz'].flatten()[0])
        if 'Time' in mat_data:
            flight_data.duration = float(mat_data['Time'].flatten()[0])

        # Helper to safely extract array
        def get_array(key: str) -> np.ndarray:
            if key in mat_data:
                return mat_data[key].flatten().astype(np.float64)
            return np.array([])

        # Extract position
        flight_data.N = get_array('N')
        flight_data.E = get_array('E')
        flight_data.D = get_array('D')

        # Extract attitude (assumed to be in radians based on validation)
        flight_data.phi = get_array('phi')
        flight_data.theta = get_array('theta')
        flight_data.psi = get_array('psi')

        # Extract control surfaces
        flight_data.delta_a = get_array('delta_a')
        flight_data.delta_e = get_array('delta_e')
        flight_data.delta_r = get_array('delta_r')

        # Extract propulsion
        flight_data.RPM_Cl = get_array('RPM_Cl')
        flight_data.RPM_Cr = get_array('RPM_Cr')
        flight_data.theta_Cl = get_array('theta_Cl')
        flight_data.theta_Cr = get_array('theta_Cr')

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
