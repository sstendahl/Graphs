# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io

from gi.repository import GLib, Gdk, Gio, Graphs, Pango

from graphs import style_io

from matplotlib import RcParams


class StyleParameters(Graphs.StyleParameters):
    """Custom Style Parameters class."""

    def __init__(self, params: tuple[RcParams, dict]):
        data = Graphs.StyleData()

        # Font
        font = Pango.FontDescription.new()
        font.set_size(params[0]["font.size"] * Pango.SCALE)
        font.set_weight(params[0]["font.weight"])
        font.set_style(Pango.parse_style(params[0]["font.style"])[1])
        font.set_variant(Pango.parse_variant(params[0]["font.variant"])[1])
        data.set_font(font)

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

        data.text_color = params[0]["text.color"]
        data.background_color = params[0]["axes.facecolor"]
        data.outline_color = params[0]["figure.facecolor"]
        data.set_color_cycle(params[0]["axes.prop_cycle"].by_key()["color"])
        data.set_errorbar_cycle(
            params[1]["errorbar.color_cycle"].by_key()["color"],
        )

        super().__init__(name=params[1]["name"], data=data)
        self.style_params = params[0]
        self.graphs_params = params[1]

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
