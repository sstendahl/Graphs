# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for item instantiation."""
from gi.repository import Graphs

from graphs import utilities
from graphs.item import ItemFactory

import pytest


def test_new_from_dict_data_item():
    """Test if new_from_dict returns a DataItem with the correct name."""
    d = {
        "type": "DataItem",
        "name": "My Dataset",
        "data": ([0.0, 1.0, 2.0], [5.0, 6.0, 7.0], [1, 3, 2], [3, 1, 2]),
        "color": "#1A5FB4",
    }
    item = ItemFactory.new_from_dict(d)
    assert isinstance(item, Graphs.DataItem)
    assert item.get_name() == "My Dataset"
    data = item.get_data()
    assert utilities.bytes_to_list(data.get_xdata_b()) == [0.0, 1.0, 2.0]
    assert utilities.bytes_to_list(data.get_ydata_b()) == [5.0, 6.0, 7.0]
    assert utilities.bytes_to_list(data.get_xerr_b()) == [1, 3, 2]
    assert utilities.bytes_to_list(data.get_yerr_b()) == [3, 1, 2]


def test_new_from_dict_text_item():
    """Test if new_from_dict returns a TextItem with the correct properties."""
    d = {
        "type": "TextItem",
        "name": "A Label",
        "text": "Hello",
        "xanchor": 0.5,
        "yanchor": 0.25,
        "color": "#000000",
    }
    item = ItemFactory.new_from_dict(d)
    assert isinstance(item, Graphs.TextItem)
    assert item.props.text == "Hello"
    assert item.props.xanchor == pytest.approx(0.5)
    assert item.props.yanchor == pytest.approx(0.25)


def test_new_from_dict_fill_item():
    """Test if new_from_dict returns a FillItem from a dict."""
    d = {
        "type": "FillItem",
        "name": "Fill",
        "data": ([], [], []),
        "color": "#62A0EA",
        "alpha": 0.25,
    }
    item = ItemFactory.new_from_dict(d)
    assert isinstance(item, Graphs.FillItem)


def test_new_from_dict_unknown_type_raises():
    """Test if new_from_dict raises ValueError for an unknown item type."""
    d = {"type": "BogusItem", "name": "X"}
    with pytest.raises(ValueError):
        ItemFactory.new_from_dict(d)


def test_data_item_default_data():
    """Test if DataItem defaults data to empty lists when not provided."""
    item = Graphs.DataItem(name="Empty")
    xdata, ydata = utilities.get_xydata(item.get_data())
    assert xdata.tolist() == []
    assert ydata.tolist() == []


def test_data_item_default_err():
    """Test if DataItem defaults err None when not provided."""
    item = Graphs.DataItem(name="NoErr")
    item_data = item.get_data()
    assert item_data.get_xerr_b() is None
    assert item_data.get_yerr_b() is None
