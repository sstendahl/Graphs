# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor."""
import asyncio
import contextlib
from gettext import gettext as _

from cycler import cycler

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk, Pango

from graphs import misc, style_io
from graphs.canvas import Canvas
from graphs.item import DataItem

from matplotlib import pyplot

import numpy

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


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-editor-box.ui")
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
        self.params, self.graphs_params = None, None

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

    def load_style(self, file: Gio.File):
        """Load style params from file."""
        self.params, self.graphs_params = None, None
        application = self.window.get_application()
        style_params, graphs_params = style_io.parse(
            file,
            application.get_figure_style_manager().get_system_style_params(),
        )
        stylename = graphs_params["name"]
        self.style_name.set_text(stylename)
        for key, value in STYLE_DICT.items():
            value = style_params[value[0]]
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
        self.line_colors = style_params["axes.prop_cycle"].by_key()["color"]
        self.reload_line_colors()

        self.params, self.graphs_params = style_params, graphs_params

        return stylename

    def save_style(self, file: Gio.File):
        """Save style params to file."""
        style_io.write(file, self.params, self.graphs_params)

    def reload_line_colors(self):
        """Reload UI representation of line colors."""
        list_box = self.line_colors_box
        while list_box.get_last_child() is not None:
            list_box.remove(list_box.get_last_child())
        if self.line_colors:
            for index in range(len(self.line_colors)):
                list_box.append(self._create_color_box(index))
        else:
            self.line_colors.append("#000000")
            list_box.append(self._create_color_box(0))

    def _create_color_box(self, index: int) -> Graphs.StyleColorBox:

        def on_color_removed(_box):
            self.line_colors.pop(index)
            self.reload_line_colors()
            self.update_line_colors()

        def on_color_changed(_box, color):
            self.line_colors[index] = color
            self.update_line_colors()

        color = self.line_colors[index]
        box = Graphs.StyleColorBox.new(index, color)
        box.connect("color-removed", on_color_removed)
        box.connect("color-changed", on_color_changed)
        return box

    def update_line_colors(self):
        """Update line colors in params."""
        if self.params is None:
            return
        self.params["axes.prop_cycle"] = cycler(color=self.line_colors)
        self.params["patch.facecolor"] = self.line_colors[0]
        self.emit("params-changed")

    def _on_font_change(self, chooser, _param):
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

    def _on_titlesize_change(self, entry):
        if self.params is None:
            return
        titlesize = round(entry.get_value() / 2 * self.font_size, 1)
        self.params["figure.titlesize"] = titlesize
        self.params["axes.titlesize"] = titlesize
        self.emit("params-changed")

    def _on_labelsize_change(self, entry):
        if self.params is None:
            return
        labelsize = round(entry.get_value() / 2 * self.font_size, 1)
        self.params["axes.labelsize"] = labelsize
        self.emit("params-changed")

    def _on_name_change(self, entry):
        if self.params is None:
            return
        self.graphs_params["name"] = entry.get_text()
        self.emit("params-changed")

    def _apply_value(self, key, value):
        if self.params is None:
            return
        with contextlib.suppress(KeyError):
            value = VALUE_DICT[key][value]
        for item in STYLE_DICT[key]:
            self.params[item] = value
        self.emit("params-changed")

    def _on_color_change(self, button, key):
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

    def _on_entry_change(self, entry, key):
        self._apply_value(key, str(entry.get_text()))

    def _on_combo_change(self, comborow, _param, key):
        self._apply_value(key, comborow.get_selected())

    def _on_scale_change(self, scale, key):
        self._apply_value(key, scale.get_value())

    def _on_switch_change(self, switchrow, _param, key):
        self._apply_value(key, bool(switchrow.get_active()))

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

        def on_accept(dialog, result):
            with contextlib.suppress(GLib.GError):
                color = dialog.choose_rgba_finish(result)
                if color is not None:
                    self.line_colors.append(Graphs.tools_rgba_to_hex(color))
                    self.reload_line_colors()
                    self.update_line_colors()

        dialog = Gtk.ColorDialog.new()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(self.window, None, None, on_accept)


_PREVIEW_XDATA1 = numpy.linspace(0, 10, 10)
_PREVIEW_YDATA1 = numpy.linspace(0, numpy.power(numpy.e, 10), 10)
_PREVIEW_XDATA2 = numpy.linspace(0, 10, 60)
_PREVIEW_YDATA2 = numpy.power(numpy.e, _PREVIEW_XDATA2)
CSS_TEMPLATE = """
.canvas-view#{name} {{
    background-color: {background_color};
    color: {color};
}}
"""


class PythonStyleEditor(Graphs.StyleEditor):
    """Graphs Style Editor Window."""

    __gtype_name__ = "GraphsPythonStyleEditor"

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        self.setup()

        style_editor = StyleEditorBox(self)
        style_editor.connect("params-changed", self._on_params_changed)
        self.set_editor_box(style_editor)
        self._test_items = Gio.ListStore()
        self._initialize_test_items()
        self.connect("load_request", self._on_load_request)
        self.connect("save_request", self._on_save_request)

        self._background_task = asyncio.create_task(
            self._reload_canvas(style_editor),
        )

    def _initialize_test_items(self):
        """Initialize example test items with predefined preview data."""
        preview_data = [(_PREVIEW_XDATA1, _PREVIEW_YDATA1),
                        (_PREVIEW_XDATA2, _PREVIEW_YDATA2)]

        for xdata, ydata in preview_data:
            self._test_items.append(
                DataItem.new(
                    pyplot.rcParams,
                    xdata=xdata,
                    ydata=ydata,
                    name=_("Example Item"),
                    color="#000000",
                ),
            )

    def _on_params_changed(self, style_editor, changes_unsaved=True):
        self._background_task.cancel()
        self._background_task = asyncio.create_task(
            self._reload_canvas(style_editor, changes_unsaved, 0.5),
        )

    async def _reload_canvas(
        self,
        style_editor: StyleEditorBox,
        changes_unsaved: bool = False,
        timeout: bool = 0,
    ) -> None:
        await asyncio.sleep(timeout)
        if style_editor.params is None:
            style_manager = self.props.application.get_figure_style_manager()
            params = style_manager.get_system_style_params()
        else:
            params = style_editor.params
            color_cycle = style_editor.line_colors
            for index, item in enumerate(self._test_items):
                # Wrap around the color_cycle using the % operator
                item.set_color(color_cycle[index % len(color_cycle)])
                for prop, value in item._extract_params(params).items():
                    item.set_property(prop, value)
            self.set_stylename(style_editor.graphs_params["name"])

        canvas = Canvas(params, self._test_items, False)
        canvas.props.title = _("Title")
        canvas.props.bottom_label = _("X Label")
        canvas.props.left_label = _("Y Label")
        self.set_canvas(canvas)

        # Set headerbar color
        css = CSS_TEMPLATE.format(
            name=self.props.content_view.get_name(),
            background_color=params["figure.facecolor"],
            color=params["text.color"],
        )
        self.props.css_provider.load_from_string(css)

        if changes_unsaved:
            self.set_unsaved(True)

    @staticmethod
    def _on_load_request(self, file: Gio.File) -> None:
        """Load a style."""
        style_editor = self.get_editor_box()
        name = style_editor.load_style(file)
        self.set_title(name)
        self._on_params_changed(style_editor, False)

    @staticmethod
    def _on_save_request(self, file: Gio.File) -> None:
        """Save current style."""
        self.get_editor_box().save_style(file)
