# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import Graphs

from graphs import misc, utilities


class _PythonItemMixin:

    def reset(
        self,
        old_style: Graphs.StyleParameters,
        new_style: Graphs.StyleParameters,
    ) -> None:
        """Reset all properties."""
        if not hasattr(self, "_style_properties"):
            return
        # Combine rcparams and graphs_params into single dict:
        old_style = old_style.style_params | old_style.graphs_params
        new_style = new_style.style_params | new_style.graphs_params
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
        style: Graphs.StyleParameters,
    ) -> None:
        """Override all properties."""
        if not hasattr(self, "_style_properties"):
            return
        # Combine rcparams and graphs_params into single dict:
        style = style.style_params | style.graphs_params
        for prop, (key, function) in self._style_properties.items():
            value = style[key] if function is None else function(style[key])
            self.set_property(prop, value)

    @staticmethod
    def _extract_params(
        cls,
        style: Graphs.StyleParameters,
        kwargs: dict,
    ) -> dict:
        # Combine rcparams and graphs_params into single dict:
        style = style.style_params | style.graphs_params
        return {
            prop: style[key] if function is None else function(style[key])
            for prop, (key, function) in cls._style_properties.items()
            if prop not in kwargs
        }


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
        style: Graphs.StyleParameters,
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
        style: Graphs.StyleParameters,
        data: Graphs.DataHolder,
        **kwargs,
    ):
        """Create new DataItem with a DataHolder."""
        return cls(
            data=data,
            **cls._extract_params(cls, style, kwargs),
            **kwargs,
        )

    def set_data_tuple(self, data: tuple[list, list, list, list]) -> None:
        """Set the data from a tuple."""
        self.props.data = Graphs.DataHolder.new(*data)


class GeneratedDataItem(Graphs.GeneratedDataItem, DataItem):
    """Generated Dataitem."""

    __gtype_name__ = "GraphsPythonGeneratedDataItem"

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        equation: Graphs.Ast,
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
    def new(
        cls,
        style: Graphs.StyleParameters,
        equation: Graphs.Ast,
        **kwargs,
    ):
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
        style: Graphs.StyleParameters,
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

    @classmethod
    def new(
        cls,
        style: Graphs.StyleParameters,
        data: tuple[list[float], list[float], list[float]],
        **kwargs,
    ):
        """Create new FillItem."""
        return cls.new_with_data(style, Graphs.FillHolder.new(*data), **kwargs)

    @classmethod
    def new_with_data(
        cls,
        _style: Graphs.StyleParameters,
        data: Graphs.FillHolder,
        **kwargs,
    ):
        """Create new FillItem with a FillItem."""
        return cls(data=data, **kwargs)

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
        self.connect("override-request", self._on_override_request)
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
                dictionary.pop("upper_source", None)
                dictionary.pop("lower_source", None)
                upper = dictionary.pop("upper_equation", None)
                lower = dictionary.pop("lower_equation", None)
                dictionary["data"] = Graphs.FillHolder.new(*dictionary["data"])
                item = FillItem(**dictionary)
                if upper is not None:
                    item.set_upper_equation(Graphs.expression_to_ast(upper))
                if lower is not None:
                    item.set_lower_equation(Graphs.expression_to_ast(lower))
                return item
            case _:
                raise ValueError(f"could not find type {dictionary['type']}")

    @staticmethod
    def resolve_dependencies(
        item: Graphs.Item,
        dictionary: dict,
        items: list[Graphs.Item],
    ) -> Graphs.Item:
        """Replace indexes with references for data dependant items."""
        if isinstance(item, Graphs.FillItem):
            upper_source = dictionary.get("upper_source")
            lower_source = dictionary.get("lower_source")
            if upper_source is not None and upper_source < len(items):
                item.set_upper_source(items[upper_source])
            if lower_source is not None and lower_source < len(items):
                item.set_lower_source(items[lower_source])
        return item

    @staticmethod
    def to_dict(item: Graphs.Item) -> dict:
        """Serialize an item to a dict."""
        dictionary = {
            key: ItemFactory.serialize_property(item, key)
            for key in dir(item.props) if key != "typename"
        }
        typename = item.__gtype__.name[12:]
        dictionary["type"] = typename
        dictionary.pop("visible")
        match typename:
            case "FillItem":
                upper = item.get_upper_equation()
                lower = item.get_lower_equation()
                dictionary["upper_equation"] = \
                    None if upper is None else Graphs.ast_to_expression(upper)
                dictionary["lower_equation"] = \
                    None if lower is None else Graphs.ast_to_expression(lower)
        return dictionary

    @staticmethod
    def link_dependencies(
        item: Graphs.Item,
        dictionary: dict,
        items: list[Graphs.Item],
    ) -> dict:
        """Replace references with indexes for data dependant items."""
        if isinstance(item, Graphs.FillItem):
            upper = item.get_upper_source()
            lower = item.get_lower_source()
            dictionary["upper_source"] = \
                None if upper is None else items.index(upper)
            dictionary["lower_source"] = \
                None if lower is None else items.index(lower)
        return dictionary

    @staticmethod
    def serialize_property(item: Graphs.Item, prop: str):
        """Serialize an items property to a picklable format."""
        if prop == "data":
            holder = item.get_data()
            if isinstance(item, Graphs.DataItem):
                return (
                    utilities.bytes_to_list(holder.get_xdata_b()),
                    utilities.bytes_to_list(holder.get_ydata_b()),
                    utilities.bytes_to_list(holder.get_xerr_b()),
                    utilities.bytes_to_list(holder.get_yerr_b()),
                )
            elif isinstance(item, Graphs.FillItem):
                return (
                    utilities.bytes_to_list(holder.get_xdata_b()),
                    utilities.bytes_to_list(holder.get_lower_b()),
                    utilities.bytes_to_list(holder.get_upper_b()),
                )
        elif prop == "equation":
            return Graphs.ast_to_expression(item.get_property(prop))
        return item.get_property(prop)

    @staticmethod
    def _on_override_request(
        self,
        item: Graphs.Item,
        style: Graphs.StyleParameters,
    ) -> None:
        item.override(style)

    @staticmethod
    def _on_request(self, *args) -> Graphs.Item:
        *args, callback = args
        return callback(*args)
