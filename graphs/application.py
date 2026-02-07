# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
from gi.repository import Graphs


class PythonApplication(Graphs.Application):
    """The main application singleton class."""

    __gtype_name__ = "GraphsPythonApplication"

    def do_startup(self):
        """Handle Application setup."""
        import logging

        logging.debug("Begin Application startup")

        from gettext import gettext as _

        from graphs.file_import import DataImporter
        from graphs.python_helper import PythonHelper
        from graphs.styles import StyleManager

        from matplotlib import font_manager

        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load {font}").format(font=font))

        # We need to keep references as per
        # https://bugzilla.gnome.org/show_bug.cgi?id=687522
        PythonHelper(self)
        self.props.figure_style_manager = StyleManager(self)
        self._data_importer = DataImporter(self)
        self.props.data_importer = self._data_importer

        Graphs.Application.do_startup(self)
