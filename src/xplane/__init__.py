"""
X-Plane Integration Module for Flight Data Playback.

This module provides real-time playback of flight simulation data (.mat files)
in X-Plane flight simulator, supporting both NASA XPlaneConnect plugin and
native UDP communication.
"""

from .player import XPlanePlayer, PlaybackState
from .coordinate_utils import NEDConverter

__all__ = ['XPlanePlayer', 'PlaybackState', 'NEDConverter']
