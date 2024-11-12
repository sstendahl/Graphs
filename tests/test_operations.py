"""Tests for operations."""
from graphs import operations
from graphs.item import DataItem
from graphs.operations import DataOperations

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
    xdata, ydata, _sort, _discard = \
        DataOperations.normalize(None, XDATA, YDATA)
    assert max(ydata) == 1


def test_translate_x():
    """Test if translate_x function correctly shifts xdata."""
    xdata, ydata, _sort, _discard = \
        DataOperations.translate_x(None, XDATA, YDATA, 15)
    assert all(x_new == (x_old + 15) for x_old, x_new in zip(XDATA, xdata))


def test_translate_y():
    """Test if translate_y function correctly shifts ydata."""
    xdata, ydata, _sort, _discard = \
        DataOperations.translate_y(None, XDATA, YDATA, 15)
    assert all(y_new == (y_old + 15) for y_old, y_new in zip(YDATA, ydata))


def test_multiply_x():
    """Test if multiply_x function correctly scales xdata."""
    xdata, ydata, _sort, _discard = \
        DataOperations.multiply_x(None, XDATA, YDATA, 15)
    assert all(x_new == (x_old * 15) for x_old, x_new in zip(XDATA, xdata))


def test_multiply_y():
    """Test if multiply_y function correctly scales ydata."""
    xdata, ydata, _sort, _discard = \
        DataOperations.multiply_y(None, XDATA, YDATA, 15)
    assert all(y_new == (y_old * 15) for y_old, y_new in zip(YDATA, ydata))


def test_center():
    """Test if center function centers ydata correctly."""
    xdata, ydata, _sort, _discard = \
        DataOperations.center(None, XDATA, YDATA, 0)
    y_max_index = YDATA.index(max(YDATA))
    assert xdata[y_max_index] == 0

    xdata, ydata, _sort, _discard = \
        DataOperations.center(None, XDATA, YDATA, 1)
    middle_value = (min(XDATA) + max(XDATA)) / 2
    assert all(x_new == (x_old - middle_value) for x_old, x_new in zip(XDATA,
                                                                       xdata))


@pytest.mark.parametrize("yscale", (0, 1, 2, 3))
def test_shift(yscale):
    """Test if shift_vertically function correctly shifts ydata."""
    ydata1 = [1.0, 1.8, 1.9, 1.1, 0.2, 0.1, 0.7, 1.7, 2.0, 1.4, 0.5]
    ydata2 = [2.0, 1.5, 0.6, 0.1, 0.3, 1.3, 2.0, 1.8, 0.9, 0.1, 0.2]
    xdata = np.linspace(0, 10, len(ydata1))

    item1 = DataItem(xdata=xdata, ydata=ydata1, uuid="a")
    item2 = DataItem(xdata=xdata, ydata=ydata2, uuid="b")

    items = [item1, item2]
    new_xdata1, new_ydata1, _sort, _discard = \
        DataOperations.shift(item1, xdata, ydata1, left_scale=yscale,
                             right_scale=yscale, items=items,
                             ranges=[2.2, 2.2], limits=None)
    new_xdata2, new_ydata2, _sort, _discard = \
        DataOperations.shift(item2, xdata, ydata2, left_scale=yscale,
                             right_scale=yscale, items=items,
                             ranges=[2.2, 2.2], limits=None)
    np.testing.assert_array_equal(new_xdata1, xdata)
    np.testing.assert_array_equal(new_xdata2, xdata)

    diff_y1 = [y_new - y_old for y_new, y_old in zip(new_ydata1, ydata1)]
    diff_y2 = [y_new - y_old for y_new, y_old in zip(new_ydata2, ydata2)]

    # Check that data is not removed
    assert len(new_ydata1) == len(ydata1)
    assert len(new_ydata2) == len(ydata2)
    # Check that distance increases with each shift
    assert all(
        diff_y2 > diff_y1 for new_y2, new_y1 in zip(new_ydata2, new_ydata1))
    # Check that shift is large enough for chosen coordinates
    assert all(
        new_y2 > new_y1 for new_y2, new_y1 in zip(new_ydata2, new_ydata1))


def test_derivative():
    """Test if get_derivative function correctly calculates derivative."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]

    _, y_new, _sort, _discard = DataOperations.derivative(None, xdata, ydata)
    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([5, 5, 0, -5, -5], rel=1e-6)


def test_integral():
    """Test if get_integral function correctly calculates integral."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]

    x_new, y_new, _sort, _discard = DataOperations.integral(None, xdata, ydata)

    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([0, 7.5, 20, 32.5, 40], rel=1e-6)
