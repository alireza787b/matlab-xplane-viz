#!/usr/bin/env python3
"""
X-Plane Flight Data Playback Script

Interactive script for playing back MATLAB .mat flight simulation data
in X-Plane flight simulator.

Usage:
    python scripts/xplane_playback.py path/to/data.mat [options]

Example:
    python scripts/xplane_playback.py sessions/session_001/data/flight_data.mat
    python scripts/xplane_playback.py sessions/session_001/data/flight_data.mat --speed 2.0
    python scripts/xplane_playback.py sessions/session_001/data/flight_data.mat --backend native
"""

import argparse
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.xplane import XPlanePlayer, PlaybackState
from src.xplane.player import PlaybackConfig


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS.s"""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


def print_status(player: XPlanePlayer, clear: bool = True) -> None:
    """Print current playback status."""
    if clear:
        print('\r', end='')

    state_str = player.state.name
    time_str = format_time(player.current_time)
    total_str = format_time(player.total_time)
    progress_pct = player.progress * 100

    # Progress bar
    bar_width = 30
    filled = int(bar_width * player.progress)
    bar = '=' * filled + '-' * (bar_width - filled)

    status = f"[{state_str:7}] [{bar}] {time_str}/{total_str} ({progress_pct:5.1f}%)"
    print(status, end='', flush=True)


def interactive_playback(player: XPlanePlayer) -> None:
    """Run interactive playback with keyboard controls."""
    print("\n" + "=" * 60)
    print("X-Plane Flight Data Playback")
    print("=" * 60)
    print("\nControls:")
    print("  ENTER  - Start/Pause/Resume")
    print("  s      - Stop and reset")
    print("  +/-    - Increase/Decrease speed")
    print("  q      - Quit")
    print("=" * 60 + "\n")

    # Status callback
    def on_frame(frame_idx: int, time_sec: float):
        print_status(player)

    player.on_frame(on_frame)

    try:
        import select
        import tty
        import termios

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

        running = True
        while running:
            # Check for input
            if select.select([sys.stdin], [], [], 0.1)[0]:
                char = sys.stdin.read(1)

                if char == '\n' or char == ' ':  # Enter or Space
                    if player.state == PlaybackState.STOPPED:
                        print("\nStarting playback...")
                        player.play()
                    elif player.state == PlaybackState.PLAYING:
                        player.pause()
                        print("\n[PAUSED]")
                    elif player.state == PlaybackState.PAUSED:
                        player.resume()
                        print("\n[RESUMED]")

                elif char == 's':
                    player.stop()
                    print("\n[STOPPED]")

                elif char == '+' or char == '=':
                    new_speed = min(10.0, player._speed * 1.5)
                    player.set_speed(new_speed)
                    print(f"\nSpeed: {new_speed:.1f}x")

                elif char == '-':
                    new_speed = max(0.1, player._speed / 1.5)
                    player.set_speed(new_speed)
                    print(f"\nSpeed: {new_speed:.1f}x")

                elif char == 'q':
                    print("\nQuitting...")
                    running = False

            # Check if playback finished
            if player.state == PlaybackState.STOPPED and player._current_frame > 0:
                print("\n\nPlayback complete!")
                player._current_frame = 0

        # Restore terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    except ImportError:
        # Windows or no termios - use simple input
        simple_playback(player)


def simple_playback(player: XPlanePlayer) -> None:
    """Simple non-interactive playback."""
    print("\nStarting playback (non-interactive mode)...")
    print("Press Ctrl+C to stop\n")

    def on_frame(frame_idx: int, time_sec: float):
        if frame_idx % 10 == 0:  # Update every 10 frames
            print_status(player)

    player.on_frame(on_frame)
    player.play()

    try:
        while player.is_playing or player.is_paused:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        player.stop()

    print("\nPlayback complete!")


def main():
    parser = argparse.ArgumentParser(
        description='Play flight simulation data in X-Plane',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s sessions/session_001/data/flight_data.mat
  %(prog)s flight_data.mat --speed 2.0
  %(prog)s flight_data.mat --host 192.168.1.100 --backend xpc
  %(prog)s flight_data.mat --origin 37.5,-122.0,100
        """
    )

    parser.add_argument('mat_file', type=str,
                        help='Path to .mat file with flight data')

    parser.add_argument('--speed', '-s', type=float, default=1.0,
                        help='Playback speed factor (default: 1.0)')

    parser.add_argument('--host', type=str, default='localhost',
                        help='X-Plane host address (default: localhost)')

    parser.add_argument('--backend', choices=['auto', 'xpc', 'native'],
                        default='auto',
                        help='Communication backend (default: auto)')

    parser.add_argument('--origin', type=str, default=None,
                        help='Geographic origin as lat,lon,alt (default: auto-detect)')

    parser.add_argument('--loop', action='store_true',
                        help='Loop playback continuously')

    parser.add_argument('--config', type=str, default=None,
                        help='Path to custom xplane.yaml config')

    parser.add_argument('--no-controls', action='store_true',
                        help='Skip sending control surface data')

    parser.add_argument('--no-propulsion', action='store_true',
                        help='Skip sending propulsion data (RPM, tilt)')

    parser.add_argument('--simple', action='store_true',
                        help='Use simple non-interactive mode')

    args = parser.parse_args()

    # Check mat file exists
    mat_path = Path(args.mat_file)
    if not mat_path.exists():
        # Try in sessions directory
        alt_path = project_root / args.mat_file
        if alt_path.exists():
            mat_path = alt_path
        else:
            print(f"Error: File not found: {args.mat_file}")
            sys.exit(1)

    # Load or create config
    if args.config:
        config = PlaybackConfig.from_yaml(args.config)
    else:
        config_path = project_root / 'config' / 'xplane.yaml'
        if config_path.exists():
            config = PlaybackConfig.from_yaml(config_path)
        else:
            config = PlaybackConfig()

    # Apply command line overrides
    config.host = args.host
    config.backend = args.backend
    config.default_speed = args.speed
    config.loop = args.loop

    if args.no_controls:
        config.send_controls = False
    if args.no_propulsion:
        config.send_propulsion = False

    # Parse origin if provided
    if args.origin:
        try:
            parts = args.origin.split(',')
            config.auto_origin = False
            config.origin_lat = float(parts[0])
            config.origin_lon = float(parts[1])
            config.origin_alt = float(parts[2]) if len(parts) > 2 else 0.0
        except (ValueError, IndexError):
            print(f"Error: Invalid origin format. Use: lat,lon[,alt]")
            sys.exit(1)

    # Create player
    print(f"Loading: {mat_path}")
    player = XPlanePlayer(config)

    if not player.load(mat_path):
        print("Error: Failed to load flight data")
        sys.exit(1)

    print(f"Connecting to X-Plane at {config.host}...")
    if not player.connect():
        print("Error: Failed to connect to X-Plane")
        print("\nTroubleshooting:")
        print("  1. Ensure X-Plane is running")
        print("  2. For XPC backend: Install XPlaneConnect plugin")
        print("  3. For remote connection: Check firewall settings")
        print("  4. Try --backend native if XPC fails")
        sys.exit(1)

    try:
        if args.simple:
            simple_playback(player)
        else:
            try:
                interactive_playback(player)
            except Exception:
                simple_playback(player)
    finally:
        player.stop()
        player.disconnect()
        print("\nDisconnected from X-Plane")


if __name__ == '__main__':
    main()
