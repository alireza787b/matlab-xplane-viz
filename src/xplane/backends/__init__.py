"""
X-Plane communication backends.

Provides multiple backends for communicating with X-Plane:
- XPCBackend: Uses NASA XPlaneConnect plugin (requires plugin installation)
- NativeUDPBackend: Uses X-Plane's built-in UDP interface (no plugin needed)
"""

from .base import XPlaneBackend
from .udp_backend import NativeUDPBackend
from .xpc_backend import XPCBackend

__all__ = ['XPlaneBackend', 'NativeUDPBackend', 'XPCBackend']
