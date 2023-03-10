# SPDX-License-Identifier: GPL-3.0-or-later
import numpy
from numpy import *


def create_dataset(x_start, x_stop, equation, step_size, name):
    """
    Create all data set parameters that are required
    to create a new data object
    """
    dataset = {}
    if name == "":
        name = f"Y = {str(equation)}"
    dataset["name"] = name
    datapoints = int(abs(eval(x_start) - eval(x_stop)) / eval(step_size))
    xdata = numpy.linspace(eval(x_start), eval(x_stop), datapoints)
    equation = equation.replace("X", "xdata")
    equation = str(equation.replace("^", "**"))
    equation += " + xdata*0"
    dataset["ydata"] = eval(equation)
    dataset["xdata"] = numpy.ndarray.tolist(xdata)
    return dataset


def operation(xdata, ydata, input_x, input_y):
    x_array = []
    y_array = []
    X_range = xdata
    Y_Range = ydata
    operations = []
    for xy_operation in [input_x, input_y]:
        xy_operation = xy_operation.replace("Y_range", "y_range")
        xy_operation = xy_operation.replace("X_range", "x_range")
        xy_operation = xy_operation.replace("Y", "ydata[index[0]]")
        xy_operation = xy_operation.replace("X", "xdata[index[0]]")
        xy_operation = xy_operation.replace("y_range", "Y_range")
        xy_operation = xy_operation.replace("x_range", "X_range")
        xy_operation = xy_operation.replace("^", "**")
        operations.append(xy_operation)
    for index in enumerate(xdata):
        x_array.append(eval(operations[0]))
        y_array.append(eval(operations[1]))
    return x_array, y_array
