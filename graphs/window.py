# SPDX-License-Identifier: GPL-3.0-or-later
"""Main window."""
from gi.repository import Graphs

from graphs.data import Data


class PythonWindow(Graphs.Window):
    """The main window class."""

    __gtype_name__ = "GraphsPythonWindow"

    def __init__(self):
        super().__init__(data=Data())
        key_controller = self.props.key_controller
        key_controller.connect("key-pressed", self._on_key_press_event)
        key_controller.connect("key-released", self._on_key_release_event)

        zoom_in_action = self.lookup_action("zoom-in")
        zoom_in_action.connect("activate", self._on_zoom_in)
        zoom_out_action = self.lookup_action("zoom-out")
        zoom_out_action.connect("activate", self._on_zoom_out)

    def _on_key_press_event(self, *args) -> None:
        """Handle key press event."""
        if self.props.canvas is not None:
            self.props.canvas.key_press_event(*args)

    def _on_key_release_event(self, *args) -> None:
        """Handle key release event."""
        if self.props.canvas is not None:
            self.props.canvas.key_release_event(*args)

    def _on_zoom_in(self, _a, _b) -> None:
        if self.props.canvas is not None:
            self.props.canvas.zoom(1.15, False)

    def _on_zoom_out(self, _a, _b) -> None:
        if self.props.canvas is not None:
            self.props.canvas.zoom(1 / 1.15, False)
