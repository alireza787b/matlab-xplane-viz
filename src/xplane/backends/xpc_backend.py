"""
NASA XPlaneConnect backend.

This backend uses the NASA XPlaneConnect library which provides a
high-level API for X-Plane communication. Requires the XPC plugin
to be installed in X-Plane.

Plugin download: https://github.com/nasa/XPlaneConnect/releases
"""

from typing import Dict, List, Optional, Tuple, Union
import re
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

    # Regex to parse array subscript notation: "dref[n]" -> ("dref", n)
    _ARRAY_SUBSCRIPT_RE = re.compile(r'^(.+)\[(\d+)\]$')

    def _parse_array_subscript(self, dref: str) -> Tuple[str, Optional[int]]:
        """
        Parse a dataref name for array subscript notation.

        Args:
            dref: Dataref name, possibly with subscript like "dref[0]"

        Returns:
            Tuple of (base_name, index) where index is None if no subscript
        """
        match = self._ARRAY_SUBSCRIPT_RE.match(dref)
        if match:
            return match.group(1), int(match.group(2))
        return dref, None

    def send_dataref(self, dref: str, value: float) -> None:
        """Set a dataref using XPC sendDREF."""
        if not self._client:
            return

        try:
            self._client.sendDREF(dref, value)
        except Exception as e:
            print(f"Failed to send DREF {dref}: {e}")

    def send_array_dataref(self, dref: str, values: List[float]) -> None:
        """
        Set an array dataref with a list of values.

        Args:
            dref: Base dataref name (without subscript)
            values: List of values to set for each array index
        """
        if not self._client:
            return

        try:
            self._client.sendDREF(dref, values)
        except Exception as e:
            print(f"Failed to send array DREF {dref}: {e}")

    def send_datarefs(self, drefs: Dict[str, float]) -> None:
        """
        Set multiple datarefs, handling array subscripts properly.

        X-Plane's XPLMFindDataRef() does NOT accept subscript notation like
        "dataref[0]". For array datarefs, we must:
        1. Parse out the subscript from the name
        2. Group values by base dataref name
        3. Send array datarefs as arrays to the base name

        Args:
            drefs: Dict mapping dataref names (possibly with subscripts) to values
        """
        if not self._client:
            return

        # Separate scalar datarefs from array datarefs
        scalar_drefs: Dict[str, float] = {}
        array_drefs: Dict[str, Dict[int, float]] = {}  # base_name -> {index: value}

        for dref, value in drefs.items():
            base_name, index = self._parse_array_subscript(dref)
            if index is not None:
                # This is an array dataref with subscript
                if base_name not in array_drefs:
                    array_drefs[base_name] = {}
                array_drefs[base_name][index] = value
            else:
                # Scalar dataref
                scalar_drefs[dref] = value

        # Send scalar datarefs using sendDREFs (batch send)
        if scalar_drefs:
            try:
                dref_list = list(scalar_drefs.keys())
                value_list = list(scalar_drefs.values())
                self._client.sendDREFs(dref_list, value_list)
            except Exception as e:
                print(f"Failed to send scalar DREFs: {e}")

        # Send array datarefs one at a time with proper array values
        for base_name, index_values in array_drefs.items():
            try:
                # Determine array size (use max index + 1, minimum 8 for X-Plane engines)
                max_index = max(index_values.keys())
                array_size = max(8, max_index + 1)

                # Build array with zeros for unset indices
                values = [0.0] * array_size
                for idx, val in index_values.items():
                    values[idx] = val

                # Send the full array
                self._client.sendDREF(base_name, values)
            except Exception as e:
                print(f"Failed to send array DREF {base_name}: {e}")

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

    def get_dataref(self, dref: str, as_array: bool = False) -> Optional[Union[float, List[float]]]:
        """
        Get a dataref value using XPC getDREF.

        Args:
            dref: Dataref name
            as_array: If True, return full array; if False, return first element

        Returns:
            Single float value, list of floats, or None on error
        """
        if not self._client:
            return None

        try:
            result = self._client.getDREF(dref)
            if result and len(result) > 0:
                if as_array:
                    return list(result)
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
