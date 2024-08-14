# SPDX-License-Identifier: GPL-3.0-or-later
"""Figure Settings Dialog."""
from gi.repository import Graphs


class FigureSettingsDialog(Graphs.FigureSettingsDialog):
    """Figure Settings Dialog."""

    __gtype_name__ = "GraphsPythonFigureSettingsDialog"

    def __init__(
        self,
        application: Graphs.Application,
        highlighted: str = None,
    ):
        """Initialize the Figure Settings window and set the widget entries."""
        super().__init__(application=application)
        self.setup(highlighted)
