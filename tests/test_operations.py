# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for operations."""
from graphs.operations import DataHelper, DataOperations

import pytest

XDATA = [0, 1, 4, 5, 7, 8, 12, 3]  # no duplicate x values
YDATA = [5, 2, 7, 1, 31, 5, 123, 156]


def is_sorted(lst):
    """Check if a list is sorted in ascending order."""
    return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))


def test_sort_data_x_is_sorted():
    """Test if sort_data sorts x data in ascending order."""
    sorted_x, sorted_y = DataHelper.sort_data(XDATA, YDATA)
    assert is_sorted(sorted_x)


def test_sort_data_xy_remain_paired():
    """Test if sort_data keeps x and y values correctly paired."""
    sorted_x, sorted_y = DataHelper.sort_data(XDATA, YDATA)
    original = dict(zip(XDATA, YDATA))
    for x, y in zip(sorted_x, sorted_y):
        assert original[x] == y


def test_filter_data_less_equal():
    """Test if filter_data keeps only values at or below the threshold."""
    xdata, ydata = DataHelper.filter_data(
        [1, 2, 3, 4, 5], [10, 20, 30, 40, 50], "<=", 3,
    )
    assert xdata == [1, 2, 3]
    assert ydata == [10, 20, 30]


def test_filter_data_greater_equal():
    """Test if filter_data keeps only values at or above the threshold."""
    xdata, ydata = DataHelper.filter_data(
        [1, 2, 3, 4, 5], [10, 20, 30, 40, 50], ">=", 3,
    )
    assert xdata == [3, 4, 5]
    assert ydata == [30, 40, 50]


def test_create_data_mask_matching_pairs():
    """Test if create_data_mask returns True only for matching (x, y) pairs."""
    xdata1 = [1, 2, 3]
    ydata1 = [10, 20, 30]
    xdata2 = [2, 3]
    ydata2 = [20, 30]
    mask = DataHelper.create_data_mask(xdata1, ydata1, xdata2, ydata2)
    assert list(mask) == [False, True, True]


def test_create_data_mask_no_matches():
    """Test if create_data_mask returns all False when no pairs match."""
    mask = DataHelper.create_data_mask([1, 2], [10, 20], [3, 4], [30, 40])
    assert not any(mask)


def test_normalize():
    """Test if normalize scales ydata to a maximum value of 1."""
    xdata, ydata, _sort, _discard = DataOperations.normalize(
        None, XDATA, YDATA,
    )
    assert max(ydata) == 1


def test_translate_x():
    """Test if translate_x shifts all x values by the given offset."""
    xdata, ydata, _sort, _discard = DataOperations.translate_x(
        None, XDATA, YDATA, 15,
    )
    assert all(x_new == x_old + 15 for x_old, x_new in zip(XDATA, xdata))


def test_translate_y():
    """Test if translate_y shifts all y values by the given offset."""
    xdata, ydata, _sort, _discard = DataOperations.translate_y(
        None, XDATA, YDATA, 15,
    )
    assert all(y_new == y_old + 15 for y_old, y_new in zip(YDATA, ydata))


def test_multiply_x():
    """Test if multiply_x scales all x values by the given multiplier."""
    xdata, ydata, _sort, _discard = DataOperations.multiply_x(
        None, XDATA, YDATA, 15,
    )
    assert all(x_new == x_old * 15 for x_old, x_new in zip(XDATA, xdata))


def test_multiply_y():
    """Test if multiply_y scales all y values by the given multiplier."""
    xdata, ydata, _sort, _discard = DataOperations.multiply_y(
        None, XDATA, YDATA, 15,
    )
    assert all(y_new == y_old * 15 for y_old, y_new in zip(YDATA, ydata))


def test_center_at_maximum():
    """Test if center places the x of the maximum y value at zero."""
    xdata, ydata, _sort, _discard = DataOperations.center(
        None, XDATA, YDATA, 0,
    )
    y_max_index = YDATA.index(max(YDATA))
    assert xdata[y_max_index] == 0


def test_center_at_middle():
    """Test if center places the midpoint of the x range at zero."""
    xdata, ydata, _sort, _discard = DataOperations.center(
        None, XDATA, YDATA, 1,
    )
    middle_value = (min(XDATA) + max(XDATA)) / 2
    assert all(
        x_new == x_old - middle_value for x_old, x_new in zip(XDATA, xdata)
    )


def test_derivative():
    """Test if derivative returns the correct gradient at each point."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]
    _, y_new, _sort, _discard = DataOperations.derivative(None, xdata, ydata)
    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([5, 5, 0, -5, -5], rel=1e-6)


def test_integral():
    """Test if integral returns the correct cumulative area at each point."""
    xdata = [1, 2, 3, 4, 5]
    ydata = [5, 10, 15, 10, 5]
    x_new, y_new, _sort, _discard = DataOperations.integral(
        None, xdata, ydata,
    )
    assert len(y_new) == len(xdata)
    assert y_new == pytest.approx([0, 7.5, 20, 32.5, 40], rel=1e-6)


def test_cut_returns_empty():
    """Test if cut returns empty x and y lists."""
    xdata, ydata, _sort, _discard = DataOperations.cut(None, XDATA, YDATA)
    assert xdata == []
    assert ydata == []


def test_fft_output_length():
    """Test if fft returns arrays of the same length as the input."""
    xdata = list(range(8))
    ydata = [0, 1, 0, -1, 0, 1, 0, -1]
    x_new, y_new, _sort, _discard = DataOperations.fft(None, xdata, ydata)
    assert len(x_new) == len(xdata)
    assert len(y_new) == len(ydata)


def test_inverse_fft_output_length():
    """Test if inverse_fft returns arrays of the same length as the input."""
    xdata = list(range(8))
    ydata = [0, 1, 0, -1, 0, 1, 0, -1]
    x_new, y_new, _sort, _discard = DataOperations.inverse_fft(
        None, xdata, ydata,
    )
    assert len(x_new) == len(xdata)
    assert len(y_new) == len(ydata)
