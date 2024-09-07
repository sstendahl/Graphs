# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gettext import gettext as _

from gi.repository import GObject, Graphs

from graphs import misc


def new_from_dict(dictionary: dict):
    """Instanciate item from dict."""
    match dictionary["type"]:
        case "GraphsDataItem":
            cls = DataItem
        case "GraphsEquationItem":
            cls = EquationItem
        case "GraphsTextItem":
            cls = TextItem
        case "GraphsFillItem":
            cls = FillItem
        case _:
            pass
    dictionary.pop("type")
    return cls(**dictionary)


class _PythonItem(Graphs.Item):

    __gtype_name__ = "GraphsPythonItem"

    def reset(self, old_style, new_style):
        """Reset all properties."""
        for prop, (key, function) in self._style_properties.items():
            old_value = old_style[key]
            new_value = new_style[key]
            if function is not None:
                old_value = function(old_value)
                new_value = function(new_value)
            if self.get_property(prop) == old_value:
                self.set_property(prop, new_value)

    def _extract_params(self, style):
        return {
            prop: style[key] if function is None else function(style[key])
            for prop, (key, function) in self._style_properties.items()
        }

    def to_dict(self):
        """Convert item to dict."""
        dictionary = {
            key: self.get_property(key)
            for key in dir(self.props) if key != "typename"
        }
        dictionary["type"] = self.__gtype_name__
        return dictionary


class DataItem(_PythonItem):
    """DataItem."""

    __gtype_name__ = "GraphsDataItem"

    xdata = GObject.Property(type=object)
    ydata = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    markerstyle = GObject.Property(type=int, default=0)
    markersize = GObject.Property(type=float, default=7)

    _style_properties = {
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
        "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
        "markersize": ("lines.markersize", None),
    }

    @classmethod
    def new(cls, style, xdata=None, ydata=None, **kwargs):
        """Create new DataItem."""
        return cls(
            xdata=xdata,
            ydata=ydata,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(typename=_("Dataset"), **kwargs)
        for prop in ("xdata", "ydata"):
            if self.get_property(prop) is None:
                self.set_property(prop, [])


class EquationItem(_PythonItem):
    """EquationItem."""

    __gtype_name__ = "GraphsEquationItem"

    xdata = GObject.Property(type=object)
    ydata = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    equation = GObject.Property(type=str, default="")

    _style_properties = {
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
    }

    @classmethod
    def new(cls, style, equation, xdata=None, ydata=None, **kwargs):
        """Create new EquationItem."""
        return cls(
            xdata=xdata,
            ydata=ydata,
            equation=equation,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(typename=_("Equation"), **kwargs)
        for prop in ("xdata", "ydata"):
            if self.get_property(prop) is None:
                self.set_property(prop, [])


class TextItem(_PythonItem):
    """TextItem."""

    __gtype_name__ = "GraphsTextItem"

    xanchor = GObject.Property(type=float, default=0)
    yanchor = GObject.Property(type=float, default=0)
    text = GObject.Property(type=str, default="")
    size = GObject.Property(type=float, default=12)
    rotation = GObject.Property(type=int, default=0, minimum=0, maximum=360)

    _style_properties = {
        "size": ("font.size", None),
        "color": ("text.color", None),
    }

    @classmethod
    def new(cls, style, xanchor=0, yanchor=0, text="", **kwargs):
        """Create new textItem."""
        return cls(
            xanchor=xanchor,
            yanchor=yanchor,
            text=text,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(typename=_("Label"), **kwargs)


class FillItem(_PythonItem):
    """FillItem."""

    __gtype_name__ = "GraphsFillItem"

    data = GObject.Property(type=object)

    @classmethod
    def new(cls, _params, data, **kwargs):
        """Create new FillItem."""
        return cls(data=data, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(typename=_("Fill"), **kwargs)
        if self.props.data is None:
            self.props.data = (None, None, None)

    def reset(self):
        """Not yet implemented."""
        raise NotImplementedError
