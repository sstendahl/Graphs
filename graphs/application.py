# SPDX-License-Identifier: GPL-3.0-or-later
"""Main application."""
from gi.repository import Gio, Graphs


class PythonApplication(Graphs.Application):
    """The main application singleton class."""

    __gtype_name__ = "GraphsPythonApplication"

    def __init__(self, application_id: str, **kwargs):
        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
            **kwargs,
        )
        self.connect("setup-request", self._setup)

    @staticmethod
    def _setup(self):
        import logging
        from gettext import gettext as _

        from graphs import operations, styles
        from graphs.python_helper import PythonHelper

        from matplotlib import font_manager

        font_list = font_manager.findSystemFonts(fontpaths=None, fontext="ttf")
        for font in font_list:
            try:
                font_manager.fontManager.addfont(font)
            except RuntimeError:
                logging.warning(_("Could not load {font}").format(font=font))

        # We need to keep references as per
        # https://bugzilla.gnome.org/show_bug.cgi?id=687522
        self._python_helper = PythonHelper(self)
        self.props.python_helper = self._python_helper
        self._figure_style_manager = styles.StyleManager(self)
        self.props.figure_style_manager = self._figure_style_manager

        self.connect("operation_invoked", operations.perform_operation)
