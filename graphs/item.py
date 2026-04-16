# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import GLib, GObject, Graphs

from graphs import misc, utilities

from matplotlib import RcParams

import numpy


class DataItem(Graphs.DataItem):
    """DataItem."""

    __gtype_name__ = "GraphsPythonDataItem"

    data = GObject.Property(type=object)

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


class FillItem(Graphs.FillItem):
    """FillItem."""

    __gtype_name__ = "GraphsPythonFillItem"

    data = GObject.Property(type=object)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = (None, None, None)


_CLASSES = {
    "DataItem": DataItem,
    "GeneratedDataItem": GeneratedDataItem,
    "EquationItem": Graphs.EquationItem,
    "TextItem": Graphs.TextItem,
    "FillItem": FillItem,
}
_INVERSE_CLASSES = dict(zip(_CLASSES.values(), _CLASSES.keys()))
_PROPERTIES = {
    DataItem: {
        "errbarsabove": ("errorbar.barsabove", None),
        "errcapsize": ("errorbar.capsize", None),
        "errcapthick": ("errorbar.capthick", None),
        "errlinewidth": ("errorbar.linewidth", None),
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
        "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
        "markersize": ("lines.markersize", None),
    },
    GeneratedDataItem: {
        "errbarsabove": ("errorbar.barsabove", None),
        "errcapsize": ("errorbar.capsize", None),
        "errcapthick": ("errorbar.capthick", None),
        "errlinewidth": ("errorbar.linewidth", None),
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
        "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
        "markersize": ("lines.markersize", None),
    },
    Graphs.EquationItem: {
        "linestyle": (
            "lines.linestyle",
            lambda x: max(misc.LINESTYLES.index(x) - 1, 0),
        ),
        "linewidth": ("lines.linewidth", None),
    },
    Graphs.TextItem: {
        "size": ("font.size", None),
        "color": ("text.color", None),
    },
}


def new_from_dict(dictionary: dict) -> Graphs.Item:
    """Instanciate item from dict."""
    tp = dictionary["type"]
    try:
        cls = _CLASSES[tp]
    except KeyError as e:
        raise ValueError(f"could not find type {tp}") from e
    dictionary.pop("type")
    return cls(**dictionary)


def to_dict(item: Graphs.Item) -> dict:
    """Convert item to dict."""
    dictionary = {
        key: item.get_property(key)
        for key in dir(item.props) if key != "typename"
    }
    dictionary["type"] = _INVERSE_CLASSES[type(item)]
    return dictionary


def reset(
    item,
    old_style: tuple[RcParams, dict],
    new_style: tuple[RcParams, dict],
) -> None:
    """Reset all properties."""
    # Combine rcparams and graphs_params into single dict:
    old_style = old_style[0] | old_style[1]
    new_style = new_style[0] | new_style[1]
    for prop, (key, function) in _PROPERTIES[type(item)].items():
        old_value = old_style[key]
        new_value = new_style[key]
        if function is not None:
            old_value = function(old_value)
            new_value = function(new_value)
        if item.get_property(prop) == old_value:
            item.set_property(prop, new_value)


def override_properties(
    item: Graphs.Item,
    style: tuple[RcParams, dict],
) -> None:
    """Override all properties to default."""
    style = style[0] | style[1]
    style_properties = _PROPERTIES[type(item)]
    for prop, (key, function) in style_properties.items():
        value = style[key] if function is None else function(style[key])
        item.set_property(prop, value)


def _extract_params(
    style: tuple[RcParams, dict],
    style_properties: dict,
    kwargs: dict,
) -> dict:
    style = style[0] | style[1]  # Add graphs_params to style dict
    return {
        prop: style[key] if function is None else function(style[key])
        for prop, (key, function) in style_properties.items()
        if prop not in kwargs
    }


class ItemFactory(Graphs.ItemFactory):
    """Item factory."""

    _default_new = {
        "generated-data-item": GeneratedDataItem,
        "equation-item": Graphs.EquationItem,
        "text-item": Graphs.TextItem,
    }

    def __init__(self):
        super().__init__()
        for item, cls in self._default_new.items():
            callback = getattr(self, "new_" + item.replace("-", "_"))
            self.connect(item + "-request", self._on_request, cls, callback)
        self.connect("data-item-request", self._on_data_item_request)

    @staticmethod
    def new_data_item(
        style: tuple[RcParams, dict],
        xdata: list[float] = None,
        ydata: list[float] = None,
        xerr: list[float] = None,
        yerr: list[float] = None,
        **kwargs,
    ) -> DataItem:
        """Create new DataItem."""
        return DataItem(
            data=(xdata, ydata, xerr, yerr),
            **_extract_params(style, _PROPERTIES[DataItem], kwargs),
            **kwargs,
        )

    @staticmethod
    def new_generated_data_item(
        style: tuple[RcParams, dict],
        equation: str,
        xstart: str,
        xstop: str,
        steps: int,
        scale: Graphs.Scale,
        **kwargs,
    ) -> GeneratedDataItem:
        """Create new GeneratedDataItem."""
        return GeneratedDataItem(
            equation=equation,
            xstart=xstart,
            xstop=xstop,
            steps=steps,
            scale=scale,
            **_extract_params(style, _PROPERTIES[GeneratedDataItem], kwargs),
            **kwargs,
        )

    @staticmethod
    def new_equation_item(
        style: tuple[RcParams, dict],
        equation: str,
        **kwargs,
    ) -> Graphs.EquationItem:
        """Create new EquationItem."""
        return Graphs.EquationItem(
            equation=equation,
            **_extract_params(style, _PROPERTIES[Graphs.EquationItem], kwargs),
            **kwargs,
        )

    @staticmethod
    def new_text_item(
        style: tuple[RcParams, dict],
        xanchor: float = 0,
        yanchor: float = 0,
        text: str = "",
        **kwargs,
    ) -> Graphs.TextItem:
        """Create new textItem."""
        return Graphs.TextItem(
            xanchor=xanchor,
            yanchor=yanchor,
            text=text,
            **_extract_params(style, _PROPERTIES[Graphs.TextItem], kwargs),
            **kwargs,
        )

    @staticmethod
    def new_fill_item(
        _params: tuple[RcParams, dict],
        data: tuple[list[float], list[float], list[float]],
        **kwargs,
    ) -> FillItem:
        """Create new FillItem."""
        return FillItem(data=data, **kwargs)

    @staticmethod
    def _on_request(self, data: Graphs.Data, *args) -> Graphs.Item:
        *args, cls, callback = args
        return callback(data.get_selected_style_params(), *args)

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
    ) -> DataItem:
        return ItemFactory.new_data_item(
            data.get_selected_style_params(),
            self._bytes_to_list(xdata),
            self._bytes_to_list(ydata),
            self._bytes_to_list(xerr),
            self._bytes_to_list(yerr),
        )
