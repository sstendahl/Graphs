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

    def __init__(self, axis, **kwargs):
        # note in older versions of matplotlib (<3.1), this worked fine.
        # mscale.ScaleBase.__init__(self)

        # In newer versions (>=3.1), you also need to pass in `axis` as an arg
        scale.ScaleBase.__init__(self, axis)


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
            return numpy.sqrt(numpy.array(a))

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

    def axisinfo(self, axis, *args, **kwargs):
        majloc = axis.get_major_locator()
        majfmt = axis.get_major_formatter()
        majfmt.set_useOffset(False)  # Prevent offset from being applied
        majfmt.set_scientific(False)  # Prevent scientific notation
        majfmt.set_useMathText(False)  # Prevent math text rendering
        return scale.AxisInfo(majloc=majloc, majfmt=majfmt)

    def transfer_transform(self, transform):
        return self.InvertedSquareRootTransform()

    def inverted(self):
        return self.InvertedSquareRootTransform()

class InverseScale(scale.ScaleBase):
    """Class for generating custom inverse scale."""
    name = "inverse"

    def set_default_locators_and_formatters(self, axis):
        class InverseLocator(ticker.Locator):
            def __call__(self):
                vmin, vmax = axis.get_view_interval()
                num_ticks = 19  # Adjust as needed
                ticklocs = numpy.linspace(vmin, vmax, num=num_ticks)
                ticklocs_transformed = 1 / numpy.array(ticklocs)
                return self.raise_if_exceeds(ticklocs_transformed)

        axis.set_major_locator(InverseLocator())
        axis.set_major_formatter(ticker.ScalarFormatter())
        axis.set_minor_locator(ticker.NullLocator())
        axis.set_minor_formatter(ticker.NullFormatter())
        def limit_range_for_scale(self, vmin, vmax, _minpos):
            return max(0, vmin), vmax

    class InverseTransform(transforms.Transform):
        """The transform to convert from linear to inverse scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Separable in X and Y dimension

        def transform_non_affine(self, a):
            return 1/numpy.array(a)

        def inverted(self):
            return InverseScale.InvertedInverseTransform()

    class InvertedInverseTransform(transforms.Transform):
        """The inverse transform to convert from square root to linear scale"""
        input_dims = 1  # Amount of input params in transform
        output_dims = 1  # Amount of output params in transform
        is_separable = True  # Separable in X and Y dimension

        def transform(self, a):
            return 1/numpy.array(a)

        def inverted(self):
            return InverseScale.InverseTransform()

    def get_transform(self):
        return self.InverseTransform()

    def axisinfo(self, axis, *args, **kwargs):
        majloc = axis.get_major_locator()
        majfmt = axis.get_major_formatter()
        majfmt.set_useOffset(False)  # Prevent offset from being applied
        majfmt.set_scientific(False)  # Prevent scientific notation
        majfmt.set_useMathText(False)  # Prevent math text rendering
        return scale.AxisInfo(majloc=majloc, majfmt=majfmt)

scale.register_scale(RadiansScale)
scale.register_scale(SquareRootScale)
scale.register_scale(InverseScale)
