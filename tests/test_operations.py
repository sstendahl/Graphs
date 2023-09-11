from unittest.mock import Mock

from graphs import operations
from graphs.item import Item

import numpy as np

import pytest

XDATA = [0, 1, 4, 5, 7, 8, 12, 1]
YDATA = [5, 2, 7, 1, 31, 5, 123, 156]


def is_sorted(lst):
    """Check if a list is sorted in ascending order."""
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))


def test_sort_data():
    """Test if sort_data function sorts x and y data."""
    sorted_x, sorted_y = operations.sort_data(XDATA, YDATA)
    assert is_sorted(sorted_x)


def test_normalize():
    """Test if normalize function scales ydata to maximum value of 1."""
    xdata, ydata, _sort, _discard = operations.normalize(None, XDATA, YDATA)
    assert max(ydata) == 1


def test_translate_x():
    """Test if translate_x function correctly shifts xdata."""
    xdata, ydata, _sort, _discard = operations.translate_x(None, XDATA, YDATA,
                                                           15)
    assert all(x_new == (x_old + 15) for x_old, x_new in zip(XDATA, xdata))


def test_translate_y():
    """Test if translate_y function correctly shifts ydata."""
    xdata, ydata, _sort, _discard = operations.translate_y(None, XDATA, YDATA,
                                                           15)
    assert all(y_new == (y_old + 15) for y_old, y_new in zip(YDATA, ydata))


def test_multiply_x():
    """Test if multiply_x function correctly scales xdata."""
    xdata, ydata, _sort, _discard = operations.multiply_x(None, XDATA, YDATA,
                                                          15)
    assert all(x_new == (x_old * 15) for x_old, x_new in zip(XDATA, xdata))


def test_multiply_y():
    """Test if multiply_y function correctly scales ydata."""
    xdata, ydata, _sort, _discard = operations.multiply_y(None, XDATA, YDATA,
                                                          15)
    assert all(y_new == (y_old * 15) for y_old, y_new in zip(YDATA, ydata))


def test_center():
    """Test if center function centers ydata correctly."""
    xdata, ydata, _sort, _discard = operations.center(None, XDATA, YDATA, 0)
    y_max_index = YDATA.index(max(YDATA))
    assert xdata[y_max_index] == 0

    xdata, ydata, _sort, _discard = operations.center(None, XDATA, YDATA, 1)
    middle_value = (min(XDATA) + max(XDATA)) / 2
    assert all(x_new == (x_old - middle_value) for x_old, x_new in zip(XDATA,
                                                                       xdata))


def test_shift():
    """Test if shift_vertically function correctly shifts ydata."""
    ydata1 = [8, 12, 10, 14, 9]
    ydata2 = [204, 128, 5, 42, 13]

    ydata1 = [value / max(ydata1) for value in ydata1]
    ydata2 = [value / max(ydata2) for value in ydata2]

    item1 = Mock(spec=Item, ydata=ydata1, selected=True, yposition="left",
                 key="a", props=Mock(item_type="Item"))
    item2 = Mock(spec=Item, ydata=ydata2, selected=True, yposition="left",
                 key="b", props=Mock(item_type="Item"))

    items = [item1, item2]
    new_xdata1, new_ydata1, _sort, _discard =\
        operations.shift(item1, XDATA, ydata1, left_scale=1,
                         right_scale=1, items=items)
    new_xdata2, new_ydata2, _sort, _discard = \
        operations.shift(item2, XDATA, ydata2, left_scale=1,
                         right_scale=1, items=items)
    np.testing.assert_array_equal(new_xdata1, XDATA)
    np.testing.assert_array_equal(new_xdata2, XDATA)
    assert len(new_ydata1) == len(ydata1)
    assert len(new_ydata2) == len(ydata2)
    assert all(new_y2 > old_y1 for new_y2, old_y1 in zip(new_ydata2, ydata1))


def test_derivative():
    """Test if get_derivative function correctly calculates derivative."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]

    _, y_new, _sort, _discard = operations.derivative(None, xdata, ydata)
    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([5, 5, 0, -5, -5], rel=1e-6)


def test_integral():
    """Test if get_integral function correctly calculates integral."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]

    x_new, y_new, _sort, _discard = operations.integral(None, xdata, ydata)

    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([0, 7.5, 20, 32.5, 40], rel=1e-6)
