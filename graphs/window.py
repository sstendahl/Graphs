# SPDX-License-Identifier: GPL-3.0-or-later
"""Main window."""
import os
from gettext import gettext as _
from urllib.parse import unquote, urlparse

from gi.repository import Graphs

from graphs import item
from graphs.canvas import Canvas
from graphs.data import Data


class PythonWindow(Graphs.Window):
    """The main window class."""

    __gtype_name__ = "GraphsPythonWindow"

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application, data=Data(application))
        self.setup()
        self.props.data.connect(
            "style_changed",
            self._on_style_changed,
        )
        self.props.data.connect(
            "notify::unsaved",
            self._on_unsaved_changed,
        )
        self._reload_canvas()
        self._on_unsaved_changed(self.props.data, None)

    def _on_unsaved_changed(self, data, _a) -> None:
        file = data.get_file()
        if file is None:
            title = _("Untitled Project")
            path = _("Draft")
        else:
            title = Graphs.tools_get_filename(file)
            uri_parse = urlparse(file.get_uri())
            filepath = os.path.dirname(
                os.path.join(uri_parse.netloc, unquote(uri_parse.path)),
            )
            if filepath.startswith("/var"):
                # Fix for rpm-ostree distros, where home is placed in /var/home
                filepath = filepath.replace("/var", "", 1)
            path = filepath.replace(os.path.expanduser("~"), "~")
            if path.startswith(f"/run/user/{os.getuid()}/doc/"):
                path = _("Document Portal")
        if data.get_unsaved():
            title = "• " + title
        self.props.content_title.set_title(title)
        self.props.content_title.set_subtitle(path)

    def _on_style_changed(self, data, recolor_items) -> None:
        """Handle style change."""
        if recolor_items:
            old_style = data.get_old_selected_style_params()
            new_style = data.get_selected_style_params()
            old_cycle = old_style["axes.prop_cycle"].by_key()["color"]
            new_cycle = new_style["axes.prop_cycle"].by_key()["color"]
            for item_ in data:
                item_.reset(old_style, new_style)
            count = 0
            for item_ in data:
                if isinstance(item_, (item.DataItem, item.EquationItem)) \
                        and item_.get_color() in old_cycle:
                    if count > len(new_cycle):
                        count = 0
                    item_.set_color(new_cycle[count])
                    count += 1
        self._reload_canvas()

    def _reload_canvas(self) -> None:
        """Reload the canvas."""
        params = self.props.data.get_selected_style_params()
        canvas = Canvas(params, self.props.data)
        figure_settings = self.props.data.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ("use_custom_style", "custom_style"):
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)

        def on_edit_request(_canvas, label_id):
            Graphs.FigureSettingsDialog.new(self, label_id)

        def on_view_changed(_canvas):
            self.props.data.add_view_history_state()

        canvas.connect("edit_request", on_edit_request)
        canvas.connect("view_changed", on_view_changed)

        # Set headerbar color and contrast
        self.props.headerbar_provider.load_from_string(
            "headerbar#canvas-headerbar { "
            f"background-color: {params['figure.facecolor']}; "
            f"color: {params['text.color']}; "
            "}",
        )

        self.set_canvas(canvas)
        self.get_cut_button().bind_property(
            "sensitive",
            canvas,
            "highlight_enabled",
            2,
        )
