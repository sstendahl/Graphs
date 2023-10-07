# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import io
import os
from gettext import gettext as _
from pathlib import Path

from PIL import Image, ImageStat

from cycler import cycler

from gi.repository import Adw, GLib, GObject, Gdk, Gio, Graphs, Gtk

import graphs
from graphs import file_io, ui, utilities

from matplotlib import pyplot, rc_context
from matplotlib.figure import Figure

import numpy


PREVIEW_XDATA = numpy.linspace(0, 10, 1000)
PREVIEW_YDATA1 = numpy.sin(PREVIEW_XDATA)
PREVIEW_YDATA2 = numpy.cos(PREVIEW_XDATA)


def _compare_styles(a, b) -> int:
    if a.file is None:
        return -1
    elif b.file is None:
        return 1
    return GLib.strcmp0(a.name.lower(), b.name.lower())


def _generate_filename(name: str) -> str:
    name = name.replace("(", "").replace(")", "")
    return f"{name.lower().replace(' ', '-')}.mplstyle"


class StyleManager(GObject.Object, Graphs.StyleManagerInterface):
    __gtype_name__ = "GraphsStyleManager"

    application = GObject.Property(type=Graphs.Application)
    use_custom_style = GObject.Property(type=bool, default=False)
    custom_style = GObject.Property(type=str, default="adwaita")
    gtk_theme = GObject.Property(type=str, default="")

    def __init__(self, application: Graphs.Application):
        gtk_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        super().__init__(
            application=application, gtk_theme=gtk_theme.lower(),
        )
        self._stylenames = []
        self._style_model = Gio.ListStore.new(Style)
        self._cache_dir = utilities.get_cache_directory()
        if not self._cache_dir.query_exists(None):
            self._cache_dir.make_directory_with_parents(None)
        enumerator = self._cache_dir.enumerate_children("default::*", 0, None)
        while True:
            file_info = enumerator.next_file(None)
            if file_info is None:
                break
            enumerator.get_child(file_info).delete(None)
        directory = Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/styles")
        enumerator = directory.enumerate_children("default::*", 0, None)
        while True:
            file_info = enumerator.next_file(None)
            if file_info is None:
                break
            file = enumerator.get_child(file_info)
            style = file_io.parse_style(file)
            # TODO: bundle in distribution
            preview = self._generate_preview(style)
            self._stylenames.append(style.name)
            self._style_model.insert_sorted(
                Style.new(style.name, file, preview, False), _compare_styles,
            )
        enumerator.close(None)
        self._system_style = Style.new(_("System"), None, None, False)
        self._style_model.insert(0, self._system_style)

        config_dir = utilities.get_config_directory()
        self._style_dir = config_dir.get_child_for_display_name("styles")
        if not self._style_dir.query_exists(None):
            self._style_dir.make_directory_with_parents(None)
        enumerator = self._style_dir.enumerate_children("default::*", 0, None)
        while True:
            file_info = enumerator.next_file(None)
            if file_info is None:
                break
            file = enumerator.get_child(file_info)
            if file.query_file_type(0, None) != 1:
                continue
            if Path(utilities.get_filename(file)).suffix != ".mplstyle":
                continue
            self._add_user_style(file)
        enumerator.close(None)
        self._style_monitor = self._style_dir.monitor_directory(0, None)
        self._style_monitor.connect("changed", self._on_file_change)
        figure_settings = application.get_data().get_figure_settings()
        figure_settings.bind_property(
            "use_custom_style", self, "use_custom_style", 1 | 2,
        )
        figure_settings.bind_property(
            "custom_style", self, "custom_style", 1 | 2,
        )
        application.get_style_manager().connect(
            "notify", self._on_style_select,
        )
        for prop in ["use-custom-style", "custom-style"]:
            figure_settings.connect(
                f"notify::{prop}", self._on_style_select,
            )
        self._on_style_change()

    def _add_user_style(self, file: Gio.File, style_params=None):
        if style_params is None:
            style_params = _get_style(file)
        if style_params.name in self._stylenames:
            style_params.name = utilities.get_duplicate_string(
                style_params.name, self._stylenames,
            )
            file.delete(None)
            file = self._style_dir.get_child_for_display_name(
                _generate_filename(style_params.name),
            )
            file_io.write_style(style_params, file)
        preview = self._generate_preview(style_params)
        self._stylenames.append(style_params.name)
        self._style_model.insert_sorted(
            Style.new(style_params.name, file, preview, True), _compare_styles,
        )

    def get_style_model(self):
        return self._style_model

    def get_stylenames(self) -> list:
        return self._stylenames

    def get_style_dir(self) -> Gio.File:
        return self._style_dir

    def _on_file_change(self, _monitor, file, _other_file, event_type):
        if Path(file.peek_path()).stem.startswith("."):
            return
        possible_visual_impact = False
        stylename = None
        if event_type == 2:
            for index in range(self._style_model.get_n_items()):
                style = self._style_model.get_item(index)
                if style.file is not None and file.equal(style.file):
                    self._stylenames.remove(style.name)
                    self._style_model.remove(index)
                    stylename = style.name
                    break
            if stylename is None:
                return
            possible_visual_impact = True
        else:
            style = _get_style(file)
            stylename = style.name
        if event_type == 1:
            for index in range(self._style_model.get_n_items()):
                obj = self._style_model.get_item(index)
                if obj.name == stylename:
                    obj.preview = self._generate_preview(style)
                    break
            possible_visual_impact = False
        elif event_type == 3:
            self._add_user_style(file, style)
        if possible_visual_impact \
                and self.props.use_custom_style \
                and self.props.custom_style == stylename:
            self._on_style_change()

    def _on_style_select(self, _a, _b):
        settings = self.props.application.get_settings("general")
        self._on_style_change(settings.get_boolean("override-item-properties"))

    def _on_style_change(self, override=False):
        # Check for Ubuntu
        system_style = "Yaru" if "SNAP" in os.environ \
            and self.props.get_gtk_theme.startswith("yaru") else "Adwaita"
        if Adw.StyleManager.get_default().get_dark():
            system_style += " Dark"
        style_params = None
        window = self.props.application.get_window()
        if self.props.use_custom_style:
            stylename = self.props.custom_style
            for index in range(self._style_model.get_n_items()):
                style = self._style_model.get_item(index)
                if stylename == style.name:
                    if style.mutable:
                        try:
                            style_params = _get_style(style.file)
                        except (ValueError, SyntaxError, AttributeError):
                            self.props.custom_style = system_style
                            self.props.use_custom_style = False
                            window.add_toast_string(
                                _(f"Could not parse {stylename}, loading "
                                  "system preferred style").format(
                                    stylename=stylename),
                            )
                    else:
                        style_params = file_io.parse_style(style.file)
                    break
            if style_params is None:
                window.add_toast_string(
                    _(f"Plot style {stylename} does not exist "
                      "loading system preferred").format(stylename=stylename))
                self.props.custom_style = system_style
                self.props.use_custom_style = False
        if style_params is None:
            filename = _generate_filename(system_style)
            style_params = file_io.parse_style(Gio.File.new_for_uri(
                "resource:///se/sjoerd/Graphs/styles/" + filename,
            ))
        pyplot.rcParams.update(style_params)

        data = self.props.application.get_data()
        if override:
            color_cycle = pyplot.rcParams["axes.prop_cycle"].by_key()["color"]
            for item in data:
                item.reset()
            count = 0
            for item in data:
                if item.__gtype_name__ == "GraphsDataItem":
                    if count > len(color_cycle):
                        count = 0
                    item.props.color = color_cycle[count]
                    count += 1

        canvas = graphs.canvas.Canvas(self.props.application)
        figure_settings = data.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ["use_custom_style", "custom_style"]:
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)
        data.bind_property("items", canvas, "items", 2)
        window.set_canvas(canvas)
        window.get_cut_button().bind_property(
            "sensitive", canvas, "highlight_enabled", 2,
        )

    def _generate_preview(self, style: dict) -> Gio.File:
        with rc_context(style):
            # set render size in inch
            figure = Figure(figsize=(5, 3))
            axis = figure.add_subplot()
            axis.plot(PREVIEW_XDATA, PREVIEW_YDATA1)
            axis.plot(PREVIEW_XDATA, PREVIEW_YDATA2)
            axis.set_xlabel(_("X Label"))
            axis.set_xlabel(_("Y Label"))
            buffer = io.BytesIO()
            figure.savefig(buffer, format="svg")
        file = \
            self._cache_dir.get_child_for_display_name(f"{style.name}.svg")
        stream = file_io.get_write_stream(file)
        stream.write(buffer.getvalue())
        buffer.close()
        stream.close()
        return file

    def copy_style(self, template: str, new_name: str):
        new_name = utilities.get_duplicate_string(
            new_name, self._stylenames,
        )
        destination = self._style_dir.get_child_for_display_name(
            _generate_filename(new_name),
        )
        for index in range(self._style_model.get_n_items()):
            style = self._style_model.get_item(index)
            if template == style.name:
                source = _get_style(style.file) \
                    if style.mutable else file_io.parse_style(style.file)
                break
        source.name = new_name
        file_io.write_style(destination, source)


