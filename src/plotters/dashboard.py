"""
Dashboard plotter for summary visualization.
"""

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from typing import Optional

from .base import BasePlotter
from ..flight_data import FlightData
from ..styles.themes import PlotStyle


class DashboardPlotter(BasePlotter):
    """Plotter for dashboard/summary visualization."""

    def plot(self, **kwargs) -> plt.Figure:
        """Generate dashboard plot."""
        return self.plot_dashboard()

    def plot_dashboard(self) -> plt.Figure:
        """Create comprehensive dashboard with all key flight data."""
        fig = plt.figure(figsize=self.style.get_figure_size('dashboard'))
        fig.suptitle('Flight Simulation Dashboard',
                     fontsize=self.style.title_size + 4, fontweight='bold', y=0.98)

        # Create grid layout
        gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.35,
                              left=0.06, right=0.94, top=0.92, bottom=0.06)

        colors = self.style.colors

        # 1. 3D Trajectory (top left, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2], projection='3d')
        self._plot_3d_trajectory(ax1)

        # 2. Ground Track (top right)
        ax2 = fig.add_subplot(gs[0, 2])
        self._plot_ground_track(ax2)

        # 3. Flight Stats (top far right)
        ax3 = fig.add_subplot(gs[0, 3])
        self._plot_flight_stats(ax3)

        # 4. Attitude (middle left, 2 columns)
        ax4 = fig.add_subplot(gs[1, :2])
        self._plot_attitude(ax4)

        # 5. Velocity & Altitude (middle right, 2 columns)
        ax5 = fig.add_subplot(gs[1, 2:])
        self._plot_velocity_altitude(ax5)

        # 6. Control Surfaces (bottom left, 2 columns)
        ax6 = fig.add_subplot(gs[2, :2])
        self._plot_controls(ax6)

        # 7. Propulsion (bottom right, 2 columns)
        ax7 = fig.add_subplot(gs[2, 2:])
        self._plot_propulsion(ax7)

        return fig

    def _plot_3d_trajectory(self, ax: plt.Axes) -> None:
        """Plot 3D trajectory on given axes."""
        colors = self.style.colors.get('trajectory', {})

        ax.plot(self.data.E, self.data.N, self.data.altitude,
                color=colors.get('path', '#1f77b4'),
                linewidth=1.5)
        ax.scatter(self.data.E[0], self.data.N[0], self.data.altitude[0],
                   c=colors.get('start', '#2ca02c'), s=60, marker='o')
        ax.scatter(self.data.E[-1], self.data.N[-1], self.data.altitude[-1],
                   c=colors.get('end', '#d62728'), s=60, marker='s')

        # Ground shadow
        ax.plot(self.data.E, self.data.N, np.zeros_like(self.data.N),
                color='gray', linewidth=0.3, alpha=0.3)

        ax.set_xlabel('E (m)', fontsize=8)
        ax.set_ylabel('N (m)', fontsize=8)
        ax.set_zlabel('Alt (m)', fontsize=8)
        ax.set_title('3D Trajectory', fontsize=self.style.title_size)
        ax.view_init(elev=25, azim=-45)
        ax.tick_params(labelsize=7)

    def _plot_ground_track(self, ax: plt.Axes) -> None:
        """Plot ground track on given axes."""
        colors = self.style.colors.get('trajectory', {})

        ax.plot(self.data.E, self.data.N,
                color=colors.get('path', '#1f77b4'),
                linewidth=1.5)
        ax.scatter(self.data.E[0], self.data.N[0],
                   c=colors.get('start', '#2ca02c'), s=50, marker='o', label='Start')
        ax.scatter(self.data.E[-1], self.data.N[-1],
                   c=colors.get('end', '#d62728'), s=50, marker='s', label='End')

        ax.set_xlabel('East (m)', fontsize=9)
        ax.set_ylabel('North (m)', fontsize=9)
        ax.set_title('Ground Track', fontsize=self.style.title_size)
        ax.set_aspect('equal', adjustable='box')
        ax.legend(fontsize=7, loc='upper left')
        self.add_grid(ax)

    def _plot_flight_stats(self, ax: plt.Axes) -> None:
        """Plot flight statistics as text."""
        ax.axis('off')
        ax.set_title('Flight Statistics', fontsize=self.style.title_size)

        # Calculate stats
        summary = self.data.get_summary()
        distance = np.sqrt((self.data.N[-1] - self.data.N[0])**2 +
                           (self.data.E[-1] - self.data.E[0])**2)
        path_length = np.sum(np.sqrt(np.diff(self.data.N)**2 +
                                      np.diff(self.data.E)**2 +
                                      np.diff(self.data.altitude)**2))

        stats_text = f"""
Duration: {self.data.duration:.1f} s
Sample Rate: {self.data.sample_rate:.0f} Hz
Samples: {self.data.n_samples}

Distance: {distance/1000:.2f} km
Path Length: {path_length/1000:.2f} km

Altitude:
  Min: {self.data.altitude.min():.1f} m
  Max: {self.data.altitude.max():.1f} m

Speed (Ground):
  Min: {self.data.V_ground.min():.1f} m/s
  Max: {self.data.V_ground.max():.1f} m/s
  Mean: {self.data.V_ground.mean():.1f} m/s
        ({self.data.V_ground.mean()*1.944:.1f} kts)

Climb Rate:
  Max: {self.data.climb_rate.max():.2f} m/s
  Min: {self.data.climb_rate.min():.2f} m/s
"""

        ax.text(0.05, 0.95, stats_text.strip(),
                transform=ax.transAxes,
                fontsize=8, fontfamily='monospace',
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    def _plot_attitude(self, ax: plt.Axes) -> None:
        """Plot attitude on given axes."""
        time = self.data.time
        colors = self.style.colors.get('attitude', {})

        ax.plot(time, self.data.phi_deg,
                color=colors.get('phi', '#d62728'),
                linewidth=1.0, label='Roll (φ)')
        ax.plot(time, self.data.theta_deg,
                color=colors.get('theta', '#ff7f0e'),
                linewidth=1.0, label='Pitch (θ)')
        ax.plot(time, self.data.psi_deg,
                color=colors.get('psi', '#9467bd'),
                linewidth=1.0, label='Yaw (ψ)')

        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.set_ylabel('Angle (deg)', fontsize=9)
        ax.set_title('Attitude (Euler Angles)', fontsize=self.style.title_size)
        ax.legend(fontsize=8, loc='upper right', ncol=3)
        self.add_grid(ax)

    def _plot_velocity_altitude(self, ax: plt.Axes) -> None:
        """Plot velocity and altitude on given axes."""
        time = self.data.time
        vel_colors = self.style.colors.get('velocity', {})
        pos_colors = self.style.colors.get('position', {})

        # Ground speed
        line1, = ax.plot(time, self.data.V_ground,
                         color=vel_colors.get('V_ground', '#17becf'),
                         linewidth=1.0, label='Ground Speed (m/s)')

        ax.set_xlabel('Time (s)', fontsize=9)
        ax.set_ylabel('Speed (m/s)', fontsize=9,
                      color=vel_colors.get('V_ground', '#17becf'))
        ax.tick_params(axis='y', labelcolor=vel_colors.get('V_ground', '#17becf'))

        # Altitude on secondary axis
        ax2 = ax.twinx()
        line2, = ax2.plot(time, self.data.altitude,
                          color=pos_colors.get('altitude', '#1f77b4'),
                          linewidth=1.0, linestyle='--', label='Altitude (m)')
        ax2.set_ylabel('Altitude (m)', fontsize=9,
                       color=pos_colors.get('altitude', '#1f77b4'))
        ax2.tick_params(axis='y', labelcolor=pos_colors.get('altitude', '#1f77b4'))

        ax.set_title('Velocity & Altitude', fontsize=self.style.title_size)
        ax.legend([line1, line2], ['Ground Speed', 'Altitude'],
                  fontsize=8, loc='upper right')
        self.add_grid(ax)

    def _plot_controls(self, ax: plt.Axes) -> None:
        """Plot control surfaces on given axes."""
        time = self.data.time
        colors = self.style.colors.get('controls', {})

        ax.plot(time, self.data.delta_a_deg,
                color=colors.get('delta_a', '#2ca02c'),
                linewidth=1.0, label='Aileron')
        ax.plot(time, self.data.delta_e_deg,
                color=colors.get('delta_e', '#17becf'),
                linewidth=1.0, label='Elevator')
        ax.plot(time, self.data.delta_r_deg,
                color=colors.get('delta_r', '#bcbd22'),
                linewidth=1.0, label='Rudder')

        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Time (s)', fontsize=9)
        ax.set_ylabel('Deflection (deg)', fontsize=9)
        ax.set_title('Control Surfaces', fontsize=self.style.title_size)
        ax.legend(fontsize=8, loc='upper right', ncol=3)
        self.add_grid(ax)

    def _plot_propulsion(self, ax: plt.Axes) -> None:
        """Plot propulsion on given axes."""
        time = self.data.time
        colors = self.style.colors.get('propulsion', {})

        # RPM
        line1, = ax.plot(time, self.data.RPM_Cl,
                         color=colors.get('RPM', '#9467bd'),
                         linewidth=1.0, label='Cruise RPM (L/R)')
        ax.plot(time, self.data.RPM_Cr,
                color=colors.get('RPM', '#9467bd'),
                linewidth=1.0, linestyle='--', alpha=0.7)

        ax.set_xlabel('Time (s)', fontsize=9)
        ax.set_ylabel('RPM', fontsize=9, color=colors.get('RPM', '#9467bd'))
        ax.tick_params(axis='y', labelcolor=colors.get('RPM', '#9467bd'))

        # Tilt on secondary axis
        ax2 = ax.twinx()
        line2, = ax2.plot(time, self.data.theta_Cl,
                          color=colors.get('tilt', '#e377c2'),
                          linewidth=1.0, label='Tilt Angle')
        ax2.plot(time, self.data.theta_Cr,
                 color=colors.get('tilt', '#e377c2'),
                 linewidth=1.0, linestyle='--', alpha=0.7)
        ax2.set_ylabel('Tilt (deg)', fontsize=9,
                       color=colors.get('tilt', '#e377c2'))
        ax2.tick_params(axis='y', labelcolor=colors.get('tilt', '#e377c2'))
        ax2.set_ylim(-5, 95)

        ax.set_title('Propulsion System', fontsize=self.style.title_size)
        ax.legend([line1, line2], ['Cruise RPM', 'Tilt Angle'],
                  fontsize=8, loc='upper right')
        self.add_grid(ax)

        # Add flight mode annotation
        mean_tilt = (self.data.theta_Cl.mean() + self.data.theta_Cr.mean()) / 2
        if mean_tilt < 10:
            mode = "CRUISE"
            mode_color = 'lightgreen'
        elif mean_tilt > 80:
            mode = "HOVER"
            mode_color = 'lightyellow'
        else:
            mode = "TRANSITION"
            mode_color = 'lightorange'

        ax.annotate(f'Mode: {mode}',
                    xy=(0.02, 0.95), xycoords='axes fraction',
                    fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor=mode_color, alpha=0.8))
