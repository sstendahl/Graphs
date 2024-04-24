# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import contextlib
import io
import os
from gettext import gettext as _
from pathlib import Path

from cycler import cycler

from gi.repository import (
    Adw,
    GLib,
    GObject,
    Gdk,
    Gio,
    Graphs,
    Gtk,
    Pango,
)

import graphs
from graphs import item, style_io

from matplotlib import RcParams, rcParams, rcParamsDefault


def _generate_filename(name: str) -> str:
    name = name.replace("(", "").replace(")", "")
    return f"{name.lower().replace(' ', '-')}.mplstyle"


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(style: RcParams) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, style)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


class StyleManager(Graphs.StyleManager):
    """
    Main Style Manager.

    Keeps track of all files in the style dir and represents them in
    the `selection_model` property.
    """

    __gtype_name__ = "GraphsPythonStyleManager"

    def __init__(self, application: Graphs.Application):
        # Check for Ubuntu
        gtk_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        self._system_style_name = "Yaru" \
            if "SNAP" in os.environ \
            and gtk_theme.lower().startswith("yaru") \
            else "Adwaita"
        super().__init__(application=application)
        style_model = self.props.selection_model.get_model()
        self._stylenames, self._selected_style_params = [], None
        directory = Gio.File.new_for_uri("resource:///se/sjoerd/Graphs/styles")
        enumerator = directory.enumerate_children("default::*", 0, None)
        for file in map(enumerator.get_child, enumerator):
            filename = file.get_basename()
            stream = Gio.DataInputStream.new(file.read(None))
            stream.read_line_utf8(None)
            name = stream.read_line_utf8(None)[0][2:]
            preview = Gdk.Texture.new_from_resource(
                "/se/sjoerd/Graphs/" + filename.replace(".mplstyle", ".png"),
            )
            self._stylenames.append(name)
            style_model.insert_sorted(
                Graphs.Style.new(name, file, preview, False),
                Graphs.style_cmp,
            )
        enumerator.close(None)

        preview_name = self._system_style_name.lower() + ".png"
        style_model.insert(
            0,
            Graphs.Style.new(
                _("System"),
                None,
                Gdk.Texture.new_from_resource(
                    "/se/sjoerd/Graphs/system-style-" + preview_name,
                ),
                False,
            ),
        )

        self._update_system_style()
        enumerator = self.props.style_dir.enumerate_children(
            "default::*",
            0,
            None,
        )
        for file in map(enumerator.get_child, enumerator):
            if file.query_file_type(0, None) != 1:
                continue
            if Path(Graphs.tools_get_filename(file)).suffix != ".mplstyle":
                continue
            self._add_user_style(file)
        enumerator.close(None)
        self._style_monitor = self.props.style_dir.monitor_directory(0, None)
        self._style_monitor.connect("changed", self._on_file_change)

        application.get_style_manager().connect(
            "notify",
            self._on_system_style_change,
        )
        notifiers = ("custom_style", "use_custom_style")
        for prop in notifiers:
            self.connect(
                "notify::" + prop.replace("_", "-"),
                getattr(self, "_on_" + prop),
            )

        self.setup_bindings(application.get_data().get_figure_settings())
        self._on_style_change()

    def _on_system_style_change(self, _a, _b):
        if not self.props.use_custom_style:
            self._on_style_change()

    def _add_user_style(
        self,
        file: Gio.File,
        style_params: RcParams = None,
        name: str = None,
    ) -> None:
        if style_params is None:
            tmp_style_params, name = style_io.parse(file)
            style_params = self._complete_style(tmp_style_params)
        if name in self._stylenames:
            new_name = Graphs.tools_get_duplicate_string(
                name,
                self._stylenames,
            )
            file.delete(None)
            file = self.props.style_dir.get_child_for_display_name(
                _generate_filename(new_name),
            )
            style_io.write(style_params, new_name, file)
        self._stylenames.append(name)
        self.props.selection_model.get_model().insert_sorted(
            Graphs.Style(
                name=name,
                file=file,
                mutable=True,
                preview=_generate_preview(style_params),
                light=_is_style_bright(style_params),
            ),
            Graphs.style_cmp,
        )
        if not self.props.use_custom_style:
            return

        old_style = self.props.custom_style
        if old_style not in self._stylenames:
            self.props.custom_style = name

        for index, style in enumerate(self.props.selection_model):
            if index > 0 and style.get_name() == self.props.custom_style:
                self.props.selection_model.set_selected(index)
                break

    def get_selected_style_params(self) -> RcParams:
        """Get the selected style properties."""
        return self._selected_style_params

    def get_system_style_params(self) -> RcParams:
        """Get the system style properties."""
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
        style_model = self.props.selection_model.get_model()
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
            style_params = self._complete_style(tmp_style_params)
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

    def _on_style_select(self, style_model, _pos, _n_items):
        """Set the style upon selection."""
        selected_item = style_model.get_selected_item()
        # Don't trigger unneccesary reloads
        if selected_item.get_file() is None:  # System style
            if self.props.use_custom_style:
                self.props.use_custom_style = False
        else:
            stylename = selected_item.get_name()
            if stylename != self.props.custom_style:
                self.props.custom_style = stylename
            if not self.props.use_custom_style:
                self.props.use_custom_style = True

    @staticmethod
    def _on_use_custom_style(self, _a) -> None:
        """Handle `use_custom_style` property change."""
        if self.props.use_custom_style:
            self._on_custom_style(self, None)
        else:
            self.props.selection_model.set_selected(0)
        self._on_style_change(True)

    @staticmethod
    def _on_custom_style(self, _a) -> None:
        """Handle `custom_style` property change."""
        if self.props.use_custom_style:
            for index, style in enumerate(self.props.selection_model):
                if index > 0 and style.get_name() == self.props.custom_style:
                    self.props.selection_model.set_selected(index)
                    break
            self._on_style_change(True)

    def _on_style_change(self, override: bool = False) -> None:
        rcParams.update(rcParamsDefault)
        self.props.selected_stylename = self.get_selected_style().get_name()
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

        window = self.props.application.get_window()
        canvas = graphs.canvas.Canvas(self._selected_style_params)
        figure_settings = data.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ("use_custom_style", "custom_style"):
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)
        data.bind_property("items", canvas, "items", 2)
        from graphs.figure_settings import FigureSettingsDialog

        def on_edit_request(_canvas, label_id):
            FigureSettingsDialog(self.props.application, label_id)

        def on_view_changed(_canvas):
            data.add_view_history_state()

        canvas.connect("edit_request", on_edit_request)
        canvas.connect("view_changed", on_view_changed)

        # Set headerbar color and contrast
        bg_color = self._selected_style_params["figure.facecolor"]
        color = self._selected_style_params["text.color"]
        css_provider = window.get_headerbar_provider()
        css_provider.load_from_string(
            f"headerbar {{ background-color: {bg_color}; color: {color}; }}",
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
            for style in self.props.selection_model.get_model():
                if stylename == style.get_name():
                    try:
                        style_params = style_io.parse(style.get_file())[0]
                        if style.get_mutable():
                            style_params = self._complete_style(style_params)
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
        """Copy a style."""
        new_name = Graphs.tools_get_duplicate_string(
            new_name,
            self._stylenames,
        )
        destination = self.props.style_dir.get_child_for_display_name(
            _generate_filename(new_name),
        )
        for style in self.props.selection_model.get_model():
            if template == style.get_name():
                style_params = style_io.parse(style.get_file())[0]
                source = self._complete_style(style_params) \
                    if style.get_mutable() else style_params
                break
        style_io.write(destination, new_name, source)

    def _complete_style(self, params: RcParams) -> RcParams:
        for key, value in self._system_style_params.items():
            if key not in params:
                params[key] = value
        return params

    def delete_style(self, file: Gio.File) -> None:
        """Delete a style."""
        style_model = self.props.selection_model.get_model()
        for index, style in enumerate(style_model):
            if style is not None:
                file2 = style.get_file()
                if file2 is not None and file.equal(file2):
                    stylename = style.get_name()
                    style_model.remove(index)
                    self._stylenames.remove(stylename)
                    self.props.use_custom_style = False
                    self.props.custom_style = self._system_style_name


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
    "text_color": [
        "text.color",
        "axes.labelcolor",
        "xtick.labelcolor",
        "ytick.labelcolor",
    ],
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
    """Format a float value as percentage string."""
    return str(value / 2 * 100).split(".")[0] + "%"


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-editor.ui")
class StyleEditor(Adw.NavigationPage):
    """Style editor widget."""

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
    poor_contrast_warning = Gtk.Template.Child()

    def __init__(self, parent):
        super().__init__()
        self.style = None
        self.parent = parent
        self._style_manager = \
            parent.get_application().get_figure_style_manager()

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

        parent.connect("load-style-request", self._load_style)
        parent.connect("save-style-request", self._save_style)

    def _load_style(self, _parent, style):
        """Load a style."""
        if not style.get_mutable():
            return
        self.style = style
        self.style_params = self._style_manager._complete_style(
            style_io.parse(self.style.get_file())[0],
        )
        stylename = self.style.get_name()
        self.set_title(stylename)
        self.style_name.set_text(stylename)
        for key, value in STYLE_DICT.items():
            value = self.style_params[value[0]]
            with contextlib.suppress(KeyError):
                value = VALUE_DICT[key].index(value)
            widget = getattr(self, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                widget.set_text(str(value))
            elif isinstance(widget, Adw.ComboRow):
                widget.set_selected(int(value))
            elif isinstance(widget, Gtk.Scale):
                widget.set_value(value)
            elif isinstance(widget, Gtk.Button):
                widget.color = Graphs.tools_hex_to_rgba(value)
            elif isinstance(widget, Adw.SwitchRow):
                widget.set_active(bool(value))
            else:
                raise ValueError

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
            hex_color = Graphs.tools_rgba_to_hex(button.color)
            button.provider.load_from_string(
                f"button {{ color: {hex_color}; }}",
            )
        self._check_contrast()

        # line colors
        self.line_colors = \
            self.style_params["axes.prop_cycle"].by_key()["color"]
        self._reload_line_colors()

    def _save_style(self, _parent):
        """Save the style."""
        if self.style is None:
            return
        for key in STYLE_DICT.keys():
            widget = getattr(self, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                value = str(widget.get_text())
            elif isinstance(widget, Adw.ComboRow):
                value = widget.get_selected()
            elif isinstance(widget, Gtk.Scale):
                value = widget.get_value()
            elif isinstance(widget, Gtk.Button):
                value = Graphs.tools_rgba_to_hex(widget.color)
            elif isinstance(widget, Adw.SwitchRow):
                value = bool(widget.get_active())
            else:
                raise ValueError
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
        self.style_params["font.style"] = \
            FONT_STYLE_DICT[font_description.get_style()]
        self.style_params["font.variant"] = \
            FONT_VARIANT_DICT[font_description.get_variant()]

        # line colors
        self.style_params["axes.prop_cycle"] = cycler(color=self.line_colors)
        self.style_params["patch.facecolor"] = self.line_colors[0]

        # name & save
        new_name = self.style_name.get_text()
        if self.style.get_name() != new_name:
            new_name = Graphs.tools_get_duplicate_string(
                new_name,
                self._style_manager.list_stylenames(),
            )
        style_io.write(self.style.get_file(), new_name, self.style_params)
        self._style_manager._on_style_change(True)
        self.style = None

    def _reload_line_colors(self):
        list_box = self.line_colors_box
        while list_box.get_last_child() is not None:
            list_box.remove(list_box.get_last_child())
        if self.line_colors:
            for index in range(len(self.line_colors)):
                list_box.append(_StyleColorBox(self, index))
        else:
            self.line_colors.append("#000000")
            list_box.append(_StyleColorBox(self, 0))

    def on_color_change(self, button):
        """Handle color change."""

        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    button.color = color
                    self._check_contrast()
                    hex_color = Graphs.tools_rgba_to_hex(button.color)
                    button.provider.load_from_string(
                        f"button {{ color: {hex_color}; }}",
                    )

        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.parent.get_application().get_window(),
            button.color,
            None,
            on_accept,
        )

    def _check_contrast(self):
        contrast = Graphs.tools_get_contrast(
            self.outline_color.color,
            self.text_color.color,
        )
        self.poor_contrast_warning.set_visible(contrast < 4.5)

    @Gtk.Template.Callback()
    def on_linestyle(self, comborow, _b):
        """Handle linestyle selection."""
        self.linewidth.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def on_markers(self, comborow, _b):
        """Handle marker selection."""
        self.markersize.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def add_color(self, _button):
        """Add a color."""
        self.line_colors.append("000000")
        self._reload_line_colors()

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        """Handle style deletion."""

        def on_response(_dialog, response):
            if response == "cancel_delete_style":
                return
            if response == "delete_style":
                file = self.style.get_file()
                self._style_manager.delete_style(file)
                file.trash(None)
                self.style = None
                self.parent.get_navigation_view().pop()

        dialog = Graphs.tools_build_dialog("delete_style_dialog")
        msg = _("Are you sure you want to delete {stylename}?")
        dialog.set_body(msg.format(stylename=self.style.get_name()))
        dialog.connect("response", on_response)
        dialog.present(self.parent)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-color-box.ui")
class _StyleColorBox(Gtk.Box):
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
        self.provider.load_from_string(f"button {{ color: {color}; }}")

    @Gtk.Template.Callback()
    def on_color_choose(self, _button):

        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    self.props.parent.line_colors[self.props.index] = \
                        Graphs.tools_rgba_to_hex(color)
                    self._reload_color()

        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.props.parent.parent,
            Graphs.tools_hex_to_rgba(
                self.props.parent.line_colors[self.props.index],
            ),
            None,
            on_accept,
        )

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        self.props.parent.line_colors.pop(self.props.index)
        self.props.parent._reload_line_colors()
