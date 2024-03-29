# SPDX-License-Identifier: GPL-3.0-or-later
import contextlib
import io
import os
from gettext import gettext as _
from pathlib import Path

from PIL import Image

from cycler import cycler

from gi.repository import (
    Adw,
    GLib,
    GObject,
    Gdk,
    GdkPixbuf,
    Gio,
    Graphs,
    Gtk,
    Pango,
)

import graphs
from graphs import item, style_io, ui, utilities

from matplotlib import RcParams, rcParams, rcParamsDefault, rc_context
from matplotlib.figure import Figure

import numpy


def _compare_styles(a: Graphs.Style, b: Graphs.Style) -> int:
    if a.get_file() is None:
        return -1
    elif b.get_file() is None:
        return 1
    return GLib.strcmp0(a.get_name().lower(), b.get_name().lower())


def _generate_filename(name: str) -> str:
    name = name.replace("(", "").replace(")", "")
    return f"{name.lower().replace(' ', '-')}.mplstyle"


def _is_style_bright(params: RcParams):
    return utilities.get_luminance(params["axes.facecolor"]) < 150


_PREVIEW_XDATA = numpy.linspace(0, 10, 30)
_PREVIEW_YDATA1 = numpy.sin(_PREVIEW_XDATA)
_PREVIEW_YDATA2 = numpy.cos(_PREVIEW_XDATA)


def _create_preview(style: RcParams, file_format: str = "svg"):
    buffer = io.BytesIO()
    with rc_context(style):
        # set render size in inch
        figure = Figure(figsize=(5, 3))
        axis = figure.add_subplot()
        axis.spines.bottom.set_visible(True)
        axis.spines.left.set_visible(True)
        if not style["axes.spines.top"]:
            axis.tick_params(which="both", top=False, right=False)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA1)
        axis.plot(_PREVIEW_XDATA, _PREVIEW_YDATA2)
        axis.set_xlabel(_("X Label"))
        axis.set_xlabel(_("Y Label"))
        figure.savefig(buffer, format=file_format)
    return buffer


def _generate_preview(style: RcParams) -> Gdk.Texture:
    buffer = _create_preview(style)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


