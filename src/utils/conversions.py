"""
Unit conversion utilities for flight simulation data.
"""

import numpy as np
from typing import Union

ArrayLike = Union[float, np.ndarray]


class UnitConverter:
    """Handles unit conversions for flight data."""

    # Length conversions
    M_TO_FT = 3.28084
    FT_TO_M = 1.0 / M_TO_FT
    M_TO_NM = 0.000539957
    NM_TO_M = 1852.0
    M_TO_KM = 0.001
    KM_TO_M = 1000.0

    # Speed conversions
    MS_TO_KNOTS = 1.94384
    KNOTS_TO_MS = 1.0 / MS_TO_KNOTS
    MS_TO_KMH = 3.6
    KMH_TO_MS = 1.0 / MS_TO_KMH
    MS_TO_FPM = 196.85  # feet per minute

    # Angle conversions
    RAD_TO_DEG = 180.0 / np.pi
    DEG_TO_RAD = np.pi / 180.0

    @classmethod
    def rad_to_deg(cls, rad: ArrayLike) -> ArrayLike:
        """Convert radians to degrees."""
        return rad * cls.RAD_TO_DEG

    @classmethod
    def deg_to_rad(cls, deg: ArrayLike) -> ArrayLike:
        """Convert degrees to radians."""
        return deg * cls.DEG_TO_RAD

    @classmethod
    def ms_to_knots(cls, ms: ArrayLike) -> ArrayLike:
        """Convert m/s to knots."""
        return ms * cls.MS_TO_KNOTS

    @classmethod
    def ms_to_kmh(cls, ms: ArrayLike) -> ArrayLike:
        """Convert m/s to km/h."""
        return ms * cls.MS_TO_KMH

    @classmethod
    def m_to_ft(cls, m: ArrayLike) -> ArrayLike:
        """Convert meters to feet."""
        return m * cls.M_TO_FT

    @classmethod
    def ms_to_fpm(cls, ms: ArrayLike) -> ArrayLike:
        """Convert m/s to feet per minute."""
        return ms * cls.MS_TO_FPM

    @classmethod
    def normalize_angle_deg(cls, angle: ArrayLike) -> ArrayLike:
        """Normalize angle to [-180, 180] degrees."""
        return ((angle + 180) % 360) - 180

    @classmethod
    def normalize_angle_rad(cls, angle: ArrayLike) -> ArrayLike:
        """Normalize angle to [-pi, pi] radians."""
        return ((angle + np.pi) % (2 * np.pi)) - np.pi
