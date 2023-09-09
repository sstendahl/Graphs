# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
from gettext import gettext as _
from pathlib import Path

from cycler import cycler

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import file_io, ui, utilities

from matplotlib import pyplot


def get_user_styles(self):
    config_dir = utilities.get_config_directory()
    directory = config_dir.get_child_for_display_name("styles")
    if not directory.query_exists(None):
        reset_user_styles(self)
    styles = {}
    enumerator = directory.enumerate_children("default::*", 0, None)
    while 1:
        file_info = enumerator.next_file(None)
        if file_info is None:
            break
        file = enumerator.get_child(file_info)
        styles[Path(utilities.get_filename(file)).stem] = file
    enumerator.close(None)
    if not styles:
        reset_user_styles(self)
        styles = get_user_styles(self)
    return styles


def reset_user_styles(self):
    config_dir = utilities.get_config_directory()
    directory = config_dir.get_child_for_display_name("styles")
    if not directory.query_exists(None):
        directory.make_directory_with_parents(None)
    enumerator = directory.enumerate_children("default::*", 0, None)
    while 1:
        file_info = enumerator.next_file(None)
        if file_info is None:
            break
        file = enumerator.get_child(file_info)
        file.trash(None)
    enumerator.close(None)
    enumerator = Gio.File.new_for_uri(
        "resource:///se/sjoerd/Graphs/styles",
    ).enumerate_children("default::*", 0, None)
    while 1:
        file_info = enumerator.next_file(None)
        if file_info is None:
            break
        enumerator.get_child(file_info).copy(
            directory.get_child_for_display_name(file_info.get_display_name()),
            0, None,
        )
    enumerator.close(None)


def get_style(file):
    """
    Get the style based on the file.

    Returns a dictionary that has always valid keys. This is ensured through
    checking against the styles base (if available) and copying missing params
    as needed.
    """
    style = file_io.parse_style(file)
    file = Gio.File.new_for_uri(
        f"resource:///se/sjoerd/Graphs/styles/{style.name}.mplstyle",
    )
    if not file.query_exists():
        file = Gio.File.new_for_uri(
            "resource:///se/sjoerd/Graphs/styles/adwaita.mplstyle",
        )
    for key, value in file_io.parse_style(file).items():
        if key not in style:
            style[key] = value
    return style


def update(self):
    system_stylename = self.get_settings().get_string("system-style")
    if Adw.StyleManager.get_default().get_dark():
        system_stylename += "-dark"
    figure_settings = self.get_figure_settings()
    if figure_settings.get_use_custom_style():
        stylename = figure_settings.get_custom_style()
        try:
            pyplot.rcParams.update(get_style(get_user_styles(self)[stylename]))
            return
        except KeyError:
            self.get_window().add_toast_string(
                _(f"Plot style {stylename} does not exist "
                  "loading system preferred"))
            figure_settings.set_custom_style(system_stylename)
            figure_settings.set_use_custom_style(False)
    pyplot.rcParams.update(file_io.parse_style(Gio.File.new_for_uri(
        f"resource:///se/sjoerd/Graphs/styles/{system_stylename}.mplstyle",
    )))