class StyleManager(GObject.Object, Graphs.StyleManagerInterface):
    __gtype_name__ = "GraphsStyleManager"
    __gsignals__ = {
        "add-style": (GObject.SIGNAL_RUN_FIRST, None, (str, )),
    }

    application = GObject.Property(type=Graphs.Application)
    use_custom_style = GObject.Property(type=bool, default=False)
    custom_style = GObject.Property(type=str, default="Adwaita")
    style_model = GObject.Property(type=Gio.ListStore)

    def __init__(self, application: Graphs.Application):
        # Check for Ubuntu
        gtk_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        self._system_style_name = "Yaru" \
            if "SNAP" in os.environ and gtk_theme.lower().startswith("yaru") \
            else "Adwaita"
        super().__init__(
            application=application,
            style_model=Gio.ListStore.new(Graphs.Style),
        )
        self._stylenames, self._selected_style_params = [], None
        directory = Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/styles")
        enumerator = directory.enumerate_children("default::*", 0, None)
        for file in map(enumerator.get_child, enumerator):
            style_params, name = style_io.parse(file)
            preview = _generate_preview(style_params)
            self._stylenames.append(name)
            self.props.style_model.insert_sorted(
                Graphs.Style.new(name, file, preview, False),
                _compare_styles,
            )
        enumerator.close(None)
        self._update_system_style()

        # generate system style preview
        def _stylename_to_array(stylename):
            style = style_io.parse(
                Gio.File.new_for_uri(
                    "resource:///se/sjoerd/Graphs/styles/"
                    + _generate_filename(stylename),
                ),
            )[0]
            buffer = _create_preview(style, file_format="png")
            return numpy.array(Image.open(buffer).convert("RGB"))

        light_array = _stylename_to_array(self._system_style_name)
        dark_array = _stylename_to_array(self._system_style_name + " Dark")
        height, width = light_array.shape[0:2]
        # create combined image
        stitched_array = numpy.concatenate(
            (light_array[:, :width // 2], dark_array[:, width // 2:]),
            axis=1,
        )
        self.props.style_model.insert(
            0,
            Graphs.Style.new(
                _("System"),
                None,
                Gdk.Texture.new_for_pixbuf(
                    GdkPixbuf.Pixbuf.new_from_bytes(
                        GLib.Bytes.new(stitched_array.tobytes()),
                        0,
                        False,
                        8,
                        width,
                        height,
                        width * 3,
                    ),
                ),
                False,
            ),
        )

        config_dir = utilities.get_config_directory()
        self._style_dir = config_dir.get_child_for_display_name("styles")
        if not self._style_dir.query_exists(None):
            self._style_dir.make_directory_with_parents(None)
        enumerator = self._style_dir.enumerate_children("default::*", 0, None)
        for file in map(enumerator.get_child, enumerator):
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
            "use_custom_style",
            self,
            "use_custom_style",
            1 | 2,
        )
        figure_settings.bind_property(
            "custom_style",
            self,
            "custom_style",
            1 | 2,
        )

        def on_style_select(_a, _b):
            self._on_style_change(True)

        application.get_style_manager().connect("notify", on_style_select)
        for prop in ("use-custom-style", "custom-style"):
            figure_settings.connect(f"notify::{prop}", on_style_select)
        self._on_style_change()

    def _add_user_style(
        self,
        file: Gio.File,
        style_params: RcParams = None,
        name: str = None,
    ) -> None:
        if style_params is None:
            tmp_style_params, name = style_io.parse(file)
            style_params = self.complete_style(tmp_style_params)
        if name in self._stylenames:
            new_name = utilities.get_duplicate_string(name, self._stylenames)
            file.delete(None)
            file = self._style_dir.get_child_for_display_name(
                _generate_filename(new_name),
            )
            style_io.write(style_params, new_name, file)
        self._stylenames.append(name)
        self.props.style_model.insert_sorted(
            Graphs.Style(
                name=name,
                file=file,
                mutable=True,
                preview=_generate_preview(style_params),
                light=_is_style_bright(style_params),
            ),
            _compare_styles,
        )
        self.emit("add-style", name)

    def get_style_model(self) -> Gio.ListStore:
        return self.props.style_model

    def get_stylenames(self) -> list:
        return self._stylenames

    def get_style_dir(self) -> Gio.File:
        return self._style_dir

    def get_selected_style_params(self) -> RcParams:
        return self._selected_style_params

    def get_system_style_params(self) -> RcParams:
        return self._system_style_params

    def _on_file_change(
        self,
        _monitor,
        file: Gio.File,
        _other_file,
        event_type: int,
    ) -> None:
        if Path(file.peek_path()).stem.startswith("."):
            return
        possible_visual_impact = False
        stylename = None
        style_model = self.get_style_model()
        if event_type == 2:
            for index, style in enumerate(style_model):
                file2 = style.get_file()
                if file2 is not None and file.equal(file2):
                    stylename = style.get_name()
                    self._stylenames.remove(stylename)
                    style_model.remove(index)
                    break
            if stylename is None:
                return
            possible_visual_impact = True
        else:
            tmp_style_params, stylename = style_io.parse(file)
            style_params = self.complete_style(tmp_style_params)
        if event_type == 1:
            for obj in style_model:
                if obj.get_name() == stylename:
                    obj.set_preview(_generate_preview(style_params))
                    obj.set_light(_is_style_bright(style_params))
                    break
            possible_visual_impact = False
        elif event_type == 3:
            self._add_user_style(file, style_params, stylename)
        if possible_visual_impact \
                and self.props.use_custom_style \
                and self.props.custom_style == stylename \
                and event_type != 2:
            self._on_style_change()

    def _on_style_change(self, override: bool = False) -> None:
        rcParams.update(rcParamsDefault)
        old_style = self._selected_style_params
        self._update_system_style()
        self._update_selected_style()
        data = self.props.application.get_data()
        if old_style is not None and override:
            old_colors = old_style["axes.prop_cycle"].by_key()["color"]
            color_cycle = self._selected_style_params["axes.prop_cycle"
                                                      ].by_key()["color"]
            for item_ in data:
                item_.reset(old_style, self._selected_style_params)
            count = 0
            for item_ in data:
                if isinstance(item_, item.DataItem) \
                        and item_.get_color() in old_colors:
                    if count > len(color_cycle):
                        count = 0
                    item_.set_color(color_cycle[count])
                    count += 1

        canvas = graphs.canvas.Canvas(
            self.props.application,
            self._selected_style_params,
        )
        figure_settings = data.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ("use_custom_style", "custom_style"):
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)
        data.bind_property("items", canvas, "items", 2)
        window = self.props.application.get_window()
        headerbar = window.get_content_headerbar()
        headerbar.provider = Gtk.CssProvider()

        # Set headerbar color and contrast
        bg_color = self._selected_style_params["figure.facecolor"]
        contrast = utilities.get_luminance(bg_color)
        color = "@dark_5" if contrast > 150 else "@light_1"
        css = f"headerbar {{ background-color: {bg_color}; color: {color}; }}"
        context = headerbar.get_style_context()
        headerbar.provider.load_from_data(css.encode())
        context.add_provider(
            headerbar.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        window.set_canvas(canvas)
        window.get_cut_button().bind_property(
            "sensitive",
            canvas,
            "highlight_enabled",
            2,
        )

    def _update_system_style(self) -> None:
        system_style = self._system_style_name
        if Adw.StyleManager.get_default().get_dark():
            system_style += " Dark"
        filename = _generate_filename(system_style)
        self._system_style_params = style_io.parse(
            Gio.File.new_for_uri(
                "resource:///se/sjoerd/Graphs/styles/" + filename,
            ),
        )[0]

    def _update_selected_style(self) -> None:
        self._selected_style_params = None
        if self.props.use_custom_style:
            stylename = self.props.custom_style
            for style in self.props.style_model:
                if stylename == style.get_name():
                    try:
                        style_params = style_io.parse(style.get_file())[0]
                        if style.get_mutable():
                            style_params = self.complete_style(style_params)
                        self._selected_style_params = style_params
                        return
                    except (ValueError, SyntaxError, AttributeError):
                        self._reset_selected_style(
                            _(
                                f"Could not parse {stylename}, loading "
                                "system preferred style",
                            ).format(stylename=stylename),
                        )
                    break
            if self._selected_style_params is None:
                self._reset_selected_style(
                    _(
                        f"Plot style {stylename} does not exist "
                        "loading system preferred",
                    ).format(stylename=stylename),
                )
        self._selected_style_params = self._system_style_params

    def _reset_selected_style(self, message: str) -> None:
        self.props.use_custom_style = False
        self.props.custom_style = self._system_style_name
        self.props.application.get_window().add_toast_string(message)

    def copy_style(self, template: str, new_name: str) -> None:
        new_name = utilities.get_duplicate_string(
            new_name,
            self._stylenames,
        )
        destination = self._style_dir.get_child_for_display_name(
            _generate_filename(new_name),
        )
        for style in self.props.style_model:
            if template == style.get_name():
                style_params = style_io.parse(style.get_file())[0]
                source = self.complete_style(style_params) \
                    if style.get_mutable() else style_params
                break
        style_io.write(destination, new_name, source)

    def complete_style(self, params: RcParams) -> RcParams:
        for key, value in self._system_style_params.items():
            if key not in params:
                params[key] = value
        return params

    def delete_style(self, file: Gio.File) -> None:
        style_model = self.props.style_model
        for index, style in enumerate(style_model):
            if style is not None:
                file2 = style.get_file()
                if file2 is not None and file.equal(file2):
                    stylename = style.get_name()
                    style_model.remove(index)
                    self._stylenames.remove(stylename)
                    self.props.use_custom_style = False
                    self.props.custom_style = self._system_style_name


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_preview.ui")
class StylePreview(Gtk.AspectFrame):
    __gtype_name__ = "GraphsStylePreview"
    label = Gtk.Template.Child()
    picture = Gtk.Template.Child()
    edit_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.provider = Gtk.CssProvider()
        self.edit_button.get_style_context().add_provider(
            self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    @GObject.Property(type=Graphs.Style)
    def style(self):
        return self._style

    @style.setter
    def style(self, style):
        self._style = style
        self._style.bind_property("name", self, "name", 2)
        self._style.bind_property("preview", self, "preview", 2)

    @GObject.Property(type=str, default="", flags=2)
    def name(self):
        pass

    @name.setter
    def name(self, name):
        self.label.set_label(utilities.shorten_label(name))

    @GObject.Property(type=Gdk.Texture, flags=2)
    def preview(self):
        pass

    @preview.setter
    def preview(self, texture):
        self.picture.set_paintable(texture)
        if self._style.get_mutable():
            color = "@light_1" if self._style.get_light() else "@dark_5"
            self.provider.load_from_data(f"button {{ color: {color}; }}", -1)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/add_style.ui")
class AddStyleDialog(Adw.Dialog):
    __gtype_name__ = "GraphsAddStyleDialog"
    new_style_name = Gtk.Template.Child()
    style_templates = Gtk.Template.Child()

    style_manager = GObject.Property(type=StyleManager)

    def __init__(self, parent):
        style_manager = parent.props.application.get_figure_style_manager()
        super().__init__(style_manager=style_manager)
        self._styles = sorted(style_manager.get_stylenames())
        self.style_templates.set_model(Gtk.StringList.new(self._styles))
        if style_manager.props.use_custom_style:
            new_style = style_manager.props.custom_style
            index = self._styles.index(new_style)
            self.style_templates.set_selected(index)
        self.present(parent)

    @Gtk.Template.Callback()
    def on_template_changed(self, _a, _b):
        self.new_style_name.set_text(
            utilities.get_duplicate_string(
                self.style_templates.get_selected_item().get_string(),
                self._styles,
            ),
        )

    @Gtk.Template.Callback()
    def on_accept(self, _button):
        self.props.style_manager.copy_style(
            self.style_templates.get_selected_item().get_string(),
            self.new_style_name.get_text(),
        )
        self.close()


STYLE_DICT = {
    "linestyle": ["lines.linestyle"],
    "linewidth": ["lines.linewidth"],
    "markers": ["lines.marker"],
    "markersize": ["lines.markersize"],
    "draw_frame": [
        "axes.spines.bottom",
        "axes.spines.left",
        "axes.spines.top",
        "axes.spines.right",
    ],
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
    "value_padding": [
        "xtick.major.pad",
        "xtick.minor.pad",
        "ytick.major.pad",
        "ytick.minor.pad",
    ],
    "label_padding": ["axes.labelpad"],
    "title_padding": ["axes.titlepad"],
    "axis_width": ["axes.linewidth"],
    "text_color":
    ["text.color", "axes.labelcolor", "xtick.labelcolor", "ytick.labelcolor"],
    "tick_color": ["xtick.color", "ytick.color"],
    "axis_color": ["axes.edgecolor"],
    "grid_color": ["grid.color"],
    "grid_opacity": ["grid.alpha"],
    "background_color": ["axes.facecolor"],
    "outline_color": ["figure.facecolor", "figure.edgecolor"],
}
VALUE_DICT = {
    "linestyle": ["none", "solid", "dotted", "dashed", "dashdot"],
    "markers": [
        "none",
        ".",
        ",",
        "o",
        "v",
        "^",
        "<",
        ">",
        "8",
        "s",
        "p",
        "*",
        "h",
        "H",
        "+",
        "x",
        "D",
        "d",
        "|",
        "_",
        "P",
        "X",
    ],
    "tick_direction": ["in", "out"],
}
FONT_STYLE_DICT = {
    0: "normal",
    1: "oblique",
    2: "italic",
}
FONT_VARIANT_DICT = {
    0: "normal",
    1: "small-caps",
}


def _title_format_function(_scale, value: float) -> str:
    """Format a float value as percentage string"""
    return str(value / 2 * 100).split(".")[0] + "%"


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_editor.ui")
class StyleEditor(Adw.NavigationPage):
    __gtype_name__ = "GraphsStyleEditor"

    style_name = Gtk.Template.Child()
    font_chooser = Gtk.Template.Child()
    titlesize = Gtk.Template.Child()
    labelsize = Gtk.Template.Child()
    linestyle = Gtk.Template.Child()
    linewidth = Gtk.Template.Child()
    markers = Gtk.Template.Child()
    markersize = Gtk.Template.Child()
    draw_frame = Gtk.Template.Child()
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
        application = self.parent.props.application
        self._style_manager = application.get_figure_style_manager()

        self.titlesize.set_format_value_func(_title_format_function)
        self.labelsize.set_format_value_func(_title_format_function)

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
                button.provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def load_style(self, style):
        if not style.get_mutable():
            return
        self.style = style
        self.style_params = self._style_manager.complete_style(
            style_io.parse(self.style.get_file())[0],
        )
        stylename = self.style.get_name()
        self.set_title(stylename)
        self.style_name.set_text(stylename)
        ui.load_values_from_dict(
            self,
            {
                key:
                VALUE_DICT[key].index(self.style_params[value[0]])
                if key in VALUE_DICT else self.style_params[value[0]]
                for key,
                value in STYLE_DICT.items()
            },
        )

        # font
        font_description = Pango.FontDescription.new()
        font_size = self.style_params["font.size"]
        font_description.set_size(font_size * Pango.SCALE)
        self.titlesize.set_value(
            round(self.style_params["figure.titlesize"] * 2 / font_size, 1),
        )
        self.labelsize.set_value(
            round(self.style_params["axes.labelsize"] * 2 / font_size, 1),
        )
        font_description.set_family(self.style_params["font.sans-serif"][0])
        font_description.set_weight(self.style_params["font.weight"])
        inverted_style_dict = {b: a for a, b in FONT_STYLE_DICT.items()}
        font_description.set_style(
            inverted_style_dict[self.style_params["font.style"]],
        )
        inverted_variant_dict = {b: a for a, b in FONT_VARIANT_DICT.items()}
        font_description.set_variant(
            inverted_variant_dict[self.style_params["font.variant"]],
        )
        self.font_chooser.set_font_desc(font_description)

        for button in self.color_buttons:
            button.provider.load_from_data(
                f"button {{ color: {button.color}; }}",
                -1,
            )

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
                for item_ in STYLE_DICT[key]:
                    self.style_params[item_] = value

        # font
        font_description = self.font_chooser.get_font_desc()
        self.style_params["font.sans-serif"] = [font_description.get_family()]
        font_size = font_description.get_size() / Pango.SCALE
        for key in (
            "font.size",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
            "figure.labelsize",
        ):
            self.style_params[key] = font_size
        titlesize = round(self.titlesize.get_value() / 2 * font_size, 1)
        labelsize = round(self.labelsize.get_value() / 2 * font_size, 1)
        self.style_params["figure.titlesize"] = titlesize
        self.style_params["axes.titlesize"] = titlesize
        self.style_params["axes.labelsize"] = labelsize
        font_weight = font_description.get_weight()
        for key in (
            "font.weight",
            "axes.titleweight",
            "axes.labelweight",
            "figure.titleweight",
            "figure.labelweight",
        ):
            self.style_params[key] = font_weight
        self.style_params["font.style"] = FONT_STYLE_DICT[
            font_description.get_style()]
        self.style_params["font.variant"] = FONT_VARIANT_DICT[
            font_description.get_variant()]

        # line colors
        self.style_params["axes.prop_cycle"] = cycler(color=self.line_colors)
        self.style_params["patch.facecolor"] = self.line_colors[0]

        # name & save
        application = self.parent.props.application
        new_name = self.style_name.get_text()
        if self.style.get_name() != new_name:
            style_manager = application.get_figure_style_manager()
            new_name = utilities.get_duplicate_string(
                new_name,
                style_manager.get_stylenames(),
            )
        style_io.write(self.style.get_file(), new_name, self.style_params)
        self._style_manager._on_style_change(True)
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
                        f"button {{ color: {button.color}; }}",
                        -1,
                    )

        color = utilities.hex_to_rgba(f"{button.color}")
        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(self.parent, color, None, on_accept)

    @Gtk.Template.Callback()
    def on_linestyle(self, comborow, _b):
        self.linewidth.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def on_markers(self, comborow, _b):
        self.markersize.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def add_color(self, _button):
        self.line_colors.append("000000")
        self.reload_line_colors()

    @Gtk.Template.Callback()
    def on_delete(self, _button):

        def on_response(_dialog, response):
            if response == "cancel_delete_style":
                return
            if response == "delete_style":
                style_manager = self._style_manager
                file = self.style.get_file()
                style_manager.delete_style(file)
                file.trash(None)
                self.style = None
                self.parent.navigation_view.pop()

        dialog = ui.build_dialog("delete_style_dialog")
        dialog.set_body(
            _(f"Are you sure you want to delete {self.style.get_name()}?"),
        )
        dialog.connect("response", on_response)
        dialog.present(self.parent)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style_color_box.ui")
class StyleColorBox(Gtk.Box):
    __gtype_name__ = "GraphsStyleColorBox"
    label = Gtk.Template.Child()
    color_button = Gtk.Template.Child()

    parent = GObject.Property(type=StyleEditor)
    index = GObject.Property(type=int, default=0)

    def __init__(self, parent, index):
        super().__init__(parent=parent, index=index)
        self.label.set_label(_("Color {number}").format(number=index + 1))
        self.provider = Gtk.CssProvider()
        self.color_button.get_style_context().add_provider(
            self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )
        self._reload_color()

    def _reload_color(self):
        color = self.props.parent.line_colors[self.props.index]
        self.provider.load_from_data(
            f"button {{ color: {color}; }}",
            -1,
        )

    @Gtk.Template.Callback()
    def on_color_choose(self, _button):

        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    self.props.parent.line_colors[self.props.index] = \
                        utilities.rgba_to_hex(color)
                    self._reload_color()

        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.props.parent.parent,
            utilities.hex_to_rgba(
                self.props.parent.line_colors[self.props.index],
            ),
            None,
            on_accept,
        )

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        self.props.parent.line_colors.pop(self.props.index)
        self.props.parent.reload_line_colors()
