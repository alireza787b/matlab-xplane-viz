"""
Base plotter class with common functionality.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
from abc import ABC, abstractmethod

from ..flight_data import FlightData
from ..styles.themes import PlotStyle, load_style


class BasePlotter(ABC):
    """Base class for all plotters."""

    def __init__(
        self,
        flight_data: FlightData,
        style: Optional[PlotStyle] = None,
        output_dir: Optional[str] = None
    ):
        """
        Initialize plotter.

        Args:
            flight_data: FlightData instance to plot
            style: PlotStyle configuration (loads default if None)
            output_dir: Directory to save plots (optional)
        """
        self.data = flight_data
        self.style = style or load_style()
        self.output_dir = Path(output_dir) if output_dir else None

        # Apply style to matplotlib
        self.style.apply_to_matplotlib()

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str,
        subdirectory: Optional[str] = None
    ) -> Optional[Path]:
        """
        Save figure to file.

        Args:
            fig: Matplotlib figure
            filename: Base filename (without extension)
            subdirectory: Optional subdirectory within output_dir

        Returns:
            Path to saved file, or None if no output_dir set
        """
        if self.output_dir is None:
            return None

        # Build output path
        if subdirectory:
            save_dir = self.output_dir / subdirectory
        else:
            save_dir = self.output_dir

        save_dir.mkdir(parents=True, exist_ok=True)

        # Add extension
        filepath = save_dir / f"{filename}.{self.style.format}"

        # Save with tight layout
        fig.savefig(filepath, dpi=self.style.dpi, bbox_inches='tight',
                    facecolor='white', edgecolor='none')

        return filepath

    def create_figure(
        self,
        size_type: str = 'single',
        nrows: int = 1,
        ncols: int = 1,
        **kwargs
    ) -> Tuple[plt.Figure, np.ndarray]:
        """
        Create figure with standard styling.

        Args:
            size_type: Figure size type from config
            nrows, ncols: Subplot grid dimensions
            **kwargs: Additional arguments to subplots()

        Returns:
            (figure, axes array)
        """
        figsize = self.style.get_figure_size(size_type)
        fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)

        # Ensure axes is always an array
        if nrows == 1 and ncols == 1:
            axes = np.array([axes])
        elif nrows == 1 or ncols == 1:
            axes = np.atleast_1d(axes)

        return fig, axes

    def add_grid(self, ax: plt.Axes) -> None:
        """Add grid to axes with standard styling."""
        ax.grid(
            self.style.grid_visible,
            alpha=self.style.grid_alpha,
            linestyle=self.style.grid_linestyle,
            color=self.style.grid_color
        )

    def format_time_axis(self, ax: plt.Axes, show_label: bool = True) -> None:
        """Format x-axis as time."""
        if show_label:
            ax.set_xlabel('Time (s)')

    def add_legend(
        self,
        ax: plt.Axes,
        loc: str = 'best',
        framealpha: float = 0.9
    ) -> None:
        """Add legend with standard styling."""
        ax.legend(loc=loc, framealpha=framealpha,
                  fontsize=self.style.legend_size)

    @abstractmethod
    def plot(self, **kwargs) -> plt.Figure:
        """Generate the plot. Must be implemented by subclasses."""
        pass

    def plot_and_save(
        self,
        filename: str,
        subdirectory: Optional[str] = None,
        show: bool = False,
        **kwargs
    ) -> Optional[Path]:
        """
        Generate plot and save to file.

        Args:
            filename: Output filename (without extension)
            subdirectory: Subdirectory within output_dir
            show: Whether to display plot
            **kwargs: Additional arguments to plot()

        Returns:
            Path to saved file
        """
        fig = self.plot(**kwargs)

        if show:
            plt.show()

        filepath = self.save_figure(fig, filename, subdirectory)
        plt.close(fig)

        return filepath
