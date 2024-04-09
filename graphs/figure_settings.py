# SPDX-License-Identifier: GPL-3.0-or-later
"""Figure Settings Dialog."""
from gettext import gettext as _

from gi.repository import Graphs

from graphs import misc, styles, ui


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
        if highlighted is None:
            highlighted = ""
        self.props.style_editor = styles.StyleEditor(self)
        self.setup(highlighted)
        self.connect("copy-request", self.copy_style)
        self.connect("closed", self.on_close)
        self.connect("entry-change", self.on_entry_change)
        self.connect("set-as-default", self.on_set_as_default)
        self.present(application.get_window())

    @staticmethod
    def on_entry_change(self, entry, prop) -> None:
        """Bind the entry upon change."""
        is_valid, value = ui.validate_entry(entry)
        if is_valid:
            self.props.figure_settings.set_property(prop, value)

    @staticmethod
    def copy_style(self, template, name) -> None:
        """Open the new style window."""
        style_manager = self.props.application.get_figure_style_manager()
        style_manager.copy_style(template, name)

    def on_close(self, *_args) -> None:
        """
        Handle closing.

        Closes the figure settings, saves the current style and adds the
        new state to the clipboard
        """
        self.emit("save-style-request")
        data = self.props.application.get_data()
        data.add_view_history_state()
        data.add_history_state()

    @staticmethod
    def on_set_as_default(self) -> None:
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
        self.add_toast_string(_("Defaults Updated"))
