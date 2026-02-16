# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io
import os
from typing import Tuple

from gi.repository import Adw, GLib, Gdk, Gio, Graphs, Gtk

from graphs import style_io

from matplotlib import RcParams


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(params: Tuple[RcParams, dict]) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, params, "png", 31)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


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
        self._system_style_name = "Yaru" \
            if "SNAP" in os.environ \
            and gtk_theme.lower().startswith("yaru") \
            else "Adwaita"
        super().__init__()
        self.connect("style-request", self._on_style_request)
        self.connect("create-style-request", self._on_create_style_request)
        Adw.StyleManager.get_default().connect(
            "notify",
            self._update_system_style,
        )

        self._update_system_style()
        self.setup(self._system_style_name.lower(), self)

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

    def get_system_style_params(self) -> Tuple[RcParams, dict]:
        """Get the system style properties."""
        return self._system_style_params

    def _update_system_style(self, *_args) -> None:
        system_style = self._system_style_name
        if Adw.StyleManager.get_default().get_dark():
            system_style += " Dark"
        filename = Graphs.filename_from_stylename(system_style)
        self._system_style_params = style_io.parse(
            Gio.File.new_for_uri(
                "resource:///se/sjoerd/Graphs/styles/" + filename,
            ),
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
            self._system_style_params,
        )
        graphs_params["name"] = new_name
        style_io.write(destination, style_params, graphs_params)
