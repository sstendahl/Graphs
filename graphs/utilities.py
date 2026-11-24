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
    """Get a python list as copy of the original data."""
    if b is None:
        return None
    return bytes_to_ndarray(b).tolist()


def get_xydata(
    holder: Graphs.DataHolder,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Get x and y data in numpy format from a DataHolder."""
    xdata = bytes_to_ndarray(holder.get_xdata_b())
    ydata = bytes_to_ndarray(holder.get_ydata_b())
    return xdata, ydata


def get_xyerr(
    holder: Graphs.DataHolder,
) -> tuple[numpy.ndarray, numpy.ndarray]:
    """Get x and y err in numpy format from a DataHolder."""
    xerr = bytes_to_ndarray(holder.get_xerr_b())
    yerr = bytes_to_ndarray(holder.get_yerr_b())
    return xerr, yerr


def equation_to_data(
    equation: Graphs.Ast,
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
    return get_xydata(holder)


def value_to_gvariant(value) -> GLib.Variant:
    """Convert a value to a GVariant."""
    if isinstance(value, dict):
        dictionary = {
            key: value_to_gvariant(val)
            for key, val in value.items()
        }
        return GLib.Variant("a{sv}", dictionary)
    elif isinstance(value, (tuple, list)):
        if len(value) == 4:
            # DataHolder
            return GLib.Variant("(adadmadmad)", value)
        elif len(value) == 3:
            # FillHolder
            return GLib.Variant("(adadad)", value)
    elif isinstance(value, bool):
        return GLib.Variant("b", value)
    elif isinstance(value, int):
        return GLib.Variant("i", value)
    elif isinstance(value, float):
        return GLib.Variant("d", value)
    elif isinstance(value, str):
        return GLib.Variant("s", value)
    else:
        raise TypeError(f"Unsupported type: {type(value).__name__}")
