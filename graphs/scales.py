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
        """Handle locators and formatters."""
        super().set_default_locators_and_formatters(axis)
        axis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _pos=None: f"{x / numpy.pi:.3g}π"),
        )
        axis.set_major_locator(RadianLocator())


class SquareRootScale(scale.ScaleBase):
    """Class for generating custom square root scale."""

    name = "squareroot"

    def set_default_locators_and_formatters(self, axis):
        """Handle locators and formatters."""
        axis.set_major_locator(CustomScaleLocator())
        axis.set_minor_locator(CustomScaleLocator(is_minor=True))
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_formatter(ticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, _minpos):
        """Limit scale range."""
        return max(0, vmin), vmax

    class SquareRootTransform(transforms.Transform):
        """The transform to convert from linear to square root scale."""

        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform_non_affine(self, a):
            """Transform data."""
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return numpy.array(a)**0.5

        def inverted(self):
            """Get the inverse transform."""
            return SquareRootScale.InvertedSquareRootTransform()

    class InvertedSquareRootTransform(transforms.Transform):
        """Inverse transform to convert from square root to linear scale."""

        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Seperable in X and Y dimension

        def transform_non_affine(self, a):
            """Transform data."""
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return numpy.array(a)**2

        def inverted(self):
            """Get the inverse transform."""
            return SquareRootScale.SquareRootTransform()

    def get_transform(self):
        """Get the transform."""
        return self.SquareRootTransform()


class InverseScale(scale.ScaleBase):
    """Inverse scale."""

    name = "inverse"

    def set_default_locators_and_formatters(self, axis):
        """Handle locators and formatters."""
        axis.set_major_locator(CustomScaleLocator())
        axis.set_minor_locator(CustomScaleLocator(is_minor=True))
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_formatter(ticker.NullFormatter())

    def limit_range_for_scale(self, vmin, vmax, minpos):
        """Limit scale range."""
        if not numpy.isfinite(minpos):
            minpos = 1e-300
        return (
            minpos if vmin <= 0 else vmin,
            minpos if vmax <= 0 else vmax,
        )

    def get_transform(self):
        """Get the transform."""
        return InverseScale.InverseTransform()

    class InverseTransform(transforms.Transform):
        """The transform to invert the scaling on the axis."""

        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True

        def inverted(self):
            """Get the inverse transform."""
            return InverseScale.InverseTransform()

        def transform_non_affine(self, a):
            """Transform data."""
            # Don't spam about invalid divide by zero errors
            with numpy.errstate(divide="ignore", invalid="ignore"):
                return 1 / numpy.array(a)


class CustomScaleLocator(ticker.MaxNLocator):
    """Dynamically find tick positions on custom scales."""

    def __init__(self, is_minor=False):
        self.is_minor = is_minor

    @property
    def numticks(self):
        """Get number of ticks."""
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
        """Set number of ticks."""
        self._numticks = numticks

    def tick_values(self, vmin, vmax):
        """Get tick values."""
        vmin, vmax = transforms.nonsingular(vmin, vmax, expander=0.05)
        vmin, vmax = min(vmin, vmax), max(vmin, vmax)  # Swap values if needed
        lin_tick_pos = numpy.linspace(vmin, vmax, self.numticks)
        lin_tick_pos = lin_tick_pos[lin_tick_pos != 0]  # Remove zeroes
        if self.axis.get_scale() == "squareroot":
            tick_pos = lin_tick_pos**2
        elif self.axis.get_scale() == "inverse":
            tick_pos = 1 / lin_tick_pos
        else:
            raise ValueError("Wrong locator for the axis type")
        tick_pos = tick_pos * ((vmax - vmin) / (max(tick_pos) - min(tick_pos)))
        tick_pos *= 2 if self.axis.get_scale() == "squareroot" else 1
        return tick_pos


class RadianLocator(ticker.MultipleLocator):
    """
    Dynamically place tick positions on radian scale.

    Places ticks at a distance of pi if there's between 4 and 8 ticks
    Otherwise it places ticks at a distance of 2pi if reasonable, or with
    a multiple of 5 pi such that a number between 3 and 8 ticks are placed
    At smaller values, the distances between the ticks are a power of 2,
    multiplied by pi. e.g. (1/2)pi, (1/4)pi, (1/8)pi etc..
    """

    def __init__(self):
        super().__init__(base=self.base)

    def tick_values(self, vmin, vmax):
        """Get tick values."""
        if vmax < vmin:
            vmin, vmax = vmax, vmin

        self._edge = ticker._Edge_integer(self.base, 0)
        step = self._edge.step
        vmin -= self._offset
        vmax -= self._offset
        vmin = self._edge.ge(vmin) * step
        n = (vmax - vmin + 0.001 * step) // step
        locs = vmin - step + numpy.arange(n + 3) * step + self._offset
        return self.raise_if_exceeds(locs)

    @property
    def base(self):
        """Get base."""
        if self.axis is None:
            return numpy.pi

        vmin, vmax = self.axis.get_view_interval()
        distance = numpy.pi
        # Amount of ticks if we use a multiple of pi
        num_ticks = (vmax - vmin) / distance
        # Desired amount of ticks, should be between 3 and 8
        numticks_goal = max(1, self.axis.get_tick_space() - 4)
        numticks_goal = numpy.clip(numticks_goal, 3, 7)
        ratio = (num_ticks / numticks_goal)
        if num_ticks > 8:
            if ratio < 2:  # Use a distance of 2pi if reasonable
                return distance * 2
            # Make sure ratio is never rounded to 0:
            ratio = 5 if round(ratio / 5) == 0 else ratio
            return distance * round(ratio / 5) * 5
        elif num_ticks < 4:
            ratio = (num_ticks / numticks_goal)
            exponent = int(numpy.log2(abs(ratio)))
            result = 2**exponent  # Return distance as a power of 2
            return distance * result
        return distance


scale.register_scale(RadiansScale)
scale.register_scale(SquareRootScale)
scale.register_scale(InverseScale)
