#!/usr/bin/env python3
"""
VTOL Flight Simulation Analysis - Main Entry Point

Usage:
    python run_analysis.py --session session_001
    python run_analysis.py --mat-file path/to/file.mat --output-dir path/to/output
    python run_analysis.py --session session_001 --animate
"""

import sys
import argparse
from pathlib import Path
from typing import Optional
import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.flight_data import FlightData
from src.styles.themes import load_style
from src.plotters import (
    TimeHistoryPlotter,
    TrajectoryPlotter,
    ControlsPlotter,
    Aircraft3DPlotter,
    DashboardPlotter
)


def find_mat_files(session_path: Path) -> list:
    """Find all .mat files in session's raw_data folder."""
    raw_data_dir = session_path / 'raw_data'
    if not raw_data_dir.exists():
        return []
    return list(raw_data_dir.glob('*.mat'))


def clean_session_plots(session_path: Path, verbose: bool = True) -> int:
    """
    Clean existing plots from a session directory.

    Args:
        session_path: Path to session directory
        verbose: Print info about deleted files

    Returns:
        Number of files deleted
    """
    plots_dir = session_path / 'plots'
    if not plots_dir.exists():
        return 0

    deleted_count = 0
    for ext in ['*.png', '*.gif', '*.mp4', '*.svg', '*.pdf']:
        for file in plots_dir.rglob(ext):
            file.unlink()
            deleted_count += 1

    if verbose and deleted_count > 0:
        print(f"Cleaned {deleted_count} existing plot(s) from previous run")

    return deleted_count


