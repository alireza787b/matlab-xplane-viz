"""
Abstract base class for X-Plane communication backends.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any


@dataclass
class AircraftState:
    """Represents current aircraft state from X-Plane."""
    latitude: float      # degrees
    longitude: float     # degrees
    altitude: float      # meters MSL
    roll: float          # degrees
    pitch: float         # degrees
    heading: float       # degrees (true)
    gear: float = 1.0    # 0=up, 1=down

    def as_tuple(self) -> Tuple[float, ...]:
        return (self.latitude, self.longitude, self.altitude,
                self.roll, self.pitch, self.heading, self.gear)


@dataclass
class ControlState:
    """Represents control surface positions."""
    aileron: float = 0.0     # degrees or normalized [-1, 1]
    elevator: float = 0.0    # degrees or normalized [-1, 1]
    rudder: float = 0.0      # degrees or normalized [-1, 1]
    throttle: float = 0.0    # [0, 1]
    flaps: float = 0.0       # [0, 1]
    speedbrake: float = 0.0  # [-0.5, 1.5]


class XPlaneBackend(ABC):
    """
    Abstract interface for X-Plane communication backends.

    Implementations must provide methods for:
    - Connection management
    - Position/attitude control
    - Control surface manipulation
    - Dataref access
    """

    def __init__(self):
        self._connected = False
        self._host: str = "localhost"
        self._port: int = 49000

    @property
    def connected(self) -> bool:
        """Returns True if connected to X-Plane."""
        return self._connected

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @abstractmethod
    def connect(self, host: str = "localhost", port: int = 49000,
                timeout: float = 3.0) -> bool:
        """
        Establish connection to X-Plane.

        Args:
            host: X-Plane host address
            port: X-Plane UDP port
            timeout: Connection timeout in seconds

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to X-Plane."""
        pass

    @abstractmethod
    def send_position(self, lat: float, lon: float, alt: float,
                      roll: float, pitch: float, heading: float,
                      gear: float = -998) -> None:
        """
        Set aircraft position and attitude.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt: Altitude in meters MSL
            roll: Roll angle in degrees
            pitch: Pitch angle in degrees
            heading: True heading in degrees [0, 360]
            gear: Gear position (0=up, 1=down, -998=no change)
        """
        pass

    @abstractmethod
    def send_controls(self, aileron: float = -998, elevator: float = -998,
                      rudder: float = -998, throttle: float = -998,
                      gear: float = -998, flaps: float = -998) -> None:
        """
        Set control surface positions.

        Args:
            aileron: Aileron position (normalized or degrees, backend-specific)
            elevator: Elevator position
            rudder: Rudder position
            throttle: Throttle position [0, 1]
            gear: Gear position (0=up, 1=down)
            flaps: Flap position [0, 1]
            -998 = don't change
        """
        pass

    @abstractmethod
    def send_dataref(self, dref: str, value: float) -> None:
        """
        Set a dataref value in X-Plane.

        Args:
            dref: Full dataref path (e.g., "sim/flightmodel/position/latitude")
            value: Value to set
        """
        pass

    @abstractmethod
    def send_datarefs(self, drefs: Dict[str, float]) -> None:
        """
        Set multiple dataref values.

        Args:
            drefs: Dictionary mapping dataref paths to values
        """
        pass

    @abstractmethod
    def get_position(self) -> Optional[AircraftState]:
        """
        Get current aircraft position and attitude.

        Returns:
            AircraftState object or None if unavailable
        """
        pass

    @abstractmethod
    def get_dataref(self, dref: str) -> Optional[float]:
        """
        Get a dataref value from X-Plane.

        Args:
            dref: Full dataref path

        Returns:
            Dataref value or None if unavailable
        """
        pass

    def pause_sim(self, pause: bool) -> None:
        """
        Pause or unpause X-Plane physics simulation.

        Args:
            pause: True to pause, False to resume
        """
        self.send_dataref("sim/time/sim_speed", 0 if pause else 1)

    def override_physics(self, override: bool) -> None:
        """
        Override X-Plane physics for external position control.

        Args:
            override: True to take control, False to release
        """
        self.send_dataref("sim/operation/override/override_planepath",
                          1.0 if override else 0.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False
