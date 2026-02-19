# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor Box."""
import contextlib

from cycler import cycler

from gi.repository import Adw, Gio, Graphs, Gtk, Pango

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
    "errorbar_capsize": ["errorbar.capsize"],
    "errorbar_capthick": ["errorbar.capthick"],
    "errorbar_linewidth": ["errorbar.linewidth"],
    "errorbar_barsabove": ["errorbar.barsabove"],
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


class StyleEditorBox(Graphs.StyleEditorBox):
    """Style editor widget."""

    __gtype_name__ = "GraphsPythonStyleEditorBox"

    def __init__(self, window):
        super().__init__(window=window)
        self.params = None

        # Setup Widgets
        for key, _value in STYLE_DICT.items():
            widget = self.get_property(key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                widget.connect("changed", self._on_entry_change, key)
            elif isinstance(widget, Adw.ComboRow):
                widget.connect("notify::selected", self._on_combo_change, key)
            elif isinstance(widget, Gtk.Scale):
                widget.connect("value-changed", self._on_scale_change, key)
            elif isinstance(widget, Graphs.StyleColorRow):
                widget.connect("notify::color", self._on_color_change, key)
            elif isinstance(widget, Adw.SwitchRow):
                widget.connect("notify::active", self._on_switch_change, key)
            else:
                raise ValueError

        self.props.style_name.connect("changed", self._on_name_change)
        self.props.font_chooser.connect(
            "notify::font-desc",
            self._on_font_change,
        )
        self.props.titlesize.connect(
            "value-changed",
            self._on_titlesize_change,
        )
        self.props.labelsize.connect(
            "value-changed",
            self._on_labelsize_change,
        )
        self.props.color_manager.connect(
            "colors-changed",
            self._on_line_colors_changed,
        )
        self.props.errbar_color_manager.connect(
            "colors-changed",
            self._on_errbar_colors_changed,
        )

    def load_style(self, file: Gio.File) -> None:
        """Load style params from file."""
        self.params = None
        style_params, graphs_params = style_io.parse(
            file,
            Graphs.StyleManager.get_instance().get_system_style_params(),
        )
        stylename = graphs_params["name"]
        self.props.style_name.set_text(stylename)
        for key, value in STYLE_DICT.items():
            value = value[0]
            value = graphs_params[
                value
            ] if value in style_io.STYLE_CUSTOM_PARAMS else style_params[value]
            with contextlib.suppress(KeyError):
                value = VALUE_DICT[key].index(value)
            widget = self.get_property(key.replace("-", "_"))
            if isinstance(widget, Adw.EntryRow):
                widget.set_text(str(value))
            elif isinstance(widget, Adw.ComboRow):
                widget.set_selected(int(value))
            elif isinstance(widget, Gtk.Scale):
                widget.set_value(value)
            elif isinstance(widget, Graphs.StyleColorRow):
                widget.set_color(Graphs.tools_hex_to_rgba(value))
            elif isinstance(widget, Adw.SwitchRow):
                widget.set_active(bool(value))
            else:
                raise ValueError

        # font
        font_description = Pango.FontDescription.new()
        self.font_size = style_params["font.size"]
        font_description.set_size(self.font_size * Pango.SCALE)
        self.props.titlesize.set_value(
            round(style_params["figure.titlesize"] * 2 / self.font_size, 1),
        )
        self.props.labelsize.set_value(
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
        self.props.font_chooser.set_font_desc(font_description)

        self.check_contrast()

        # line colors
        self.props.color_manager.set_colors(
            style_params["axes.prop_cycle"].by_key()["color"],
        )

        errbar_cycle = graphs_params["errorbar.color_cycle"]
        errbar_colors = errbar_cycle.by_key()["color"]
        self.props.errbar_color_manager.set_colors(errbar_colors)

        self.params, self.graphs_params = style_params, graphs_params

        return stylename

    def save_style(self, file: Gio.File) -> None:
        """Save style params to file."""
        style_io.write(file, self.params, self.graphs_params)

    def _on_line_colors_changed(
        self,
        color_manager: Graphs.StyleColorManager,
    ) -> None:
        """Update line colors in params."""
        if self.params is None:
            return
        line_colors = color_manager.get_colors()
        self.params["axes.prop_cycle"] = cycler(color=line_colors)
        self.params["patch.facecolor"] = line_colors[0]
        self.emit("params-changed")

    def _on_errbar_colors_changed(
        self,
        color_manager: Graphs.StyleColorManager,
    ) -> None:
        """Update errorbar colors in graph-params."""
        if self.graphs_params is None:
            return
        err_colors = color_manager.get_colors()
        self.graphs_params["errorbar.color_cycle"] = cycler(color=err_colors)
        self.graphs_params["errorbar.ecolor"] = err_colors[0]
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

    def _on_color_change(
        self,
        row: Graphs.StyleColorRow,
        _param,
        key: str,
    ) -> None:
        self._apply_value(key, Graphs.tools_rgba_to_hex(row.get_color()))
        self.check_contrast()

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