def generate_all_plots(
    flight_data: FlightData,
    output_dir: Path,
    style_config: Optional[str] = None,
    create_animation: bool = False,
    animation_fps: int = 30
) -> dict:
    """
    Generate all visualization plots for flight data.

    Args:
        flight_data: Loaded FlightData instance
        output_dir: Base output directory for plots
        style_config: Path to custom style config (optional)
        create_animation: Whether to create animated visualization
        animation_fps: Frames per second for animation

    Returns:
        Dictionary with paths to generated files
    """
    # Load style
    style = load_style(style_config)

    # Ensure output directories exist
    plots_dir = output_dir / 'plots'
    for subdir in ['time_histories', 'trajectory', 'controls', '3d_aircraft', 'summary', 'animations']:
        (plots_dir / subdir).mkdir(parents=True, exist_ok=True)

    generated_files = {}

    print("\n" + "=" * 60)
    print("VTOL Flight Simulation Analysis")
    print("=" * 60)
    print(f"Source: {flight_data.source_file}")
    print(f"Duration: {flight_data.duration}s @ {flight_data.sample_rate}Hz")
    print(f"Samples: {flight_data.n_samples}")
    print(f"Output: {output_dir}")
    print("=" * 60 + "\n")

    # 1. Time History Plots
    print("Generating time history plots...")
    th_plotter = TimeHistoryPlotter(flight_data, style, str(plots_dir))

    # All states combined
    fig = th_plotter.plot_all_states()
    path = th_plotter.save_figure(fig, 'time_history_all', 'time_histories')
    generated_files['time_history_all'] = path
    fig.clf()

    # Attitude only
    fig = th_plotter.plot_attitude()
    path = th_plotter.save_figure(fig, 'attitude', 'time_histories')
    generated_files['attitude'] = path
    fig.clf()

    # Position only
    fig = th_plotter.plot_position()
    path = th_plotter.save_figure(fig, 'position', 'time_histories')
    generated_files['position'] = path
    fig.clf()

    # Velocity
    fig = th_plotter.plot_velocity()
    path = th_plotter.save_figure(fig, 'velocity', 'time_histories')
    generated_files['velocity'] = path
    fig.clf()

    print(f"  Created {len([k for k in generated_files if 'time' in k or 'attitude' in k or 'position' in k or 'velocity' in k])} time history plots")

    # 2. Trajectory Plots
    print("Generating trajectory plots...")
    traj_plotter = TrajectoryPlotter(flight_data, style, str(plots_dir))

    # Ground track
    fig = traj_plotter.plot_ground_track()
    path = traj_plotter.save_figure(fig, 'ground_track', 'trajectory')
    generated_files['ground_track'] = path
    fig.clf()

    # 3D trajectory
    fig = traj_plotter.plot_3d_trajectory()
    path = traj_plotter.save_figure(fig, 'trajectory_3d', 'trajectory')
    generated_files['trajectory_3d'] = path
    fig.clf()

    # Combined views
    fig = traj_plotter.plot_combined()
    path = traj_plotter.save_figure(fig, 'trajectory_combined', 'trajectory')
    generated_files['trajectory_combined'] = path
    fig.clf()

    # Altitude profile
    fig = traj_plotter.plot_altitude_profile()
    path = traj_plotter.save_figure(fig, 'altitude_profile', 'trajectory')
    generated_files['altitude_profile'] = path
    fig.clf()

    print(f"  Created 4 trajectory plots")

    # 3. Controls Plots
    print("Generating controls plots...")
    ctrl_plotter = ControlsPlotter(flight_data, style, str(plots_dir))

    # All controls
    fig = ctrl_plotter.plot_all_controls()
    path = ctrl_plotter.save_figure(fig, 'controls_all', 'controls')
    generated_files['controls_all'] = path
    fig.clf()

    # Control surfaces only
    fig = ctrl_plotter.plot_control_surfaces()
    path = ctrl_plotter.save_figure(fig, 'control_surfaces', 'controls')
    generated_files['control_surfaces'] = path
    fig.clf()

    # Propulsion only
    fig = ctrl_plotter.plot_propulsion()
    path = ctrl_plotter.save_figure(fig, 'propulsion', 'controls')
    generated_files['propulsion'] = path
    fig.clf()

    print(f"  Created 3 controls plots")

    # 4. 3D Aircraft Visualization
    print("Generating 3D aircraft visualization...")
    ac_plotter = Aircraft3DPlotter(flight_data, style, str(plots_dir))

    # Static 3D with aircraft
    fig = ac_plotter.plot_trajectory_with_aircraft(n_aircraft=8)
    path = ac_plotter.save_figure(fig, 'aircraft_3d_trajectory', '3d_aircraft')
    generated_files['aircraft_3d'] = path
    fig.clf()

    print(f"  Created 1 3D aircraft plot")

    # 5. Dashboard
    print("Generating dashboard...")
    dash_plotter = DashboardPlotter(flight_data, style, str(plots_dir))

    fig = dash_plotter.plot_dashboard()
    path = dash_plotter.save_figure(fig, 'dashboard', 'summary')
    generated_files['dashboard'] = path
    fig.clf()

    print(f"  Created 1 dashboard")

    # 6. Animation (if requested)
    if create_animation:
        print("\nGenerating animation (this may take a while)...")
        anim_path = plots_dir / 'animations' / 'flight_animation.gif'

        try:
            ac_plotter.create_animation(
                output_path=str(anim_path),
                fps=animation_fps,
                duration_factor=0.3,  # 3x speed for shorter animation
                trail_length=100
            )
            generated_files['animation'] = anim_path
            print(f"  Created animation: {anim_path}")
        except Exception as e:
            print(f"  Warning: Animation creation failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print(f"COMPLETE: Generated {len(generated_files)} files")
    print("=" * 60)

    for name, path in generated_files.items():
        if path:
            print(f"  {name}: {path}")

    return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='VTOL Flight Simulation Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Analyze a session:
    python run_analysis.py --session session_001

  Analyze a specific MAT file:
    python run_analysis.py --mat-file data.mat --output-dir ./output

  Generate with animation:
    python run_analysis.py --session session_001 --animate
        """
    )

    parser.add_argument(
        '--session', '-s',
        type=str,
        help='Session name (folder in sessions/)'
    )

    parser.add_argument(
        '--mat-file', '-m',
        type=str,
        help='Path to MAT file (alternative to --session)'
    )

    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help='Output directory (required with --mat-file)'
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to custom style configuration YAML'
    )

    parser.add_argument(
        '--animate', '-a',
        action='store_true',
        help='Generate animated visualization (GIF)'
    )

    parser.add_argument(
        '--fps',
        type=int,
        default=30,
        help='Animation frames per second (default: 30)'
    )

    parser.add_argument(
        '--list-sessions',
        action='store_true',
        help='List available sessions and exit'
    )

    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Do not clean existing plots before generating new ones'
    )

    args = parser.parse_args()

    # Get project root
    project_root = Path(__file__).parent

    # List sessions mode
    if args.list_sessions:
        sessions_dir = project_root / 'sessions'
        if sessions_dir.exists():
            sessions = [d.name for d in sessions_dir.iterdir() if d.is_dir()]
            print("Available sessions:")
            for s in sorted(sessions):
                mat_files = find_mat_files(sessions_dir / s)
                print(f"  {s}: {len(mat_files)} MAT file(s)")
        else:
            print("No sessions directory found.")
        return 0

    # Validate arguments
    if not args.session and not args.mat_file:
        parser.error("Either --session or --mat-file is required")

    if args.mat_file and not args.output_dir:
        parser.error("--output-dir is required when using --mat-file")

    # Determine paths
    if args.session:
        session_path = project_root / 'sessions' / args.session
        if not session_path.exists():
            print(f"Error: Session '{args.session}' not found")
            return 1

        mat_files = find_mat_files(session_path)
        if not mat_files:
            print(f"Error: No MAT files found in {session_path / 'raw_data'}")
            return 1

        mat_file = mat_files[0]  # Use first MAT file
        output_dir = session_path

    else:
        mat_file = Path(args.mat_file)
        if not mat_file.exists():
            print(f"Error: MAT file not found: {mat_file}")
            return 1

        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing plots if not disabled
    if not args.no_clean:
        clean_session_plots(output_dir)

    # Load flight data
    print(f"Loading {mat_file}...")
    try:
        flight_data = FlightData.from_mat_file(str(mat_file))
    except Exception as e:
        print(f"Error loading MAT file: {e}")
        return 1

    # Generate plots
    try:
        generate_all_plots(
            flight_data=flight_data,
            output_dir=output_dir,
            style_config=args.config,
            create_animation=args.animate,
            animation_fps=args.fps
        )
    except Exception as e:
        print(f"Error generating plots: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
