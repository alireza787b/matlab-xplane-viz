"""
Trajectory plotter for 2D and 3D flight path visualization.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import Optional, Tuple

from .base import BasePlotter
from ..flight_data import FlightData
from ..styles.themes import PlotStyle


class TrajectoryPlotter(BasePlotter):
    """Plotter for trajectory visualizations."""

    def plot(self, mode: str = '3d', **kwargs) -> plt.Figure:
        """
        Generate trajectory plot.

        Args:
            mode: '2d', '3d', or 'combined'
        """
        if mode == '2d':
            return self.plot_ground_track()
        elif mode == '3d':
            return self.plot_3d_trajectory()
        else:
            return self.plot_combined()

    def plot_ground_track(self) -> plt.Figure:
        """Create 2D ground track plot."""
        fig, ax = plt.subplots(figsize=self.style.get_figure_size('single'))
        fig.suptitle('Ground Track (Top View)', fontsize=self.style.title_size + 2)

        colors = self.style.colors.get('trajectory', {})

        # Plot path
        path = ax.plot(self.data.E, self.data.N,
                       color=colors.get('path', '#1f77b4'),
                       linewidth=self.style.line_width_main,
                       label='Flight Path')

        # Mark start and end
        ax.scatter(self.data.E[0], self.data.N[0],
                   c=colors.get('start', '#2ca02c'),
                   s=100, marker='o', zorder=5, label='Start')
        ax.scatter(self.data.E[-1], self.data.N[-1],
                   c=colors.get('end', '#d62728'),
                   s=100, marker='s', zorder=5, label='End')

        # Add direction arrows at intervals
        arrow_interval = len(self.data.N) // 10
        for i in range(arrow_interval, len(self.data.N) - arrow_interval, arrow_interval):
            dx = self.data.E[i + 10] - self.data.E[i]
            dy = self.data.N[i + 10] - self.data.N[i]
            ax.annotate('', xy=(self.data.E[i + 10], self.data.N[i + 10]),
                        xytext=(self.data.E[i], self.data.N[i]),
                        arrowprops=dict(arrowstyle='->', color=colors.get('path', '#1f77b4'),
                                        lw=1.5))

        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_aspect('equal', adjustable='box')
        self.add_grid(ax)
        self.add_legend(ax)

        # Add distance annotation
        distance = np.sqrt((self.data.N[-1] - self.data.N[0])**2 +
                           (self.data.E[-1] - self.data.E[0])**2)
        ax.annotate(f'Distance: {distance/1000:.2f} km',
                    xy=(0.02, 0.98), xycoords='axes fraction',
                    fontsize=self.style.label_size,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()
        return fig

    def plot_3d_trajectory(self) -> plt.Figure:
        """Create 3D trajectory plot."""
        fig = plt.figure(figsize=self.style.get_figure_size('trajectory_3d'))
        ax = fig.add_subplot(111, projection='3d')
        fig.suptitle('3D Flight Trajectory', fontsize=self.style.title_size + 2)

        colors = self.style.colors.get('trajectory', {})

        # Plot 3D path (using altitude = -D)
        ax.plot(self.data.E, self.data.N, self.data.altitude,
                color=colors.get('path', '#1f77b4'),
                linewidth=self.style.line_width_main,
                label='Flight Path')

        # Mark start and end
        ax.scatter(self.data.E[0], self.data.N[0], self.data.altitude[0],
                   c=colors.get('start', '#2ca02c'),
                   s=100, marker='o', label='Start')
        ax.scatter(self.data.E[-1], self.data.N[-1], self.data.altitude[-1],
                   c=colors.get('end', '#d62728'),
                   s=100, marker='s', label='End')

        # Project path onto ground plane
        ax.plot(self.data.E, self.data.N, np.zeros_like(self.data.N),
                color='gray', linewidth=0.5, alpha=0.5, linestyle='--',
                label='Ground Track')

        # Draw vertical lines at key points
        key_points = [0, len(self.data.N) // 4, len(self.data.N) // 2,
                      3 * len(self.data.N) // 4, -1]
        for i in key_points:
            ax.plot([self.data.E[i], self.data.E[i]],
                    [self.data.N[i], self.data.N[i]],
                    [0, self.data.altitude[i]],
                    color='gray', linestyle=':', alpha=0.5, linewidth=0.8)

        ax.set_xlabel('East (m)')
        ax.set_ylabel('North (m)')
        ax.set_zlabel('Altitude (m)')

        # Set equal aspect ratio for x and y
        max_range = max(
            self.data.E.max() - self.data.E.min(),
            self.data.N.max() - self.data.N.min()
        ) / 2

        mid_e = (self.data.E.max() + self.data.E.min()) / 2
        mid_n = (self.data.N.max() + self.data.N.min()) / 2

        ax.set_xlim(mid_e - max_range, mid_e + max_range)
        ax.set_ylim(mid_n - max_range, mid_n + max_range)

        ax.legend(loc='upper left')

        # Good viewing angle
        ax.view_init(elev=25, azim=-45)

        plt.tight_layout()
        return fig

    def plot_combined(self) -> plt.Figure:
        """Create combined trajectory visualization with multiple views."""
        fig = plt.figure(figsize=self.style.get_figure_size('dashboard'))
        fig.suptitle('Flight Trajectory Analysis', fontsize=self.style.title_size + 2,
                     fontweight='bold')

        colors = self.style.colors.get('trajectory', {})
        pos_colors = self.style.colors.get('position', {})

        # 3D view (main, left side)
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        ax1.plot(self.data.E, self.data.N, self.data.altitude,
                 color=colors.get('path', '#1f77b4'),
                 linewidth=self.style.line_width_main)
        ax1.scatter(self.data.E[0], self.data.N[0], self.data.altitude[0],
                    c=colors.get('start', '#2ca02c'), s=100, marker='o')
        ax1.scatter(self.data.E[-1], self.data.N[-1], self.data.altitude[-1],
                    c=colors.get('end', '#d62728'), s=100, marker='s')
        ax1.set_xlabel('East (m)')
        ax1.set_ylabel('North (m)')
        ax1.set_zlabel('Altitude (m)')
        ax1.set_title('3D View', fontsize=self.style.title_size)
        ax1.view_init(elev=25, azim=-45)

        # Top view (ground track)
        ax2 = fig.add_subplot(2, 2, 2)
        ax2.plot(self.data.E, self.data.N,
                 color=colors.get('path', '#1f77b4'),
                 linewidth=self.style.line_width_main)
        ax2.scatter(self.data.E[0], self.data.N[0],
                    c=colors.get('start', '#2ca02c'), s=80, marker='o', label='Start')
        ax2.scatter(self.data.E[-1], self.data.N[-1],
                    c=colors.get('end', '#d62728'), s=80, marker='s', label='End')
        ax2.set_xlabel('East (m)')
        ax2.set_ylabel('North (m)')
        ax2.set_title('Top View (Ground Track)', fontsize=self.style.title_size)
        ax2.set_aspect('equal', adjustable='box')
        self.add_grid(ax2)
        ax2.legend()

        # Side view (North-Altitude)
        ax3 = fig.add_subplot(2, 2, 3)
        ax3.plot(self.data.N / 1000, self.data.altitude,
                 color=colors.get('path', '#1f77b4'),
                 linewidth=self.style.line_width_main)
        ax3.scatter(self.data.N[0] / 1000, self.data.altitude[0],
                    c=colors.get('start', '#2ca02c'), s=80, marker='o')
        ax3.scatter(self.data.N[-1] / 1000, self.data.altitude[-1],
                    c=colors.get('end', '#d62728'), s=80, marker='s')
        ax3.fill_between(self.data.N / 1000, 0, self.data.altitude, alpha=0.2,
                         color=pos_colors.get('altitude', '#1f77b4'))
        ax3.set_xlabel('North (km)')
        ax3.set_ylabel('Altitude (m)')
        ax3.set_title('Side View (Altitude Profile)', fontsize=self.style.title_size)
        self.add_grid(ax3)

        # Altitude vs Time
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.plot(self.data.time, self.data.altitude,
                 color=pos_colors.get('altitude', '#1f77b4'),
                 linewidth=self.style.line_width_main)
        ax4.fill_between(self.data.time, 0, self.data.altitude, alpha=0.2,
                         color=pos_colors.get('altitude', '#1f77b4'))
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Altitude (m)')
        ax4.set_title('Altitude vs Time', fontsize=self.style.title_size)
        self.add_grid(ax4)

        plt.tight_layout()
        return fig

    def plot_altitude_profile(self) -> plt.Figure:
        """Create detailed altitude profile plot."""
        fig, axes = self.create_figure('single', nrows=2, ncols=1, sharex=True)
        fig.suptitle('Altitude Profile', fontsize=self.style.title_size + 2)

        colors = self.style.colors.get('position', {})
        vel_colors = self.style.colors.get('velocity', {})

        # Altitude
        axes[0].plot(self.data.time, self.data.altitude,
                     color=colors.get('altitude', '#1f77b4'),
                     linewidth=self.style.line_width_main,
                     label='Altitude')
        axes[0].fill_between(self.data.time, 0, self.data.altitude, alpha=0.2,
                             color=colors.get('altitude', '#1f77b4'))
        axes[0].set_ylabel('Altitude (m)')
        axes[0].set_title('Altitude', fontsize=self.style.title_size)
        self.add_grid(axes[0])

        # Climb rate with fill
        axes[1].plot(self.data.time, self.data.climb_rate,
                     color=vel_colors.get('climb_rate', '#2ca02c'),
                     linewidth=self.style.line_width_main,
                     label='Climb Rate')
        axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[1].fill_between(self.data.time, 0, self.data.climb_rate,
                             where=self.data.climb_rate > 0,
                             alpha=0.3, color='green')
        axes[1].fill_between(self.data.time, 0, self.data.climb_rate,
                             where=self.data.climb_rate < 0,
                             alpha=0.3, color='red')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylabel('Climb Rate (m/s)')
        axes[1].set_title('Vertical Speed', fontsize=self.style.title_size)
        self.add_grid(axes[1])

        plt.tight_layout()
        return fig
