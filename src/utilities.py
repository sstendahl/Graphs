# SPDX-License-Identifier: GPL-3.0-or-later
import os
from gi.repository import Gdk
from pathlib import Path

import numpy


def remove_unused_config_keys(config, template):
    delete_list = []
    for key in config.keys():
        if key not in template.keys():
            delete_list.append(key)
    for key in delete_list:
        del config[key]
    return config


def sig_fig_round(number, digits):
    """Round a number to the specified number of significant digits."""
    if number is None:
        return None
    power = "{:e}".format(float(number)).split("e")[1]
    return round(float(number), -(int(power) - digits + 1))

def swap_key_positions(d, key1, key2):
    new_dict = {}
    for key, value in d.items():
        if key == key1:
            new_dict[key2] = d[key2]
        elif key == key2:
            new_dict[key1] = d[key1]
        else:
            new_dict[key] = value
    return new_dict


def get_used_axes(self):
    used_axes = {
        "left": False,
        "right": False,
        "top": False,
        "bottom": False
    }
    items = {
        "left": [],
        "right": [],
        "top": [],
        "bottom": []
    }
    for _key, item in self.datadict.items():
        if item.plot_y_position == "left":
            used_axes["left"] = True
            items["left"].append(item)
        if item.plot_y_position == "right":
            used_axes["right"] = True
            items["right"].append(item)
        if item.plot_x_position == "top":
            used_axes["top"] = True
            items["top"].append(item)
        if item.plot_x_position == "bottom":
            used_axes["bottom"] = True
            items["bottom"].append(item)
    return used_axes, items


def add_new_config_keys(config, template):
    add_list = []
    for key in template.keys():
        if key not in config.keys():
            add_list.append(key)
    for key in add_list:
        config[key] = template[key]
    return config


def set_chooser(chooser, choice):
    """Set the value of a dropdown menu to the choice parameter string"""
    model = chooser.get_model()
    for index, option in enumerate(model):
        if option.get_string() == choice:
            chooser.set_selected(index)


def empty_chooser(chooser):
    """Remove all the values in a dropdown menu"""
    model = chooser.get_model()
    for _index in model:
        model.remove(0)


def populate_chooser(chooser, chooser_list, clear=True):
    """Fill the dropdown menu with the strings in a chooser_list"""
    model = chooser.get_model()
    if clear:
        for item in model:
            model.remove(0)
    for item in chooser_list:
        if item != "nothing":
            model.append(str(item))


def get_chooser_list(chooser):
    chooser_list = []
    for item in chooser.get_model():
        chooser_list.append(item.get_string())
    return chooser_list


def get_all_names(parent):
    """Get a list of all filenames present in the datadict dictionary"""
    names = []
    for item in parent.datadict.items():
        names.append(item[1].name)
    return names


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


def get_selected_keys(self):
    """Get a list of ID's of all the datasets that are currently selected"""
    selected_keys = []
    for key, item in self.datadict.items():
        if item.selected:
            selected_keys.append(key)
    return selected_keys


def create_rgba(red, green, blue, alpha=1):
    """Create a valid RGBA object from rgba values."""
    res = Gdk.RGBA()
    res.red = red
    res.green = green
    res.blue = blue
    res.alpha = alpha
    return res


def tuple_to_rgba(rgba_tuple):
    red, green, blue = rgba_tuple
    return create_rgba(red, green, blue)


def lookup_color(self, color):
    return self.main_window.get_style_context().lookup_color(color)[1]


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
    str1 = str1.replace("third", ".")
    return str1


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


def set_attributes(new_object, template):
    """
    Sets the attributes of `new_object` to match those of `template`.
    This function sets the attributes of `new_object` to the values of the
    attributes in `template` if they don"t already exist in `new_object`.
    Additionally, it removes any attributes from `new_object` that are
    not present in `template`.
    """
    for attribute in template.__dict__:
        if not hasattr(new_object, attribute):
            setattr(new_object, attribute, getattr(template, attribute))
    for attribute in new_object.__dict__:
        if not hasattr(template, attribute):
            delattr(new_object, attribute)


def shorten_label(label, max_length=20):
    if len(label) > max_length:
        label = f"{label[:max_length]}..."
    return label


def get_config_path() -> str:
    if os.getenv("XDG_CONFIG_HOME"):
        return os.path.join(os.getenv("XDG_CONFIG_HOME"), "Graphs")
    return os.path.join(str(Path.home()), ".local", "share", "Graphs")
