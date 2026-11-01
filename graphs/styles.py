# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io

from cycler import cycler

from gi.repository import GLib, Gdk, Gio, Graphs, Pango

from graphs import style_io

from matplotlib import RcParams


class StyleParameters(Graphs.StyleParameters):
    """Custom Style Parameters class."""

    def __init__(self, params: tuple[RcParams, dict]):
        super().__init__(name=params[1]["name"])
        data = self.props.data

        font = Pango.FontDescription.new()
        font.set_family(params[0]["font.sans-serif"][0])
        font_size = params[0]["font.size"]
        font.set_size(font_size * Pango.SCALE)
        font.set_weight(params[0]["font.weight"])
        font.set_style(Pango.parse_style(params[0]["font.style"])[1])
        font.set_variant(Pango.parse_variant(params[0]["font.variant"])[1])
        data.set_font(font)
        data.titlesize = \
            round(params[0]["figure.titlesize"] * 2 / font_size, 1)
        data.labelsize = round(params[0]["axes.labelsize"] * 2 / font_size, 1)

        data.linestyle = \
            Graphs.data_linestyle_from_style(params[0]["lines.linestyle"])
        data.linewidth = params[0]["lines.linewidth"]
        data.markerstyle = \
            Graphs.data_markerstyle_from_style(params[0]["lines.marker"])
        data.markersize = params[0]["lines.markersize"]

        data.errorbar_capsize = params[1]["errorbar.capsize"]
        data.errorbar_capthick = params[1]["errorbar.capthick"]
        data.errorbar_linewidth = params[1]["errorbar.linewidth"]
        data.errorbar_barsabove = params[1]["errorbar.barsabove"]

        data.axis_width = params[0]["axes.linewidth"]
        data.draw_frame = params[0]["axes.spines.bottom"]
        data.tick_direction = \
            Graphs.tick_direction_from_string(params[0]["xtick.direction"])
        data.minor_ticks = params[0]["xtick.minor.visible"]
        data.major_tick_width = params[0]["xtick.major.width"]
        data.minor_tick_width = params[0]["xtick.minor.width"]
        data.major_tick_length = params[0]["xtick.major.size"]
        data.minor_tick_length = params[0]["xtick.minor.size"]
        data.tick_bottom = params[0]["xtick.bottom"]
        data.tick_left = params[0]["ytick.left"]
        data.tick_top = params[0]["xtick.top"]
        data.tick_right = params[0]["ytick.right"]
        data.tick_labels = params[1]["ticklabels"]

        data.show_grid = params[0]["axes.grid"]
        data.grid_linewidth = params[0]["grid.linewidth"]
        data.grid_opacity = params[0]["grid.alpha"]

        data.value_padding = params[0]["xtick.major.pad"]
        data.label_padding = params[0]["axes.labelpad"]
        data.title_padding = params[0]["axes.titlepad"]

        data.text_color = params[0]["text.color"]
        data.tick_color = params[0]["xtick.color"]
        data.axis_color = params[0]["axes.edgecolor"]
        data.grid_color = params[0]["grid.color"]
        data.background_color = params[0]["axes.facecolor"]
        data.outline_color = params[0]["figure.facecolor"]

        data.set_color_cycle(params[0]["axes.prop_cycle"].by_key()["color"])
        data.set_errorbar_cycle(
            params[1]["errorbar.color_cycle"].by_key()["color"],
        )

        self.style_params = params[0]
        self.graphs_params = params[1]

    def update(self) -> None:
        """Update style parameters."""
        self.graphs_params["name"] = self.props.name
        data = self.props.data

        font = data.font
        self.style_params["font.sans-serif"] = [font.get_family()]
        font_size = font.get_size() / Pango.SCALE
        for key in (
            "font.size",
            "xtick.labelsize",
            "ytick.labelsize",
            "legend.fontsize",
            "figure.labelsize",
        ):
            self.style_params[key] = font_size
        font_weight = font.get_weight()
        for key in (
            "font.weight",
            "axes.titleweight",
            "axes.labelweight",
            "figure.titleweight",
            "figure.labelweight",
        ):
            self.style_params[key] = font_weight
        self.style_params["font.style"] = \
            Graphs.tools_font_style_to_string(font.get_style())
        self.style_params["font.variant"] = \
            Graphs.tools_font_variant_to_string(font.get_variant())
        titlesize = round(data.titlesize / 2 * font_size, 1)
        self.style_params["figure.titlesize"] = titlesize
        self.style_params["axes.titlesize"] = titlesize
        labelsize = round(data.labelsize / 2 * font_size, 1)
        self.style_params["axes.labelsize"] = labelsize

        self.style_params["lines.linestyle"] = \
            Graphs.python_data_linestyle_to_style(data.linestyle)
        self.style_params["lines.linewidth"] = data.linewidth
        self.style_params["lines.marker"] = \
            Graphs.python_data_markerstyle_to_style(data.markerstyle)
        self.style_params["lines.markersize"] = data.markersize

        self.graphs_params["errorbar.capsize"] = data.errorbar_capsize
        self.graphs_params["errorbar.capthick"] = data.errorbar_capthick
        self.graphs_params["errorbar.linewidth"] = data.errorbar_linewidth
        self.graphs_params["errorbar.barsabove"] = data.errorbar_barsabove

        for key in (
            "axes.spines.bottom",
            "axes.spines.left",
            "axes.spines.top",
            "axes.spines.right",
        ):
            self.style_params[key] = data.draw_frame

        tick_direction = Graphs.tick_direction_to_string(data.tick_direction)
        self.style_params["xtick.direction"] = tick_direction
        self.style_params["ytick.direction"] = tick_direction
        self.style_params["xtick.minor.visible"] = data.minor_ticks
        self.style_params["ytick.minor.visible"] = data.minor_ticks
        self.style_params["xtick.major.width"] = data.major_tick_width
        self.style_params["ytick.major.width"] = data.major_tick_width
        self.style_params["xtick.minor.width"] = data.minor_tick_width
        self.style_params["ytick.minor.width"] = data.minor_tick_width
        self.style_params["xtick.major.size"] = data.major_tick_length
        self.style_params["ytick.major.size"] = data.major_tick_length
        self.style_params["xtick.minor.size"] = data.minor_tick_length
        self.style_params["ytick.minor.size"] = data.minor_tick_length
        self.style_params["xtick.bottom"] = data.tick_bottom
        self.style_params["ytick.left"] = data.tick_left
        self.style_params["xtick.top"] = data.tick_top
        self.style_params["ytick.right"] = data.tick_right
        self.graphs_params["ticklabels"] = data.tick_labels

        self.style_params["axes.grid"] = data.show_grid
        self.style_params["axes.linewidth"] = data.axis_width
        self.style_params["grid.linewidth"] = data.grid_linewidth
        self.style_params["grid.alpha"] = data.grid_opacity

        for key in (
            "xtick.major.pad",
            "ytick.minor.pad",
            "xtick.major.pad",
            "ytick.minor.pad",
        ):
            self.style_params[key] = data.value_padding
        self.style_params["axes.labelpad"] = data.label_padding
        self.style_params["axes.titlepad"] = data.title_padding

        self.style_params["xtick.color"] = data.tick_color
        self.style_params["ytick.color"] = data.tick_color
        self.style_params["axes.edgecolor"] = data.axis_color
        self.style_params["grid.color"] = data.grid_color
        self.style_params["axes.facecolor"] = data.background_color
        self.style_params["figure.facecolor"] = data.outline_color
        self.style_params["figure.edgecolor"] = data.outline_color

        line_colors = data.color_cycle
        self.style_params["axes.prop_cycle"] = cycler(color=line_colors)
        self.style_params["patch.facecolor"] = line_colors[0]

        err_colors = data.errorbar_cycle
        self.graphs_params["errorbar.color_cycle"] = cycler(color=err_colors)

    def as_tuple(self) -> tuple[RcParams, dict]:
        """Return params as tuple."""
        return self.style_params, self.graphs_params


