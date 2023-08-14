# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import operator as op
import re
from gettext import gettext as _

from gi.repository import GLib, Gdk, Gio, Gtk

import numpy


def get_used_axes(items):
    used_axes = {
        "left": False,
        "right": False,
        "top": False,
        "bottom": False,
    }
    axes_items = {
        "left": [],
        "right": [],
        "top": [],
        "bottom": [],
    }
    for item in items:
        if item.yposition == 0:
            used_axes["left"] = True
            axes_items["left"].append(item)
        if item.yposition == 1:
            used_axes["right"] = True
            axes_items["right"].append(item)
        if item.xposition == 1:
            used_axes["top"] = True
            axes_items["top"].append(item)
        if item.xposition == 0:
            used_axes["bottom"] = True
            axes_items["bottom"].append(item)
    return used_axes, axes_items


def get_dict_by_value(dictionary, value):
    """Return the key associated with the given value in the dictionary"""
    for key, dict_value in dictionary.items():
        if dict_value == value:
            return key
    return "none"


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


def get_value_at_fraction(fraction, start, end):
    """
    Obtain the selected value of an axis given at which percentage (in terms of
    fraction) of the length this axis is selected given the start and end range
    of this axis
    """
    log_start = numpy.log10(start)
    log_end = numpy.log10(end)
    log_range = log_end - log_start
    log_value = log_start + log_range * fraction
    return pow(10, log_value)


def get_fraction_at_value(value, start, end):
    """
    Obtain the fraction of the total length of the selected axis a specific
    value corresponds to given the start and end range of the axis.
    """
    log_start = numpy.log10(start)
    log_end = numpy.log10(end)
    log_value = numpy.log10(value)
    log_range = log_end - log_start
    return (log_value - log_start) / log_range


def shorten_label(label, max_length=20):
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

    string = string.replace("pi", f"({float(numpy.pi)})")
    string = string.replace("^", "**")
    string = re.sub(r"d\((.*?)\)", convert_degrees, string)
    return string.lower()


def get_filename(file: Gio.File):
    return file.query_info("standard::*", 0, None).get_display_name()
