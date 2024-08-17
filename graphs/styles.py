# SPDX-License-Identifier: GPL-3.0-or-later
"""Module for style utilities."""
import io
import os
from gettext import gettext as _

from gi.repository import Adw, GLib, Gdk, Gio, Graphs, Gtk

from graphs import style_io

from matplotlib import RcParams


def _generate_filename(name: str) -> str:
    name = name.replace("(", "").replace(")", "")
    return f"{name.lower().replace(' ', '-')}.mplstyle"


def _is_style_bright(params: RcParams):
    return Graphs.tools_get_luminance_from_hex(params["axes.facecolor"]) < 0.4


def _generate_preview(style: RcParams) -> Gdk.Texture:
    buffer = io.BytesIO()
    style_io.create_preview(buffer, style)
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(buffer.getvalue()))


class StyleManager(Graphs.StyleManager):
    """
    Main Style Manager.

    Keeps track of all files in the style dir and represents them in
    the `selection_model` property.
    """

    __gtype_name__ = "GraphsPythonStyleManager"

    def __init__(self, application: Graphs.Application):
        # Check for Ubuntu
        gtk_theme = Gtk.Settings.get_default().get_property("gtk-theme-name")
        self._system_style_name = "Yaru" \
            if "SNAP" in os.environ \
            and gtk_theme.lower().startswith("yaru") \
            else "Adwaita"
        super().__init__(application=application)
        self._selected_style_params = None
        self.connect("style_request", self._on_style_request)
        self.connect("copy_request", self._on_copy_request)

        style_io.set_base_style(
            style_io.parse(
                Gio.File.new_for_uri(
                    "resource:///se/sjoerd/Graphs/styles/matplotlib.mplstyle",
                ),
            )[0],
        )

        self.setup(self._system_style_name.lower())

    @staticmethod
    def _on_style_request(self, file: Gio.File) -> Graphs.Style:
        style_params, graphs_params = style_io.parse(file, True)
        return Graphs.Style(
            name=graphs_params["name"],
            file=file,
            mutable=True,
            preview=_generate_preview(style_params),
            light=_is_style_bright(style_params),
        )

    def get_old_selected_style_params(self) -> RcParams:
        """Get the old selected style properties."""
        return self._old_style_params

    def get_selected_style_params(self) -> RcParams:
        """Get the selected style properties."""
        return self._selected_style_params

    def get_system_style_params(self) -> RcParams:
        """Get the system style properties."""
        return self._system_style_params

    def _update_system_style(self) -> None:
        system_style = self._system_style_name
        if Adw.StyleManager.get_default().get_dark():
            system_style += " Dark"
        filename = _generate_filename(system_style)
        self._system_style_params = style_io.parse(
            Gio.File.new_for_uri(
                "resource:///se/sjoerd/Graphs/styles/" + filename,
            ),
        )[0]

    def _update_selected_style(self) -> None:
        self._old_style_params = self._selected_style_params
        self._selected_style_params = None
        if self.props.use_custom_style:
            stylename = self.props.custom_style
            for style in self.props.selection_model.get_model():
                if stylename == style.get_name():
                    try:
                        self._selected_style_params = style_io.parse(
                            style.get_file(),
                            style.get_mutable(),
                        )[0]
                        return
                    except (ValueError, SyntaxError, AttributeError):
                        self._reset_selected_style(
                            _(
                                f"Could not parse {stylename}, loading "
                                "system preferred style",
                            ).format(stylename=stylename),
                        )
                    break
            if self._selected_style_params is None:
                self._reset_selected_style(
                    _(
                        f"Plot style {stylename} does not exist "
                        "loading system preferred",
                    ).format(stylename=stylename),
                )
        self._selected_style_params = self._system_style_params

    def _reset_selected_style(self, message: str) -> None:
        self.props.use_custom_style = False
        self.props.custom_style = self._system_style_name
        self.props.application.get_window().add_toast_string(message)

    @staticmethod
    def _on_copy_request(self, template: str, new_name: str) -> None:
        """Copy a style."""
        destination = self.props.style_dir.get_child_for_display_name(
            _generate_filename(new_name),
        )
        for style in self.props.selection_model.get_model():
            if template == style.get_name():
                style_params = style_io.parse(
                    style.get_file(),
                    style.get_mutable(),
                )[0]
                break
        style_io.write(destination, {"name": new_name}, style_params)