class StyleManager(Graphs.StyleManager):
    """
    Main Style Manager.

    Keeps track of all files in the style dir and represents them in
    the `selection_model` property.
    """

    __gtype_name__ = "GraphsPythonStyleManager"

    def __init__(self):
        super().__init__()
        self.connect("params-request", self._on_params_request)
        self.connect("preview-request", self._on_preview_request)
        self.connect("create-style-request", self._on_create_style_request)
        self.connect("save-request", self._on_save_request)

        self.setup()

    @staticmethod
    def _on_params_request(
        self,
        file: Gio.File,
        validate: Graphs.StyleParameters,
    ) -> Graphs.StyleParameters:
        validate = None if validate is None else validate.as_tuple()
        return StyleParameters(style_io.parse(file, validate))

    @staticmethod
    def _on_save_request(
        self,
        file: Gio.File,
        style: Graphs.StyleParameters,
    ) -> None:
        style_io.write(file, style.style_params, style.graphs_params)

    @staticmethod
    def _on_preview_request(
        self,
        params: Graphs.StyleParameters,
    ) -> Gdk.Texture:
        buffer = io.BytesIO()
        style_io.create_preview(buffer, params.as_tuple(), "png", 31)
        return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))

    @staticmethod
    def _on_create_style_request(
        self,
        template: Graphs.Style,
        destination: Gio.File,
        new_name: str,
    ) -> None:
        """Copy a style."""
        style_params, graphs_params = style_io.parse(
            template.get_file(),
            self.get_system_style_params().as_tuple(),
        )
        graphs_params["name"] = new_name
        style_io.write(destination, style_params, graphs_params)
