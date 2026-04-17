# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import GLib, GObject, Graphs

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

    data = GObject.Property(type=object)

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
        return cls(
            data=(xdata, ydata, xerr, yerr),
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = ([], [], None, None)

    def get_xydata(self) -> tuple[list, list]:
        """Get x- and y-data."""
        return self.props.data[:2]

    def set_xydata(self, xydata: tuple[list, list]) -> None:
        """Set x- and y-data."""
        self.props.data = xydata + self.props.data[2:]

    def get_xdata(self) -> list:
        """Get xdata."""
        return self.props.data[0]

    def get_ydata(self) -> list:
        """Get ydata."""
        return self.props.data[1]

    def get_xerr(self) -> list:
        """Get xerr."""
        return self.props.data[2]

    def get_yerr(self) -> list:
        """Get yerr."""
        return self.props.data[3]


class GeneratedDataItem(Graphs.GeneratedDataItem, DataItem):
    """Generated Dataitem."""

    __gtype_name__ = "GraphsPythonGeneratedDataItem"

    # we cannot inherit properties from a mixin
    data = GObject.Property(type=object)

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
        self.props.data = utilities.equation_to_data(
            Graphs.preprocess_equation(self.props.equation),
            [
                Graphs.evaluate_string(self.props.xstart),
                Graphs.evaluate_string(self.props.xstop),
            ],
            self.props.steps,
            self.props.scale,
        ) + (None, None)


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
            self.props.data = (None, None, None)


class ItemFactory(Graphs.ItemFactory):
    """Item factory."""

    _default_new = {
        "generated-data-item": GeneratedDataItem,
        "equation-item": EquationItem,
        "text-item": TextItem,
    }

    def __init__(self):
        super().__init__()
        for item, cls in self._default_new.items():
            self.connect(item + "-request", self._on_request, cls)
        self.connect("data-item-request", self._on_data_item_request)

    @staticmethod
    def new_from_dict(dictionary: dict) -> Graphs.Item:
        """Instanciate item from dict."""
        match dictionary["type"]:
            case "DataItem":
                cls = DataItem
            case "GeneratedDataItem":
                cls = GeneratedDataItem
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
        *args, cls = args
        return cls.new(data.get_selected_style_params(), *args)

    @staticmethod
    def _bytes_to_list(b: GLib.Bytes) -> list[float]:
        if b is None:
            return None
        return numpy.frombuffer(b.get_data(), dtype=numpy.float64).tolist()

    @staticmethod
    def _on_data_item_request(
        self,
        data: Graphs.Data,
        xdata: GLib.Bytes,
        ydata: GLib.Bytes,
        xerr: GLib.Bytes,
        yerr: GLib.Bytes,
    ) -> Graphs.DataItem:
        return DataItem.new(
            data.get_selected_style_params(),
            self._bytes_to_list(xdata),
            self._bytes_to_list(ydata),
            self._bytes_to_list(xerr),
            self._bytes_to_list(yerr),
        )
