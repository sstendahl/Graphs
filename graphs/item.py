# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gettext import gettext as _

from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import rcParams


def new_from_dict(dictionary: dict):
    """Instanciate item from dict."""
    match dictionary["type"]:
        case "GraphsDataItem":
            cls = DataItem
        case "GraphsGeneratedDataItem":
            cls = GeneratedDataItem
        case "GraphsEquationItem":
            cls = EquationItem
        case "GraphsTextItem":
            cls = TextItem
        case "GraphsFillItem":
            cls = FillItem
        case _:
            raise ValueError(f"could not find type {dictionary['type']}")
    dictionary.pop("type")
    return cls(**dictionary)


class _PythonItem(Graphs.Item):

    __gtype_name__ = "GraphsPythonItem"

    def __init__(self, **kwargs):
        super().__init__(typename=self._typename, **kwargs)

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
    _typename = _("Dataset")

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
        super().__init__(**kwargs)
        for prop in ("xdata", "ydata"):
            if self.get_property(prop) is None:
                self.set_property(prop, [])


class GeneratedDataItem(DataItem):
    """Generated Dataitem."""

    __gtype_name__ = "GraphsGeneratedDataItem"
    _typename = _("Generated Dataset")

    xstart = GObject.Property(type=str, default="0")
    xstop = GObject.Property(type=str, default="10")
    steps = GObject.Property(type=int, default=100)

    @classmethod
    def new(
        cls,
        style: rcParams,
        equation: str,
        xstart: str,
        xstop: str,
        steps: int,
        **kwargs,
    ):
        """Create new GeneratedDataItem."""
        return cls(
            equation=equation,
            xstart=xstart,
            xstop=xstop,
            steps=steps,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        self._equation = ""
        super().__init__(**kwargs)
        self._regenerate()
        for prop in ("equation", "xstart", "xstop", "steps"):
            self.connect("notify::" + prop, self._regenerate)

    @GObject.Property(type=str)
    def equation(self) -> str:
        """Equation."""
        return self._equation

    @equation.setter
    def equation(self, equation: str) -> None:
        old_equation = self._equation
        valid_equation = utilities.validate_equation(str(equation))
        if old_equation == equation or not valid_equation:
            return
        self._equation = equation
        self.notify("equation")

        if "Y = " + old_equation == self.props.name:
            self.props.name = "Y = " + equation

    def _regenerate(self, *_args) -> None:
        """Regenerate Data."""
        self.props.xdata, self.props.ydata = utilities.equation_to_data(
            self._equation,
            [
                utilities.string_to_float(self.props.xstart),
                utilities.string_to_float(self.props.xstop),
            ],
            self.props.steps,
        )


class EquationItem(_PythonItem):
    """EquationItem."""

    __gtype_name__ = "GraphsEquationItem"
    _typename = _("Equation")

    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)

    _style_properties = {
        "linestyle": (
            "lines.linestyle",
            lambda x: max(misc.LINESTYLES.index(x) - 1, 0),
        ),
        "linewidth": ("lines.linewidth", None),
    }

    @classmethod
    def new(cls, style, equation, **kwargs):
        """Create new EquationItem."""
        return cls(
            equation=equation,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        self._equation = ""
        super().__init__(**kwargs)

    @GObject.Property(type=str)
    def equation(self) -> str:
        """Equation."""
        return self._equation

    @equation.setter
    def equation(self, equation: str) -> None:
        old_equation = self._equation
        valid_equation = utilities.validate_equation(str(equation))
        if old_equation == equation or not valid_equation:
            return
        self._equation = equation
        self.notify("equation")

        if "Y = " + old_equation == self.props.name:
            self.props.name = "Y = " + equation


class TextItem(_PythonItem):
    """TextItem."""

    __gtype_name__ = "GraphsTextItem"
    _typename = _("Label")

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


class FillItem(_PythonItem):
    """FillItem."""

    __gtype_name__ = "GraphsFillItem"
    _typename = _("Fill")

    data = GObject.Property(type=object)

    @classmethod
    def new(cls, _params, data, **kwargs):
        """Create new FillItem."""
        return cls(data=data, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = (None, None, None)

    def reset(self):
        """Not yet implemented."""
        raise NotImplementedError
