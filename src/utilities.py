# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import operator as op
import re
from gettext import gettext as _

from gi.repository import GLib, Gdk, Gio, Gtk

import numpy

import sympy


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
        return 1 / (1 / end + fraction * scaled_range)


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
        return (scaled_data_point - 1 / end) / scaled_range


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
    try:
        return _eval(ast.parse(preprocess(string), mode="eval").body)
    except SyntaxError:
        return


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
    figure_settings = self.get_figure_settings()
    axes = [
        [direction, False, [], [],
         figure_settings.get_property(f"{direction}_scale")]
        for direction in ["bottom", "left", "top", "right"]
    ]
    for item in self.get_data():
        if item.__gtype_name__ != "GraphsDataItem":
            continue
        for index in item.get_xposition() * 2, 1 + item.get_yposition() * 2:
            axes[index][1] = True
            data = numpy.asarray(item.ydata if index % 2 else item.xdata)
            data = data[numpy.isfinite(data)]
            nonzero_data = numpy.array([value for value in data if value != 0])
            axes[index][2].append(
                nonzero_data.min()
                if axes[index][4] in (1, 4) and len(nonzero_data) > 0
                else data.min(),
            )
            axes[index][3].append(data.max())

    for count, (direction, used, min_all, max_all, scale) in enumerate(axes):
        if not used:
            continue
        min_all = min(min_all)
        max_all = max(max_all)
        if scale != 1:  # For non-logarithmic scales
            span = max_all - min_all
            # 0.05 padding on y-axis, 0.015 padding on x-axis
            padding_factor = 0.05 if count % 2 else 0.015
            max_all += padding_factor * span

            # For inverse scale, calculate padding using a factor
            min_all = (min_all - padding_factor * span if scale != 4
                       else min_all * 0.99)
        else:  # Use different scaling type for logarithmic scale
            # Use padding factor of 2 for y-axis, 1.025 for x-axis
            padding_factor = 2 if count % 2 else 1.025
            min_all *= 1 / padding_factor
            max_all *= padding_factor
        figure_settings.set_property(f"min_{direction}", min_all)
        figure_settings.set_property(f"max_{direction}", max_all)
    self.get_view_clipboard().add()


def string_to_function(equation_name):
    variables = ["x"] + re.findall(
        r"\b(?!x\b|X\b|sin\b|cos\b|tan\b)[a-wy-zA-WY-Z]+\b",
        equation_name,
    )
    sym_vars = sympy.symbols(variables)
    try:
        symbolic = sympy.sympify(equation_name,
                                 locals=dict(zip(variables, sym_vars)))
        return sympy.lambdify(sym_vars, symbolic)
    except (sympy.SympifyError, TypeError):
        return
