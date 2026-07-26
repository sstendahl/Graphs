# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io

from cycler import cycler

from gi.repository import GLib, Gdk, Gio, Graphs, GObject

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
        super().__init__()
        self.style_params = params[0]
        self.graphs_params = params[1]

        for key, val in self.style_params.items():
            if key == "axes.prop_cycle":
                value = GObject.Value(GObject.TYPE_STRV)
                value.set_boxed(val.by_key()["color"])
                val = value
            elif key == "font.sans-serif":
                val = val[0]
            self.set_param(key, val, False)

        for key, val in self.graphs_params.items():
            if key == "errorbar.color_cycle":
                value = GObject.Value(GObject.TYPE_STRV)
                value.set_boxed(val.by_key()["color"])
                val = value
            self.set_param(key, val, True)

    def update(self):
        for key in self.get_params():
            val = self.get_param(key, False)
            if key == "axes.prop_cycle":
                val = cycler(color=val)
            elif key == "font.sans-serif":
                val = [val]
            print(val)
            self.style_params[key] = val

        for key in self.get_graphs_params():
            val = self.get_param(key, True)
            if key == "errorbar.color_cycle":
                val = cycler(color=val)
            print(val)
            self.graphs_params[key] = val

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
        self.connect("save-request", self._on_save_request)
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
        style_io.write(file, params.params, params.graphs_params)

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
