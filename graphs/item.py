# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import Graphs

from graphs import utilities

import numpy


class _PythonItemMixin:
    def to_dict(self) -> dict:
        """Convert item to dict."""
        dictionary = {
            key: self.get_property(key)
            for key in dir(self.props) if key != "typename"
        }
        dictionary["type"] = self.__gtype_name__[12:]
        return dictionary


class DataItem(Graphs.DataItem, _PythonItemMixin):
    """DataItem."""

    __gtype_name__ = "GraphsPythonDataItem"

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        xdata: list[float] = None,
        ydata: list[float] = None,
        xerr: list[float] = None,
        yerr: list[float] = None,
    ):
        """Create new DataItem."""
        data = Graphs.DataHolder.new(xdata, ydata, xerr, yerr)
        return cls.new_with_data(style, data)

    @classmethod
    def new_with_data(
        cls,
        style: Graphs.StyleParameters,
        data: Graphs.DataHolder,
    ):
        """Create new DataItem with a DataHolder."""
        inst = cls(data=data)
        inst.override(style)
        return inst

    def to_dict(self) -> dict:
        """Convert item to dict."""
        dictionary = super().to_dict()
        dictionary["data"] = self.get_data_tuple()
        return dictionary

    def get_data_tuple(self) -> tuple[list, list, list, list]:
        """Get the data as a picklable tuple."""
        return (
            self.get_xdata().tolist(),
            self.get_ydata().tolist(),
            self.get_xerr().tolist() if self.has_xerr() else None,
            self.get_yerr().tolist() if self.has_yerr() else None,
        )

    def set_data_tuple(self, data: tuple[list, list, list, list]) -> None:
        """Set the data from a tuple."""
        self.props.data = Graphs.DataHolder.new(*data)

    def get_xydata(self) -> tuple[numpy.ndarray, numpy.ndarray]:
        """Get x- and y-data."""
        return self.get_xdata(), self.get_ydata()

    def set_xydata(self, xydata: tuple[numpy.ndarray, numpy.ndarray]) -> None:
        """Set x- and y-data."""
        self.set_data_tuple((*xydata, self.get_xerr(), self.get_yerr()))

    def get_xdata(self) -> numpy.ndarray:
        """Get xdata."""
        return utilities.bytes_to_ndarray(self.props.data.get_xdata_b())

    def get_ydata(self) -> numpy.ndarray:
        """Get ydata."""
        return utilities.bytes_to_ndarray(self.props.data.get_ydata_b())

    def get_xerr(self) -> numpy.ndarray:
        """Get xerr."""
        return utilities.bytes_to_ndarray(self.props.data.get_xerr_b())

    def get_yerr(self) -> numpy.ndarray:
        """Get yerr."""
        return utilities.bytes_to_ndarray(self.props.data.get_yerr_b())


class GeneratedDataItem(Graphs.GeneratedDataItem, DataItem):
    """Generated Dataitem."""

    __gtype_name__ = "GraphsPythonGeneratedDataItem"

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        equation: Graphs.Expression,
        xstart: str,
        xstop: str,
        steps: int,
        scale: Graphs.Scale,
    ):
        """Create new GeneratedDataItem."""
        inst = cls(
            equation=equation,
            xstart=xstart,
            xstop=xstop,
            steps=steps,
            scale=scale,
        )
        inst.override(style)
        return inst

    def to_dict(self) -> dict:
        """Convert item to dict."""
        dictionary = super().to_dict()
        dictionary["equation"] = Graphs.ast_to_expression(self.props.equation)
        return dictionary


class EquationItem(Graphs.EquationItem, _PythonItemMixin):
    """EquationItem."""

    __gtype_name__ = "GraphsPythonEquationItem"

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        equation: Graphs.Expression,
    ):
        """Create new EquationItem."""
        inst = cls(equation=equation)
        inst.override(style)
        return inst

    def to_dict(self) -> dict:
        """Convert item to dict."""
        dictionary = super().to_dict()
        dictionary["equation"] = Graphs.ast_to_expression(self.props.equation)
        return dictionary


class TextItem(Graphs.TextItem, _PythonItemMixin):
    """TextItem."""

    __gtype_name__ = "GraphsPythonTextItem"

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        xanchor: float = 0,
        yanchor: float = 0,
        text: str = "",
    ):
        """Create new textItem."""
        inst = cls(
            xanchor=xanchor,
            yanchor=yanchor,
            text=text,
        )
        inst.override(style)
        return inst


class FillItem(Graphs.FillItem, _PythonItemMixin):
    """FillItem."""

    __gtype_name__ = "GraphsPythonFillItem"

    @classmethod
    def new(
        cls,
        params: Graphs.StyleParameters,
        data: tuple[list[float], list[float], list[float]],
    ):
        """Create new FillItem."""
        data = Graphs.FillHolder.new(*data)
        return cls.new_with_data(params, data)

    @classmethod
    def new_with_data(
        cls,
        _params: Graphs.StyleParameters,
        data: Graphs.FillHolder,
    ):
        """Create new FillItem."""
        return cls(data=data)

    def get_data_tuple(self) -> tuple[list, list, list]:
        """Get the data as a picklable tuple."""
        return (
            utilities.bytes_to_ndarray(self.props.data.get_xdata_b()),
            utilities.bytes_to_ndarray(self.props.data.get_lower_b()),
            utilities.bytes_to_ndarray(self.props.data.get_upper_b()),
        )

    def set_data_tuple(self, data: tuple[list, list, list]) -> None:
        """Set the data from a tuple."""
        self.props.data = Graphs.FillHolder.new(*data)


class ItemFactory(Graphs.ItemFactory):
    """Item factory."""

    _constructors = {
        "data-item": DataItem.new_with_data,
        "generated-data-item": GeneratedDataItem.new,
        "equation-item": EquationItem.new,
        "text-item": TextItem.new,
        "fill-item": FillItem.new_with_data,
    }

    def __init__(self):
        super().__init__()
        for item, callback in self._constructors.items():
            self.connect(item + "-request", self._on_request, callback)

    @staticmethod
    def new_from_dict(dictionary: dict) -> Graphs.Item:
        """Instanciate item from dict."""
        match dictionary["type"]:
            case "DataItem":
                dictionary.pop("type")
                dictionary["data"] = Graphs.DataHolder.new(*dictionary["data"])
                return DataItem(**dictionary)
            case "GeneratedDataItem":
                dictionary.pop("type")
                dictionary["data"] = Graphs.DataHolder.new(*dictionary["data"])
                equation = Graphs.expression_to_ast(dictionary["equation"])
                dictionary["equation"] = equation
                return GeneratedDataItem(**dictionary)
            case "EquationItem":
                dictionary.pop("type")
                equation = Graphs.expression_to_ast(dictionary["equation"])
                dictionary["equation"] = equation
                return EquationItem(**dictionary)
            case "TextItem":
                dictionary.pop("type")
                return TextItem(**dictionary)
            case "FillItem":
                dictionary.pop("type")
                dictionary["data"] = Graphs.FillHolder.new(*dictionary["data"])
                return FillItem(**dictionary)
            case _:
                raise ValueError(f"could not find type {dictionary['type']}")

    @staticmethod
    def _on_request(self, *args) -> Graphs.Item:
        *args, callback = args
        return callback(*args)
