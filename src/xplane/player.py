"""
X-Plane Flight Data Player.

Plays back flight simulation data in X-Plane, controlling aircraft position,
attitude, control surfaces, and propulsion state in real-time.
"""

import math
import time
import threading
from enum import Enum, auto
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Union, List
import yaml
import numpy as np

from .backends.base import XPlaneBackend
from .backends.xpc_backend import XPCBackend
from .backends.udp_backend import NativeUDPBackend
from .coordinate_utils import NEDConverter, euler_to_xplane, radians_to_normalized

# Import flight data loader - handle both module and direct execution
try:
    from ..flight_data import FlightData
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from flight_data import FlightData


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


# =============================================================================
# Dataref Mapping Configuration Classes
# =============================================================================

@dataclass
class ControlMapping:
    """Configuration for a single control surface dataref."""
    target_dref: str
    source_unit: str = "radians"
    target_unit: str = "degrees"
    max_deflection: float = 30.0
    inverted: bool = False


@dataclass
class PropulsionMapping:
    """Configuration for a propulsion-related dataref."""
    target_dref: str
    max_value: float = 10000.0
    scale: float = 0.01
    source_unit: str = "radians"
    target_unit: str = "degrees"
    index: Optional[int] = None  # For array datarefs like acf_vertcant[n]
    invert_convention: bool = False  # For tilt: transform = 90 - value
    offset: float = 0.0  # Fixed offset to add (in target units, e.g., degrees)
    inverted: bool = False  # Negate value if True (multiply by -1)


@dataclass
class DatarefConfig:
    """
    Complete configuration for X-Plane dataref mappings.

    Loaded from config/xplane.yaml's variable_mapping section.
    Allows users to customize which datarefs are used without code changes.
    """
    # Control surface mappings
    aileron: Optional[ControlMapping] = None
    elevator: Optional[ControlMapping] = None
    rudder: Optional[ControlMapping] = None

    # Propulsion mappings
    rpm_left: Optional[PropulsionMapping] = None
    rpm_right: Optional[PropulsionMapping] = None
    tilt_left: Optional[PropulsionMapping] = None
    tilt_right: Optional[PropulsionMapping] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatarefConfig':
        """Create DatarefConfig from a dictionary (loaded from YAML)."""
        config = cls()

        # Parse control surface mappings
        controls = data.get('controls', {})
        if 'aileron' in controls:
            config.aileron = ControlMapping(**controls['aileron'])
        if 'elevator' in controls:
            config.elevator = ControlMapping(**controls['elevator'])
        if 'rudder' in controls:
            config.rudder = ControlMapping(**controls['rudder'])

        # Parse propulsion mappings
        propulsion = data.get('propulsion', {})
        if 'rpm_left' in propulsion:
            config.rpm_left = PropulsionMapping(**propulsion['rpm_left'])
        if 'rpm_right' in propulsion:
            config.rpm_right = PropulsionMapping(**propulsion['rpm_right'])
        if 'tilt_left' in propulsion:
            config.tilt_left = PropulsionMapping(**propulsion['tilt_left'])
        if 'tilt_right' in propulsion:
            config.tilt_right = PropulsionMapping(**propulsion['tilt_right'])

        return config

    @classmethod
    def defaults(cls) -> 'DatarefConfig':
        """Return default dataref configuration."""
        return cls(
            aileron=ControlMapping(
                target_dref="sim/flightmodel/controls/wing1l_ail1def",
                max_deflection=30.0
            ),
            elevator=ControlMapping(
                target_dref="sim/flightmodel/controls/hstab1_elv1def",
                max_deflection=30.0
            ),
            rudder=ControlMapping(
                target_dref="sim/flightmodel/controls/vstab1_rud1def",
                max_deflection=30.0
            ),
            rpm_left=PropulsionMapping(
                target_dref="sim/flightmodel/engine/ENGN_N1_[0]",
                max_value=10000.0,
                scale=0.01
            ),
            rpm_right=PropulsionMapping(
                target_dref="sim/flightmodel/engine/ENGN_N1_[1]",
                max_value=10000.0,
                scale=0.01
            ),
            tilt_left=PropulsionMapping(
                target_dref="sim/aircraft/prop/acf_vertcant",
                source_unit="radians",
                target_unit="degrees",
                index=1,  # X-Plane uses index 1 for left motor
                invert_convention=False,
                offset=-90.0  # -90° = forward flight
            ),
            tilt_right=PropulsionMapping(
                target_dref="sim/aircraft/prop/acf_vertcant",
                source_unit="radians",
                target_unit="degrees",
                index=0,  # X-Plane uses index 0 for right motor
                invert_convention=False,
                offset=-90.0  # -90° = forward flight
            ),
        )


