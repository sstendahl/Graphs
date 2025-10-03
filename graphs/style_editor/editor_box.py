# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor Box."""
import contextlib

from cycler import cycler

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk, Pango

from graphs import misc, style_io

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
    "tick_labels": ["ticklabels"],
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
    "linestyle": misc.LINESTYLES,
    "markers": misc.MARKERSTYLES,
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
    return str(value / 2 * 100).split(".", maxsplit=1)[0] + "%"


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-editor/editor-box.ui")
class StyleEditorBox(Gtk.Box):
    """Style editor widget."""

    __gtype_name__ = "GraphsStyleEditorBox"

    __gsignals__ = {
        "params-changed": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

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
    tick_labels = Gtk.Template.Child()
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

    def __init__(self, window):
        super().__init__()
        self.window = window
        self.params = None

        self._style_color_manager = Graphs.StyleColorManager.new(
            self.line_colors_box,
        )

        self.titlesize.set_format_value_func(_title_format_function)
        self.labelsize.set_format_value_func(_title_format_function)

        self.color_buttons = [
            self.text_color,
            self.tick_color,
            self.axis_color,
            self.grid_color,
            self.background_color,
            self.outline_color,
        ]

        # Setup Widgets
        for key, _value in STYLE_DICT.items():
            widget = getattr(self, key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                widget.connect("changed", self._on_entry_change, key)
            elif isinstance(widget, Adw.ComboRow):
                widget.connect("notify::selected", self._on_combo_change, key)
            elif isinstance(widget, Gtk.Scale):
                widget.connect("value-changed", self._on_scale_change, key)
            elif isinstance(widget, Gtk.Button):
                # Color buttons
                widget.connect("clicked", self._on_color_change, key)
                widget.provider = Gtk.CssProvider()
                widget.get_style_context().add_provider(
                    widget.provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )
            elif isinstance(widget, Adw.SwitchRow):
                widget.connect("notify::active", self._on_switch_change, key)
            else:
                raise ValueError

        self.style_name.connect("changed", self._on_name_change)
        self.font_chooser.connect("notify::font-desc", self._on_font_change)
        self.titlesize.connect("value-changed", self._on_titlesize_change)
        self.labelsize.connect("value-changed", self._on_labelsize_change)
        self._style_color_manager.connect(
            "colors-changed",
            self._on_line_colors_changed,
        )

    def load_style(self, file: Gio.File) -> None:
        """Load style params from file."""
        self.params = None
        application = self.window.get_application()
        style_params, graphs_params = style_io.parse(
            file,
            application.get_figure_style_manager().get_system_style_params(),
        )
        stylename = graphs_params["name"]
        self.style_name.set_text(stylename)
        for key, value in STYLE_DICT.items():
            value = value[0]
            value = graphs_params[
                value
            ] if value in style_io.STYLE_CUSTOM_PARAMS else style_params[value]
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
        self.font_size = style_params["font.size"]
        font_description.set_size(self.font_size * Pango.SCALE)
        self.titlesize.set_value(
            round(style_params["figure.titlesize"] * 2 / self.font_size, 1),
        )
        self.labelsize.set_value(
            round(style_params["axes.labelsize"] * 2 / self.font_size, 1),
        )
        font_description.set_family(style_params["font.sans-serif"][0])
        font_description.set_weight(style_params["font.weight"])
        inverted_style_dict = {b: a for a, b in FONT_STYLE_DICT.items()}
        font_description.set_style(
            inverted_style_dict[style_params["font.style"]],
        )
        inverted_variant_dict = {b: a for a, b in FONT_VARIANT_DICT.items()}
        font_description.set_variant(
            inverted_variant_dict[style_params["font.variant"]],
        )
        self.font_chooser.set_font_desc(font_description)

        for button in self.color_buttons:
            hex_color = Graphs.tools_rgba_to_hex(button.color)
            button.provider.load_from_string(
                f"button {{ color: {hex_color}; }}",
            )
        self._check_contrast()

        # line colors
        self._style_color_manager.set_colors(
            style_params["axes.prop_cycle"].by_key()["color"],
        )

        self.params, self.graphs_params = style_params, graphs_params

        return stylename

    def save_style(self, file: Gio.File) -> None:
        """Save style params to file."""
        style_io.write(file, self.params, self.graphs_params)

    def _on_line_colors_changed(
        self,
        style_color_manager: Graphs.StyleColorManager,
    ) -> None:
        """Update line colors in params."""
        if self.params is None:
            return
        line_colors = style_color_manager.get_colors()
        self.params["axes.prop_cycle"] = cycler(color=line_colors)
        self.params["patch.facecolor"] = line_colors[0]
        self.emit("params-changed")

    def _on_font_change(self, chooser: Gtk.FontChooser, _param) -> None:
        if self.params is None:
            return
        font_description = chooser.get_font_desc()
        self.params["font.sans-serif"] = [font_description.get_family()]
        self.font_size = font_description.get_size() / Pango.SCALE
        for key in (
            "font.size",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
            "figure.labelsize",
        ):
            self.params[key] = self.font_size
        font_weight = font_description.get_weight()
        for key in (
            "font.weight",
            "axes.titleweight",
            "axes.labelweight",
            "figure.titleweight",
            "figure.labelweight",
        ):
            self.params[key] = font_weight
        self.params["font.style"] = \
            FONT_STYLE_DICT[font_description.get_style()]
        self.params["font.variant"] = \
            FONT_VARIANT_DICT[font_description.get_variant()]
        self.emit("params-changed")

    def _on_titlesize_change(self, entry: Gtk.Entry) -> None:
        if self.params is None:
            return
        titlesize = round(entry.get_value() / 2 * self.font_size, 1)
        self.params["figure.titlesize"] = titlesize
        self.params["axes.titlesize"] = titlesize
        self.emit("params-changed")

    def _on_labelsize_change(self, entry: Gtk.Entry) -> None:
        if self.params is None:
            return
        labelsize = round(entry.get_value() / 2 * self.font_size, 1)
        self.params["axes.labelsize"] = labelsize
        self.emit("params-changed")

    def _on_name_change(self, entry: Gtk.Entry) -> None:
        if self.params is None:
            return
        self.graphs_params["name"] = entry.get_text()
        self.emit("params-changed")

    def _apply_value(self, key: str, value) -> None:
        if self.params is None:
            return
        with contextlib.suppress(KeyError):
            value = VALUE_DICT[key][value]
        for item in STYLE_DICT[key]:
            if item in style_io.STYLE_CUSTOM_PARAMS:
                self.graphs_params[item] = value
            else:
                self.params[item] = value

        self.emit("params-changed")

    def _on_color_change(self, button: Gtk.Button, key: str) -> None:
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
                    self._apply_value(key, hex_color)

        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(self.window, button.color, None, on_accept)

    def _on_entry_change(self, entry: Gtk.Entry, key: str) -> None:
        self._apply_value(key, str(entry.get_text()))

    def _on_combo_change(
        self,
        comborow: Adw.ComboRow,
        _param,
        key: str,
    ) -> None:
        self._apply_value(key, comborow.get_selected())

    def _on_scale_change(self, scale: Gtk.Scale, key: str) -> None:
        self._apply_value(key, scale.get_value())

    def _on_switch_change(
        self,
        switchrow: Adw.SwitchRow,
        _param,
        key: str,
    ) -> None:
        self._apply_value(key, bool(switchrow.get_active()))

    def _check_contrast(self) -> None:
        contrast = Graphs.tools_get_contrast(
            self.outline_color.color,
            self.text_color.color,
        )
        self.poor_contrast_warning.set_visible(contrast < 4.5)

    @Gtk.Template.Callback()
    def _on_linestyle(self, comborow: Adw.ComboRow, _b) -> None:
        """Handle linestyle selection."""
        self.linewidth.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def _on_markers(self, comborow: Adw.ComboRow, _b) -> None:
        """Handle marker selection."""
        self.markersize.set_sensitive(comborow.get_selected() != 0)

    @Gtk.Template.Callback()
    def _add_color(self, _button) -> None:
        """Add a color."""

        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    color = Graphs.tools_rgba_to_hex(color)
                    self._style_color_manager.add_color(color)

        dialog = Gtk.ColorDialog.new()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(self.window, None, None, on_accept)
