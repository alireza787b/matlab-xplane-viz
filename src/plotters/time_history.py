"""
Time history plotter for flight data.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, List, Tuple

from .base import BasePlotter
from ..flight_data import FlightData
from ..styles.themes import PlotStyle


class TimeHistoryPlotter(BasePlotter):
    """Plotter for time history plots (attitude, position, velocity)."""

    def plot(self, **kwargs) -> plt.Figure:
        """Generate complete time history plot."""
        return self.plot_all_states()

    def plot_all_states(self) -> plt.Figure:
        """Create comprehensive time history plot with all states."""
        fig, axes = self.create_figure('multi_panel', nrows=4, ncols=1)
        fig.suptitle(f'Flight Time History - {self.data.source_file.split("/")[-1]}',
                     fontsize=self.style.title_size + 2, fontweight='bold')

        # Plot each category
        self._plot_attitude(axes[0])
        self._plot_position(axes[1])
        self._plot_velocity(axes[2])
        self._plot_altitude(axes[3])

        # Only show x-label on bottom plot
        for ax in axes[:-1]:
            ax.set_xlabel('')
            ax.tick_params(labelbottom=False)

        plt.tight_layout()
        return fig

    def plot_attitude(self) -> plt.Figure:
        """Create attitude-only time history plot."""
        fig, axes = self.create_figure('single', nrows=3, ncols=1, sharex=True)
        fig.suptitle('Attitude Time History', fontsize=self.style.title_size + 2)

        time = self.data.time
        colors = self.style.colors.get('attitude', {})

        # Roll
        axes[0].plot(time, self.data.phi_deg,
                     color=colors.get('phi', '#d62728'),
                     linewidth=self.style.line_width_main,
                     label='Roll (φ)')
        axes[0].set_ylabel('Roll (deg)')
        axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        self.add_grid(axes[0])
        self.add_legend(axes[0])

        # Pitch
        axes[1].plot(time, self.data.theta_deg,
                     color=colors.get('theta', '#ff7f0e'),
                     linewidth=self.style.line_width_main,
                     label='Pitch (θ)')
        axes[1].set_ylabel('Pitch (deg)')
        axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        self.add_grid(axes[1])
        self.add_legend(axes[1])

        # Yaw
        axes[2].plot(time, self.data.psi_deg,
                     color=colors.get('psi', '#9467bd'),
                     linewidth=self.style.line_width_main,
                     label='Yaw (ψ)')
        axes[2].set_ylabel('Yaw (deg)')
        axes[2].set_xlabel('Time (s)')
        self.add_grid(axes[2])
        self.add_legend(axes[2])

        plt.tight_layout()
        return fig

    def plot_position(self) -> plt.Figure:
        """Create position time history plot."""
        fig, axes = self.create_figure('single', nrows=3, ncols=1, sharex=True)
        fig.suptitle('Position Time History (NED Frame)', fontsize=self.style.title_size + 2)

        time = self.data.time
        colors = self.style.colors.get('position', {})

        # North
        axes[0].plot(time, self.data.N,
                     color=colors.get('N', '#1f77b4'),
                     linewidth=self.style.line_width_main,
                     label='North')
        axes[0].set_ylabel('North (m)')
        self.add_grid(axes[0])
        self.add_legend(axes[0])

        # East
        axes[1].plot(time, self.data.E,
                     color=colors.get('E', '#4a9fd4'),
                     linewidth=self.style.line_width_main,
                     label='East')
        axes[1].set_ylabel('East (m)')
        self.add_grid(axes[1])
        self.add_legend(axes[1])

        # Down (show as negative for intuitive altitude interpretation)
        axes[2].plot(time, self.data.D,
                     color=colors.get('D', '#7ec8e3'),
                     linewidth=self.style.line_width_main,
                     label='Down')
        axes[2].set_ylabel('Down (m)')
        axes[2].set_xlabel('Time (s)')
        axes[2].invert_yaxis()  # Invert so "up" appears up
        self.add_grid(axes[2])
        self.add_legend(axes[2])

        plt.tight_layout()
        return fig

    def plot_velocity(self) -> plt.Figure:
        """Create velocity time history plot."""
        fig, axes = self.create_figure('single', nrows=2, ncols=1, sharex=True)
        fig.suptitle('Velocity Time History', fontsize=self.style.title_size + 2)

        time = self.data.time
        colors = self.style.colors.get('velocity', {})

        # Ground speed
        axes[0].plot(time, self.data.V_ground,
                     color=colors.get('V_ground', '#17becf'),
                     linewidth=self.style.line_width_main,
                     label=f'Ground Speed (mean: {self.data.V_ground.mean():.1f} m/s)')
        axes[0].set_ylabel('Ground Speed (m/s)')
        self.add_grid(axes[0])
        self.add_legend(axes[0])

        # Add secondary axis for knots
        ax2 = axes[0].twinx()
        ax2.set_ylabel('Speed (knots)', color='gray')
        ax2.set_ylim(axes[0].get_ylim()[0] * 1.944, axes[0].get_ylim()[1] * 1.944)
        ax2.tick_params(axis='y', labelcolor='gray')

        # Climb rate
        axes[1].plot(time, self.data.climb_rate,
                     color=colors.get('climb_rate', '#2ca02c'),
                     linewidth=self.style.line_width_main,
                     label='Climb Rate')
        axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[1].set_ylabel('Climb Rate (m/s)')
        axes[1].set_xlabel('Time (s)')
        axes[1].fill_between(time, 0, self.data.climb_rate,
                             where=self.data.climb_rate > 0,
                             alpha=0.3, color='green', label='Climbing')
        axes[1].fill_between(time, 0, self.data.climb_rate,
                             where=self.data.climb_rate < 0,
                             alpha=0.3, color='red', label='Descending')
        self.add_grid(axes[1])
        self.add_legend(axes[1])

        plt.tight_layout()
        return fig

    def _plot_attitude(self, ax: plt.Axes) -> None:
        """Plot attitude on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('attitude', {})

        ax.plot(time, self.data.phi_deg,
                color=colors.get('phi', '#d62728'),
                linewidth=self.style.line_width_main,
                label='Roll (φ)')
        ax.plot(time, self.data.theta_deg,
                color=colors.get('theta', '#ff7f0e'),
                linewidth=self.style.line_width_main,
                label='Pitch (θ)')
        ax.plot(time, self.data.psi_deg,
                color=colors.get('psi', '#9467bd'),
                linewidth=self.style.line_width_main,
                label='Yaw (ψ)')

        ax.set_ylabel('Attitude (deg)')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')
        ax.set_title('Attitude (Euler Angles)', fontsize=self.style.title_size)

    def _plot_position(self, ax: plt.Axes) -> None:
        """Plot position on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('position', {})

        ax.plot(time, self.data.N / 1000,
                color=colors.get('N', '#1f77b4'),
                linewidth=self.style.line_width_main,
                label='North')
        ax.plot(time, self.data.E,
                color=colors.get('E', '#4a9fd4'),
                linewidth=self.style.line_width_main,
                label='East')

        ax.set_ylabel('Position (km N, m E)')
        self.add_grid(ax)
        self.add_legend(ax, loc='upper left')
        ax.set_title('Position (NED Frame)', fontsize=self.style.title_size)

    def _plot_velocity(self, ax: plt.Axes) -> None:
        """Plot velocity on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('velocity', {})

        ax.plot(time, self.data.V_ground,
                color=colors.get('V_ground', '#17becf'),
                linewidth=self.style.line_width_main,
                label=f'Ground Speed')
        ax.plot(time, self.data.climb_rate,
                color=colors.get('climb_rate', '#2ca02c'),
                linewidth=self.style.line_width_main,
                label='Climb Rate')

        ax.set_ylabel('Velocity (m/s)')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')
        ax.set_title('Velocity', fontsize=self.style.title_size)

    def _plot_altitude(self, ax: plt.Axes) -> None:
        """Plot altitude on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('position', {})

        ax.plot(time, self.data.altitude,
                color=colors.get('altitude', '#1f77b4'),
                linewidth=self.style.line_width_main,
                label='Altitude')
        ax.fill_between(time, 0, self.data.altitude, alpha=0.2,
                        color=colors.get('altitude', '#1f77b4'))

        ax.set_ylabel('Altitude (m)')
        ax.set_xlabel('Time (s)')
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')
        ax.set_title('Altitude', fontsize=self.style.title_size)