def _get_style(file: Gio.File):
    """
    Get the style based on the file.

    Returns a dictionary that has always valid keys. This is ensured through
    checking against adwaita and copying missing params as needed.
    """
    style = file_io.parse_style(file)
    adwaita = Gio.File.new_for_uri(
        "resource:///se/sjoerd/Graphs/styles/adwaita.mplstyle",
    )
    for key, value in file_io.parse_style(adwaita).items():
        if key not in style:
            style[key] = value
    return style


class Style(GObject.Object):
    name = GObject.Property(type=str, default="")
    preview = GObject.Property(type=Gio.File)
    file = GObject.Property(type=Gio.File)
    mutable = GObject.Property(type=bool, default=False)

    @staticmethod
    def new(name, file, preview, mutable):
        return Style(name=name, file=file, preview=preview, mutable=mutable)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_preview.ui")
class StylePreview(Gtk.AspectFrame):
    __gtype_name__ = "GraphsStylePreview"
    label = Gtk.Template.Child()
    picture = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()
    delete_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.provider = Gtk.CssProvider()
        self.edit_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self.delete_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    @GObject.Property(type=Style)
    def style(self):
        return self._style

    @style.setter
    def style(self, style):
        self._style = style
        self._style.bind_property("name", self.label, "label", 2)
        self._style.bind_property("preview", self, "preview", 2)

    @GObject.Property(type=Gio.File)
    def preview(self):
        pass

    @preview.setter
    def preview(self, file):
        if file is None:
            return
        texture = Gdk.Texture.new_from_file(file)
        self.picture.set_paintable(texture)
        if self._style.mutable:
            buffer = io.BytesIO(texture.save_to_png_bytes().get_data())
            mean = ImageStat.Stat(Image.open(buffer).convert("L")).mean[0]
            buffer.close()
            color = "@dark_5" if mean > 200 else "@light_1"
            self.provider.load_from_data(f"button {{ color: {color}; }}", -1)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_style.ui")