@dataclass
class PlaybackConfig:
    """Configuration for flight data playback."""
    # Connection settings
    host: str = "localhost"
    xpc_port: int = 49009
    native_port: int = 49000
    backend: str = "auto"  # "auto", "xpc", "native"
    timeout: float = 1000  # milliseconds

    # Playback settings
    default_speed: float = 1.0
    loop: bool = False
    show_status: bool = True

    # Origin settings
    auto_origin: bool = True
    origin_lat: float = 0.0
    origin_lon: float = 0.0
    origin_alt: float = 0.0

    # Control surface settings (max deflection for normalization)
    # Note: These are DEPRECATED - use dataref_config instead
    aileron_max_deg: float = 30.0
    elevator_max_deg: float = 30.0
    rudder_max_deg: float = 30.0

    # Features to send
    send_position: bool = True
    send_attitude: bool = True
    send_controls: bool = True
    send_propulsion: bool = True

    # Dataref mapping configuration (loaded from variable_mapping in YAML)
    dataref_config: Optional[DatarefConfig] = None

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'PlaybackConfig':
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)

        config = cls()

        # Connection settings
        conn = data.get('connection', {})
        config.host = conn.get('host', config.host)
        config.xpc_port = conn.get('port', config.xpc_port)
        config.native_port = conn.get('native_port', config.native_port)
        config.backend = conn.get('backend', config.backend)
        config.timeout = conn.get('timeout', config.timeout)

        # Playback settings
        play = data.get('playback', {})
        config.default_speed = play.get('default_speed', config.default_speed)
        config.loop = play.get('loop', config.loop)
        config.show_status = play.get('show_status', config.show_status)

        # Origin settings
        origin = data.get('origin', {})
        config.auto_origin = origin.get('auto_detect', config.auto_origin)
        config.origin_lat = origin.get('latitude', config.origin_lat)
        config.origin_lon = origin.get('longitude', config.origin_lon)
        config.origin_alt = origin.get('altitude', config.origin_alt)

        # Control settings (legacy - for backward compatibility)
        controls = data.get('controls', {})
        config.aileron_max_deg = controls.get('aileron_max_deg', config.aileron_max_deg)
        config.elevator_max_deg = controls.get('elevator_max_deg', config.elevator_max_deg)
        config.rudder_max_deg = controls.get('rudder_max_deg', config.rudder_max_deg)

        # Features
        features = data.get('features', {})
        config.send_position = features.get('position', config.send_position)
        config.send_attitude = features.get('attitude', config.send_attitude)
        config.send_controls = features.get('controls', config.send_controls)
        config.send_propulsion = features.get('propulsion', config.send_propulsion)

        # Load variable mapping configuration (the key feature for customization)
        variable_mapping = data.get('variable_mapping', {})
        if variable_mapping:
            config.dataref_config = DatarefConfig.from_dict(variable_mapping)
        else:
            # Use defaults if no mapping provided
            config.dataref_config = DatarefConfig.defaults()

        return config

    def get_dataref_config(self) -> DatarefConfig:
        """Get dataref configuration, using defaults if not set."""
        if self.dataref_config is None:
            return DatarefConfig.defaults()
        return self.dataref_config


