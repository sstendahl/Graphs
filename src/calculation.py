# SPDX-License-Identifier: GPL-3.0-or-later
from graphs import utilities

import numexpr

import numpy


def create_dataset(x_start: float, x_stop: float, equation, step_size: float):
    """Create a new dataset with given start, stop and step size."""
    datapoints = int(abs(x_start - x_stop) / step_size) + 1
    xdata = numpy.linspace(x_start, x_stop, datapoints)
    equation = utilities.preprocess(equation).replace("x", "xdata")
    equation += " + xdata*0"
    ydata = numpy.ndarray.tolist(numexpr.evaluate(equation))
    xdata = numpy.ndarray.tolist(xdata)
    return xdata, ydata


def operation(x, y, input_x: str, input_y: str):
    """Perform custom transformation on given x- and y-data"""
    x_min, x_max = min(x), max(x)
    y_min, y_max = min(y), max(y)
    return (
        numexpr.evaluate(utilities.preprocess(input_x) + "+ 0*x"),
        numexpr.evaluate(utilities.preprocess(input_y) + "+ 0*y"),
    ))
