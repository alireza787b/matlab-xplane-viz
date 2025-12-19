"""
Native X-Plane UDP backend using VEHX and DREF commands.

This backend communicates directly with X-Plane's built-in UDP interface,
requiring no plugin installation. Uses VEHX command which automatically
overrides X-Plane physics for position control.
"""

import socket
import struct
from typing import Dict, Optional

from .base import XPlaneBackend, AircraftState


class NativeUDPBackend(XPlaneBackend):
    """
    Native X-Plane UDP backend using VEHX/DREF commands.

    Advantages:
    - No plugin required
    - VEHX automatically overrides physics
    - Works with all X-Plane versions

    Note: VEHX sets position/attitude for the player aircraft (index 0)
    """

    def __init__(self):
        super().__init__()
        self._socket: Optional[socket.socket] = None
        self._timeout: float = 3.0

    def connect(self, host: str = "localhost", port: int = 49000,
                timeout: float = 3.0) -> bool:
        """
        Create UDP socket for X-Plane communication.

        Args:
            host: X-Plane host address
            port: X-Plane UDP port (default 49000)
            timeout: Socket timeout in seconds

        Returns:
            True (UDP is connectionless, always succeeds)
        """
        try:
            self._host = host
            self._port = port
            self._timeout = timeout

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(timeout)

            # Bind to any available port for receiving responses
            self._socket.bind(('', 0))

            self._connected = True
            return True
        except Exception as e:
            print(f"Failed to create UDP socket: {e}")
            return False

    def disconnect(self) -> None:
        """Close UDP socket."""
        if self._socket:
            try:
                # Release physics override before disconnecting
                self.override_physics(False)
            except:
                pass
            self._socket.close()
            self._socket = None
        self._connected = False

    def send_position(self, lat: float, lon: float, alt: float,
                      roll: float, pitch: float, heading: float,
                      gear: float = -998) -> None:
        """
        Set aircraft position using VEHX command.

        VEHX packet format (45 bytes):
        - Header: "VEHX" + null (5 bytes)
        - Aircraft index: int (4 bytes)
        - Latitude: double (8 bytes)
        - Longitude: double (8 bytes)
        - Elevation: double (8 bytes) - meters MSL
        - Heading: float (4 bytes) - degrees
        - Pitch: float (4 bytes) - degrees
        - Roll: float (4 bytes) - degrees

        Note: VEHX automatically overrides X-Plane physics.
        """
        if not self._socket:
            return

        # Normalize heading to [0, 360]
        heading = heading % 360
        if heading < 0:
            heading += 360

        # Pack VEHX message
        # Format: <4sxidddfff = little-endian, 4-char string, null, int, 3 doubles, 3 floats
        message = struct.pack(
            '<4sxidddfff',
            b'VEHX',           # Header
            0,                 # Aircraft index (0 = player aircraft)
            lat,               # Latitude (double)
            lon,               # Longitude (double)
            alt,               # Elevation MSL (double)
            heading,           # Heading (float)
            pitch,             # Pitch (float)
            roll               # Roll (float)
        )

        try:
            self._socket.sendto(message, (self._host, self._port))
        except Exception as e:
            print(f"Failed to send VEHX: {e}")

    def send_controls(self, aileron: float = -998, elevator: float = -998,
                      rudder: float = -998, throttle: float = -998,
                      gear: float = -998, flaps: float = -998) -> None:
        """
        Set control surfaces using DREF commands.

        For native UDP, we use direct dataref writes for control surfaces.
        Values should be in degrees for deflection datarefs.
        """
        drefs = {}

        # Control surface deflections (in degrees)
        if aileron != -998:
            # Set both left and right aileron
            drefs["sim/flightmodel/controls/wing1l_ail1def"] = aileron
            drefs["sim/flightmodel/controls/wing1r_ail1def"] = -aileron  # Opposite

        if elevator != -998:
            drefs["sim/flightmodel/controls/hstab1_elv1def"] = elevator
            drefs["sim/flightmodel/controls/hstab2_elv1def"] = elevator

        if rudder != -998:
            drefs["sim/flightmodel/controls/vstab1_rud1def"] = rudder

        if throttle != -998:
            # Set throttle for all engines
            for i in range(8):
                drefs[f"sim/flightmodel/engine/ENGN_thro[{i}]"] = throttle

        if gear != -998:
            drefs["sim/cockpit/switches/gear_handle_status"] = int(gear)

        if flaps != -998:
            drefs["sim/flightmodel/controls/flaprqst"] = flaps

        if drefs:
            self.send_datarefs(drefs)

    def send_dataref(self, dref: str, value: float) -> None:
        """
        Set a single dataref using DREF command.

        DREF packet format (509 bytes):
        - Header: "DREF" + null (5 bytes)
        - Value: float (4 bytes)
        - Dataref path: 500 bytes (null-padded)
        """
        if not self._socket:
            return

        # Ensure dataref is null-terminated and padded to 500 bytes
        dref_bytes = dref.encode('utf-8')
        if len(dref_bytes) > 499:
            dref_bytes = dref_bytes[:499]
        dref_padded = dref_bytes.ljust(500, b'\x00')

        # Pack DREF message
        message = struct.pack('<4sf500s', b'DREF', float(value), dref_padded)

        try:
            self._socket.sendto(message, (self._host, self._port))
        except Exception as e:
            print(f"Failed to send DREF {dref}: {e}")

    def send_datarefs(self, drefs: Dict[str, float]) -> None:
        """Send multiple datarefs as individual DREF commands."""
        for dref, value in drefs.items():
            self.send_dataref(dref, value)

    def get_position(self) -> Optional[AircraftState]:
        """
        Get current aircraft position using RREF subscription.

        Note: This requires setting up a RREF subscription first.
        For simplicity, we use specific datarefs.
        """
        if not self._socket:
            return None

        try:
            # Request position datarefs
            drefs = [
                "sim/flightmodel/position/latitude",
                "sim/flightmodel/position/longitude",
                "sim/flightmodel/position/elevation",
                "sim/flightmodel/position/phi",      # Roll
                "sim/flightmodel/position/theta",    # Pitch
                "sim/flightmodel/position/psi",      # Heading
            ]

            values = []
            for dref in drefs:
                val = self.get_dataref(dref)
                if val is None:
                    return None
                values.append(val)

            return AircraftState(
                latitude=values[0],
                longitude=values[1],
                altitude=values[2],
                roll=values[3],
                pitch=values[4],
                heading=values[5]
            )
        except Exception as e:
            print(f"Failed to get position: {e}")
            return None

    def get_dataref(self, dref: str) -> Optional[float]:
        """
        Request a dataref value using RREF.

        RREF request format:
        - Header: "RREF" + null (5 bytes)
        - Frequency: int (4 bytes) - Hz, use 1 for one-shot
        - Index: int (4 bytes) - arbitrary identifier
        - Dataref path: 400 bytes (null-padded)

        Response format:
        - Header: "RREF," (5 bytes)
        - For each requested dataref:
          - Index: int (4 bytes)
          - Value: float (4 bytes)
        """
        if not self._socket:
            return None

        try:
            # Prepare RREF request
            dref_bytes = dref.encode('utf-8')
            if len(dref_bytes) > 399:
                dref_bytes = dref_bytes[:399]
            dref_padded = dref_bytes.ljust(400, b'\x00')

            # Request at 1 Hz with index 0
            message = struct.pack('<4sxii400s', b'RREF', 1, 0, dref_padded)
            self._socket.sendto(message, (self._host, self._port))

            # Wait for response
            self._socket.settimeout(self._timeout)
            data, addr = self._socket.recvfrom(1024)

            # Parse response
            if data[:5] == b'RREF,':
                idx, value = struct.unpack('<if', data[5:13])
                # Cancel subscription
                cancel = struct.pack('<4sxii400s', b'RREF', 0, 0, dref_padded)
                self._socket.sendto(cancel, (self._host, self._port))
                return value

            return None
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Failed to get dataref {dref}: {e}")
            return None

    def send_vehs(self, lat: float, lon: float, alt: float,
                  roll: float, pitch: float, heading: float) -> None:
        """
        Send position using VEHS (single update, doesn't override physics).

        Use this for one-off position updates without taking over physics.
        """
        if not self._socket:
            return

        heading = heading % 360
        if heading < 0:
            heading += 360

        message = struct.pack(
            '<4sxidddfff',
            b'VEHS',
            0, lat, lon, alt, heading, pitch, roll
        )

        try:
            self._socket.sendto(message, (self._host, self._port))
        except Exception as e:
            print(f"Failed to send VEHS: {e}")
