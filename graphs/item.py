# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gettext import gettext as _
from typing import Tuple

from gi.repository import GObject, Graphs

from graphs import misc, utilities

from matplotlib import RcParams


def new_from_dict(dictionary: dict) -> Graphs.Item:
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

    def reset(
        self,
        old_style: Tuple[RcParams, dict],
        new_style: Tuple[RcParams, dict],
    ) -> None:
        """Reset all properties."""
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

    def _extract_params(
        self,
        style: Tuple[RcParams, dict],
        kwargs: dict = None,
    ) -> dict:
        style = style[0] | style[1]  # Add graphs_params to style dict
        return {
            prop: style[key] if function is None else function(style[key])
            for prop, (key, function) in self._style_properties.items()
            if kwargs is None or prop not in kwargs
        }

    def to_dict(self) -> dict:
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

    data = GObject.Property(type=object)
    xerr = GObject.Property(type=object)
    yerr = GObject.Property(type=object)
    linestyle = GObject.Property(type=int, default=1)
    linewidth = GObject.Property(type=float, default=3)
    markerstyle = GObject.Property(type=int, default=0)
    markersize = GObject.Property(type=float, default=7)
    showxerr = GObject.Property(type=bool, default=True)
    showyerr = GObject.Property(type=bool, default=True)

    _style_properties = {
        "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
        "linewidth": ("lines.linewidth", None),
        "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
        "markersize": ("lines.markersize", None),
    }

    @classmethod
    def new(
        cls,
        style: Tuple[RcParams, dict],
        xdata: list[float] = None,
        ydata: list[float] = None,
        xerr: list[float] = None,
        yerr: list[float] = None,
        **kwargs,
    ):
        """Create new DataItem."""
        return cls(
            data=(xdata, ydata),
            xerr=xerr,
            yerr=yerr,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = ([], [])

    def get_xdata(self) -> list:
        """Get xdata."""
        return self.props.data[0]

    def get_ydata(self) -> list:
        """Get ydata."""
        return self.props.data[1]

    def get_xerr(self):
        """Get xerr."""
        return self.props.xerr

    def get_yerr(self):
        """Get yerr."""
        return self.props.yerr


class GeneratedDataItem(DataItem):
    """Generated Dataitem."""

    __gtype_name__ = "GraphsGeneratedDataItem"
    _typename = _("Generated Dataset")

    xstart = GObject.Property(type=str, default="0")
    xstop = GObject.Property(type=str, default="10")
    steps = GObject.Property(type=int, default=100)
    scale = GObject.Property(type=int, default=0)

    @classmethod
    def new(
        cls,
        style: Tuple[RcParams, dict],
        equation: str,
        xstart: str,
        xstop: str,
        steps: int,
        scale: int,
        **kwargs,
    ):
        """Create new GeneratedDataItem."""
        return cls(
            equation=equation,
            xstart=xstart,
            xstop=xstop,
            steps=steps,
            scale=scale,
            **cls._extract_params(cls, style),
            **kwargs,
        )

    def __init__(self, **kwargs):
        self._equation = ""
        super().__init__(**kwargs)
        self._regenerate()
        for prop in ("equation", "xstart", "xstop", "steps", "scale"):
            self.connect("notify::" + prop, self._regenerate)

    @GObject.Property(type=str)
    def equation(self) -> str:
        """Equation."""
        return self._equation

    @equation.setter
    def equation(self, equation: str) -> None:
        old_equation = self._equation
        if old_equation == equation:
            return
        self._equation = equation
        self.notify("equation")

        if "Y = " + old_equation == self.props.name:
            self.props.name = "Y = " + equation

    def _regenerate(self, *_args) -> None:
        """Regenerate Data."""
        self.props.data = utilities.equation_to_data(
            Graphs.preprocess_equation(self._equation),
            [
                Graphs.evaluate_string(self.props.xstart),
                Graphs.evaluate_string(self.props.xstop),
            ],
            self.props.steps,
            self.props.scale,
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
    def new(cls, style: Tuple[RcParams, dict], equation: str, **kwargs):
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
        if old_equation == equation:
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
    def new(
        cls,
        style: Tuple[RcParams, dict],
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
            **cls._extract_params(cls, style),
            **kwargs,
        )


class FillItem(_PythonItem):
    """FillItem."""

    __gtype_name__ = "GraphsFillItem"
    _typename = _("Fill")

    data = GObject.Property(type=object)

    @classmethod
    def new(
        cls,
        _params: Tuple[RcParams, dict],
        data: tuple[list[float], list[float], list[float]],
        **kwargs,
    ):
        """Create new FillItem."""
        return cls(data=data, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.props.data is None:
            self.props.data = (None, None, None)

    def reset(self):
        """Not yet implemented."""
        raise NotImplementedError
