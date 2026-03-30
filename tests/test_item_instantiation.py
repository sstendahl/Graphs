# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for item instantiation."""
from graphs.item import DataItem, FillItem, TextItem, new_from_dict

import pytest


def test_new_from_dict_data_item():
    """Test if new_from_dict returns a DataItem with the correct name."""
    d = {
        "type": "DataItem",
        "name": "My Dataset",
        "data": ([0.0, 1.0, 2.0], [5.0, 6.0, 7.0], [1, 3, 2], [3, 1, 2]),
        "color": "#1A5FB4",
    }
    item = new_from_dict(d)
    assert isinstance(item, DataItem)
    assert item.get_name() == "My Dataset"
    assert item.get_xydata() == ([0.0, 1.0, 2.0], [5.0, 6.0, 7.0])
    assert item.get_xerr() == [1, 3, 2]
    assert item.get_yerr() == [3, 1, 2]


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
    item = new_from_dict(d)
    assert isinstance(item, TextItem)
    assert item.props.text == "Hello"
    assert item.props.xanchor == pytest.approx(0.5)
    assert item.props.yanchor == pytest.approx(0.25)


def test_new_from_dict_fill_item():
    """Test if new_from_dict returns a FillItem from a dict."""
    d = {
        "type": "FillItem",
        "name": "Fill",
        "data": (None, None, None),
        "color": "#62A0EA",
        "alpha": 0.25,
    }
    item = new_from_dict(d)
    assert isinstance(item, FillItem)


def test_new_from_dict_unknown_type_raises():
    """Test if new_from_dict raises ValueError for an unknown item type."""
    d = {"type": "BogusItem", "name": "X"}
    with pytest.raises(ValueError):
        new_from_dict(d)


def test_data_item_default_data():
    """Test if DataItem defaults data to empty lists when not provided."""
    item = DataItem(name="Empty")
    xdata, ydata = item.get_xydata()
    assert xdata == []
    assert ydata == []


def test_data_item_default_err():
    """Test if DataItem defaults err None when not provided."""
    item = DataItem(name="NoErr")
    assert item.get_xerr() is None
    assert item.get_yerr() is None
