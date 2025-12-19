"""
Coordinate conversion utilities for X-Plane integration.

Converts between NED (North-East-Down) local coordinates and
geodetic coordinates (Latitude, Longitude, Altitude).
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np


# WGS84 Earth parameters
EARTH_RADIUS_EQUATORIAL = 6378137.0  # meters
EARTH_RADIUS_POLAR = 6356752.3142    # meters
EARTH_FLATTENING = 1 / 298.257223563

# Simplified mean radius for flat-earth approximation
EARTH_RADIUS_MEAN = 6371000.0  # meters


@dataclass
class GeoPoint:
    """Geodetic point with latitude, longitude, and altitude."""
    latitude: float   # degrees
    longitude: float  # degrees
    altitude: float   # meters MSL

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.latitude, self.longitude, self.altitude)


@dataclass
class NEDPoint:
    """Local NED (North-East-Down) point in meters."""
    north: float  # meters, positive north
    east: float   # meters, positive east
    down: float   # meters, positive down (negative = up)

    def as_tuple(self) -> Tuple[float, float, float]:
        return (self.north, self.east, self.down)


class NEDConverter:
    """
    Converts between NED local coordinates and geodetic coordinates.

    Uses flat-earth approximation which is accurate for distances up to
    several hundred kilometers from the origin.
    """

    def __init__(self, origin_lat: float = 0.0, origin_lon: float = 0.0,
                 origin_alt: float = 0.0):
        """
        Initialize converter with a geodetic origin.

        Args:
            origin_lat: Origin latitude in degrees
            origin_lon: Origin longitude in degrees
            origin_alt: Origin altitude in meters MSL
        """
        self._origin_lat = origin_lat
        self._origin_lon = origin_lon
        self._origin_alt = origin_alt

        # Precompute scaling factors for efficiency
        self._update_scaling()

    def _update_scaling(self) -> None:
        """Update scaling factors based on origin latitude."""
        lat_rad = math.radians(self._origin_lat)

        # Radius of curvature in the meridian (north-south)
        self._R_n = EARTH_RADIUS_MEAN

        # Radius of curvature in the prime vertical (east-west)
        # Accounts for latitude-dependent Earth radius
        self._R_e = EARTH_RADIUS_MEAN * math.cos(lat_rad)

        # Meters per degree
        self._meters_per_deg_lat = (math.pi / 180.0) * self._R_n
        self._meters_per_deg_lon = (math.pi / 180.0) * self._R_e

    @property
    def origin(self) -> GeoPoint:
        """Get the current geodetic origin."""
        return GeoPoint(self._origin_lat, self._origin_lon, self._origin_alt)

    def set_origin(self, lat: float, lon: float, alt: float = 0.0) -> None:
        """
        Set a new geodetic origin.

        Args:
            lat: Origin latitude in degrees
            lon: Origin longitude in degrees
            alt: Origin altitude in meters MSL
        """
        self._origin_lat = lat
        self._origin_lon = lon
        self._origin_alt = alt
        self._update_scaling()

    def ned_to_geo(self, north: float, east: float, down: float) -> GeoPoint:
        """
        Convert NED coordinates to geodetic coordinates.

        Args:
            north: North position in meters
            east: East position in meters
            down: Down position in meters (positive = below origin)

        Returns:
            GeoPoint with latitude, longitude, altitude
        """
        # Latitude change from north displacement
        delta_lat = north / self._meters_per_deg_lat

        # Longitude change from east displacement
        delta_lon = east / self._meters_per_deg_lon

        # Altitude (MSL) from down displacement
        # Down is positive going below the origin
        alt = self._origin_alt - down

        return GeoPoint(
            latitude=self._origin_lat + delta_lat,
            longitude=self._origin_lon + delta_lon,
            altitude=alt
        )

    def geo_to_ned(self, lat: float, lon: float, alt: float) -> NEDPoint:
        """
        Convert geodetic coordinates to NED coordinates.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt: Altitude in meters MSL

        Returns:
            NEDPoint with north, east, down
        """
        # North from latitude difference
        north = (lat - self._origin_lat) * self._meters_per_deg_lat

        # East from longitude difference
        east = (lon - self._origin_lon) * self._meters_per_deg_lon

        # Down from altitude difference
        down = self._origin_alt - alt

        return NEDPoint(north=north, east=east, down=down)

    def ned_array_to_geo(self, N: np.ndarray, E: np.ndarray,
                         D: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Convert arrays of NED coordinates to geodetic coordinates.

        Args:
            N: Array of north positions in meters
            E: Array of east positions in meters
            D: Array of down positions in meters

        Returns:
            Tuple of (lat_array, lon_array, alt_array) in degrees and meters
        """
        lat = self._origin_lat + N / self._meters_per_deg_lat
        lon = self._origin_lon + E / self._meters_per_deg_lon
        alt = self._origin_alt - D

        return lat, lon, alt


def euler_to_xplane(phi: float, theta: float, psi: float,
                    input_degrees: bool = False) -> Tuple[float, float, float]:
    """
    Convert Euler angles to X-Plane convention.

    Args:
        phi: Roll angle (bank)
        theta: Pitch angle
        psi: Yaw/heading angle
        input_degrees: True if input is in degrees, False for radians

    Returns:
        Tuple of (roll, pitch, heading) in degrees for X-Plane
    """
    if input_degrees:
        roll = phi
        pitch = theta
        heading = psi
    else:
        roll = math.degrees(phi)
        pitch = math.degrees(theta)
        heading = math.degrees(psi)

    # Normalize heading to [0, 360]
    heading = heading % 360
    if heading < 0:
        heading += 360

    return roll, pitch, heading


def normalize_heading(heading: float) -> float:
    """Normalize heading to [0, 360) degrees."""
    heading = heading % 360
    if heading < 0:
        heading += 360
    return heading


def normalize_control(value: float, max_deflection: float = 30.0) -> float:
    """
    Normalize control surface deflection to [-1, 1] range.

    Args:
        value: Control deflection in degrees
        max_deflection: Maximum deflection in degrees (for normalization)

    Returns:
        Normalized value in [-1, 1]
    """
    normalized = value / max_deflection
    return max(-1.0, min(1.0, normalized))


def degrees_to_normalized(degrees: float, max_deg: float) -> float:
    """Convert degrees to normalized [-1, 1] based on max deflection."""
    return max(-1.0, min(1.0, degrees / max_deg))


def radians_to_normalized(radians: float, max_deg: float) -> float:
    """Convert radians to normalized [-1, 1] based on max deflection in degrees."""
    degrees = math.degrees(radians)
    return degrees_to_normalized(degrees, max_deg)
