# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io

from cycler import cycler

from gi.repository import GLib, GObject, Gdk, Gio, Graphs

from graphs import style_io

from matplotlib import RcParams


class StyleParameters(Graphs.StyleParameters):
    """Custom Style Parameters class."""

    def __init__(self, params: tuple[RcParams, dict]):
        super().__init__()
        self.style_params = params[0]
        self.graphs_params = params[1]
        combined = params[0] | params[1]

        for key, val in combined.items():
            if key in ("axes.prop_cycle", "errorbar.color_cycle"):
                value = GObject.Value(GObject.TYPE_STRV)
                value.set_boxed(val.by_key()["color"])
                val = value
            elif key == "font.sans-serif":
                val = val[0]
            self.set_param(key, val)

    def update(self):
        """Update parameters from vala controlled storage."""
        for key in self.get_params():
            val = self.get_param(key)
            if key in ("axes.prop_cycle", "errorbar.color_cycle"):
                val = cycler(color=val)
            elif key == "font.sans-serif":
                val = [val]
            if key in style_io.STYLE_CUSTOM_PARAMS:
                self.graphs_params[key] = val
            else:
                self.style_params[key] = val

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
        self.connect("preview-request", self._on_preview_request)
        self.connect("params-request", self._on_params_request)
        self.connect("save-request", self._on_save_request)

        self.setup()

    @staticmethod
    def _on_preview_request(
        self,
        params: Graphs.StyleParameters,
    ) -> Gdk.Texture:
        buffer = io.BytesIO()
        style_io.create_preview(buffer, params.as_tuple(), "png", 31)
        return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))

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
        params: Graphs.StyleParameters,
        file: Gio.File,
    ) -> None:
        style_io.write(file, params.as_tuple())