STYLE_DICT = {
    "linestyle": ["lines.linestyle"],
    "linewidth": ["lines.linewidth"],
    "markers": ["lines.marker"],
    "markersize": ["lines.markersize"],
    "tick_direction": ["xtick.direction", "ytick.direction"],
    "minor_ticks": ["xtick.minor.visible", "ytick.minor.visible"],
    "major_tick_width": ["xtick.major.width", "ytick.major.width"],
    "minor_tick_width": ["xtick.minor.width", "ytick.minor.width"],
    "major_tick_length": ["xtick.major.size", "ytick.major.size"],
    "minor_tick_length": ["xtick.minor.size", "ytick.minor.size"],
    "tick_bottom": ["xtick.bottom"],
    "tick_left": ["ytick.left"],
    "tick_top": ["xtick.top"],
    "tick_right": ["ytick.right"],
    "show_grid": ["axes.grid"],
    "grid_linewidth": ["grid.linewidth"],
    "value_padding": ["xtick.major.pad", "xtick.minor.pad",
                      "ytick.major.pad", "ytick.minor.pad"],
    "label_padding": ["axes.labelpad"],
    "title_padding": ["axes.titlepad"],
    "axis_width": ["axes.linewidth"],
    "text_color": ["text.color", "axes.labelcolor", "xtick.labelcolor",
                   "ytick.labelcolor"],
    "tick_color": ["xtick.color", "ytick.color"],
    "axis_color": ["axes.edgecolor"],
    "grid_color": ["grid.color"],
    "grid_opacity": ["grid.alpha"],
    "background_color": ["axes.facecolor"],
    "outline_color": ["figure.facecolor", "figure.edgecolor"],
}
VALUE_DICT = {
    "linestyle": ["none", "solid", "dotted", "dashed", "dashdot"],
    "markers": ["none", ".", ",", "o", "v", "^", "<", ">", "8", "s", "p", "*",
                "h", "H", "+", "x", "D", "d", "|", "_", "P", "X"],
    "tick_direction": ["in", "out"],
}


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_window.ui")
class StylesWindow(Adw.Window):
    __gtype_name__ = "StylesWindow"

    leaflet = Gtk.Template.Child()
    styles_box = Gtk.Template.Child()
    line_colors_box = Gtk.Template.Child()

    style_name = Gtk.Template.Child()
    font_chooser = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markers = Gtk.Template.Child()
    markersize = Gtk.Template.Child()
    tick_direction = Gtk.Template.Child()
    minor_ticks = Gtk.Template.Child()
    major_tick_width = Gtk.Template.Child()
    minor_tick_width = Gtk.Template.Child()
    major_tick_length = Gtk.Template.Child()
    minor_tick_length = Gtk.Template.Child()
    tick_bottom = Gtk.Template.Child()
    tick_left = Gtk.Template.Child()
    tick_top = Gtk.Template.Child()
    tick_right = Gtk.Template.Child()
    show_grid = Gtk.Template.Child()
    grid_linewidth = Gtk.Template.Child()
    grid_opacity = Gtk.Template.Child()
    value_padding = Gtk.Template.Child()
    label_padding = Gtk.Template.Child()
    title_padding = Gtk.Template.Child()
    axis_width = Gtk.Template.Child()
    text_color = Gtk.Template.Child()
    tick_color = Gtk.Template.Child()
    axis_color = Gtk.Template.Child()
    grid_color = Gtk.Template.Child()
    background_color = Gtk.Template.Child()
    outline_color = Gtk.Template.Child()

    def __init__(self, application):
        super().__init__(application=application,
                         transient_for=application.get_window())
        self.styles = []
        self.style = None
        self.reload_styles()

        # color actions
        self.color_buttons = [
            self.text_color,
            self.tick_color,
            self.axis_color,
            self.grid_color,
            self.background_color,
            self.outline_color,
        ]
        for button in self.color_buttons:
            button.connect("clicked", self.on_color_change)
            button.provider = Gtk.CssProvider()
            button.get_style_context().add_provider(
                button.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # line colors
        self.color_boxes = {}

        self.present()

    @Gtk.Template.Callback()
    def back(self, _button):
        self.save_style()
        self.reload_styles()
        self.style = None
        self.leaflet.navigate(0)
        self.set_title(_("Styles"))

    @Gtk.Template.Callback()
    def edit_line_colors(self, _button):
        self.leaflet.navigate(1)
        self.set_title(
            _("{name} - line colors").format(name=self.style.name))

    @Gtk.Template.Callback()
    def back_line_colors(self, _):
        self.leaflet.navigate(0)
        self.set_title(self.style.name)

    def load_style(self):
        self.style_name.set_text(self.style.name)
        ui.load_values_from_dict(self, {
            key: VALUE_DICT[key].index(self.style[value[0]])
            if key in VALUE_DICT else self.style[value[0]]
            for key, value in STYLE_DICT.items()
        })

        # font
        font_description = self.font_chooser.get_font_desc().from_string(
            f"{self.style['font.sans-serif']} {self.style['font.size']}")
        self.font_chooser.set_font_desc(font_description)

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: {button.color}; }}", -1)

        # line colors
        for color in self.style["axes.prop_cycle"].by_key()["color"]:
            box = StyleColorBox(self, color)
            self.line_colors_box.append(box)
            self.color_boxes[box] = self.line_colors_box.get_last_child()

    def save_style(self):
        new_values = ui.save_values_to_dict(self, STYLE_DICT.keys())
        for key, value in new_values.items():
            if value is not None:
                with contextlib.suppress(KeyError):
                    value = VALUE_DICT[key][value]
                for item in STYLE_DICT[key]:
                    self.style[item] = value

        # font
        font_description = self.font_chooser.get_font_desc()
        self.style["font.sans-serif"] = font_description.get_family()
        font_name = font_description.to_string().lower().split(" ")
        self.style["font.style"] = utilities.get_font_style(font_name)
        font_weight = utilities.get_font_weight(font_name)
        for key in ["font.weight", "axes.titleweight", "axes.labelweight",
                    "figure.titleweight", "figure.labelweight"]:
            self.style[key] = font_weight
        font_size = font_name[-1]
        for key in ["font.size", "axes.labelsize", "xtick.labelsize",
                    "ytick.labelsize", "axes.titlesize", "legend.fontsize",
                    "figure.titlesize", "figure.labelsize"]:
            self.style[key] = font_size

        # line colors
        line_colors = []
        for color_box, list_box in self.color_boxes.copy().items():
            line_colors.append(color_box.color_button.color)
            self.line_colors_box.remove(list_box)
            del self.color_boxes[color_box]
        self.style["axes.prop_cycle"] = cycler(color=line_colors)
        self.style["patch.facecolor"] = line_colors[0]

        # name & save
        config_dir = utilities.get_config_directory()
        directory = config_dir.get_child_for_display_name("styles")
        file = \
            directory.get_child_for_display_name(f"{self.style.name}.mplstyle")
        file_io.write_style(file, self.style)

        figure_settings = self.get_application().get_figure_settings()
        if figure_settings.get_use_custom_style() \
                and figure_settings.get_custom_style() == self.style.name:
            ui.reload_canvas(self.get_application())

    @Gtk.Template.Callback()
    def add_color(self, _button):
        box = StyleColorBox(self, "#000000")
        self.line_colors_box.append(box)
        self.color_boxes[box] = self.line_colors_box.get_last_child()

    @Gtk.Template.Callback()
    def add_style(self, _button):
        AddStyleWindow(self.get_application(), self)

    @Gtk.Template.Callback()
    def reset_styles(self, _button):
        def on_accept(_dialog, response):
            if response == "reset":
                reset_user_styles(self.get_application())
                self.reload_styles()
        body = _("Are you sure you want to reset to the default styles?")
        dialog = ui.build_dialog("reset_to_defaults")
        dialog.set_body(body)
        dialog.set_transient_for(self)
        dialog.connect("response", on_accept)
        dialog.present()

    def reload_styles(self):
        for box in self.styles.copy():
            self.styles.remove(box)
            self.styles_box.remove(self.styles_box.get_row_at_index(0))
        for style, file in \
                sorted(get_user_styles(self.get_application()).items()):
            box = StyleBox(self, style, file)
            figure_settings = self.get_application().get_figure_settings()
            if not (figure_settings.get_use_custom_style()
                    and figure_settings.get_custom_style() == self.style):
                box.check_mark.hide()
                box.label.set_hexpand(True)
            self.styles.append(box)
            self.styles_box.append(box)

    @Gtk.Template.Callback()
    def on_close(self, _button):
        if self.style is not None:
            self.save_style()
        self.destroy()

    def on_color_change(self, button):
        color = utilities.hex_to_rgba(f"{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.get_application().get_window(), color, None,
            self.on_color_change_accept, button)

    def on_color_change_accept(self, dialog, result, button):
        try:
            color = dialog.choose_rgba_finish(result)
            if color is not None:
                button.color = utilities.rgba_to_hex(color)
                button.provider.load_from_data(
                    f"button {{ color: {button.color}; }}", -1)
        except GLib.GError:
            pass


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_box.ui")
class StyleBox(Gtk.Box):
    __gtype_name__ = "StyleBox"
    label = Gtk.Template.Child()
    check_mark = Gtk.Template.Child()

    def __init__(self, parent, style, file):
        super().__init__()
        self.parent, self.style, self.file = parent, style, file
        self.label.set_label(utilities.shorten_label(self.style, 50))

    @Gtk.Template.Callback()
    def on_edit(self, _button):
        self.parent.style = get_style(self.file)
        self.parent.load_style()
        self.parent.leaflet.navigate(1)
        self.parent.set_title(self.style)

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        def remove_style(_dialog, response):
            if response == "delete":
                self.file.trash(None)
                self.parent.reload_styles()
        body = _(
            "Are you sure you want to delete the {stylename} style?",
        ).format(stylename=self.style)
        dialog = ui.build_dialog("delete_style")
        dialog.set_body(body)
        dialog.set_transient_for(self.parent)
        dialog.connect("response", remove_style)
        dialog.present()


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_color_box.ui")
class StyleColorBox(Gtk.Box):
    __gtype_name__ = "StyleColorBox"
    label = Gtk.Template.Child()
    color_button = Gtk.Template.Child()

    def __init__(self, parent, color):
        super().__init__()
        self.parent = parent
        self.label.set_label(
            _("Color {}").format(len(self.parent.color_boxes) + 1))
        self.color_button.color = color
        self.color_button.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.color_button.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.color_button.provider.load_from_data(
            f"button {{ color: {color}; }}", -1)
        self.color_button.connect("clicked", self.parent.on_color_change)

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        self.parent.line_colors_box.remove(self.parent.color_boxes[self])
        del self.parent.color_boxes[self]
        if not self.parent.color_boxes:
            self.parent.add_color(None)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_style.ui")
