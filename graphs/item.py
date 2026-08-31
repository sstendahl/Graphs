# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import Graphs

from graphs import misc, utilities


class ItemFactory(Graphs.ItemFactory):
    """Item factory."""

    _style_properties = {
        "DataItem": {
            "errbarsabove": ("errorbar.barsabove", None),
            "errcapsize": ("errorbar.capsize", None),
            "errcapthick": ("errorbar.capthick", None),
            "errlinewidth": ("errorbar.linewidth", None),
            "linestyle": ("lines.linestyle", misc.LINESTYLES.index),
            "linewidth": ("lines.linewidth", None),
            "markerstyle": ("lines.marker", misc.MARKERSTYLES.index),
            "markersize": ("lines.markersize", None),
        },
        "EquationItem": {
            "linestyle": (
                "lines.linestyle",
                lambda x: max(misc.LINESTYLES.index(x) - 1, 0),
            ),
            "linewidth": ("lines.linewidth", None),
        },
        "TextItem": {
            "size": ("font.size", None),
            "color": ("text.color", None),
        },
    }

    def __init__(self):
        super().__init__()
        self.connect("override-request", self._on_override_request)
        self.connect("reset-request", self._on_reset_request)

    @staticmethod
    def new_from_dict(dictionary: dict) -> Graphs.Item:
        """Instanciate item from dict."""
        dictionary = dict(dictionary)
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
                dictionary.pop("upper_source", None)
                dictionary.pop("lower_source", None)
                upper = dictionary.pop("upper_equation", None)
                lower = dictionary.pop("lower_equation", None)
                dictionary["data"] = Graphs.FillHolder.new(*dictionary["data"])
                item = Graphs.FillItem(**dictionary)
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
        """Replace indexes with references for data dependent items."""
        if isinstance(item, Graphs.FillItem):
            upper_source = dictionary.get("upper_source")
            lower_source = dictionary.get("lower_source")
            if upper_source is not None and upper_source < len(items):
                item.set_upper_source(items[upper_source])
            if lower_source is not None and lower_source < len(items):
                item.set_lower_source(items[lower_source])
        return item

    @staticmethod
    def deserialize_property(item: Graphs.Item, prop: str, value) -> None:
        """Set an item's property from a serializable format."""
        if prop == "data":
            if isinstance(item, Graphs.DataItem):
                item.set_data(Graphs.DataHolder.new(*value))
            elif isinstance(item, Graphs.FillItem):
                item.set_data(Graphs.FillHolder.new(*value))
        elif prop == "equation":
            item.set_property(prop, Graphs.expression_to_ast(value))
        else:
            item.set_property(prop, value)

    @staticmethod
    def to_dict(item: Graphs.Item) -> dict:
        """Serialize an item to a dict."""
        dictionary = {
            key: ItemFactory.serialize_property(item, key)
            for key in dir(item.props) if key != "typename"
        }
        typename = item.__gtype__.name[6:]
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
        """Return an item's property in a serializable format."""
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

    def _item_style_properties(self, item: Graphs.Item) -> dict:
        if isinstance(item, Graphs.DataItem):
            return self._style_properties["DataItem"]
        elif isinstance(item, Graphs.EquationItem):
            return self._style_properties["EquationItem"]
        elif isinstance(item, Graphs.TextItem):
            return self._style_properties["TextItem"]
        return None

    @staticmethod
    def _on_override_request(
        self,
        item: Graphs.Item,
        style: Graphs.StyleParameters,
    ) -> None:
        style_properties = self._item_style_properties(item)
        if style_properties is None:
            return
        # Combine rcparams and graphs_params into single dict:
        style = style.style_params | style.graphs_params
        for prop, (key, function) in style_properties.items():
            value = style[key] if function is None else function(style[key])
            item.set_property(prop, value)

    @staticmethod
    def _on_reset_request(
        self,
        item: Graphs.Item,
        old_style: Graphs.StyleParameters,
        new_style: Graphs.StyleParameters,
    ) -> None:
        style_properties = self._item_style_properties(item)
        if style_properties is None:
            return
        # Combine rcparams and graphs_params into single dict:
        old_style = old_style.style_params | old_style.graphs_params
        new_style = new_style.style_params | new_style.graphs_params
        for prop, (key, function) in style_properties.items():
            old_value = old_style[key]
            new_value = new_style[key]
            if function is not None:
                old_value = function(old_value)
                new_value = function(new_value)
            if item.get_property(prop) == old_value:
                item.set_property(prop, new_value)
