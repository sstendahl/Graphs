# SPDX-License-Identifier: GPL-3.0-or-later
"""
Scales Module.

Contains helper functions to convert between string and int as well as
custom Scale classes.

    Functions:
        to_string
        to_int
"""
from matplotlib import scale, ticker, transforms

import numpy

_SCALES = ["linear", "log", "radians", "squareroot"]


def to_string(scale: int) -> str:
    """Convert an int to a string."""
    return _SCALES[scale]


def to_int(scale: str) -> int:
    """Convert a string to an int."""
    return _SCALES.index(scale)


class RadiansScale(scale.LinearScale):
    """Radians Scale."""

    name = "radians"

    def set_default_locators_and_formatters(self, axis):
        super().set_default_locators_and_formatters(axis)
        axis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _pos=None: f"{x / numpy.pi:.0f}π"),
        )
        axis.set_major_locator(ticker.MultipleLocator(base=numpy.pi))


class SquareRootScale(scale.ScaleBase):
    """Class for generating custom square root scale."""
    name = "squareroot"

    def set_default_locators_and_formatters(self, axis):
        axis.set_major_locator(ticker.AutoLocator())
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_locator(ticker.NullLocator())
        axis.set_minor_formatter(ticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, _minpos):
        return max(0, vmin), vmax

    class SquareRootTransform(transforms.Transform):
        """The transform to convert from linear to square root scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform_non_affine(self, a):
            return numpy.array(a)**0.5

        def inverted(self):
            return SquareRootScale.InvertedSquareRootTransform()

    class InvertedSquareRootTransform(transforms.Transform):
        """The inverse transform to convert from square root to linear scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform(self, a):
            return numpy.array(a)**2

        def inverted(self):
            return SquareRootScale.SquareRootTransform()

    def get_transform(self):
        return self.SquareRootTransform()


scale.register_scale(RadiansScale)
scale.register_scale(SquareRootScale)
