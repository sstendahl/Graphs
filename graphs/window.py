# SPDX-License-Identifier: GPL-3.0-or-later
"""Main window."""
from gi.repository import Graphs

from graphs import item
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

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application, data=Data())
        self.setup()
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
            for item_ in data:
                item_.reset(old_style, new_style)
            count = 0
            for item_ in data:
                if isinstance(item_, (item.DataItem, item.EquationItem)) \
                        and item_.get_color() in old_cycle:
                    if count > len(new_cycle):
                        count = 0
                    item_.set_color(new_cycle[count])
                    count += 1
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

        canvas = Canvas(params, self.props.data)
        figure_settings = self.props.data.get_figure_settings()
        canvas_props = ("min_selected", "max_selected")

        for prop in dir(figure_settings.props):
            if prop not in canvas_props + ("use_custom_style", "custom_style"):
                figure_settings.bind_property(prop, canvas.figure, prop, 1 | 2)

        for prop in canvas_props:
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
