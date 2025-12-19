"""
3D Aircraft visualization with trajectory and attitude.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from typing import Optional, List, Tuple
import imageio
from pathlib import Path
from tqdm import tqdm

from .base import BasePlotter
from ..flight_data import FlightData
from ..styles.themes import PlotStyle
from ..utils.rotations import RotationUtils


class Aircraft3DPlotter(BasePlotter):
    """Plotter for 3D aircraft visualization with attitude."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.aircraft_scale = 100.0  # Scale factor for aircraft size in plots

    def plot(self, **kwargs) -> plt.Figure:
        """Generate 3D aircraft visualization."""
        return self.plot_trajectory_with_aircraft()

    def _create_aircraft_geometry(self, scale: float = 1.0) -> Tuple[np.ndarray, List]:
        """
        Create simple aircraft geometry.

        Returns:
            vertices: (N, 3) array of vertex positions in body frame
            faces: List of face definitions (vertex indices)
        """
        # Scale factor
        s = scale

        # Simplified VTOL aircraft geometry (nose pointing +X in body frame)
        # Coordinates are [x, y, z] where x=forward, y=right, z=down

        vertices = np.array([
            # Fuselage
            [4 * s, 0, 0],           # 0: Nose
            [-3 * s, 0, 0],          # 1: Tail
            [0, 0.5 * s, 0],         # 2: Fuselage right
            [0, -0.5 * s, 0],        # 3: Fuselage left
            [0, 0, 0.3 * s],         # 4: Fuselage bottom
            [0, 0, -0.2 * s],        # 5: Fuselage top

            # Right wing
            [0.5 * s, 5 * s, 0],     # 6: Right wing tip leading
            [-0.5 * s, 5 * s, 0],    # 7: Right wing tip trailing
            [0.5 * s, 0.8 * s, 0],   # 8: Right wing root leading
            [-0.5 * s, 0.8 * s, 0],  # 9: Right wing root trailing

            # Left wing
            [0.5 * s, -5 * s, 0],    # 10: Left wing tip leading
            [-0.5 * s, -5 * s, 0],   # 11: Left wing tip trailing
            [0.5 * s, -0.8 * s, 0],  # 12: Left wing root leading
            [-0.5 * s, -0.8 * s, 0], # 13: Left wing root trailing

            # Horizontal tail
            [-2.5 * s, 1.5 * s, 0],  # 14: Right tail tip
            [-2.5 * s, -1.5 * s, 0], # 15: Left tail tip
            [-2 * s, 0, 0],          # 16: Tail leading edge

            # Vertical tail
            [-2 * s, 0, -0.2 * s],   # 17: Vertical tail bottom
            [-3 * s, 0, -0.2 * s],   # 18: Vertical tail trailing
            [-2.5 * s, 0, -1.2 * s], # 19: Vertical tail top
        ])

        # Define faces (triangles) for 3D plotting
        faces = [
            # Fuselage (simplified)
            [0, 2, 5], [0, 5, 3], [0, 3, 4], [0, 4, 2],  # Nose cone
            [1, 5, 2], [1, 3, 5], [1, 4, 3], [1, 2, 4],  # Tail cone

            # Right wing
            [6, 7, 9, 8],

            # Left wing
            [10, 12, 13, 11],

            # Horizontal tail
            [14, 1, 15], [14, 16, 1], [1, 16, 15],

            # Vertical tail
            [17, 18, 19],
        ]

        return vertices, faces

    def _transform_aircraft(
        self,
        vertices: np.ndarray,
        position: np.ndarray,
        phi: float,
        theta: float,
        psi: float
    ) -> np.ndarray:
        """Transform aircraft vertices to world coordinates."""
        # Create rotation matrix (body to NED)
        dcm = RotationUtils.euler_to_dcm(phi, theta, psi)

        # Transform vertices
        transformed = (dcm @ vertices.T).T

        # Add position offset
        transformed += position

        return transformed

    def plot_trajectory_with_aircraft(
        self,
        n_aircraft: int = 8,
        show_ground_track: bool = True
    ) -> plt.Figure:
        """
        Plot 3D trajectory with aircraft models showing attitude.

        Args:
            n_aircraft: Number of aircraft to show along path
            show_ground_track: Whether to show ground projection
        """
        fig = plt.figure(figsize=self.style.get_figure_size('trajectory_3d'))
        ax = fig.add_subplot(111, projection='3d')
        fig.suptitle('3D Flight Visualization with Aircraft Attitude',
                     fontsize=self.style.title_size + 2, fontweight='bold')

        colors = self.style.colors.get('trajectory', {})
        ac_colors = self.style.colors.get('aircraft', {})

        # Plot trajectory path
        ax.plot(self.data.E, self.data.N, self.data.altitude,
                color=colors.get('path', '#1f77b4'),
                linewidth=1.0, alpha=0.7, label='Flight Path')

        # Ground track
        if show_ground_track:
            ax.plot(self.data.E, self.data.N, np.zeros_like(self.data.N),
                    color='gray', linewidth=0.5, alpha=0.3, linestyle='--')

        # Create aircraft geometry
        vertices, faces = self._create_aircraft_geometry(scale=self.aircraft_scale)

        # Select indices for aircraft placement
        indices = np.linspace(0, len(self.data.N) - 1, n_aircraft + 2).astype(int)[1:-1]

        # Draw aircraft at selected points
        for i, idx in enumerate(indices):
            # Get position and attitude
            pos = np.array([self.data.E[idx], self.data.N[idx], self.data.altitude[idx]])
            phi = self.data.phi[idx]
            theta = self.data.theta[idx]
            psi = self.data.psi[idx]

            # Transform aircraft
            transformed = self._transform_aircraft(vertices, pos, phi, theta, psi)

            # Color gradient along path
            alpha = 0.3 + 0.7 * (i / len(indices))

            # Draw aircraft as wireframe
            # Fuselage
            for face_idx in range(8):
                face = faces[face_idx]
                verts = transformed[face]
                ax.plot(verts[[0, 1, 2, 0], 0],
                        verts[[0, 1, 2, 0], 1],
                        verts[[0, 1, 2, 0], 2],
                        color=ac_colors.get('fuselage', '#4a90d9'),
                        linewidth=0.8, alpha=alpha)

            # Wings
            for face_idx in [8, 9]:
                face = faces[face_idx]
                verts = transformed[face]
                xs = np.append(verts[:, 0], verts[0, 0])
                ys = np.append(verts[:, 1], verts[0, 1])
                zs = np.append(verts[:, 2], verts[0, 2])
                ax.plot(xs, ys, zs,
                        color=ac_colors.get('wings', '#6ab7ff'),
                        linewidth=1.0, alpha=alpha)

            # Draw vertical line to ground
            ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [0, pos[2]],
                    color='gray', linestyle=':', alpha=0.3, linewidth=0.5)

        # Mark start and end
        ax.scatter(self.data.E[0], self.data.N[0], self.data.altitude[0],
                   c=colors.get('start', '#2ca02c'), s=100, marker='o',
                   label='Start', zorder=10)
        ax.scatter(self.data.E[-1], self.data.N[-1], self.data.altitude[-1],
                   c=colors.get('end', '#d62728'), s=100, marker='s',
                   label='End', zorder=10)

        # Set labels
        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_zlabel('Altitude (m)')

        # Set equal aspect for x and y
        max_range = max(
            self.data.E.max() - self.data.E.min(),
            self.data.N.max() - self.data.N.min()
        ) / 2 * 1.1

        mid_e = (self.data.E.max() + self.data.E.min()) / 2
        mid_n = (self.data.N.max() + self.data.N.min()) / 2

        ax.set_xlim(mid_e - max_range, mid_e + max_range)
        ax.set_ylim(mid_n - max_range, mid_n + max_range)

        ax.legend(loc='upper left')
        ax.view_init(elev=25, azim=-60)

        plt.tight_layout()
        return fig

    def create_animation(
        self,
        output_path: str,
        fps: int = 30,
        duration_factor: float = 1.0,
        trail_length: int = 50,
        format: str = 'gif'
    ) -> Path:
        """
        Create animated flight visualization.

        Args:
            output_path: Output file path
            fps: Frames per second
            duration_factor: Speed factor (1.0 = real-time, 0.5 = 2x speed)
            trail_length: Number of past positions to show in trail
            format: Output format ('gif' or 'mp4')

        Returns:
            Path to output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate frame indices
        real_duration = self.data.duration
        anim_duration = real_duration * duration_factor
        n_frames = int(anim_duration * fps)

        # Sample indices from data
        frame_indices = np.linspace(0, len(self.data.N) - 1, n_frames).astype(int)

        # Create aircraft geometry
        vertices, faces = self._create_aircraft_geometry(scale=self.aircraft_scale)

        colors = self.style.colors.get('trajectory', {})
        ac_colors = self.style.colors.get('aircraft', {})

        # Generate frames
        frames = []
        print(f"Generating {n_frames} frames for animation...")

        for frame_num, idx in enumerate(tqdm(frame_indices, desc="Rendering")):
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')

            # Determine trail range
            trail_start = max(0, idx - trail_length)

            # Plot trail
            ax.plot(self.data.E[trail_start:idx + 1],
                    self.data.N[trail_start:idx + 1],
                    self.data.altitude[trail_start:idx + 1],
                    color=colors.get('path', '#1f77b4'),
                    linewidth=2.0, alpha=0.8)

            # Plot future path (faded)
            ax.plot(self.data.E[idx:],
                    self.data.N[idx:],
                    self.data.altitude[idx:],
                    color=colors.get('path', '#1f77b4'),
                    linewidth=0.5, alpha=0.2)

            # Ground track
            ax.plot(self.data.E, self.data.N, np.zeros_like(self.data.N),
                    color='gray', linewidth=0.5, alpha=0.2, linestyle='--')

            # Current position
            pos = np.array([self.data.E[idx], self.data.N[idx], self.data.altitude[idx]])
            phi = self.data.phi[idx]
            theta = self.data.theta[idx]
            psi = self.data.psi[idx]

            # Transform and draw aircraft
            transformed = self._transform_aircraft(vertices, pos, phi, theta, psi)

            # Draw filled polygons for aircraft
            # Wings
            for face_idx in [8, 9]:
                face = faces[face_idx]
                verts = [list(zip(transformed[face, 0],
                                  transformed[face, 1],
                                  transformed[face, 2]))]
                poly = Poly3DCollection(verts, alpha=0.8,
                                        facecolor=ac_colors.get('wings', '#6ab7ff'),
                                        edgecolor='black', linewidth=0.5)
                ax.add_collection3d(poly)

            # Fuselage outline
            for face_idx in range(8):
                face = faces[face_idx]
                verts = transformed[face]
                ax.plot(verts[[0, 1, 2, 0], 0],
                        verts[[0, 1, 2, 0], 1],
                        verts[[0, 1, 2, 0], 2],
                        color=ac_colors.get('fuselage', '#4a90d9'),
                        linewidth=1.0)

            # Vertical line to ground
            ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [0, pos[2]],
                    color='gray', linestyle=':', alpha=0.5)

            # Start marker
            ax.scatter(self.data.E[0], self.data.N[0], self.data.altitude[0],
                       c=colors.get('start', '#2ca02c'), s=80, marker='o')

            # Set consistent view limits
            max_range = max(
                self.data.E.max() - self.data.E.min(),
                self.data.N.max() - self.data.N.min()
            ) / 2 * 1.1

            mid_e = (self.data.E.max() + self.data.E.min()) / 2
            mid_n = (self.data.N.max() + self.data.N.min()) / 2

            ax.set_xlim(mid_e - max_range, mid_e + max_range)
            ax.set_ylim(mid_n - max_range, mid_n + max_range)
            ax.set_zlim(0, self.data.altitude.max() * 1.2)

            ax.set_xlabel('East (m)')
            ax.set_ylabel('North (m)')
            ax.set_zlabel('Altitude (m)')

            # Add time annotation
            time = self.data.time[idx]
            ax.set_title(f'Flight Simulation - t = {time:.1f}s',
                         fontsize=14, fontweight='bold')

            ax.view_init(elev=25, azim=-60 + frame_num * 0.1)  # Slow rotation

            # Convert figure to image (compatible with newer matplotlib)
            fig.canvas.draw()
            buf = fig.canvas.buffer_rgba()
            image = np.asarray(buf)[:, :, :3]  # Remove alpha channel
            frames.append(image.copy())

            plt.close(fig)

        # Save animation
        print(f"Saving animation to {output_path}...")
        if format == 'gif':
            imageio.mimsave(output_path, frames, fps=fps, loop=0)
        else:  # mp4
            imageio.mimsave(output_path, frames, fps=fps)

        print(f"Animation saved: {output_path}")
        return output_path