class XPlanePlayer:
    """
    Flight data player for X-Plane.

    Plays back .mat file flight data in X-Plane, showing aircraft
    position, attitude, control surfaces, and propulsion state.

    Example:
        player = XPlanePlayer()
        player.load("session_001/data.mat")
        player.play(speed=1.0)
    """

    def __init__(self, config: Optional[PlaybackConfig] = None,
                 config_path: Optional[Union[str, Path]] = None,
                 verbose: bool = False,
                 debug: bool = False):
        """
        Initialize the X-Plane player.

        Args:
            config: PlaybackConfig object
            config_path: Path to YAML configuration file
            verbose: Enable verbose debug logging
            debug: Enable detailed debug mode with dataref verification
        """
        if config_path:
            self.config = PlaybackConfig.from_yaml(config_path)
        elif config:
            self.config = config
        else:
            self.config = PlaybackConfig()

        self._backend: Optional[XPlaneBackend] = None
        self._flight_data: Optional[FlightData] = None
        self._converter: Optional[NEDConverter] = None
        self._verbose = verbose
        self._debug = debug  # Detailed debug mode
        self._debug_interval = 30  # Debug output every N frames
        self._frame_log_interval = 100  # Log every N frames when verbose

        self._state = PlaybackState.STOPPED
        self._speed: float = self.config.default_speed
        self._current_frame: int = 0
        self._start_time: float = 0
        self._pause_time: float = 0

        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()

        # Callbacks
        self._on_frame: Optional[Callable[[int, float], None]] = None
        self._on_complete: Optional[Callable[[], None]] = None

        # Prop rotation tracking (cumulative angles for smooth animation)
        # Required because physics override disables automatic prop animation
        self._prop_angles: List[float] = [0.0] * 8  # Track per-engine

    @property
    def state(self) -> PlaybackState:
        """Current playback state."""
        return self._state

    @property
    def is_playing(self) -> bool:
        """True if currently playing."""
        return self._state == PlaybackState.PLAYING

    @property
    def is_paused(self) -> bool:
        """True if paused."""
        return self._state == PlaybackState.PAUSED

    @property
    def current_time(self) -> float:
        """Current playback time in seconds."""
        if self._flight_data is None:
            return 0.0
        return self._flight_data.time[self._current_frame]

    @property
    def total_time(self) -> float:
        """Total flight duration in seconds."""
        if self._flight_data is None:
            return 0.0
        return self._flight_data.time[-1] - self._flight_data.time[0]

    @property
    def progress(self) -> float:
        """Playback progress as fraction [0, 1]."""
        if self._flight_data is None:
            return 0.0
        return self._current_frame / (len(self._flight_data.time) - 1)

    def connect(self) -> bool:
        """
        Connect to X-Plane using configured backend.

        Returns:
            True if connection successful
        """
        # Select backend
        if self.config.backend == "xpc":
            self._backend = XPCBackend()
            port = self.config.xpc_port
        elif self.config.backend == "native":
            self._backend = NativeUDPBackend()
            port = self.config.native_port
        else:  # auto
            # Try XPC first, fall back to native
            if XPCBackend.is_available():
                self._backend = XPCBackend()
                port = self.config.xpc_port
                if self._backend.connect(self.config.host, port, self.config.timeout):
                    print(f"Connected via XPlaneConnect to {self.config.host}:{port}")
                    return True

            # Fall back to native UDP
            self._backend = NativeUDPBackend()
            port = self.config.native_port

        success = self._backend.connect(self.config.host, port, self.config.timeout)
        if success:
            backend_name = "XPC" if isinstance(self._backend, XPCBackend) else "Native UDP"
            print(f"Connected via {backend_name} to {self.config.host}:{port}")
        else:
            print(f"Failed to connect to X-Plane at {self.config.host}:{port}")

        return success

    def disconnect(self) -> None:
        """Disconnect from X-Plane."""
        if self._backend:
            self._backend.disconnect()
            self._backend = None

    def _debug_read_prop_state(self) -> Dict[str, Any]:
        """
        Read current prop/engine state from X-Plane for debugging.

        Returns dict with current values of key datarefs.
        """
        if not self._backend:
            return {}

        state = {}
        # Array datarefs - read full array to see engine 0 and 1
        drefs_to_read = [
            ("sim/flightmodel2/engines/prop_disc/override", True),  # Array - prop override status
            ("sim/flightmodel2/engines/prop_disc/prop_is_disc", True),  # Array - disc mode
            ("sim/flightmodel2/engines/prop_rotation_angle_deg", True),  # Array
            ("sim/flightmodel/engine/ENGN_running", True),  # Array
            ("sim/flightmodel/engine/ENGN_thro", True),  # Array
            ("sim/flightmodel/engine/ENGN_N1_", True),  # Array
            ("sim/aircraft/prop/acf_vertcant", True),  # Array
            ("sim/flightmodel/engine/POINT_tacrad", True),  # Prop rotation speed array
        ]

        for dref, as_array in drefs_to_read:
            try:
                # Try to get with as_array parameter if backend supports it
                if hasattr(self._backend, 'get_dataref'):
                    import inspect
                    sig = inspect.signature(self._backend.get_dataref)
                    if 'as_array' in sig.parameters:
                        val = self._backend.get_dataref(dref, as_array=as_array)
                    else:
                        val = self._backend.get_dataref(dref)
                else:
                    val = self._backend.get_dataref(dref)

                # Format array values nicely (show first 4 elements)
                if isinstance(val, (list, tuple)) and len(val) > 4:
                    val = f"[{val[0]:.2f}, {val[1]:.2f}, {val[2]:.2f}, {val[3]:.2f}, ...]"
                elif isinstance(val, (list, tuple)):
                    val = [round(v, 2) for v in val]

                state[dref] = val
            except Exception as e:
                state[dref] = f"ERROR: {e}"

        return state

    def _debug_print_prop_state(self, frame_idx: int, sent_drefs: Dict[str, float]) -> None:
        """Print detailed debug info about prop state."""
        print(f"\n{'='*60}")
        print(f"[DEBUG] Frame {frame_idx} - Prop/Engine State")
        print(f"{'='*60}")

        print("\n--- SENT to X-Plane ---")
        for dref, val in sorted(sent_drefs.items()):
            print(f"  {dref} = {val:.4f}")

        print("\n--- READ BACK from X-Plane ---")
        state = self._debug_read_prop_state()
        for dref, val in state.items():
            if val is not None:
                print(f"  {dref} = {val}")
            else:
                print(f"  {dref} = None (not readable or not set)")

        print(f"{'='*60}\n")

    def load(self, source: Union[str, Path, FlightData]) -> bool:
        """
        Load flight data for playback.

        Args:
            source: Path to .mat file or FlightData object

        Returns:
            True if loaded successfully
        """
        try:
            if isinstance(source, FlightData):
                self._flight_data = source
            else:
                self._flight_data = FlightData.from_mat_file(str(source))

            # Reset playback position
            self._current_frame = 0

            print(f"Loaded flight data: {len(self._flight_data.time)} frames, "
                  f"{self.total_time:.1f}s duration")
            return True

        except Exception as e:
            print(f"Failed to load flight data: {e}")
            return False

    def set_origin(self, lat: float, lon: float, alt: float = 0.0) -> None:
        """
        Set the geodetic origin for NED to lat/lon conversion.

        Args:
            lat: Origin latitude in degrees
            lon: Origin longitude in degrees
            alt: Origin altitude in meters MSL
        """
        self._converter = NEDConverter(lat, lon, alt)
        self.config.auto_origin = False
        print(f"Origin set to: {lat:.6f}, {lon:.6f}, {alt:.1f}m")

    def auto_detect_origin(self) -> bool:
        """
        Use current X-Plane aircraft position as origin.

        Returns:
            True if origin was set successfully
        """
        if not self._backend or not self._backend.connected:
            if not self.connect():
                return False

        state = self._backend.get_position()
        if state:
            self.set_origin(state.latitude, state.longitude, state.altitude)
            return True

        print("Failed to get aircraft position from X-Plane")
        return False

    def play(self, speed: Optional[float] = None, start_time: float = 0,
             end_time: Optional[float] = None) -> bool:
        """
        Start playback.

        Args:
            speed: Playback speed factor (1.0 = real-time)
            start_time: Start time in seconds
            end_time: End time in seconds (None = end of recording)

        Returns:
            True if playback started successfully
        """
        if self._flight_data is None:
            print("No flight data loaded")
            return False

        if self._state == PlaybackState.PLAYING:
            print("Already playing")
            return False

        # Connect if needed
        if not self._backend or not self._backend.connected:
            if not self.connect():
                return False

        # Set up origin if needed
        if self._converter is None:
            if self.config.auto_origin:
                if not self.auto_detect_origin():
                    print("Warning: Using default origin (0, 0, 0)")
                    self._converter = NEDConverter(0, 0, 0)
            else:
                self._converter = NEDConverter(
                    self.config.origin_lat,
                    self.config.origin_lon,
                    self.config.origin_alt
                )

        # Set speed
        if speed is not None:
            self._speed = speed

        # Find start frame
        self._current_frame = 0
        if start_time > 0:
            time_array = self._flight_data.time
            self._current_frame = int(np.searchsorted(time_array, start_time))

        # Calculate end frame
        end_frame = len(self._flight_data.time)
        if end_time is not None:
            end_frame = int(np.searchsorted(self._flight_data.time, end_time))

        # Enable physics override to prevent X-Plane fighting our commands
        if self._backend:
            self._backend.override_physics(True)

        # Debug: Print X-Plane aircraft configuration at start
        if self._debug and self._backend:
            print("\n" + "="*60)
            print("[DEBUG] X-Plane Aircraft Configuration at Playback Start")
            print("="*60)
            # (dref, description, is_array)
            acf_drefs = [
                ("sim/aircraft/view/acf_tailnum", "Tail Number", False),
                ("sim/aircraft/engine/acf_num_engines", "Number of Engines", False),
                ("sim/aircraft/prop/acf_num_blades", "Blades per Prop", True),
                ("sim/aircraft/prop/acf_vertcant", "Prop Vertical Cant [0,1]", True),
                ("sim/flightmodel2/engines/prop_rotation_angle_deg", "Prop Rotation [0,1]", True),
                ("sim/flightmodel/engine/ENGN_running", "Engine Running [0,1]", True),
                ("sim/flightmodel/engine/ENGN_thro", "Throttle [0,1]", True),
                ("sim/flightmodel/engine/ENGN_N1_", "Engine N1 [0,1]", True),
            ]
            for dref, desc, is_array in acf_drefs:
                try:
                    import inspect
                    sig = inspect.signature(self._backend.get_dataref)
                    if 'as_array' in sig.parameters:
                        val = self._backend.get_dataref(dref, as_array=is_array)
                    else:
                        val = self._backend.get_dataref(dref)
                    # Format array to show first 2 elements
                    if isinstance(val, (list, tuple)) and len(val) > 2:
                        val = f"[{val[0]:.2f}, {val[1]:.2f}, ...]"
                    elif isinstance(val, (list, tuple)):
                        val = [round(v, 2) for v in val]
                    print(f"  {desc}: {val}")
                except Exception as e:
                    print(f"  {desc}: ERROR - {e}")
            print("="*60 + "\n")

        # Reset prop rotation angles for smooth animation from start
        self._prop_angles = [0.0] * 8

        # Start playback thread
        self._stop_event.clear()
        self._pause_event.clear()
        self._state = PlaybackState.PLAYING

        self._playback_thread = threading.Thread(
            target=self._playback_loop,
            args=(end_frame,),
            daemon=True
        )
        self._playback_thread.start()

        return True

    def pause(self) -> None:
        """Pause playback."""
        if self._state == PlaybackState.PLAYING:
            self._pause_event.set()
            self._pause_time = time.perf_counter()
            self._state = PlaybackState.PAUSED

    def resume(self) -> None:
        """Resume paused playback."""
        if self._state == PlaybackState.PAUSED:
            self._pause_event.clear()
            self._state = PlaybackState.PLAYING

    def stop(self) -> None:
        """Stop playback."""
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
        self._state = PlaybackState.STOPPED
        self._current_frame = 0

        # Release physics override
        if self._backend and self._backend.connected:
            self._backend.override_physics(False)

    def seek(self, time_seconds: float) -> None:
        """
        Seek to a specific time.

        Args:
            time_seconds: Target time in seconds
        """
        if self._flight_data is None:
            return

        time_array = self._flight_data.time
        self._current_frame = int(np.searchsorted(time_array, time_seconds))
        self._current_frame = max(0, min(self._current_frame, len(time_array) - 1))

    def set_speed(self, speed: float) -> None:
        """
        Set playback speed.

        Args:
            speed: Speed factor (1.0 = real-time, 2.0 = double speed)
        """
        self._speed = max(0.1, min(10.0, speed))

    def _playback_loop(self, end_frame: int) -> None:
        """Main playback loop (runs in separate thread)."""
        data = self._flight_data
        sample_rate = data.sample_rate
        base_dt = 1.0 / sample_rate

        while self._current_frame < end_frame and not self._stop_event.is_set():
            # Handle pause
            while self._pause_event.is_set() and not self._stop_event.is_set():
                time.sleep(0.05)

            if self._stop_event.is_set():
                break

            frame_start = time.perf_counter()
            i = self._current_frame

            # Send frame data to X-Plane
            self._send_frame(i)

            # Callback
            if self._on_frame:
                self._on_frame(i, data.time[i])

            # Calculate sleep time
            target_dt = base_dt / self._speed
            elapsed = time.perf_counter() - frame_start
            sleep_time = max(0, target_dt - elapsed)
            time.sleep(sleep_time)

            self._current_frame += 1

        # Handle loop
        if self.config.loop and not self._stop_event.is_set():
            self._current_frame = 0
            self._playback_loop(end_frame)
        else:
            self._state = PlaybackState.STOPPED
            if self._on_complete:
                self._on_complete()

    def _send_frame(self, frame_idx: int) -> None:
        """Send a single frame of data to X-Plane."""
        data = self._flight_data
        backend = self._backend

        if not backend or not backend.connected:
            return

        # Get dataref configuration
        dref_cfg = self.config.get_dataref_config()

        # Verbose debug logging
        if self._verbose and frame_idx % self._frame_log_interval == 0:
            print(f"\n[Frame {frame_idx}] Debug data:")
            if len(data.theta_Cl) > 0:
                print(f"  Tilt L: {math.degrees(data.theta_Cl[frame_idx]):.2f}°")
            else:
                print(f"  Tilt L: EMPTY ARRAY")
            if len(data.theta_Cr) > 0:
                print(f"  Tilt R: {math.degrees(data.theta_Cr[frame_idx]):.2f}°")
            else:
                print(f"  Tilt R: EMPTY ARRAY")
            if len(data.RPM_Cl) > 0:
                print(f"  RPM L: {data.RPM_Cl[frame_idx]:.0f}")
            else:
                print(f"  RPM L: EMPTY ARRAY")
            if len(data.RPM_Cr) > 0:
                print(f"  RPM R: {data.RPM_Cr[frame_idx]:.0f}")
            else:
                print(f"  RPM R: EMPTY ARRAY")
            if len(data.delta_e) > 0:
                print(f"  Elevator: {math.degrees(data.delta_e[frame_idx]):.2f}°")
            else:
                print(f"  Elevator: EMPTY ARRAY")

        # Position and attitude
        if self.config.send_position or self.config.send_attitude:
            # Convert NED to lat/lon/alt
            N = data.N[frame_idx]
            E = data.E[frame_idx]
            D = data.D[frame_idx]
            geo = self._converter.ned_to_geo(N, E, D)

            # Convert attitude (radians to degrees)
            roll, pitch, heading = euler_to_xplane(
                data.phi[frame_idx],
                data.theta[frame_idx],
                data.psi[frame_idx]
            )

            backend.send_position(
                geo.latitude, geo.longitude, geo.altitude,
                roll, pitch, heading
            )

        # Control surfaces - using configurable datarefs
        if self.config.send_controls:
            drefs = {}

            # Enable control surface override to prevent physics from fighting our values
            drefs["sim/operation/override/override_control_surfaces"] = 1

            # Aileron - use config for max deflection and target dref
            if dref_cfg.aileron and len(data.delta_a) > 0:
                cfg = dref_cfg.aileron
                max_deg = cfg.max_deflection
                value_deg = math.degrees(data.delta_a[frame_idx])
                if cfg.inverted:
                    value_deg = -value_deg
                drefs[cfg.target_dref] = value_deg
                # Also set right aileron (opposite direction)
                right_dref = cfg.target_dref.replace("wing1l", "wing1r")
                if right_dref != cfg.target_dref:
                    drefs[right_dref] = -value_deg

            # Elevator - use config for max deflection and target dref
            if dref_cfg.elevator and len(data.delta_e) > 0:
                cfg = dref_cfg.elevator
                value_deg = math.degrees(data.delta_e[frame_idx])
                if cfg.inverted:
                    value_deg = -value_deg
                drefs[cfg.target_dref] = value_deg
                # Set both elevator surfaces
                second_dref = cfg.target_dref.replace("hstab1", "hstab2")
                if second_dref != cfg.target_dref:
                    drefs[second_dref] = value_deg

            # Rudder - use config for max deflection and target dref
            if dref_cfg.rudder and len(data.delta_r) > 0:
                cfg = dref_cfg.rudder
                value_deg = math.degrees(data.delta_r[frame_idx])
                if cfg.inverted:
                    value_deg = -value_deg
                drefs[cfg.target_dref] = value_deg

            if drefs:
                backend.send_datarefs(drefs)

        # Propulsion - using configurable datarefs
        if self.config.send_propulsion:
            drefs = {}
            sample_rate = data.sample_rate

            # Debug: Print propulsion status on first frame (only if verbose)
            if self._verbose and frame_idx == 0:
                print(f"\n[Propulsion Config]")
                print(f"  rpm_left: {dref_cfg.rpm_left}")
                print(f"  rpm_right: {dref_cfg.rpm_right}")
                print(f"  tilt_left: {dref_cfg.tilt_left}")
                print(f"  tilt_right: {dref_cfg.tilt_right}")
                print(f"  RPM_Cl samples: {len(data.RPM_Cl) if data.RPM_Cl is not None else 'None'}")
                print(f"  RPM_Cr samples: {len(data.RPM_Cr) if data.RPM_Cr is not None else 'None'}")
                print(f"  theta_Cl samples: {len(data.theta_Cl) if data.theta_Cl is not None else 'None'}")
                print(f"  theta_Cr samples: {len(data.theta_Cr) if data.theta_Cr is not None else 'None'}")

            # Note: Engine indices are SWAPPED in X-Plane (0=right, 1=left)
            # Left RPM -> X-Plane engine index 1
            if dref_cfg.rpm_left and len(data.RPM_Cl) > 0:
                cfg = dref_cfg.rpm_left
                rpm_value = data.RPM_Cl[frame_idx]
                xp_idx = 1  # Left motor = X-Plane index 1

                # Set throttle (0-1)
                throttle = min(1.0, rpm_value / cfg.max_value)
                drefs[f"sim/flightmodel/engine/ENGN_thro[{xp_idx}]"] = throttle
                # Mark engine as running
                drefs[f"sim/flightmodel/engine/ENGN_running[{xp_idx}]"] = 1
                # Set N1 percentage (engine speed indicator)
                n1_pct = (rpm_value / cfg.max_value) * 100
                drefs[f"sim/flightmodel/engine/ENGN_N1_[{xp_idx}]"] = n1_pct

                # Enable prop disc override - REQUIRED for manual prop animation!
                # Without this, X-Plane manages the prop disc and ignores our angle writes
                drefs[f"sim/flightmodel2/engines/prop_disc/override[{xp_idx}]"] = 1
                # Force BLADE mode (not disc) - T-Tail uses PlaneMaker blades, not OBJ disc
                drefs[f"sim/flightmodel2/engines/prop_disc/prop_is_disc[{xp_idx}]"] = 0

                # Manually set prop rotation angle - REQUIRED when physics are overridden
                # X-Plane cannot auto-animate props when VEHX/sendPOSI disables physics.
                # Use wall-clock time for smooth, continuous rotation (avoids sampling aliasing)
                # At 6000 RPM: 100 rev/sec, frame-based calc gives 3600°/frame = 0 after mod!
                degrees_per_second = rpm_value * 6.0  # RPM * 360 / 60
                prop_angle = (time.time() * degrees_per_second) % 360.0
                drefs[f"sim/flightmodel2/engines/prop_rotation_angle_deg[{xp_idx}]"] = prop_angle

            # Right RPM -> X-Plane engine index 0
            if dref_cfg.rpm_right and len(data.RPM_Cr) > 0:
                cfg = dref_cfg.rpm_right
                rpm_value = data.RPM_Cr[frame_idx]
                xp_idx = 0  # Right motor = X-Plane index 0

                # Set throttle (0-1)
                throttle = min(1.0, rpm_value / cfg.max_value)
                drefs[f"sim/flightmodel/engine/ENGN_thro[{xp_idx}]"] = throttle
                # Mark engine as running
                drefs[f"sim/flightmodel/engine/ENGN_running[{xp_idx}]"] = 1
                # Set N1 percentage (engine speed indicator)
                n1_pct = (rpm_value / cfg.max_value) * 100
                drefs[f"sim/flightmodel/engine/ENGN_N1_[{xp_idx}]"] = n1_pct

                # Enable prop disc override - REQUIRED for manual prop animation!
                drefs[f"sim/flightmodel2/engines/prop_disc/override[{xp_idx}]"] = 1
                # Force BLADE mode (not disc) - T-Tail uses PlaneMaker blades, not OBJ disc
                drefs[f"sim/flightmodel2/engines/prop_disc/prop_is_disc[{xp_idx}]"] = 0

                # Manually set prop rotation angle - REQUIRED when physics are overridden
                degrees_per_second = rpm_value * 6.0
                prop_angle = (time.time() * degrees_per_second) % 360.0
                drefs[f"sim/flightmodel2/engines/prop_rotation_angle_deg[{xp_idx}]"] = prop_angle

            # Left tilt angle - use config for target dref and unit conversion
            if dref_cfg.tilt_left and len(data.theta_Cl) > 0:
                cfg = dref_cfg.tilt_left
                value = data.theta_Cl[frame_idx]
                if cfg.source_unit == "radians" and cfg.target_unit == "degrees":
                    value = math.degrees(value)
                # Apply convention inversion if needed (sim: 0=hover, xplane: 0=forward)
                if cfg.invert_convention:
                    value = 90.0 - value
                # Apply inverted (negate) if configured
                if cfg.inverted:
                    value = -value
                # Apply offset (e.g., 180° to flip direction)
                value = value + cfg.offset
                # Handle array dataref with index (e.g., acf_vertcant[0])
                target = cfg.target_dref
                if cfg.index is not None and '[' not in target:
                    target = f"{target}[{cfg.index}]"
                drefs[target] = value
                # Debug: Print tilt value on first frame (only if verbose)
                if self._verbose and frame_idx == 0:
                    print(f"  Tilt LEFT: raw={math.degrees(data.theta_Cl[0]):.1f}°, offset={cfg.offset}, final={value:.1f}° -> {target}")

            # Right tilt angle - use config for target dref and unit conversion
            if dref_cfg.tilt_right and len(data.theta_Cr) > 0:
                cfg = dref_cfg.tilt_right
                value = data.theta_Cr[frame_idx]
                if cfg.source_unit == "radians" and cfg.target_unit == "degrees":
                    value = math.degrees(value)
                # Apply convention inversion if needed (sim: 0=hover, xplane: 0=forward)
                if cfg.invert_convention:
                    value = 90.0 - value
                # Apply inverted (negate) if configured
                if cfg.inverted:
                    value = -value
                # Apply offset (e.g., 180° to flip direction)
                value = value + cfg.offset
                # Handle array dataref with index (e.g., acf_vertcant[1])
                target = cfg.target_dref
                if cfg.index is not None and '[' not in target:
                    target = f"{target}[{cfg.index}]"
                drefs[target] = value
                # Debug: Print tilt value on first frame (only if verbose)
                if self._verbose and frame_idx == 0:
                    print(f"  Tilt RIGHT: raw={math.degrees(data.theta_Cr[0]):.1f}°, offset={cfg.offset}, final={value:.1f}° -> {target}")

            # Debug: Print all datarefs being sent on first frame (only if verbose)
            if self._verbose and frame_idx == 0 and drefs:
                print(f"\n[Sending {len(drefs)} propulsion datarefs]")
                for dref, val in drefs.items():
                    print(f"  {dref} = {val}")

            if drefs:
                backend.send_datarefs(drefs)

                # Enhanced debug: Read back values every N frames
                if self._debug and (frame_idx == 0 or frame_idx % self._debug_interval == 0):
                    self._debug_print_prop_state(frame_idx, drefs)

    def on_frame(self, callback: Callable[[int, float], None]) -> None:
        """
        Register callback for each frame.

        Args:
            callback: Function(frame_index, time_seconds)
        """
        self._on_frame = callback

    def on_complete(self, callback: Callable[[], None]) -> None:
        """
        Register callback for playback completion.

        Args:
            callback: Function to call when playback completes
        """
        self._on_complete = callback

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.disconnect()
        return False


def quick_play(mat_file: Union[str, Path], speed: float = 1.0,
               host: str = "localhost", backend: str = "auto") -> None:
    """
    Quick playback utility function.

    Args:
        mat_file: Path to .mat file
        speed: Playback speed
        host: X-Plane host
        backend: Backend to use ("auto", "xpc", "native")
    """
    config = PlaybackConfig(host=host, backend=backend)

    with XPlanePlayer(config) as player:
        if player.load(mat_file):
            player.play(speed=speed)

            # Wait for completion
            while player.is_playing or player.is_paused:
                time.sleep(0.1)
