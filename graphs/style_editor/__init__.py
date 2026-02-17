# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor."""
import asyncio
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs.canvas import Canvas
from graphs.item import DataItem
from graphs.style_editor.editor_box import StyleEditorBox

from matplotlib import pyplot

import numpy

_PREVIEW_XDATA1 = numpy.linspace(0, 10, 10)
_PREVIEW_YDATA1 = numpy.linspace(0, numpy.power(numpy.e, 10), 10)
_PREVIEW_YERR1 = numpy.linspace(500, 2500, 10)
_PREVIEW_XERR1 = numpy.linspace(0.1, 0.5, 10)
_PREVIEW_XDATA2 = numpy.linspace(0, 10, 60)
_PREVIEW_YDATA2 = numpy.power(numpy.e, _PREVIEW_XDATA2)
CSS_TEMPLATE = """
.canvas-view#{name} {{
    background-color: {background_color};
    color: {color};
}}
"""


class PythonStyleEditor(Graphs.StyleEditor):
    """Graphs Style Editor Window."""

    __gtype_name__ = "GraphsPythonStyleEditor"

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)
        self.setup()
        self.props.content_view.set_name(
            "view" + str(application.get_next_css_counter()),
        )

        style_editor = StyleEditorBox(self)
        style_editor.connect("params-changed", self._on_params_changed)
        self.set_editor_box(style_editor)
        self._test_items = Gio.ListStore()
        self._initialize_test_items()
        self.connect("load_request", self._on_load_request)
        self.connect("save_request", self._on_save_request)

        self._background_task = asyncio.create_task(
            self._reload_canvas(style_editor),
        )

    def _initialize_test_items(self):
        """Initialize example test items with predefined preview data."""
        preview_data = [
            (_PREVIEW_XDATA1, _PREVIEW_YDATA1, _PREVIEW_XERR1, _PREVIEW_YERR1),
            (_PREVIEW_XDATA2, _PREVIEW_YDATA2, None, None),
        ]
        test_style = pyplot.rcParams, {}
        for xdata, ydata, xerr, yerr in preview_data:
            self._test_items.append(
                DataItem.new(
                    test_style,
                    xdata=xdata,
                    ydata=ydata,
                    xerr=xerr,
                    yerr=yerr,
                    showxerr=True,
                    showyerr=True,
                    name=_("Example Item"),
                    color="#000000",
                ),
            )

    def _on_params_changed(self, style_editor, changes_unsaved=True):
        self._background_task.cancel()
        self._background_task = asyncio.create_task(
            self._reload_canvas(style_editor, changes_unsaved, 0.5),
        )

    async def _reload_canvas(
        self,
        style_editor: StyleEditorBox,
        changes_unsaved: bool = False,
        timeout: int = 0,
    ) -> None:
        await asyncio.sleep(timeout)
        if style_editor.params is None:
            style_manager = Graphs.StyleManager.get_instance()
            params, graphs_params = style_manager.get_system_style_params()
        else:
            params = style_editor.params
            graphs_params = style_editor.graphs_params
            color_cycle = params["axes.prop_cycle"].by_key()["color"]
            for index, item in enumerate(self._test_items):
                # Wrap around the color_cycle using the % operator
                item.set_color(color_cycle[index % len(color_cycle)])
                item_params = params, graphs_params
                for prop, value in item._extract_params(item_params).items():
                    item.set_property(prop, value)
            self.set_stylename(style_editor.graphs_params["name"])

        all_params = params, graphs_params
        canvas = Canvas(all_params, self._test_items, False)
        canvas.figure.props.title = _("Title")
        canvas.figure.props.bottom_label = _("X Label")
        canvas.figure.props.left_label = _("Y Label")
        self.set_canvas(canvas)

        # Set headerbar color
        css = CSS_TEMPLATE.format(
            name=self.props.content_view.get_name(),
            background_color=params["figure.facecolor"],
            color=params["text.color"],
        )
        self.props.css_provider.load_from_string(css)

        if changes_unsaved:
            self.set_unsaved(True)

    @staticmethod
    def _on_load_request(self, file: Gio.File) -> None:
        """Load a style."""
        style_editor = self.get_editor_box()
        name = style_editor.load_style(file)
        self.set_title(name)
        self._background_task = asyncio.create_task(
            self._reload_canvas(style_editor, False, 0),
        )

    @staticmethod
    def _on_save_request(self, file: Gio.File) -> None:
        """Save current style."""
        self.get_editor_box().save_style(file)
