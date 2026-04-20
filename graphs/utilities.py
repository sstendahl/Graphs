# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
from gi.repository import GLib, Graphs

import numexpr

import numpy


def bytes_to_ndarray(b: GLib.Bytes) -> numpy.ndarray:
    """Get a readonly ndarray referencing the original data."""
    if b is None:
        return None
    return numpy.frombuffer(b.get_data(), dtype=numpy.float64)


def create_equidistant_xdata(
    limits: tuple,
    scale: Graphs.Scale = Graphs.Scale.LINEAR,
    steps: int = 5000,
) -> numpy.ndarray:
    """Generate evenly-spaced x-values on the given scale."""
    x_start, x_stop = limits
    match scale:
        case Graphs.Scale.LINEAR | Graphs.Scale.RADIANS:
            xdata = numpy.linspace(x_start, x_stop, steps)
        case Graphs.Scale.LOG:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log10(x_start),
                numpy.log10(x_stop),
                steps,
            )
        case Graphs.Scale.LOG2:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log2(x_start),
                numpy.log2(x_stop),
                steps,
                base=2,
            )
        case Graphs.Scale.SQUAREROOT:
            x_start = max(x_start, 1e-300)
            xdata = numpy.linspace(
                numpy.sqrt(x_start),
                numpy.sqrt(x_stop),
                steps,
            )
            xdata = xdata**2
        case Graphs.Scale.INVERSE:
            xdata = (1 / numpy.linspace(1 / x_start, 1 / x_stop, steps))
        case _:
            raise ValueError
    return xdata


def equation_to_data(
    equation: str,
    limits: tuple,
    steps: int = 5000,
    scale: Graphs.Scale = Graphs.Scale.LINEAR,
) -> tuple:
    """Convert an equation into data over a specified range of x-values."""
    xdata = create_equidistant_xdata(limits, scale, steps)
    try:
        ydata = numexpr.evaluate(equation, local_dict={"x": xdata})
        if ydata.ndim == 0:
            ydata = numpy.full(steps, ydata)

        # Remove invalid values
        mask = numpy.isfinite(ydata)
        xdata = xdata[mask]
        ydata = ydata[mask]
    except (KeyError, SyntaxError, ValueError, TypeError):
        return None, None
    return xdata, ydata
