"""
NASA XPlaneConnect backend.

This backend uses the NASA XPlaneConnect library which provides a
high-level API for X-Plane communication. Requires the XPC plugin
to be installed in X-Plane.

Plugin download: https://github.com/nasa/XPlaneConnect/releases
"""

from typing import Dict, Optional
import sys
import os

# Add vendors directory to path for xpc module
_vendors_path = os.path.join(os.path.dirname(__file__), '..', 'vendors')
if _vendors_path not in sys.path:
    sys.path.insert(0, _vendors_path)

from .base import XPlaneBackend, AircraftState

# Try to import xpc
try:
    from ..vendors import xpc
    XPC_AVAILABLE = True
except ImportError:
    try:
        import xpc
        XPC_AVAILABLE = True
    except ImportError:
        XPC_AVAILABLE = False
        xpc = None


class XPCBackend(XPlaneBackend):
    """
    NASA XPlaneConnect backend.

    Advantages:
    - High-level, easy-to-use API
    - Well-tested and documented
    - Built-in playback examples
    - MATLAB support available

    Requirements:
    - XPC plugin must be installed in X-Plane
    - Plugin listens on port 49009 by default
    """

    def __init__(self):
        super().__init__()
        self._client = None
        self._port = 49009  # XPC default port

    @staticmethod
    def is_available() -> bool:
        """Check if XPC library is available."""
        return XPC_AVAILABLE

    def connect(self, host: str = "localhost", port: int = 49009,
                timeout: float = 1000) -> bool:
        """
        Connect to X-Plane via XPC plugin.

        Args:
            host: X-Plane host address
            port: XPC plugin port (default 49009)
            timeout: Timeout in milliseconds

        Returns:
            True if connection successful
        """
        if not XPC_AVAILABLE:
            print("XPlaneConnect library not available")
            return False

        try:
            self._host = host
            self._port = port

            # XPC timeout is in milliseconds
            self._client = xpc.XPlaneConnect(host, port, 0, int(timeout))
            self._connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to XPC: {e}")
            return False

    def disconnect(self) -> None:
        """Close XPC connection."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._connected = False

    def send_position(self, lat: float, lon: float, alt: float,
                      roll: float, pitch: float, heading: float,
                      gear: float = -998) -> None:
        """
        Set aircraft position using XPC sendPOSI.

        XPC sendPOSI format:
        [lat, lon, alt, pitch, roll, heading, gear]

        Note: XPC uses pitch, roll order (different from our method signature)
        """
        if not self._client:
            return

        # Normalize heading to [0, 360]
        heading = heading % 360
        if heading < 0:
            heading += 360

        try:
            # XPC POSI format: [lat, lon, alt, pitch, roll, heading, gear]
            posi = [lat, lon, alt, pitch, roll, heading, gear]
            self._client.sendPOSI(posi, 0)  # 0 = player aircraft
        except Exception as e:
            print(f"Failed to send position: {e}")

    def send_controls(self, aileron: float = -998, elevator: float = -998,
                      rudder: float = -998, throttle: float = -998,
                      gear: float = -998, flaps: float = -998) -> None:
        """
        Set control surfaces using XPC sendCTRL.

        XPC sendCTRL format:
        [latStick, lonStick, rudder, throttle, gear, flaps, speedbrake]

        Values are normalized:
        - latStick (aileron): [-1, 1]
        - lonStick (elevator): [-1, 1]
        - rudder: [-1, 1]
        - throttle: [0, 1]
        - gear: 0=up, 1=down
        - flaps: [0, 1]
        """
        if not self._client:
            return

        try:
            # Build control array
            ctrl = [aileron, elevator, rudder, throttle, gear, flaps]
            self._client.sendCTRL(ctrl, 0)  # 0 = player aircraft
        except Exception as e:
            print(f"Failed to send controls: {e}")

    def send_dataref(self, dref: str, value: float) -> None:
        """Set a dataref using XPC sendDREF."""
        if not self._client:
            return

        try:
            self._client.sendDREF(dref, value)
        except Exception as e:
            print(f"Failed to send DREF {dref}: {e}")

    def send_datarefs(self, drefs: Dict[str, float]) -> None:
        """Set multiple datarefs using XPC sendDREFs."""
        if not self._client:
            return

        try:
            dref_list = list(drefs.keys())
            value_list = list(drefs.values())
            self._client.sendDREFs(dref_list, value_list)
        except Exception as e:
            print(f"Failed to send DREFs: {e}")

    def get_position(self) -> Optional[AircraftState]:
        """Get current aircraft position using XPC getPOSI."""
        if not self._client:
            return None

        try:
            # XPC getPOSI returns: (lat, lon, alt, pitch, roll, heading, gear)
            posi = self._client.getPOSI(0)  # 0 = player aircraft
            return AircraftState(
                latitude=posi[0],
                longitude=posi[1],
                altitude=posi[2],
                pitch=posi[3],
                roll=posi[4],
                heading=posi[5],
                gear=posi[6] if len(posi) > 6 else 1.0
            )
        except Exception as e:
            print(f"Failed to get position: {e}")
            return None

    def get_dataref(self, dref: str) -> Optional[float]:
        """Get a dataref value using XPC getDREF."""
        if not self._client:
            return None

        try:
            result = self._client.getDREF(dref)
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Failed to get DREF {dref}: {e}")
            return None

    def pause_sim(self, pause: bool) -> None:
        """Pause or unpause X-Plane simulation."""
        if not self._client:
            return

        try:
            self._client.pauseSim(pause)
        except Exception as e:
            print(f"Failed to pause sim: {e}")

    def send_text(self, message: str, x: int = -1, y: int = -1) -> None:
        """Display text message on X-Plane screen."""
        if not self._client:
            return

        try:
            self._client.sendTEXT(message, x, y)
        except Exception as e:
            print(f"Failed to send text: {e}")

    def clear_text(self) -> None:
        """Clear any displayed text."""
        if not self._client:
            return

        try:
            self._client.sendTEXT("")
        except Exception:
            pass
