# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
from gi.repository import GLib, Graphs

import numpy


def bytes_to_ndarray(b: GLib.Bytes) -> numpy.ndarray:
    """Get a readonly ndarray referencing the original data."""
    if b is None:
        return None
    return numpy.frombuffer(b.get_data(), dtype=numpy.float64)


def get_xy_data(
    holder: Graphs.DataHolder,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Get x and y data in numpy format from a DataHolder."""
    xdata = bytes_to_ndarray(holder.get_xdata_b())
    ydata = bytes_to_ndarray(holder.get_ydata_b())
    return xdata, ydata


def equation_to_data(
    equation: Graphs.Expression,
    limits: tuple[float, float],
    steps: int = 5000,
    scale: Graphs.Scale = Graphs.Scale.LINEAR,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Evaluate an equation."""
    holder = Graphs.math_tools_equation_to_data(
        equation,
        limits[0],
        limits[1],
        steps,
        scale,
    )
    return get_xy_data(holder)
