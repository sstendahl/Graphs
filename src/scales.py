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

_SCALES = ["linear", "log", "radians", "squareroot", "inverse"]


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
        axis.set_major_locator(CustomScaleLocator())
        axis.set_minor_locator(CustomScaleLocator(is_minor=True))
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_formatter(ticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, _minpos):
        return max(0, vmin), vmax

    class SquareRootTransform(transforms.Transform):
        """The transform to convert from linear to square root scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform_non_affine(self, a):
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return numpy.array(a)**0.5

        def inverted(self):
            return SquareRootScale.InvertedSquareRootTransform()

    class InvertedSquareRootTransform(transforms.Transform):
        """The inverse transform to convert from square root to linear scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform_non_affine(self, a):
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return numpy.array(a)**2

        def inverted(self):
            return SquareRootScale.SquareRootTransform()

    def get_transform(self):
        return self.SquareRootTransform()


class InverseScale(scale.ScaleBase):
    name = "inverse"

    def set_default_locators_and_formatters(self, axis):
        axis.set_major_locator(CustomScaleLocator())
        axis.set_minor_locator(CustomScaleLocator(is_minor=True))
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_formatter(ticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, minpos):
        if not numpy.isfinite(minpos):
            minpos = 1e-300
        return (
            minpos if vmin <= 0 else vmin,
            minpos if vmax <= 0 else vmax,
        )

    def get_transform(self):
        return InverseScale.InverseTransform()

    class InverseTransform(transforms.Transform):
        """The transform to invert the scaling on the axis"""
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True

        def inverted(self):
            return InverseScale.InverseTransform()

        def transform_non_affine(self, a):
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return 1 / numpy.array(a)


class CustomScaleLocator(ticker.MaxNLocator):
    """Dynamically find tick positions on custom scales."""
    def __init__(self, is_minor=False):
        self.is_minor = is_minor

    @property
    def numticks(self):
        if self.axis is not None:
            numticks = max(1, self.axis.get_tick_space() - 4)
            # Amount of ticks is set between 3 and 9
            self._numticks = numpy.clip(numticks, 3, 9)
        else:
            self._numticks = 9
        if self.is_minor:
            # Amount of minor ticks is equal to amount of major ticks
            # times (N+1) minus N. Where N is the amount of minor ticks
            # in between the major ticks.
            self._numticks = len(self.axis.get_majorticklocs()) * 4 - 3
        return self._numticks

    @numticks.setter
    def numticks(self, numticks):
        self._numticks = numticks

    def tick_values(self, vmin, vmax):
        vmin, vmax = transforms.nonsingular(vmin, vmax, expander=0.05)
        vmin, vmax = min(vmin, vmax), max(vmin, vmax)  # Swap values if needed
        lin_tick_pos = numpy.linspace(vmin, vmax, self.numticks)
        lin_tick_pos = lin_tick_pos[lin_tick_pos != 0]  # Remove zeroes
        if self.axis.get_scale() == "squareroot":
            tick_pos = lin_tick_pos ** 2
        elif self.axis.get_scale() == "inverse":
            tick_pos = 1 / lin_tick_pos
        else:
            raise ValueError("Wrong locator for the axis type")
        tick_pos = tick_pos * ((vmax - vmin) / (max(tick_pos) - min(tick_pos)))
        tick_pos *= 2 if self.axis.get_scale() == "squareroot" else 1
        return tick_pos


scale.register_scale(RadiansScale)
scale.register_scale(SquareRootScale)
scale.register_scale(InverseScale)
