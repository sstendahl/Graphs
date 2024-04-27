# SPDX-License-Identifier: GPL-3.0-or-later
"""Figure Settings Dialog."""
from gi.repository import Graphs

from graphs import misc, styles, utilities


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
        self.props.style_editor = styles.StyleEditor(self)
        self.setup(highlighted)
        self.connect("entry-change", self.on_entry_change)

    @staticmethod
    def on_entry_change(self, entry, prop) -> None:
        """Bind the entry upon change."""
        is_valid, value = utilities.validate_entry(entry)
        if is_valid:
            self.props.figure_settings.set_property(prop, value)

    def _set_as_default(self) -> None:
        """Set the current figure settings as the new default."""
        figure_settings = self.props.figure_settings
        settings = self.props.application.get_settings_child("figure")
        ignorelist = ["min_selected", "max_selected"] + misc.LIMITS
        for prop in dir(figure_settings.props):
            if prop in ignorelist:
                continue
            value = figure_settings.get_property(prop)
            prop = prop.replace("_", "-")
            if isinstance(value, str):
                settings.set_string(prop, value)
            elif isinstance(value, bool):
                settings.set_boolean(prop, value)
            elif isinstance(value, int):
                settings.set_enum(prop, value)
