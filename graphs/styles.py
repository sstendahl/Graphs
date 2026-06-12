# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io
import os

from gi.repository import GLib, Gdk, Gio, Graphs, Gtk

from graphs import style_io

from matplotlib import RcParams


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(params: tuple[RcParams, dict]) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, params, "png", 31)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


def _params_for_bundled_style(name: str) -> tuple[RcParams, dict]:
    filename = Graphs.filename_from_stylename(name)
    uri = "resource:///se/sjoerd/Graphs/styles/" + filename
    params = style_io.parse(Gio.File.new_for_uri(uri))
    return StyleParameters(params)


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


class StyleManager(Graphs.StyleManager):
    """
    Main Style Manager.

    Keeps track of all files in the style dir and represents them in
    the `selection_model` property.
    """

    __gtype_name__ = "GraphsPythonStyleManager"

    def __init__(self):
        # Check for Ubuntu
        gtk_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        system_style_name = "Yaru" \
            if "SNAP" in os.environ \
            and gtk_theme.lower().startswith("yaru") \
            else "Adwaita"
        super().__init__()
        self.connect("style-request", self._on_style_request)
        self.connect("create-style-request", self._on_create_style_request)

        self.props.system_style_light_params = \
            _params_for_bundled_style(system_style_name)
        self.props.system_style_dark_params = \
            _params_for_bundled_style(system_style_name + " Dark")

        self.setup(system_style_name.lower())

    @staticmethod
    def _on_style_request(self, file: Gio.File) -> Graphs.Style:
        try:
            params = style_io.parse(
                file,
                self.get_system_style_params(),
            )
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
    def _on_create_style_request(
        self,
        template: Graphs.Style,
        destination: Gio.File,
        new_name: str,
    ) -> None:
        """Copy a style."""
        style_params, graphs_params = style_io.parse(
            template.get_file(),
            self.get_system_style_params(),
        )
        graphs_params["name"] = new_name
        style_io.write(destination, style_params, graphs_params)
