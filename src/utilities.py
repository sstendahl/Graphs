# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import operator as op
import re
from gettext import gettext as _

from gi.repository import GLib, Gdk, Gio, Gtk

from matplotlib import pyplot

import numpy


def get_font_weight(font_name):
    """Get the weight of the font that is used using the full font name"""
    valid_weights = ["normal", "bold", "heavy",
                     "light", "ultrabold", "ultralight"]
    if font_name[-2] != "italic":
        new_weight = font_name[-2]
    else:
        new_weight = font_name[-3]
    if new_weight not in valid_weights:
        new_weight = "normal"
    return new_weight


def get_font_style(font_name):
    """Get the style of the font that is used using the full font name"""
    new_style = "normal"
    if font_name[-2] == ("italic" or "oblique" or "normal"):
        new_style = font_name[-2]
    return new_style


def hex_to_rgba(hex_str):
    rgba = Gdk.RGBA()
    rgba.parse(str(hex_str))
    return rgba


def rgba_to_hex(rgba):
    return "#{:02x}{:02x}{:02x}".format(
        round(rgba.red * 255),
        round(rgba.green * 255),
        round(rgba.blue * 255))


def rgba_to_tuple(rgba, alpha=False):
    if alpha:
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)
    return (rgba.red, rgba.green, rgba.blue)


def swap(str1):
    str1 = str1.replace(",", "third")
    str1 = str1.replace(".", ", ")
    return str1.replace("third", ".")


def get_value_at_fraction(fraction, start, end, scale):
    """
    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis.
    """
    if scale == 0 or scale == 2:  # Linear or radian scale
        return start + fraction * (end - start)
    elif scale == 1:  # Logarithmic scale
        log_start = numpy.log10(start)
        log_end = numpy.log10(end)
        log_range = log_end - log_start
        log_value = log_start + log_range * fraction
        return pow(10, log_value)
    elif scale == 3:  # Square root scale
        # Use min limit as defined by scales.py
        start = max(0, start)
        sqrt_start = numpy.sqrt(start)
        sqrt_end = numpy.sqrt(end)
        sqrt_range = sqrt_end - sqrt_start
        sqrt_value = sqrt_start + sqrt_range * fraction
        return sqrt_value * sqrt_value
    elif scale == 4:  # Inverted scale (1/X)'
        # Use min limit as defined by scales.py if min equals zero
        start = end / 10 if end > 0 and start <= 0 else start
        scaled_range = 1 / start - 1 / end

        # Calculate the inverse-scaled value at the given percentage
        scaled_value = 1 / (1 / end + fraction * scaled_range)
        return scaled_value


