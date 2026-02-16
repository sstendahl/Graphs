# SPDX-License-Identifier: GPL-3.0-or-later
"""Various utility functions."""
import contextlib

from gi.repository import GLib, Graphs

from graphs import scales

import numexpr

import numpy

import sympy


def get_value_at_fraction(
    fraction: float,
    start: float,
    end: float,
    scale: int,
) -> float:
    """
    Get value at axis fraction.

    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis.
    """
    match scales.Scale(scale):
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            return start + fraction * (end - start)
        case scales.Scale.LOG:
            log_start = numpy.log10(start)
            log_end = numpy.log10(end)
            log_range = log_end - log_start
            log_value = log_start + log_range * fraction
            return pow(10, log_value)
        case scales.Scale.LOG2:
            log_start = numpy.log2(start)
            log_end = numpy.log2(end)
            log_range = log_end - log_start
            log_value = log_start + log_range * fraction
            return pow(2, log_value)
        case scales.Scale.SQUAREROOT:
            # Use min limit as defined by scales.py
            sqrt_start = max(0, numpy.sqrt(start))
            sqrt_end = numpy.sqrt(end)
            sqrt_range = sqrt_end - sqrt_start
            # Square root value does not really work for negative fractions
            sqrt_value = sqrt_start + sqrt_range * max(0, fraction)
            return sqrt_value * sqrt_value
        case scales.Scale.INVERSE:
            # Use min limit as defined by scales.py if min equals zero
            start = end / 10 if start <= 0 < end else start
            scaled_range = 1 / start - 1 / end
            return 1 / (1 / end + fraction * scaled_range)
        case _:
            raise ValueError


def get_fraction_at_value(
    value: float,
    start: float,
    end: float,
    scale: int,
) -> float:
    """
    Get fraction of axis at absolute value.

    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    match scales.Scale(scale):
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            return (value - start) / (end - start)
        case scales.Scale.LOG:
            log_start = numpy.log10(start)
            log_end = numpy.log10(end)
            log_value = numpy.log10(value)
            log_range = log_end - log_start
            return (log_value - log_start) / log_range
        case scales.Scale.LOG2:
            log_start = numpy.log2(start)
            log_end = numpy.log2(end)
            log_value = numpy.log2(value)
            log_range = log_end - log_start
            return (log_value - log_start) / log_range
        case scales.Scale.SQUAREROOT:
            # Use min limit as defined by scales.py
            start = max(0, start)
            sqrt_start = numpy.sqrt(start)
            sqrt_end = numpy.sqrt(end)
            sqrt_value = numpy.sqrt(value)
            sqrt_range = sqrt_end - sqrt_start
            return (sqrt_value - sqrt_start) / sqrt_range
        case scales.Scale.INVERSE:
            # Use min limit as defined by scales.py if min equals zero
            start = end / 10 if start <= 0 < end else start
            scaled_range = 1 / start - 1 / end

            # Calculate the scaled percentage corresponding to the data point
            scaled_data_point = 1 / value
            return (scaled_data_point - 1 / end) / scaled_range
        case _:
            raise ValueError


def create_equidistant_xdata(
    limits: tuple,
    scale: int = 1,
    steps: int = 5000,
) -> list:
    """Generate evenly-spaced x-values on the given scale."""
    x_start, x_stop = limits
    scale = scales.Scale(scale)
    match scale:
        case scales.Scale.LINEAR | scales.Scale.RADIANS:
            xdata = numpy.linspace(x_start, x_stop, steps).tolist()
        case scales.Scale.LOG:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log10(x_start),
                numpy.log10(x_stop),
                steps,
            ).tolist()
        case scales.Scale.LOG2:
            x_start = max(x_start, 1e-300)
            x_stop = x_stop if numpy.isfinite(x_stop) else 1e300
            xdata = numpy.logspace(
                numpy.log2(x_start),
                numpy.log2(x_stop),
                steps,
                base=2,
            ).tolist()
        case scales.Scale.SQUAREROOT:
            x_start = max(x_start, 1e-300)
            xdata = numpy.linspace(
                numpy.sqrt(x_start),
                numpy.sqrt(x_stop),
                steps,
            )
            xdata = (xdata**2).tolist()
        case scales.Scale.INVERSE:
            xdata = \
                (1 / numpy.linspace(1 / x_start, 1 / x_stop, steps)).tolist()
        case _:
            raise ValueError
    return xdata


def equation_to_data(
    equation: str,
    limits: tuple = None,
    steps: int = 5000,
    scale: int = 0,
) -> tuple:
    """Convert an equation into data over a specified range of x-values."""
    if limits is None:
        limits = (0, 10)
    xdata = create_equidistant_xdata(limits, scale, steps)
    try:
        ydata = numexpr.evaluate(equation + " + x*0", local_dict={"x": xdata})

        # Remove invalid values
        mask = numpy.isfinite(ydata)
        xdata = numpy.asarray(xdata)[mask]
        ydata = ydata[mask]
    except (KeyError, SyntaxError, ValueError, TypeError):
        return None, None
    return numpy.ndarray.tolist(xdata), numpy.ndarray.tolist(ydata)


def validate_equation(equation: str, limits: tuple = None) -> bool:
    """Validate whether an equation can be parsed."""
    try:
        equation = Graphs.preprocess_equation(equation)
        validate, _ = equation_to_data(equation, limits, steps=10)
        return validate is not None
    except GLib.Error:
        return False


def string_to_function(equation_name: str) -> sympy.FunctionClass:
    """Convert a string into a sympy function."""
    variables = ["x"] + Graphs.math_tools_get_free_variables(equation_name)
    sym_vars = sympy.symbols(variables)
    with contextlib.suppress(sympy.SympifyError, TypeError, SyntaxError):
        symbolic = sympy.sympify(
            equation_name,
            locals=dict(zip(variables, sym_vars)),
        )
        return sympy.lambdify(sym_vars, symbolic)
