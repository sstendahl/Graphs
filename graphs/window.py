# SPDX-License-Identifier: GPL-3.0-or-later
"""Main window."""
from gi.repository import Graphs

from graphs import misc
from graphs.canvas import Canvas
from graphs.data import Data

from matplotlib import rcParams, rcParamsDefault

CSS_TEMPLATE = """
.canvas-view#{name} {{
    background-color: {background_color};
    color: {color};
}}
"""


class PythonWindow(Graphs.Window):
    """The main window class."""

    __gtype_name__ = "GraphsPythonWindow"

    def __init__(self):
        super().__init__(data=Data())
        self.props.data.connect(
            "style-changed",
            self._on_style_changed,
        )
        key_controller = self.props.key_controller
        key_controller.connect("key-pressed", self._on_key_press_event)
        key_controller.connect("key-released", self._on_key_release_event)

        zoom_in_action = self.lookup_action("zoom-in")
        zoom_in_action.connect("activate", self._on_zoom_in)
        zoom_out_action = self.lookup_action("zoom-out")
        zoom_out_action.connect("activate", self._on_zoom_out)

        self._reload_canvas()

    def _on_style_changed(
        self,
        data: Graphs.Data,
        recolor_items: bool,
    ) -> None:
        """Handle style change."""
        if recolor_items:
            old_style = data.get_old_selected_style_params()
            new_style = data.get_selected_style_params()

            old_cycle = old_style[0]["axes.prop_cycle"].by_key()["color"]
            new_cycle = new_style[0]["axes.prop_cycle"].by_key()["color"]
            old_errbar_cycle = \
                old_style[1]["errorbar.color_cycle"].by_key()["color"]
            new_errbar_cycle = \
                new_style[1]["errorbar.color_cycle"].by_key()["color"]

            for item in data:
                item.reset(old_style, new_style)

            count = 0
            errbar_count = 0
            for item in data:
                if (
                    isinstance(item, (Graphs.DataItem, Graphs.EquationItem))
                    and item.get_color() in old_cycle
                ):
                    count %= len(new_cycle)
                    item.set_color(new_cycle[count])
                    count += 1

                    if isinstance(item, Graphs.DataItem):
                        has_err = item.get_xerr() or item.get_yerr()
                        if not has_err:
                            continue
                        if item.get_errcolor() in old_errbar_cycle:
                            errbar_count %= len(new_errbar_cycle)
                            item.set_errcolor(new_errbar_cycle[errbar_count])
                            errbar_count += 1

        self._reload_canvas()

    def _on_key_press_event(self, *args) -> None:
        """Handle key press event."""
        if self.props.canvas is not None:
            self.props.canvas.key_press_event(*args)

    def _on_key_release_event(self, *args) -> None:
        """Handle key release event."""
        if self.props.canvas is not None:
            self.props.canvas.key_release_event(*args)

    def _on_edit_request(self, _canvas, label_id: str) -> None:
        """Handle edit request."""
        self.open_figure_settings(label_id)

    def _on_view_changed(self, _canvas) -> None:
        """Handle view change."""
        self.props.data.add_view_history_state()

    def _on_zoom_in(self, _a, _b) -> None:
        if self.props.canvas is not None:
            self.props.canvas.zoom(1.15, False)

    def _on_zoom_out(self, _a, _b) -> None:
        if self.props.canvas is not None:
            self.props.canvas.zoom(1 / 1.15, False)

    def _reload_canvas(self) -> None:
        """Reload the canvas."""
        rcParams.update(rcParamsDefault)
        params = self.props.data.get_selected_style_params()

        figure_settings = self.props.data.get_figure_settings()
        limits = figure_settings.get_limits()
        canvas = Canvas(params, self.props.data, limits=limits)

        for prop in misc.FIGURE_PROPERTIES:
            figure_settings.bind_property(prop, canvas.figure, prop, 1 | 2)

        for limit in misc.LIMITS:
            prop = limit.replace("-", "_")
            figure_settings.bind_property(prop, canvas.figure, prop, 1)

        for prop in ("min_selected", "max_selected"):
            figure_settings.bind_property(prop, canvas, prop, 1 | 2)

        canvas.connect("edit-request", self._on_edit_request)
        canvas.connect("view-changed", self._on_view_changed)

        # Set headerbar color and contrast
        css = CSS_TEMPLATE.format(
            name=self.props.content_view.get_name(),
            background_color=params[0]["figure.facecolor"],
            color=params[0]["text.color"],
        )
        self.props.css_provider.load_from_string(css)

        self.set_canvas(canvas)
