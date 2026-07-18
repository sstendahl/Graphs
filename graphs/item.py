# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for data Items."""
from gi.repository import Graphs

from graphs import utilities


class ItemFactory:
    """Item factory."""

    @staticmethod
    def new_from_dict(dictionary: dict) -> Graphs.Item:
        """Instanciate item from dict."""
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
                dictionary["data"] = Graphs.FillHolder.new(*dictionary["data"])
                return Graphs.FillItem(**dictionary)
            case _:
                raise ValueError(f"could not find type {dictionary['type']}")

    @staticmethod
    def to_dict(item: Graphs.Item) -> dict:
        """Convert an item to a dict."""
        dictionary = {
            key: item.get_property(key)
            for key in dir(item.props) if key != "typename"
        }
        item_type = item.__gtype__.name[6:]
        dictionary["type"] = item_type
        match item_type:
            case "DataItem":
                data_tuple = utilities.data_holder_to_tuple(item.get_data())
                dictionary["data"] = data_tuple
            case "GeneratedDataItem":
                data_tuple = utilities.data_holder_to_tuple(item.get_data())
                dictionary["data"] = data_tuple
                equation = Graphs.ast_to_expression(item.props.equation)
                dictionary["equation"] = equation
            case "EquationItem":
                equation = Graphs.ast_to_expression(item.props.equation)
                dictionary["equation"] = equation
            case "FillItem":
                data_tuple = utilities.fill_holder_to_tuple(item.get_data())
                dictionary["data"] = data_tuple
        return dictionary
