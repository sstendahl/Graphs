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

    def _reset_items(self) -> None:
        """Reset items to match new style."""
        old_style = self.props.data.get_old_selected_style_params()
        new_style = self.props.data.get_selected_style_params()

        old_cycle = old_style.get_color_cycle()
        new_cycle = new_style.get_color_cycle()
        old_err_cycle = old_style.get_errorbar_cycle()
        new_err_cycle = new_style.get_errorbar_cycle()

        count = 0
        errbar_count = 0
        for item in self.props.data:
            item.reset(old_style, new_style)

            if not isinstance(item, (Graphs.DataItem, Graphs.EquationItem)) \
                    or item.get_color() not in old_cycle:
                continue

            count %= len(new_cycle)
            item.set_color(new_cycle[count])
            count += 1

            if not isinstance(item, Graphs.DataItem) \
                    or not item.has_xerr() and not item.has_yerr() \
                    or item.get_errcolor() not in old_err_cycle:
                continue

            errbar_count %= len(new_err_cycle)
            item.set_errcolor(new_err_cycle[errbar_count])
            errbar_count += 1

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
