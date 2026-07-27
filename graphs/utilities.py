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
    if b is None:
        return None
    return bytes_to_ndarray(b).tolist()


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


def item_from_dict(dictionary: dict) -> Graphs.Item:
    """Instanciate item from dict."""
    match dictionary["type"]:
        case "DataItem":
            dictionary.pop("type")
            dictionary["data"] = Graphs.DataHolder.new(*dictionary["data"])
            return Graphs.DataItem(**dictionary)
        case "GeneratedDataItem":
            dictionary.pop("type")
            dictionary["data"] = Graphs.DataHolder.new(*dictionary["data"])
            equation = Graphs.expression_to_ast(dictionary["equation"])
            dictionary["equation"] = equation
            return Graphs.GeneratedDataItem(**dictionary)
        case "EquationItem":
            dictionary.pop("type")
            equation = Graphs.expression_to_ast(dictionary["equation"])
            dictionary["equation"] = equation
            return Graphs.EquationItem(**dictionary)
        case "TextItem":
            dictionary.pop("type")
            return Graphs.TextItem(**dictionary)
        case "FillItem":
            dictionary.pop("type")
            dictionary["data"] = Graphs.FillHolder.new(*dictionary["data"])
            return Graphs.FillItem(**dictionary)
        case _:
            raise ValueError(f"could not find type {dictionary['type']}")


def item_to_dict(item: Graphs.Item) -> dict:
    """Convert an item to a dict."""
    dictionary = {
        key: item.get_property(key)
        for key in dir(item.props) if key != "typename"
    }
    item_type = item.__gtype__.name[6:]
    dictionary["type"] = item_type
    match item_type:
        case "DataItem":
            dictionary["data"] = data_holder_to_tuple(item.get_data())
        case "GeneratedDataItem":
            dictionary["data"] = data_holder_to_tuple(item.get_data())
            equation = Graphs.ast_to_expression(item.props.equation)
            dictionary["equation"] = equation
        case "EquationItem":
            equation = Graphs.ast_to_expression(item.props.equation)
            dictionary["equation"] = equation
        case "FillItem":
            dictionary["data"] = fill_holder_to_tuple(item.get_data())
    return dictionary


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
    return get_xy_data(holder)
