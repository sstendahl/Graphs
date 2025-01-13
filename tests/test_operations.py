"""Tests for operations."""
from graphs.operations import DataHelper
from graphs.operations import DataOperations

import pytest

XDATA = [0, 1, 4, 5, 7, 8, 12, 1]
YDATA = [5, 2, 7, 1, 31, 5, 123, 156]


def is_sorted(lst):
    """Check if a list is sorted in ascending order."""
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))


def test_sort_data():
    """Test if sort_data function sorts x and y data."""
    sorted_x, sorted_y = DataHelper.sort_data(XDATA, YDATA)
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
