# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io

from gi.repository import GLib, Gdk, Gio, Graphs

from graphs import style_io

from matplotlib import RcParams


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(params: tuple[RcParams, dict]) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, params, "png", 31)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


class StyleParameters(Graphs.StyleParameters):
    """Custom Style Parameters class."""

    def __init__(self, params: tuple[RcParams, dict]):
        super().__init__(
            color=params[0]["text.color"],
            background_color=params[0]["figure.facecolor"],
            color_cycle=params[0]["axes.prop_cycle"].by_key()["color"],
            errorbar_cycle=params[1]["errorbar.color_cycle"].by_key()["color"],
        )
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
        self.connect("style-request", self._on_style_request)
        self.connect("create-style-request", self._on_create_style_request)

        self.setup()

    @staticmethod
    def _on_style_request(self, file: Gio.File) -> Graphs.Style:
        try:
            system_params = self.get_system_style_params()
            validate = system_params.style_params, system_params.graphs_params
            params = style_io.parse(file, validate)
            style_params, graphs_params = params
            name = graphs_params["name"]
            preview = _generate_preview(params)
            light = _is_style_bright(style_params)
        except style_io.StyleParseError:
            name = ""
            preview = None
            light = False
        return Graphs.Style(
            name=name,
            file=file,
            mutable=True,
            preview=preview,
            light=light,
        )

    @staticmethod
    def _on_params_request(self, file: Gio.File) -> Graphs.StyleParameters:
        return StyleParameters(style_io.parse(file))

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