def get_fraction_at_value(value, start, end, scale):
    """
    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    if scale == 0 or scale == 2:  # Linear or radian scale
        return (value - start) / (end - start)
    elif scale == 1:  # Logarithmic scale
        log_start = numpy.log10(start)
        log_end = numpy.log10(end)
        log_value = numpy.log10(value)
        log_range = log_end - log_start
        return (log_value - log_start) / log_range
    elif scale == 3:  # Square root scale
        # Use min limit as defined by scales.py
        start = max(0, start)
        sqrt_start = numpy.sqrt(start)
        sqrt_end = numpy.sqrt(end)
        sqrt_value = numpy.sqrt(value)
        sqrt_range = sqrt_end - sqrt_start
        return (sqrt_value - sqrt_start) / sqrt_range
    elif scale == 4:  # Inverted scale (1/X)
        # Use min limit as defined by scales.py if min equals zero
        start = end / 10 if end > 0 and start <= 0 else start
        scaled_range = 1 / start - 1 / end

        # Calculate the scaled percentage corresponding to the data point
        scaled_data_point = 1 / value
        scaled_percentage = (scaled_data_point - 1 / end) / scaled_range
        return scaled_percentage


def shorten_label(label, max_length=19):
    if len(label) > max_length:
        label = f"{label[:max_length]}…"
    return label


def get_config_directory():
    main_directory = Gio.File.new_for_path(GLib.get_user_config_dir())
    return main_directory.get_child_for_display_name("Graphs")


def create_file_filters(filters, add_all=True):
    list_store = Gio.ListStore()
    for name, suffix_list in filters:
        file_filter = Gtk.FileFilter()
        file_filter.set_name(name)
        for suffix in suffix_list:
            file_filter.add_suffix(suffix)
        list_store.append(file_filter)
    if add_all:
        file_filter = Gtk.FileFilter()
        file_filter.set_name("All Files")
        file_filter.add_pattern("*")
        list_store.append(file_filter)
    return list_store


def string_to_float(string: str):
    return _eval(ast.parse(preprocess(string), mode="eval").body)


OPERATORS = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}


def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return OPERATORS[type(node.op)](_eval(node.operand))
    else:
        raise ValueError(_("No valid number specified"))


def preprocess(string: str):
    def convert_degrees(match):
        expression = match.group(1)  # Get the content inside the brackets
        return f"(({expression})*{float(numpy.pi)}/180)"

    def convert_cot(match):
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(tan({expression}))"

    def convert_sec(match):
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(cos({expression}))"

    def convert_csc(match):
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(sin({expression}))"

    string = string.replace("pi", f"({float(numpy.pi)})")
    string = string.replace("^", "**")
    string = re.sub(r"cot\((.*?)\)", convert_cot, string)
    string = re.sub(r"sec\((.*?)\)", convert_sec, string)
    string = re.sub(r"csc\((.*?)\)", convert_csc, string)
    string = re.sub(r"d\((.*?)\)", convert_degrees, string)
    return string.lower()


def get_filename(file: Gio.File):
    return file.query_info("standard::*", 0, None).get_display_name()


def optimize_limits(self):
    axes = [
        [direction, False, []]
        for direction in ["bottom", "left", "top", "right"]
    ]
    for item in self.get_data():
        for index in item.xposition * 2, 1 + item.yposition * 2:
            axes[index][1] = True
            axes[index][2].append(item)

    for count, (direction, used, items) in enumerate(axes):
        if not used:
            continue
        scale = self.get_figure_settings().get_property(f"{direction}_scale")
        datalist = [item.ydata if count % 2 else item.xdata for item in items
                    if item.props.item_type == "Item"]
        min_all, max_all = [], []
        for data in datalist:
            data = numpy.asarray(data)
            nonzero_data = list(filter(lambda x: (x != 0), data))
            if (scale == 1 or scale == 4) and len(nonzero_data) > 0:
                min_all.append(
                    nonzero_data[numpy.isfinite(nonzero_data)].min())
            else:
                min_all.append(data[numpy.isfinite(data)].min())
            max_all.append(data[numpy.isfinite(data)].max())
        min_all = min(min_all)
        max_all = max(max_all)
        span = max_all - min_all
        if scale != 1:  # For non-logarithmic scales
            # 0.05 padding on y-axis, 0.015 padding on x-axis
            padding_factor = 0.05 if count % 2 else 0.015
            max_all += padding_factor * span

            # For inverse scale, calculate padding using a factor
            min_all = (min_all - padding_factor * span if scale != 4
                       else min_all * 0.99)
        elif scale == 1:  # Use different scaling type for logarithmic scale
            # Use padding factor of 2 for y-axis, 1.025 for x-axis
            padding_factor = 2 if count % 2 else 1.025
            min_all *= 1 / padding_factor
            max_all *= padding_factor
        self.get_figure_settings().set_property(f"min_{direction}", min_all)
        self.get_figure_settings().set_property(f"max_{direction}", max_all)
    self.get_view_clipboard().add()


def get_next_color(items):
    """Get the color that is to be used for the next data set"""
    color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
    used_colors = []
    for item in items:
        used_colors.append(item.color)
        # If we've got all colors once, remove those from used_colors so we
        # can loop around
        if set(used_colors) == set(color_cycle):
            for color in color_cycle:
                used_colors.remove(color)

    for color in color_cycle:
        if color not in used_colors:
            return color
    return "000000"
