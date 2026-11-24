# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import Graphs


class ItemFactory():
    """Item factory."""

    @staticmethod
    def new_from_dicts(dictionaries: list[dict]) -> list[Graphs.Item]:
        """Instanciate items from dict."""
        for i, dictionary in enumerate(dictionaries):
            if dictionary["type"] in ("FillItem", ):
                continue
            dictionaries[i] = ItemFactory.new_from_dict(dictionary, None)

        for i, dictionary in enumerate(dictionaries):
            if isinstance(dictionary, Graphs.Item):
                continue
            dictionaries[i] = ItemFactory.new_from_dict(
                dictionary,
                dictionaries,
            )

        return dictionaries

    @staticmethod
    def new_from_dict(
        dictionary: dict,
        items: list[Graphs.item],
    ) -> Graphs.Item:
        """Instanciate item from dict."""
        dictionary = dict(dictionary)
        match dictionary["type"]:
            case "DataItem":
                dictionary.pop("type")
                dictionary["data"] = Graphs.DataHolder.new(*dictionary["data"])
                return Graphs.DataItem(**dictionary)
            case "GeneratedDataItem":
                dictionary.pop("type")
                data = dictionary.pop("data")
                equation = Graphs.expression_to_ast(dictionary["equation"])
                dictionary["equation"] = equation
                item = Graphs.GeneratedDataItem(**dictionary)
                item.set_data(Graphs.DataHolder.new(*data))
                return item
            case "EquationItem":
                dictionary.pop("type")
                equation = Graphs.expression_to_ast(dictionary["equation"])
                dictionary["equation"] = equation
                return Graphs.EquationItem(**dictionary)
            case "TextItem":
                dictionary.pop("type")
                return Graphs.TextItem(**dictionary)
            case "VariableItem":
                dictionary.pop("type")
                # The range follows the value, so it has to be set last
                limits = {
                    prop: dictionary.pop(prop, None) for prop in ("min", "max")
                }
                item = Graphs.VariableItem(**dictionary)
                for prop, limit in limits.items():
                    if limit is not None:
                        item.set_property(prop, limit)
                return item
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
                upper_source = dictionary.get("upper_source")
                lower_source = dictionary.get("lower_source")
                if upper_source is not None and upper_source < len(items):
                    item.set_upper_source(items[upper_source])
                if lower_source is not None and lower_source < len(items):
                    item.set_lower_source(items[lower_source])
                return item
            case _:
                raise ValueError(f"could not find type {dictionary['type']}")
