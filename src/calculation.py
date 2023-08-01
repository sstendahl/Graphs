# SPDX-License-Identifier: GPL-3.0-or-later
import numexpr

import numpy
from numpy import *

from graphs import utilities


def create_dataset(x_start: float, x_stop: float, equation, step_size: float):
    """
    Create all data set parameters that are required
    to create a new data object
    """
    datapoints = int(abs(x_start - x_stop) / step_size) + 1
    xdata = numpy.linspace(x_start, x_stop, datapoints)
    equation = utilities.preprocess(equation).replace("x", "xdata")
    equation += " + xdata*0"
    ydata = numpy.ndarray.tolist(numexpr.evaluate(equation))
    xdata = numpy.ndarray.tolist(xdata)
    return xdata, ydata


def operation(xdata, ydata, input_x, input_y):
    x_array = []
    y_array = []
    x_range = xdata
    y_range = ydata
    operations = []
    for xy_operation in [input_x, input_y]:
        xy_operation = xy_operation.replace("Y_range", "y_range")
        xy_operation = xy_operation.replace("X_range", "x_range")
        xy_operation = xy_operation.replace("Y", "ydata[_index[0]]")
        xy_operation = xy_operation.replace("X", "xdata[_index[0]]")
        xy_operation = xy_operation.replace("^", "**")
        operations.append(xy_operation)
    for _index in enumerate(xdata):
        x_array.append(eval(operations[0]))
        y_array.append(eval(operations[1]))
    return x_array, y_array
