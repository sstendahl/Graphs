# SPDX-License-Identifier: GPL-3.0-or-later
from gettext import gettext as _
from pathlib import Path

from cycler import cycler

from gi.repository import Adw, GLib, Gio, Gtk

from graphs import file_io, graphs, misc, ui, utilities


def _styles_in_directory(directory):
    enumerator = directory.enumerate_children("default::*", 0, None)
    styles = {}
    loop = True
    while loop:
        file_info = enumerator.next_file(None)
        if file_info is None:
            loop = False
            continue
        file = enumerator.get_child(file_info)
        filename = file.query_info("standard::*", 0, None).get_display_name()
        styles[Path(filename).stem] = file
    enumerator.close(None)
    return styles


def get_system_styles(self):
    return _styles_in_directory(
        Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/styles"))


def get_user_styles(self):
    config_dir = utilities.get_config_directory()
    directory = config_dir.get_child_for_display_name("styles")
    if not directory.query_exists(None):
        reset_user_styles(self)
    styles = _styles_in_directory(directory)
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
    loop = True
    while loop:
        file_info = enumerator.next_file(None)
        if file_info is None:
            loop = False
            continue
        file = enumerator.get_child(file_info)
        file.trash(None)
    enumerator.close(None)
    for style, file in get_system_styles(self).items():
        style_file = directory.get_child_for_display_name(f"{style}.mplstyle")
        file.copy(style_file, 0, None)


def get_system_preferred_style(self):
    system_style = "adwaita"
    if Adw.StyleManager.get_default().get_dark():
        system_style += "-dark"
    return get_system_styles(self)[system_style]


def get_preferred_style(self):
    if not self.plot_settings.use_custom_plot_style:
        return get_system_preferred_style(self)
    stylename = self.plot_settings.custom_plot_style
    try:
        return get_user_styles(self)[stylename]
    except KeyError:
        self.main_window.add_toast(
            _(f"Plot style {stylename} does not exist "
              "loading system preferred"))
        self.plot_settings.use_custom_plot_style = False
        return get_system_preferred_style(self)


def get_style(self, stylename):
    """
    Get the style based on the stylename.

    Returns a dictionary that has always valid keys. This is ensured through
    checking against the styles base (if available) and copying missing params
    as needed. The property "axes.prop_cycle" is parsed into a cycler. All
    other ones are treated as a string.
    """
    user_styles = get_user_styles(self)
    system_styles = get_system_styles(self)
    style = file_io.parse_style(user_styles[stylename])
    try:
        base_style = file_io.parse_style(system_styles[stylename])
        for key, item in base_style.items():
            if key not in style.keys():
                style[key] = item
    except KeyError:
        pass
    for key, item in file_io.parse_style(system_styles["adwaita"]).items():
        if key not in style.keys():
            style[key] = item
    return style


STYLE_DICT = {
    "linestyle": ["lines.linestyle"],
    "linewidth": ["lines.linewidth"],
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
    "background_color": ["axes.facecolor"],
    "outline_color": ["figure.facecolor", "figure.edgecolor"],
}


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/plot_styles.ui")
class PlotStylesWindow(Adw.Window):
    __gtype_name__ = "PlotStylesWindow"
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
                         transient_for=application.main_window)
        self.styles = []
        self.style = None
        self.reload_styles()

        # setup editor
        utilities.populate_chooser(self.linestyle, misc.LINESTYLES)
        utilities.populate_chooser(self.markers, sorted(misc.MARKERS.keys()))
        utilities.populate_chooser(self.tick_direction, misc.TICK_DIRECTIONS)

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
        ui.load_values_from_dict(
            self,
            {key: self.style[value[0]] for key, value in STYLE_DICT.items()})

        # font
        font_description = self.font_chooser.get_font_desc().from_string(
            f"{self.style['font.sans-serif']} {self.style['font.size']}")
        self.font_chooser.set_font_desc(font_description)

        # lines
        utilities.set_chooser(
            self.markers, utilities.get_dict_by_value(
                misc.MARKERS, self.style["lines.marker"]))

        # grid
        self.grid_opacity.set_value(
            1 - (float(self.style["grid.alpha"]) * 100))

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: {button.color}; }}", -1)

        # line colors
        for color in self.style["axes.prop_cycle"].by_key()["color"]:
            box = StyleColorBox(self, color)
            self.line_colors_box.append(box)
            self.color_boxes[box] = self.line_colors_box.get_last_child()

    def save_style(self):
        new_values = {key: None for key in STYLE_DICT.keys()}
        ui.save_values_to_dict(self, new_values)
        for key, value in new_values.items():
            if value is not None:
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

        # lines
        self.style["lines.marker"] = \
            misc.MARKERS[utilities.get_selected_chooser_item(self.markers)]

        # grid
        self.style["grid.alpha"] = 1 - (self.grid_opacity.get_value() / 100)

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

    @Gtk.Template.Callback()
    def add_color(self, _button):
        box = StyleColorBox(self, "#000000")
        self.line_colors_box.append(box)
        self.color_boxes[box] = self.line_colors_box.get_last_child()

    @Gtk.Template.Callback()
    def add_style(self, _button):
        AddStyleWindow(self.props.application, self)

    @Gtk.Template.Callback()
    def reset_styles(self, _button):
        def on_accept(_dialog, response):
            if response == "reset":
                reset_user_styles(self.props.application)
                self.reload_styles()
        dialog = ui.build_dialog("reset_styles")
        dialog.set_transient_for(self)
        dialog.connect("response", on_accept)
        dialog.present()

    def reload_styles(self):
        for box in self.styles.copy():
            self.styles.remove(box)
            self.styles_box.remove(self.styles_box.get_row_at_index(0))
        for style, file in \
                sorted(get_user_styles(self.props.application).items()):
            box = StyleBox(self, style)
            if not file.equal(get_preferred_style(self.props.application)):
                box.check_mark.hide()
                box.label.set_hexpand(True)
            self.styles.append(box)
            self.styles_box.append(box)

    @Gtk.Template.Callback()
    def on_close(self, _button):
        if self.style is not None:
            self.save_style()
        graphs.reload(self.props.application)
        self.destroy()

    def on_color_change(self, button):
        color = utilities.hex_to_rgba(f"{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.props.application.main_window, color, None,
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

    def __init__(self, parent, style):
        super().__init__()
        self.parent = parent
        self.style = style
        self.label.set_label(utilities.shorten_label(self.style, 50))

    @Gtk.Template.Callback()
    def on_edit(self, _button):
        self.parent.style = get_style(
            self.parent.props.application, self.style)
        self.parent.load_style()
        self.parent.leaflet.navigate(1)
        self.parent.set_title(self.style)

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        style = self.style

        def remove_style(_dialog, response):
            if response == "delete":
                get_user_styles(
                    self.parent.props.application)[style].trash(None)
                self.parent.reload_styles()
        body = _("Are you sure you want to delete the {} style?").format(style)
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
    plot_style_templates = Gtk.Template.Child()

    def __init__(self, application, parent):
        super().__init__(application=application,
                         transient_for=parent)
        self.parent = parent
        utilities.populate_chooser(
            self.plot_style_templates,
            sorted(get_user_styles(self.parent).keys()), False)
        self.present()

    @Gtk.Template.Callback()
    def on_template_changed(self, _a, _b):
        selected_item = \
            utilities.get_selected_chooser_item(self.plot_style_templates)
        self.new_style_name.set_text(
            _("{name} (copy)").format(name=selected_item))

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        style = utilities.get_selected_chooser_item(self.plot_style_templates)
        new_style = self.new_style_name.get_text()
        i = 0
        user_styles = get_user_styles(self.props.application)
        for style_1 in user_styles.keys():
            if new_style == style_1:
                while True:
                    i += 1
                    if f"{new_style} ({i})" not in user_styles.keys():
                        new_style = f"{new_style} ({i})"
                        break
        config_dir = utilities.get_config_directory()
        directory = config_dir.get_child_for_display_name("styles")
        destination = directory.get_child_for_display_name(
            f"{new_style}.mplstyle")
        user_styles[style].copy(destination, 0, None)
        self.parent.reload_styles()
        self.close()
