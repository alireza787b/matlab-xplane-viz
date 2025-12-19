"""
Control surfaces plotter.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import Optional

from .base import BasePlotter
from ..flight_data import FlightData
from ..styles.themes import PlotStyle


class ControlsPlotter(BasePlotter):
    """Plotter for control surface and propulsion data."""

    def plot(self, **kwargs) -> plt.Figure:
        """Generate complete controls plot."""
        return self.plot_all_controls()

    def plot_all_controls(self) -> plt.Figure:
        """Create comprehensive control surfaces and propulsion plot."""
        fig, axes = self.create_figure('multi_panel', nrows=3, ncols=1)
        fig.suptitle('Control Inputs & Propulsion',
                     fontsize=self.style.title_size + 2, fontweight='bold')

        self._plot_control_surfaces(axes[0])
        self._plot_propulsion_rpm(axes[1])
        self._plot_propulsion_tilt(axes[2])

        # Only show x-label on bottom
        for ax in axes[:-1]:
            ax.set_xlabel('')
            ax.tick_params(labelbottom=False)

        plt.tight_layout()
        return fig

    def plot_control_surfaces(self) -> plt.Figure:
        """Create control surfaces only plot."""
        fig, axes = self.create_figure('single', nrows=3, ncols=1, sharex=True)
        fig.suptitle('Control Surface Deflections', fontsize=self.style.title_size + 2)

        time = self.data.time
        colors = self.style.colors.get('controls', {})

        # Aileron
        axes[0].plot(time, self.data.delta_a_deg,
                     color=colors.get('delta_a', '#2ca02c'),
                     linewidth=self.style.line_width_main,
                     label='Aileron (δa)')
        axes[0].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[0].set_ylabel('Aileron (deg)')
        axes[0].set_ylim(-35, 35)
        self.add_grid(axes[0])
        self.add_legend(axes[0])

        # Elevator
        axes[1].plot(time, self.data.delta_e_deg,
                     color=colors.get('delta_e', '#17becf'),
                     linewidth=self.style.line_width_main,
                     label='Elevator (δe)')
        axes[1].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[1].set_ylabel('Elevator (deg)')
        self.add_grid(axes[1])
        self.add_legend(axes[1])

        # Add note about large trim
        mean_elev = self.data.delta_e_deg.mean()
        if abs(mean_elev) > 20:
            axes[1].annotate(f'Mean trim: {mean_elev:.1f}°',
                             xy=(0.98, 0.95), xycoords='axes fraction',
                             fontsize=self.style.tick_size,
                             ha='right', va='top',
                             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

        # Rudder
        axes[2].plot(time, self.data.delta_r_deg,
                     color=colors.get('delta_r', '#bcbd22'),
                     linewidth=self.style.line_width_main,
                     label='Rudder (δr)')
        axes[2].axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        axes[2].set_ylabel('Rudder (deg)')
        axes[2].set_xlabel('Time (s)')
        axes[2].set_ylim(-35, 35)
        self.add_grid(axes[2])
        self.add_legend(axes[2])

        plt.tight_layout()
        return fig

    def plot_propulsion(self) -> plt.Figure:
        """Create propulsion-only plot."""
        fig, axes = self.create_figure('single', nrows=2, ncols=1, sharex=True)
        fig.suptitle('Propulsion System', fontsize=self.style.title_size + 2)

        time = self.data.time
        colors = self.style.colors.get('propulsion', {})

        # RPM
        axes[0].plot(time, self.data.RPM_Cl,
                     color=colors.get('RPM', '#9467bd'),
                     linewidth=self.style.line_width_main,
                     label='Left Cruise RPM')
        axes[0].plot(time, self.data.RPM_Cr,
                     color='#e377c2',
                     linewidth=self.style.line_width_main,
                     linestyle='--',
                     label='Right Cruise RPM')
        axes[0].set_ylabel('RPM')
        self.add_grid(axes[0])
        self.add_legend(axes[0])

        # Tilt angles
        axes[1].plot(time, self.data.theta_Cl,
                     color=colors.get('tilt', '#e377c2'),
                     linewidth=self.style.line_width_main,
                     label='Left Tilt')
        axes[1].plot(time, self.data.theta_Cr,
                     color='#9467bd',
                     linewidth=self.style.line_width_main,
                     linestyle='--',
                     label='Right Tilt')
        axes[1].set_ylabel('Tilt Angle (deg)')
        axes[1].set_xlabel('Time (s)')
        axes[1].set_ylim(-5, 95)
        self.add_grid(axes[1])
        self.add_legend(axes[1])

        # Add labels for flight mode
        mean_tilt = (self.data.theta_Cl.mean() + self.data.theta_Cr.mean()) / 2
        if mean_tilt < 10:
            mode = "CRUISE MODE (Tilt = 0°)"
        elif mean_tilt > 80:
            mode = "HOVER MODE (Tilt = 90°)"
        else:
            mode = f"TRANSITION MODE (Tilt ≈ {mean_tilt:.0f}°)"

        axes[1].annotate(mode,
                         xy=(0.02, 0.95), xycoords='axes fraction',
                         fontsize=self.style.tick_size,
                         fontweight='bold',
                         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

        plt.tight_layout()
        return fig

    def _plot_control_surfaces(self, ax: plt.Axes) -> None:
        """Plot control surfaces on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('controls', {})

        ax.plot(time, self.data.delta_a_deg,
                color=colors.get('delta_a', '#2ca02c'),
                linewidth=self.style.line_width_main,
                label='Aileron (δa)')
        ax.plot(time, self.data.delta_e_deg,
                color=colors.get('delta_e', '#17becf'),
                linewidth=self.style.line_width_main,
                label='Elevator (δe)')
        ax.plot(time, self.data.delta_r_deg,
                color=colors.get('delta_r', '#bcbd22'),
                linewidth=self.style.line_width_main,
                label='Rudder (δr)')

        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_ylabel('Deflection (deg)')
        ax.set_title('Control Surfaces', fontsize=self.style.title_size)
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')

    def _plot_propulsion_rpm(self, ax: plt.Axes) -> None:
        """Plot propulsion RPM on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('propulsion', {})

        ax.plot(time, self.data.RPM_Cl,
                color=colors.get('RPM', '#9467bd'),
                linewidth=self.style.line_width_main,
                label='Left Cruise')
        ax.plot(time, self.data.RPM_Cr,
                color='#e377c2',
                linewidth=self.style.line_width_main,
                linestyle='--',
                label='Right Cruise')

        ax.set_ylabel('RPM')
        ax.set_title('Cruise Propeller RPM', fontsize=self.style.title_size)
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')

    def _plot_propulsion_tilt(self, ax: plt.Axes) -> None:
        """Plot propulsion tilt angles on a single axes."""
        time = self.data.time
        colors = self.style.colors.get('propulsion', {})

        ax.plot(time, self.data.theta_Cl,
                color=colors.get('tilt', '#e377c2'),
                linewidth=self.style.line_width_main,
                label='Left Tilt')
        ax.plot(time, self.data.theta_Cr,
                color='#9467bd',
                linewidth=self.style.line_width_main,
                linestyle='--',
                label='Right Tilt')

        ax.axhline(y=0, color='green', linestyle=':', alpha=0.7, label='Cruise (0°)')
        ax.axhline(y=90, color='red', linestyle=':', alpha=0.7, label='Hover (90°)')

        ax.set_ylabel('Tilt Angle (deg)')
        ax.set_xlabel('Time (s)')
        ax.set_ylim(-5, 95)
        ax.set_title('Propeller Tilt Angle', fontsize=self.style.title_size)
        self.add_grid(ax)
        self.add_legend(ax, loc='upper right')
