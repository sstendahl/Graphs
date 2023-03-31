# SPDX-License-Identifier: GPL-3.0-or-later
import os
import shutil
from pathlib import Path

from gi.repository import Adw, Gtk

from graphs import utilities


def get_system_styles(self):
    path = os.path.join(self.modulepath, "styles")
    styles = {}
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    return styles


def get_user_styles(self):
    path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(path):
        reset_user_styles(self)
    styles = {}
    for file in sorted(os.listdir(path)):
        if os.path.isfile(os.path.join(path, file)):
            styles[Path(file).stem] = os.path.join(path, file)
    if not styles:
        reset_user_styles(self)
        styles = get_user_styles(self)
    return styles


def reset_user_styles(self):
    user_path = os.path.join(utilities.get_config_path(), "styles")
    if not os.path.exists(user_path):
        os.makedirs(user_path)
    os.chdir(user_path)
    for file in os.listdir(user_path):
        if os.path.isfile(os.path.join(user_path, file)):
            os.remove(file)
    for style, path in get_system_styles(self).items():
        shutil.copy(path, os.path.join(user_path, f"{style}.mplstyle"))


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_styles.ui")
class PlotStylesWindow(Adw.Window):
    __gtype_name__ = "PlotStylesWindow"
    leaflet = Gtk.Template.Child()
    styles_box = Gtk.Template.Child()
    editor_box = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(self.parent.main_window)
        self.styles = []
        self.reload()
        self.reset_button.connect("clicked", self.reset)
        self.set_title("Plot Styles")
        self.present()

    def edit(self, _, style):
        pass

    def delete(self, _, style):
        os.remove(get_user_styles(self.parent)[style])
        self.reload()

    def copy(self, _, style):
        loop = True
        i = 0
        while loop:
            i += 1
            new_style = f"{style} ({i})"
            loop = False
            for style_1 in get_user_styles(self.parent).keys():
                if new_style == style_1:
                    loop = True
        user_path = os.path.join(utilities.get_config_path(), "styles")
        shutil.copy(
            os.path.join(user_path, f"{style}.mplstyle"),
            os.path.join(user_path, f"{new_style}.mplstyle"))
        self.reload()

    def reset(self, _):
        reset_user_styles(self.parent)
        self.reload()

    def reload(self):
        for box in self.styles.copy():
            self.styles.remove(box)
            self.styles_box.remove(self.styles_box.get_row_at_index(0))
        for style in get_user_styles(self.parent).keys():
            box = StyleBox(self, style)
            self.styles.append(box)
            self.styles_box.append(box)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_box.ui")
class StyleBox(Gtk.Box):
    __gtype_name__ = "StyleBox"
    label = Gtk.Template.Child()
    copy_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()

    def __init__(self, parent, style):
        super().__init__()
        self.label.set_label(utilities.shorten_label(style, 50))
        self.copy_button.connect("clicked", parent.copy, style)
        self.delete_button.connect("clicked", parent.delete, style)
        self.edit_button.connect("clicked", parent.edit, style)
