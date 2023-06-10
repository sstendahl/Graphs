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
    grid_transparency = Gtk.Template.Child()
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

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.set_transient_for(self.parent.main_window)
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
        self.set_title(_("Plot Styles"))

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
        style = self.style
        self.style_name.set_text(style.name)

        # font
        font_description = self.font_chooser.get_font_desc().from_string(
            f"{style['font.sans-serif']} {style['font.size']}")
        self.font_chooser.set_font_desc(font_description)

        # lines
        utilities.set_chooser(self.linestyle, style["lines.linestyle"])
        self.linewidth.set_value(float(style["lines.linewidth"]))
        utilities.set_chooser(
            self.markers, utilities.get_dict_by_value(
                misc.MARKERS, style["lines.marker"]))
        self.markersize.set_value(float(style["lines.markersize"]))

        # ticks
        utilities.set_chooser(self.tick_direction, style["xtick.direction"])
        self.minor_ticks.set_active(style["xtick.minor.visible"])
        self.major_tick_width.set_value(float(style["xtick.major.width"]))
        self.minor_tick_width.set_value(float(style["xtick.minor.width"]))
        self.major_tick_length.set_value(float(style["xtick.major.size"]))
        self.minor_tick_length.set_value(float(style["xtick.minor.size"]))
        self.tick_bottom.set_active(style["xtick.bottom"])
        self.tick_left.set_active(style["ytick.left"])
        self.tick_top.set_active(style["xtick.top"])
        self.tick_right.set_active(style["ytick.right"])

        # grid
        self.show_grid.set_active(style["axes.grid"])
        self.grid_linewidth.set_value(float(style["grid.linewidth"]))
        self.grid_transparency.set_value(1 - float(style["grid.alpha"]))

        # padding
        self.value_padding.set_value(float(style["xtick.major.pad"]))
        self.label_padding.set_value(float(style["axes.labelpad"]))
        self.title_padding.set_value(float(style["axes.titlepad"]))

        # colors
        self.text_color.color = style["text.color"]
        self.tick_color.color = style["xtick.color"]
        self.axis_color.color = style["axes.edgecolor"]
        self.grid_color.color = style["grid.color"]
        self.background_color.color = style["axes.facecolor"]
        self.outline_color.color = style["figure.facecolor"]

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: {button.color}; }}", -1)

        # line colors
        for color in self.style["axes.prop_cycle"].by_key()["color"]:
            box = StyleColorBox(self, color)
            self.line_colors_box.append(box)
            self.color_boxes[box] = self.line_colors_box.get_last_child()

        # other
        self.axis_width.set_value(float(style["axes.linewidth"]))

    def save_style(self):
        style = self.style

        # font
        font_description = self.font_chooser.get_font_desc()
        style["font.sans-serif"] = font_description.get_family()
        font_name = font_description.to_string().lower().split(" ")
        style["font.style"] = utilities.get_font_style(font_name)
        font_weight = utilities.get_font_weight(font_name)
        style["font.weight"] = font_weight
        style["axes.titleweight"] = font_weight
        style["axes.labelweight"] = font_weight
        style["figure.titleweight"] = font_weight
        style["figure.labelweight"] = font_weight
        font_size = font_name[-1]
        style["font.size"] = font_size
        style["axes.labelsize"] = font_size
        style["xtick.labelsize"] = font_size
        style["ytick.labelsize"] = font_size
        style["axes.titlesize"] = font_size
        style["legend.fontsize"] = font_size
        style["figure.titlesize"] = font_size
        style["figure.labelsize"] = font_size

        # lines
        style["lines.linestyle"] = \
            utilities.get_selected_chooser_item(self.linestyle)
        style["lines.linewidth"] = self.linewidth.get_value()
        style["lines.marker"] = \
            misc.MARKERS[utilities.get_selected_chooser_item(self.markers)]
        style["lines.markersize"] = self.markersize.get_value()

        # ticks
        tick_direction = \
            utilities.get_selected_chooser_item(self.tick_direction)
        style["xtick.direction"] = tick_direction
        style["ytick.direction"] = tick_direction
        minor_ticks = self.minor_ticks.get_active()
        style["xtick.minor.visible"] = minor_ticks
        style["ytick.minor.visible"] = minor_ticks
        style["xtick.major.width"] = self.major_tick_width.get_value()
        style["ytick.major.width"] = self.major_tick_width.get_value()
        style["xtick.minor.width"] = self.minor_tick_width.get_value()
        style["ytick.minor.width"] = self.minor_tick_width.get_value()
        style["xtick.major.size"] = self.major_tick_length.get_value()
        style["ytick.major.size"] = self.major_tick_length.get_value()
        style["xtick.minor.size"] = self.minor_tick_length.get_value()
        style["ytick.minor.size"] = self.minor_tick_length.get_value()
        style["xtick.bottom"] = self.tick_bottom.get_active()
        style["ytick.left"] = self.tick_left.get_active()
        style["xtick.top"] = self.tick_top.get_active()
        style["ytick.right"] = self.tick_right.get_active()

        # grid
        style["axes.grid"] = self.show_grid.get_active()
        style["grid.linewidth"] = self.grid_linewidth.get_value()
        style["grid.alpha"] = 1 - self.grid_transparency.get_value()

        # padding
        style["xtick.major.pad"] = self.value_padding.get_value()
        style["xtick.minor.pad"] = self.value_padding.get_value()
        style["ytick.major.pad"] = self.value_padding.get_value()
        style["ytick.minor.pad"] = self.value_padding.get_value()
        style["axes.labelpad"] = self.label_padding.get_value()
        style["axes.titlepad"] = self.title_padding.get_value()

        # colors
        style["text.color"] = self.text_color.color
        style["axes.labelcolor"] = self.text_color.color
        style["xtick.labelcolor"] = self.text_color.color
        style["ytick.labelcolor"] = self.text_color.color
        style["xtick.color"] = self.tick_color.color
        style["ytick.color"] = self.tick_color.color
        style["axes.edgecolor"] = self.axis_color.color
        style["grid.color"] = self.grid_color.color
        style["axes.facecolor"] = self.background_color.color
        style["figure.facecolor"] = self.outline_color.color
        style["figure.edgecolor"] = self.outline_color.color

        # line colors
        line_colors = []
        for color_box, list_box in self.color_boxes.copy().items():
            line_colors.append(color_box.color_button.color)
            self.line_colors_box.remove(list_box)
            del self.color_boxes[color_box]
        style["axes.prop_cycle"] = cycler(color=line_colors)
        style["patch.facecolor"] = line_colors[0]

        # other
        style["axes.linewidth"] = self.axis_width.get_value()

        # name & save
        config_dir = utilities.get_config_directory()
        directory = config_dir.get_child_for_display_name("styles")
        file = directory.get_child_for_display_name(f"{style.name}.mplstyle")
        file_io.write_style(file, style)

    @Gtk.Template.Callback()
    def add_color(self, _button):
        box = StyleColorBox(self, "#000000")
        self.line_colors_box.append(box)
        self.color_boxes[box] = self.line_colors_box.get_last_child()

    def copy_style(self, _button, style, new_style):
        i = 0
        user_styles = get_user_styles(self.parent)
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
        self.reload_styles()

    @Gtk.Template.Callback()
    def add_style(self, _button):
        AddStyleWindow(self)

    @Gtk.Template.Callback()
    def reset_styles(self, _button):
        def on_accept(_dialog, response):
            if response == "reset":
                reset_user_styles(self.parent)
                self.reload_styles()
        dialog = ui.build_dialog("reset_styles")
        dialog.set_transient_for(self)
        dialog.connect("response", on_accept)
        dialog.present()

    def reload_styles(self):
        for box in self.styles.copy():
            self.styles.remove(box)
            self.styles_box.remove(self.styles_box.get_row_at_index(0))
        custom_style = self.parent.plot_settings.use_custom_plot_style
        for style, file in sorted(get_user_styles(self.parent).items()):
            box = StyleBox(self, style)
            if not custom_style and \
                    not file.equal(get_preferred_style(self.parent)):
                box.check_mark.hide()
                box.label.set_hexpand(True)
            self.styles.append(box)
            self.styles_box.append(box)

    @Gtk.Template.Callback()
    def on_close(self, _button):
        if self.style is not None:
            self.save_style()
        graphs.reload(self.parent)
        self.destroy()

    def on_color_change(self, button):
        color = utilities.hex_to_rgba(f"{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.parent.main_window, color, None, self.on_color_change_accept,
            button)

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
        self.parent.style = get_style(self.parent.parent, self.style)
        self.parent.load_style()
        self.parent.leaflet.navigate(1)
        self.parent.set_title(self.style)


    @Gtk.Template.Callback()
    def on_delete(self, _button):
        style = self.style
        def remove_style(_dialog, response):
            if response == "delete":
                get_user_styles(self.parent.parent)[style].trash(None)
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
        self.label.set_label(_("Color {}").format(len(parent.color_boxes) + 1))
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

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        utilities.populate_chooser(
            self.plot_style_templates,
            sorted(get_user_styles(parent).keys()), False)
        self.set_transient_for(parent)
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
        name = self.new_style_name.get_text()
        self.parent.copy_style(self, style, name)
        self.close()
