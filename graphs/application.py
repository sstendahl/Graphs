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

        PythonHelper(self)
        self.props.figure_style_manager = StyleManager(self)
        DataImporter(self)

        Graphs.Application.do_startup(self)