class AddStyleWindow(Adw.Window):
    __gtype_name__ = "AddStyleWindow"
    new_style_name = Gtk.Template.Child()
    style_templates = Gtk.Template.Child()

    def __init__(self, application, parent):
        super().__init__(application=application,
                         transient_for=parent)
        self.styles = get_user_styles(parent)
        self.style_templates.set_model(Gtk.StringList.new(
            sorted(self.styles.keys()),
        ))
        self.present()

    @Gtk.Template.Callback()
    def on_template_changed(self, _a, _b):
        self.new_style_name.set_text(_("{name} (copy)").format(
            name=self.style_templates.get_selected_item().get_string(),
        ))

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        new_style = self.new_style_name.get_text()
        i = 0
        for style_1 in self.styles.keys():
            if new_style == style_1:
                while True:
                    i += 1
                    if f"{new_style} ({i})" not in self.styles.keys():
                        new_style = f"{new_style} ({i})"
                        break
        config_dir = utilities.get_config_directory()
        directory = config_dir.get_child_for_display_name("styles")
        destination = directory.get_child_for_display_name(
            f"{new_style}.mplstyle")
        self.styles[
            self.style_templates.get_selected_item().get_string()
        ].copy(destination, 0, None)
        self.get_transient_for().reload_styles()
        self.close()
