# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io
import os

from gi.repository import Adw, GLib, Gdk, Gio, Graphs, Gtk

from graphs import style_io

from matplotlib import RcParams

CSS_TEMPLATE = """
.system-canvas-view {{
    background-color: {background_color};
    color: {color};
}}
"""


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(params: tuple[RcParams, dict]) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, params, "png", 31)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


def _params_for_bundled_style(name: str) -> tuple[RcParams, dict]:
    filename = Graphs.filename_from_stylename(name)
    uri = "resource:///se/sjoerd/Graphs/styles/" + filename
    return style_io.parse(Gio.File.new_for_uri(uri))


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
        Adw.StyleManager.get_default().connect("notify", self._on_system_style)

        self._system_style_light_params = \
            _params_for_bundled_style(system_style_name)
        self._system_style_dark_params = \
            _params_for_bundled_style(system_style_name + " Dark")

        self._on_system_style()
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

    def get_system_style_params(self) -> tuple[RcParams, dict]:
        """Get the system style properties."""
        if Adw.StyleManager.get_default().get_dark():
            return self._system_style_dark_params
        else:
            return self._system_style_light_params

    def _on_system_style(self, *_args) -> None:
        params = self.get_system_style_params()
        css = CSS_TEMPLATE.format(
            background_color=params[0]["figure.facecolor"],
            color=params[0]["text.color"],
        )
        self.props.css_provider.load_from_string(css)

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
