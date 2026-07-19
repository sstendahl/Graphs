# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
from gi.repository import GLib, Graphs

import numpy


def bytes_to_ndarray(b: GLib.Bytes) -> numpy.ndarray:
    """Get a readonly ndarray referencing the original data."""
    if b is None:
        return None
    return numpy.frombuffer(b.get_data(), dtype=numpy.float64)


def bytes_to_list(b: GLib.Bytes) -> list[float]:
    ndarray = bytes_to_ndarray(b)
    if ndarray is None:
        return None
    return ndarray.tolist()


def get_xy_data(
    holder: Graphs.DataHolder,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Get x and y data in numpy format from a DataHolder."""
    xdata = bytes_to_ndarray(holder.get_xdata_b())
    ydata = bytes_to_ndarray(holder.get_ydata_b())
    return xdata, ydata


def get_xy_err(
    holder: Graphs.DataHolder,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Get x and y err in numpy format from a DataHolder."""
    xerr = bytes_to_ndarray(holder.get_xerr_b())
    yerr = bytes_to_ndarray(holder.get_yerr_b())
    return xerr, yerr


def data_holder_to_tuple(holder: Graphs.DataHolder) -> tuple[list, list, list, list]:
    """Get the data as a picklable tuple."""
    return (
        bytes_to_list(holder.get_xdata_b()),
        bytes_to_list(holder.get_ydata_b()),
        bytes_to_list(holder.get_xerr_b()),
        bytes_to_list(holder.get_yerr_b()),
    )


def fill_holder_to_tuple(holder: Graphs.FillHolder) -> tuple[list, list, list]:
    """Get the data as a picklable tuple."""
    return (
        bytes_to_list(holder.get_xdata_b()),
        bytes_to_list(holder.get_lower_b()),
        bytes_to_list(holder.get_upper_b()),
    )


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
