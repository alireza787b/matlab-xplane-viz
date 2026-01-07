#!/usr/bin/env python3
"""
Debug playback script - Run with debug=True to see detailed prop/engine state.

Usage:
    python debug_playback.py

This script will:
1. Connect to X-Plane
2. Load the test flight data
3. Play back with detailed debug output showing:
   - What datarefs are being SENT to X-Plane
   - What values are being READ BACK from X-Plane
   - Aircraft configuration at startup

Press Ctrl+C to stop.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from xplane.player import XPlanePlayer


def main():
    print("="*60)
    print("DEBUG PLAYBACK - Prop/Engine State Verification")
    print("="*60)
    print()
    print("Make sure:")
    print("  1. X-Plane is running with T-Tail-v2.acf loaded")
    print("  2. XPlaneConnect plugin is installed")
    print()

    # Path to test data
    mat_file = Path("sessions/session_001/raw_data/sim_test1.mat")

    if not mat_file.exists():
        print(f"ERROR: Flight data not found: {mat_file}")
        return 1

    # Create player with DEBUG MODE ENABLED
    player = XPlanePlayer(debug=True, verbose=True)

    # Connect
    print("Connecting to X-Plane...")
    if not player.connect():
        print("ERROR: Could not connect to X-Plane!")
        print("  - Is X-Plane running?")
        print("  - Is XPlaneConnect plugin installed?")
        return 1

    # Load flight data
    print(f"\nLoading flight data: {mat_file}")
    if not player.load(mat_file):
        print("ERROR: Could not load flight data!")
        return 1

    # Detect origin from X-Plane
    print("\nDetecting origin from current X-Plane position...")
    player.detect_origin()

    # Play with debug output
    print("\n" + "="*60)
    print("STARTING PLAYBACK WITH DEBUG OUTPUT")
    print("="*60)
    print("Watch the output below to see:")
    print("  - SENT: What we're sending to X-Plane")
    print("  - READ BACK: What X-Plane reports back")
    print()
    print("Press Ctrl+C to stop playback")
    print("="*60 + "\n")

    try:
        player.play(speed=1.0)

        # Wait for playback
        while player.is_playing:
            time.sleep(0.5)
            # Print progress
            print(f"\r[Progress: {player.progress*100:.1f}%]", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\nPlayback interrupted by user")

    finally:
        player.stop()
        player.disconnect()
        print("\nPlayback stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
