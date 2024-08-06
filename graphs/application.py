# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
import logging
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs import file_import, item, migrate, operations, styles
from graphs.canvas import Canvas
from graphs.data import Data
from graphs.python_helper import PythonHelper
from graphs.style_editor import StyleEditor

from matplotlib import font_manager


class PythonApplication(Graphs.Application):
    """The main application singleton class."""

    __gtype_name__ = "GraphsPythonApplication"

    def __init__(self, application_id, **kwargs):
        settings = Gio.Settings(application_id)
        migrate.migrate_config(settings)
        data = Data(settings.get_child("figure"))
        super().__init__(
            application_id=application_id,
            settings=settings,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            data=data,
            **kwargs,
        )
        # We need to keep references as per
        # https://bugzilla.gnome.org/show_bug.cgi?id=687522
        self._python_helper = PythonHelper(self)
        self.props.python_helper = self._python_helper
        self._figure_style_manager = styles.StyleManager(self)
        self.props.figure_style_manager = self._figure_style_manager
        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load {font}").format(font=font))

        self.setup_actions()
        self.connect("operation_invoked", operations.perform_operation)
        self.props.figure_style_manager.connect(
            "style_changed",
            self._on_style_changed,
        )

    def do_open(self, files: list, nfiles: int, _hint: str) -> None:
        """Open Graphs with a File as argument."""
        self.activate()
        data = self.get_data()
        if nfiles == 1:
            uri = files[0].get_uri()
            if uri.endswith(".graphs"):

                def load():
                    data.set_file(files[0])
                    data.load()

                if data.get_unsaved():

                    def on_response(_dialog, response):
                        if response == "discard_close":
                            load()
                        if response == "save_close":

                            def on_save(_o, response):
                                Graphs.project_save_finish(response)
                                load()

                            Graphs.project_save(self, False, on_save)

                    dialog = Graphs.tools_build_dialog("save_changes")
                    dialog.connect("response", on_response)
                    dialog.present(self.get_window())
                else:
                    load()

            elif uri.endswith(".mplstyle"):
                window = StyleEditor(self)
                window.load_style(files[0])
                window.present()
        else:
            file_import.import_from_files(self, files)

    def _on_style_changed(self, style_manager, recolor_items) -> None:
        """Handle style change."""
        if recolor_items:
            old_style = style_manager.get_old_selected_style_params()
            new_style = style_manager.get_selected_style_params()
            old_cycle = old_style["axes.prop_cycle"].by_key()["color"]
            new_cycle = new_style["axes.prop_cycle"].by_key()["color"]
            data = self.get_data()
            for item_ in data:
                item_.reset(old_style, new_style)
            count = 0
            for item_ in data:
                if isinstance(item_, item.DataItem) \
                        and item_.get_color() in old_cycle:
                    if count > len(new_cycle):
                        count = 0
                    item_.set_color(new_cycle[count])
                    count += 1
        self._reload_canvas()

    def _reload_canvas(self) -> None:
        """Reload the canvas."""
        window = self.get_window()
        if window is None:
            return
        data = self.get_data()
        params = self.get_figure_style_manager().get_selected_style_params()
        canvas = Canvas(params, data)
        figure_settings = data.get_figure_settings()
        for prop in dir(figure_settings.props):
            if prop not in ("use_custom_style", "custom_style"):
                figure_settings.bind_property(prop, canvas, prop, 1 | 2)

        def on_edit_request(_canvas, label_id):
            Graphs.FigureSettingsDialog.new(self, label_id)

        def on_view_changed(_canvas):
            data.add_view_history_state()

        canvas.connect("edit_request", on_edit_request)
        canvas.connect("view_changed", on_view_changed)

        # Set headerbar color and contrast
        css_provider = self.get_css_provider()
        css_provider.load_from_string(
            "headerbar#canvas-headerbar { "
            f"background-color: {params['figure.facecolor']}; "
            f"color: {params['text.color']}; "
            "}",
        )

        window.set_canvas(canvas)
        window.get_cut_button().bind_property(
            "sensitive",
            canvas,
            "highlight_enabled",
            2,
        )
