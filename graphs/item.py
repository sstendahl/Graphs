# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import RcParams

import numpy


class _PythonItemMixin:

    def reset(
        self,
        old_style: tuple[RcParams, dict],
        new_style: tuple[RcParams, dict],
    ) -> None:
        """Reset all properties."""
        if not hasattr(self, "_style_properties"):
            return
        # Combine rcparams and graphs_params into single dict:
        old_style = old_style[0] | old_style[1]
        new_style = new_style[0] | new_style[1]
        for prop, (key, function) in self._style_properties.items():
            old_value = old_style[key]
            new_value = new_style[key]
            if function is not None:
                old_value = function(old_value)
                new_value = function(new_value)
            if self.get_property(prop) == old_value:
                self.set_property(prop, new_value)

    def override(
        self,
        style: tuple[RcParams, dict],
    ) -> None:
        """Override all properties."""
        if not hasattr(self, "_style_properties"):
            return
        # Combine rcparams and graphs_params into single dict:
        style = style[0] | style[1]
        for prop, (key, function) in self._style_properties.items():
            value = style[key] if function is None else function(style[key])
            self.set_property(prop, value)

    @staticmethod
    def _extract_params(
        cls,
        style: tuple[RcParams, dict],
        kwargs: dict,
    ) -> dict:
        style = style[0] | style[1]  # Add graphs_params to style dict
        return {
            prop: style[key] if function is None else function(style[key])
            for prop, (key, function) in cls._style_properties.items()
            if prop not in kwargs
        }

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

    _style_properties = {
        "errbarsabove": ("errorbar.barsabove", None),
        "errcapsize": ("errorbar.capsize", None),
        "errcapthick": ("errorbar.capthick", None),
        "errlinewidth": ("errorbar.linewidth", None),
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
        "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
        "markersize": ("lines.markersize", None),
    }

    @classmethod
    def new(
        cls,
        style: tuple[RcParams, dict],
        xdata: list[float] = None,
        ydata: list[float] = None,
        xerr: list[float] = None,
        yerr: list[float] = None,
        **kwargs,
    ):
        """Create new DataItem."""
        data = Graphs.DataHolder.new(xdata, ydata, xerr, yerr)
        return cls.new_with_data(style, data, **kwargs)

    @classmethod
    def new_with_data(
        cls,
        style: tuple[RcParams, dict],
        data: Graphs.DataHolder,
        **kwargs,
    ):
        """Create new DataItem with a DataHolder."""
        return cls(
            data=data,
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )

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
            None if (xerr := self.get_xerr()) is None else xerr.tolist(),
            None if (yerr := self.get_yerr()) is None else yerr.tolist(),
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
        style: tuple[RcParams, dict],
        equation: str,
        xstart: str,
        xstop: str,
        steps: int,
        scale: Graphs.Scale,
        **kwargs,
    ):
        """Create new GeneratedDataItem."""
        return cls(
            equation=equation,
            xstart=xstart,
            xstop=xstop,
            steps=steps,
            scale=scale,
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._regenerate()
        for prop in ("equation", "xstart", "xstop", "steps", "scale"):
            self.connect("notify::" + prop, self._regenerate)

    def _regenerate(self, *_args) -> None:
        """Regenerate Data."""
        xdata, ydata = utilities.equation_to_data(
            Graphs.preprocess_equation(self.props.equation),
            [
                Graphs.evaluate_string(self.props.xstart),
                Graphs.evaluate_string(self.props.xstop),
            ],
            self.props.steps,
            self.props.scale,
        )
        self.props.data = Graphs.DataHolder.new(xdata, ydata, None, None)


class EquationItem(Graphs.EquationItem, _PythonItemMixin):
    """EquationItem."""

    __gtype_name__ = "GraphsPythonEquationItem"

    _style_properties = {
        "linestyle": (
            "lines.linestyle",
            lambda x: max(misc.LINESTYLES.index(x) - 1, 0),
        ),
        "linewidth": ("lines.linewidth", None),
    }

    @classmethod
    def new(cls, style: tuple[RcParams, dict], equation: str, **kwargs):
        """Create new EquationItem."""
        return cls(
            equation=equation,
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )


class TextItem(Graphs.TextItem, _PythonItemMixin):
    """TextItem."""

    __gtype_name__ = "GraphsPythonTextItem"

    _style_properties = {
        "size": ("font.size", None),
        "color": ("text.color", None),
    }

    @classmethod
    def new(
        cls,
        style: tuple[RcParams, dict],
        xanchor: float = 0,
        yanchor: float = 0,
        text: str = "",
        **kwargs,
    ):
        """Create new textItem."""
        return cls(
            xanchor=xanchor,
            yanchor=yanchor,
            text=text,
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )


class FillItem(Graphs.FillItem, _PythonItemMixin):
    """FillItem."""

    __gtype_name__ = "GraphsPythonFillItem"

    data = GObject.Property(type=object)

    @classmethod
    def new(
        cls,
        _params: tuple[RcParams, dict],
        data: tuple[list[float], list[float], list[float]],
        **kwargs,
    ):
        """Create new FillItem."""
        return cls(data=data, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = ([], [], [])

    def get_data_tuple(self) -> tuple[list, list, list]:
        """Get the data as a picklable tuple."""
        return self.props.data

    def set_data_tuple(self, data: tuple[list, list, list]) -> None:
        """Set the data from a tuple."""
        self.props.data = data


class ItemFactory(Graphs.ItemFactory):
    """Item factory."""

    _constructors = {
        "data-item": DataItem.new_with_data,
        "generated-data-item": GeneratedDataItem.new,
        "equation-item": EquationItem.new,
        "text-item": TextItem.new,
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
                return GeneratedDataItem(**dictionary)
            case "EquationItem":
                cls = EquationItem
            case "TextItem":
                cls = TextItem
            case "FillItem":
                cls = FillItem
            case _:
                raise ValueError(f"could not find type {dictionary['type']}")
        dictionary.pop("type")
        return cls(**dictionary)

    @staticmethod
    def _on_request(self, data: Graphs.Data, *args) -> Graphs.Item:
        *args, callback = args
        return callback(data.get_selected_style_params(), *args)
