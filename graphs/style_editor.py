"""Style editor."""
import contextlib
from gettext import gettext as _

from cycler import cycler

from gi.repository import Adw, GLib, GObject, Graphs, Gtk, Pango, Gio

from graphs import style_io

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

    def __init__(self):
        super().__init__()

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

    def load_style(self, file: Gio.File):
        """Load a style."""
        self.style_params, graphs_paramns = style_io.parse(file, True)
        stylename = graphs_paramns["name"]
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

        return stylename

    def _save_style(self, file: Gio.File):
        """Save the style."""
        graphs_params = {}
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

        # name
        graphs_params["name"] = self.style_name.get_text()

        # save
        style_io.write(file, graphs_params, self.style_params)

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
        dialog.choose_rgba(self, button.color, None, on_accept)

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
            self.props.parent,
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

@Gtk.Template(resource_path="/se/sjoerd/Graphs/ui/style-editor-window.ui")
class StyleEditorWindow(Adw.Window):
    __gtype_name__ = "GraphsStyleEditorWindow"

    split_view = Gtk.Template.Child()
    editor_clamp = Gtk.Template.Child()

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        self._style_editor = StyleEditor()
        self.editor_clamp.set_child(self._style_editor)
        self._file = None

    def load_style(self, file: Gio.File) -> None:
        self._file = file
        name = self._style_editor.load_style(file)
        self.set_title(name)

    def save_style(self) -> None:
        if self._file is None:
            return
        self._style_editor.save_style(self._file)
        self._file = None

    @staticmethod
    @Gtk.Template.Callback()
    def on_close_request(self):
        """Handle close request."""
        self.save_style()