class AddStyleWindow(Adw.Window):
    __gtype_name__ = "GraphsAddStyleWindow"
    new_style_name = Gtk.Template.Child()
    style_templates = Gtk.Template.Child()

    def __init__(self, parent):
        application = parent.get_application()
        super().__init__(application=application, transient_for=parent)
        style_manager = application.get_figure_style_manager()
        self._styles = sorted(style_manager.get_stylenames())
        self.style_templates.set_model(Gtk.StringList.new(self._styles))
        self.present()

    @Gtk.Template.Callback()
    def on_template_changed(self, _a, _b):
        self.new_style_name.set_text(utilities.get_duplicate_string(
            self.style_templates.get_selected_item().get_string(),
            self._styles,
        ))

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        self.get_application().get_figure_style_manager().copy_style(
            self.style_templates.get_selected_item().get_string(),
            self.new_style_name.get_text(),
        )
        self.close()


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


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_editor.ui")
class StyleEditor(Adw.NavigationPage):
    __gtype_name__ = "GraphsStyleEditor"

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

    line_colors_box = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.style = None
        self.parent = parent

        # color buttons
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

    def load_style(self, style):
        if not style.mutable:
            return
        self.style = style
        self.style_params = _get_style(self.style.file)
        self.set_title(self.style.name)
        self.style_name.set_text(self.style.name)
        ui.load_values_from_dict(self, {
            key: VALUE_DICT[key].index(self.style_params[value[0]])
            if key in VALUE_DICT else self.style_params[value[0]]
            for key, value in STYLE_DICT.items()
        })

        # font
        # borked
        """"
        a = self.style_params['font.sans-serif']
        b = self.style_params['font.size']
        font_description = self.font_chooser.get_font_desc().from_string(
            f"{a} {b}")
        self.font_chooser.set_font_desc(font_description)
        """

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: {button.color}; }}", -1)

        # line colors
        self.line_colors = \
            self.style_params["axes.prop_cycle"].by_key()["color"]
        self.reload_line_colors()

    def save_style(self):
        if self.style is None:
            return
        new_values = ui.save_values_to_dict(self, STYLE_DICT.keys())
        for key, value in new_values.items():
            if value is not None:
                with contextlib.suppress(KeyError):
                    value = VALUE_DICT[key][value]
                for item in STYLE_DICT[key]:
                    self.style_params[item] = value

        # font
        """"
        font_description = self.font_chooser.get_font_desc()
        self.style_params["font.sans-serif"] = font_description.get_family()
        font_name = font_description.to_string().lower().split(" ")
        self.style_params["font.style"] = utilities.get_font_style(font_name)
        font_weight = utilities.get_font_weight(font_name)
        for key in ["font.weight", "axes.titleweight", "axes.labelweight",
                    "figure.titleweight", "figure.labelweight"]:
            self.style_params[key] = font_weight
        font_size = font_name[-1]
        for key in ["font.size", "axes.labelsize", "xtick.labelsize",
                    "ytick.labelsize", "axes.titlesize", "legend.fontsize",
                    "figure.titlesize", "figure.labelsize"]:
            self.style_params[key] = font_size
        """

        # line colors
        self.style_params["axes.prop_cycle"] = cycler(color=self.line_colors)
        self.style_params["patch.facecolor"] = self.line_colors[0]

        # name & save
        new_name = self.style_name.get_text()
        self.style_params.name = new_name
        file_io.write_style(self.style.file, self.style_params)
        application = self.parent.get_application()
        if self.style.name != new_name:
            style_manager = application.get_figure_style_manager()
            new_name = utilities.get_duplicate_string(
                new_name, style_manager.get_stylenames(),
            )
        figure_settings = application.get_data().get_figure_settings()
        if figure_settings.get_use_custom_style() \
                and figure_settings.get_custom_style() == self.style.name:
            figure_settings.set_custom_style(new_name)
        self.style = None

    def reload_line_colors(self):
        list_box = self.line_colors_box
        while list_box.get_last_child() is not None:
            list_box.remove(list_box.get_last_child())
        if self.line_colors:
            for index in range(len(self.line_colors)):
                list_box.append(StyleColorBox(self, index))
        else:
            self.line_colors.append("#000000")
            list_box.append(StyleColorBox(self, 0))

    def on_color_change(self, button):
        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    button.color = utilities.rgba_to_hex(color)
                    button.provider.load_from_data(
                        f"button {{ color: {button.color}; }}", -1,
                    )
        color = utilities.hex_to_rgba(f"{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(self.parent, color, None, on_accept)

    @Gtk.Template.Callback()
    def add_color(self, _button):
        self.line_colors.append("000000")
        self.reload_line_colors()


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_color_box.ui")
class StyleColorBox(Gtk.Box):
    __gtype_name__ = "GraphsStyleColorBox"
    label = Gtk.Template.Child()
    color_button = Gtk.Template.Child()

    parent = GObject.Property(type=StyleEditor)
    index = GObject.Property(type=int, default=0)

    def __init__(self, parent, index):
        super().__init__(parent=parent, index=index)
        self.label.set_label(_("Color {}").format(index + 1))
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._reload_color()

    def _reload_color(self):
        color = self.props.parent.line_colors[self.props.index]
        self.provider.load_from_data(
            f"button {{ color: {color}; }}", -1,
        )

    @Gtk.Template.Callback()
    def on_color_choose(self, _button):
        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    self.props.parent.line_colors[self.props.index] = \
                        utilities.rgba_to_hex(color)
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.props.parent.parent, utilities.hex_to_rgba(
                self.props.parent.line_colors[self.props.index],
            ), None, on_accept,
        )

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        self.props.parent.line_colors.pop(self.props.index)
        self.props.parent.reload_line_colors()
