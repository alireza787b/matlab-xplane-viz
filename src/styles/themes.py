"""
Plot styling and theme management.
"""

import yaml
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PlotStyle:
    """Container for plot styling configuration."""

    # Figure settings
    dpi: int = 300
    format: str = 'png'

    # Figure sizes
    figure_sizes: Dict[str, tuple] = field(default_factory=lambda: {
        'single': (10, 6),
        'multi_panel': (12, 10),
        'dashboard': (16, 12),
        'trajectory_3d': (12, 10),
        'animation_frame': (10, 8),
    })

    # Font settings
    font_family: str = 'DejaVu Sans'
    title_size: int = 14
    label_size: int = 12
    tick_size: int = 10
    legend_size: int = 10

    # Grid settings
    grid_visible: bool = True
    grid_alpha: float = 0.3
    grid_linestyle: str = '--'
    grid_color: str = '#888888'

    # Line widths
    line_width_main: float = 1.5
    line_width_secondary: float = 1.0
    line_width_reference: float = 0.8

    # Color palettes
    colors: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'PlotStyle':
        """Create PlotStyle from configuration dictionary."""
        style = cls()

        plot_config = config.get('plot', {})
        style.dpi = plot_config.get('dpi', style.dpi)
        style.format = plot_config.get('format', style.format)

        # Figure sizes
        fig_sizes = plot_config.get('figure_sizes', {})
        for key, value in fig_sizes.items():
            style.figure_sizes[key] = tuple(value)

        # Fonts
        fonts = plot_config.get('fonts', {})
        style.font_family = fonts.get('family', style.font_family)
        style.title_size = fonts.get('title_size', style.title_size)
        style.label_size = fonts.get('label_size', style.label_size)
        style.tick_size = fonts.get('tick_size', style.tick_size)
        style.legend_size = fonts.get('legend_size', style.legend_size)

        # Grid
        grid = plot_config.get('grid', {})
        style.grid_visible = grid.get('visible', style.grid_visible)
        style.grid_alpha = grid.get('alpha', style.grid_alpha)
        style.grid_linestyle = grid.get('linestyle', style.grid_linestyle)
        style.grid_color = grid.get('color', style.grid_color)

        # Line widths
        lw = plot_config.get('line_width', {})
        style.line_width_main = lw.get('main', style.line_width_main)
        style.line_width_secondary = lw.get('secondary', style.line_width_secondary)
        style.line_width_reference = lw.get('reference', style.line_width_reference)

        # Colors
        style.colors = config.get('colors', {})

        return style

    def apply_to_matplotlib(self) -> None:
        """Apply style settings to matplotlib defaults."""
        plt.rcParams.update({
            'font.family': self.font_family,
            'font.size': self.label_size,
            'axes.titlesize': self.title_size,
            'axes.labelsize': self.label_size,
            'xtick.labelsize': self.tick_size,
            'ytick.labelsize': self.tick_size,
            'legend.fontsize': self.legend_size,
            'figure.dpi': self.dpi,
            'savefig.dpi': self.dpi,
            'axes.grid': self.grid_visible,
            'grid.alpha': self.grid_alpha,
            'grid.linestyle': self.grid_linestyle,
            'grid.color': self.grid_color,
            'lines.linewidth': self.line_width_main,
        })

    def get_color(self, category: str, variable: str) -> str:
        """Get color for a specific variable."""
        if category in self.colors and variable in self.colors[category]:
            return self.colors[category][variable]
        # Fallback colors
        fallback = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        return fallback[hash(variable) % len(fallback)]

    def get_figure_size(self, size_type: str) -> tuple:
        """Get figure size by type."""
        return self.figure_sizes.get(size_type, (10, 6))


def load_style(config_path: Optional[str] = None) -> PlotStyle:
    """
    Load plot style from configuration file.

    Args:
        config_path: Path to YAML config file. If None, uses default.

    Returns:
        PlotStyle instance
    """
    if config_path is None:
        # Find default config
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'default.yaml'

    config_path = Path(config_path)
    if not config_path.exists():
        print(f"Warning: Config not found at {config_path}, using defaults")
        return PlotStyle()

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return PlotStyle.from_config(config)


def setup_publication_style() -> None:
    """Configure matplotlib for publication-quality figures."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
        'axes.linewidth': 0.8,
        'lines.linewidth': 1.2,
        'patch.linewidth': 0.8,
    })
