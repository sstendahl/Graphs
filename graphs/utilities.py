# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import contextlib
import operator as op
import re
from gettext import gettext as _

from gi.repository import GLib, Gdk, Gio, Gtk

import numpy

import sympy


def hex_to_rgba(hex_str: str) -> Gdk.RGBA:
    rgba = Gdk.RGBA()
    rgba.parse(str(hex_str))
    return rgba


def get_luminance(hex_color: str) -> float:
    color = hex_color[1:]
    hex_red = int(color[0:2], base=16)
    hex_green = int(color[2:4], base=16)
    hex_blue = int(color[4:6], base=16)
    return hex_red * 0.2126 + hex_green * 0.7152 + hex_blue * 0.0722


def sig_fig_round(number: float, digits: int) -> float:
    """Round a number to the specified number of significant digits."""
    try:
        # Convert to scientific notation, and get power
        power = "{:e}".format(float(number)).split("e")[1]
    except IndexError:
        return None
    return round(float(number), -(int(power) - digits + 1))


def rgba_to_hex(rgba: Gdk.RGBA) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        round(rgba.red * 255), round(rgba.green * 255), round(rgba.blue * 255),
    )


def rgba_to_tuple(rgba: Gdk.RGBA, alpha: bool = False) -> [int, int, int]:
    if alpha:
        return (rgba.red, rgba.green, rgba.blue, rgba.alpha)
    return (rgba.red, rgba.green, rgba.blue)


def get_value_at_fraction(
    fraction: float, start: float, end: float, scale: int,
) -> float:
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


def get_fraction_at_value(
    value: float, start: float, end: float, scale: int,
) -> float:
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


def shorten_label(label: str, max_length: bool = 20) -> str:
    return f"{label[:max_length - 1]}…" if len(label) > max_length else label


def get_config_directory() -> Gio.File:
    main_directory = Gio.File.new_for_path(GLib.get_user_config_dir())
    return main_directory.get_child_for_display_name("graphs")


def create_file_filters(filters, add_all: bool = True) -> Gio.ListStore:
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


def string_to_float(string: str) -> float:
    try:
        return _eval(ast.parse(_preprocess(string), mode="eval").body)
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


def _preprocess(string: str) -> str:
    """Preprocesses an equation to be compatible with numexpr syntax"""

    def convert_degrees(match):
        """Converts degree expressions to radian expressions"""
        expression = match.group(1)  # Get the content inside the brackets
        return f"(({expression})*{float(numpy.pi)}/180)"

    def convert_cot(match):
        """Converts cotangent expressions to reciprocal tangent expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(tan({expression}))"

    def convert_sec(match):
        """Converts secant expressions to reciprocal cosine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(cos({expression}))"

    def convert_csc(match):
        """Converts cosecant expressions to reciprocal sine expressions."""
        expression = match.group(1)  # Get the content inside the brackets
        return f"1/(sin({expression}))"

    def convert_superscript(match):
        """Converts superscript expressions to Python's power operator."""
        superscript_mapping = {
            "⁰": "0",
            "¹": "1",
            "²": "2",
            "³": "3",
            "⁴": "4",
            "⁵": "5",
            "⁶": "6",
            "⁷": "7",
            "⁸": "8",
            "⁹": "9",
        }
        sequence = match.group(1)  # Get the content inside the superscript
        sequence = "".join(superscript_mapping.get(char, char)
                           for char in sequence)
        return f"**{sequence}"

    def add_asterix(match):
        """
        Adds asterix in equation when missing in case a number is followed
        by an alphabetical character, and adds parantheses around.

        Pattern is to check for least one digit, followed by at least one
        alphabetical character. e.g y = 24*x + 3sigma -> y = (24*x) + (3*sigma)
        """
        exp1, exp2 = match.group(1), match.group(2)
        return f"({exp1}*{exp2})"

    string = re.sub(r"(\d+)([a-zA-Z]+)", add_asterix, string)
    string = string.replace("pi", f"({float(numpy.pi)})")
    string = string.replace("^", "**")
    string = re.sub(r"cot\((.*?)\)", convert_cot, string)
    string = re.sub(r"sec\((.*?)\)", convert_sec, string)
    string = re.sub(r"csc\((.*?)\)", convert_csc, string)
    string = re.sub(r"d\((.*?)\)", convert_degrees, string)
    string = re.sub(r"([\u2070-\u209f\u00b0-\u00be]+)",
                    convert_superscript, string)
    return string.lower()


def get_filename(file: Gio.File) -> str:
    info = file.query_info(
        "standard::display-name", Gio.FileQueryInfoFlags.NONE, None,
    )
    if info:
        return info.get_display_name()
    return file.get_basename()


def string_to_function(equation_name: str):
    pattern = (
        r"\b(?!x\b|X\b|csc\b|cot\b|sec\b|sin\b|cos\b|log\b|tan\b|exp\b)"
        r"[a-zA-Z]+\b"
    )
    variables = ["x"] + re.findall(pattern, equation_name)
    sym_vars = sympy.symbols(variables)
    with contextlib.suppress(sympy.SympifyError, TypeError, SyntaxError):
        symbolic = sympy.sympify(
            equation_name, locals=dict(zip(variables, sym_vars)),
        )
        return sympy.lambdify(sym_vars, symbolic)


def get_duplicate_string(original_string: str, used_strings: list[str]) -> str:
    if original_string not in used_strings:
        return original_string
    m = re.compile(r"(?P<string>.+) \(\d+\)").match(original_string)
    if m:
        original_string = m.group("string")
    i = 1
    while True:
        new_string = f"{original_string} ({i})"
        if new_string not in used_strings:
            return new_string
        i += 1


def create_menu_model(data: dict) -> Gio.Menu:
    """
    Create a menu model based on a dict.

    The format should be:
    {
        *section*: (*name*, [
            (*entry*, *value*),
        ]),
    }
    Actions will be in the form of `win.*section*::*value*`.
    """
    menu = Gio.Menu.new()
    for section_name, section_data in data.items():
        section = Gio.Menu.new()
        for entry in section_data[1]:
            section.append_item(Gio.MenuItem.new(
                entry[0], f"win.{section_name}::{entry[1]}",
            ))
        menu.append_section(section_data[0], section)
    return menu
