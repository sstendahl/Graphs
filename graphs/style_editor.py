"""Style editor."""
import contextlib
from gettext import gettext as _

from cycler import cycler

from gi.repository import Adw, GLib, GObject, Gio, Graphs, Gtk, Pango

from graphs import style_io
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
class StyleEditor(Gtk.Box):
    """Style editor widget."""

    __gtype_name__ = "GraphsStyleEditor"

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
        for key in STYLE_DICT.keys():
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
        style_params, graphs_params = style_io.parse(file, True)
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
        style_io.write(file, self.graphs_params, self.params)

    def reload_line_colors(self):
        """Reload UI representation of line colors."""
        list_box = self.line_colors_box
        while list_box.get_last_child() is not None:
            list_box.remove(list_box.get_last_child())
        if self.line_colors:
            for index in range(len(self.line_colors)):
                list_box.append(_StyleColorBox(self, index))
        else:
            self.line_colors.append("#000000")
            list_box.append(_StyleColorBox(self, 0))

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
        self.line_colors.append("#000000")
        self.reload_line_colors()
        self.update_line_colors()


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
                    self.props.parent.update_line_colors()

        dialog = Gtk.ColorDialog()
        dialog.set_with_alpha(False)
        dialog.choose_rgba(
            self.props.parent.window,
            Graphs.tools_hex_to_rgba(
                self.props.parent.line_colors[self.props.index],
            ),
            None,
            on_accept,
        )

    @Gtk.Template.Callback()
    def on_delete(self, _button):
        self.props.parent.line_colors.pop(self.props.index)
        self.props.parent.reload_line_colors()
        self.props.parent.update_line_colors()


_PREVIEW_XDATA1 = numpy.linspace(0, 10, 10)
_PREVIEW_YDATA1 = numpy.linspace(0, numpy.power(numpy.e, 10), 10)
_PREVIEW_XDATA2 = numpy.linspace(0, 10, 60)
_PREVIEW_YDATA2 = numpy.power(numpy.e, _PREVIEW_XDATA2)


@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-editor-window.ui")
class StyleEditorWindow(Adw.Window):
    """Graphs Style Editor Window."""

    __gtype_name__ = "GraphsStyleEditorWindow"

    split_view = Gtk.Template.Child()
    editor_clamp = Gtk.Template.Child()
    content_view = Gtk.Template.Child()

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        application.register_style_editor()
        self._style_editor = StyleEditor(self)
        self.editor_clamp.set_child(self._style_editor)
        self._file = None
        self._test_items = Gio.ListStore()
        self._test_items.append(
            DataItem.new(
                pyplot.rcParams,
                xdata=_PREVIEW_XDATA1,
                ydata=_PREVIEW_YDATA1,
                name=_("Example Item"),
                color="#000000",
            ),
        )
        self._test_items.append(
            DataItem.new(
                pyplot.rcParams,
                xdata=_PREVIEW_XDATA2,
                ydata=_PREVIEW_YDATA2,
                name=_("Example Item"),
                color="#000000",
            ),
        )
        self._style_editor.connect("params-changed", self._on_params_changed)
        self._on_params_changed(self._style_editor)

    def _on_params_changed(self, style_editor):
        if style_editor.params is None:
            style_manager = self.props.application.get_figure_style_manager()
            params = style_manager.get_system_style_params()
        else:
            params = style_editor.params
            color_cycle = style_editor.line_colors
            count = 1
            for item in self._test_items:
                if count > len(color_cycle):
                    count = 1
                item.set_color(color_cycle[count - 1])
                count += 1
                for (prop, value) in item._extract_params(params).items():
                    item.set_property(prop, value)
        canvas = Canvas(params, self._test_items, False)
        canvas.props.title = _("Title")
        canvas.props.bottom_label = _("X Label")
        canvas.props.left_label = _("Y Label")
        self.content_view.set_content(canvas)

        # Set headerbar color
        css_provider = self.props.application.get_css_provider()
        css_provider.load_from_string(
            "headerbar#preview-headerbar { "
            f"background-color: {params['figure.facecolor']}; "
            f"color: {params['text.color']}; "
            "}",
        )

    def load_style(self, file: Gio.File) -> None:
        """Load a style."""
        self._file = file
        name = self._style_editor.load_style(file)
        self.set_title(name)
        self._on_params_changed(self._style_editor)

    def save_style(self) -> None:
        """Save current style."""
        if self._file is None:
            return
        self._style_editor.save_style(self._file)
        self._file = None

    @Gtk.Template.Callback()
    def on_close_request(self, _window):
        """Handle close request."""
        self.save_style()
        self.props.application.on_style_editor_closed()
