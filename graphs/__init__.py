# SPDX-License-Identifier: GPL-3.0-or-later
"""graphs module init."""
import gettext
import logging

import gi

gi.require_version("Graphs", "1")


def startup(debug: bool, localedir: str, gettext_package: str) -> None:
    """Handle Application setup."""
    from gi.repository import Graphs

    from graphs import scales
    from graphs.file_import.parsers import project, xrdml
    from graphs.item import ItemFactory
    from graphs.python_helper import PythonHelper
    from graphs.styles import StyleManager

    import matplotlib
    from matplotlib import font_manager

    logging.basicConfig(
        format="%(levelname)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    logging.getLogger("matplotlib.font_manager").disabled = True
    logging.debug("Begin Application startup")

    gettext.bindtextdomain(gettext_package, localedir)
    gettext.textdomain(gettext_package)

    matplotlib.use("Gtk4Cairo", force=True)

    _ = gettext.gettext
    for f in font_manager.findSystemFonts(fontpaths=None, fontext="ttf"):
        try:
            font_manager.fontManager.addfont(f)
        except RuntimeError:
            logging.warning(_("Could not load {font}").format(font=f))

    scales.register_scales()

    PythonHelper()
    StyleManager()
    ItemFactory()

    parsers = [
        Graphs.ColumnsParser.new(),
        project.ProjectParser(),
        Graphs.SqlParser.new(),
        Graphs.SpreadsheetParser.new(),
        xrdml.XrdmlParser(),
        Graphs.XryParser.new(),
    ]
    Graphs.DataImporter.new(parsers)
