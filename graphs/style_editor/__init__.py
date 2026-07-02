# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor."""
from gettext import gettext as _

from gi.repository import Gio, Graphs

from graphs.item import DataItem
from graphs.style_editor.editor_box import StyleEditorBox

import numpy

_PREVIEW_XDATA1 = numpy.linspace(0, 10, 10)
_PREVIEW_YDATA1 = numpy.linspace(0, numpy.power(numpy.e, 10), 10)
_PREVIEW_XERR1 = numpy.linspace(0.1, 0.5, 10)
_PREVIEW_YERR1 = numpy.linspace(500, 2500, 10)
_PREVIEW_XDATA2 = numpy.linspace(0, 10, 60)
_PREVIEW_YDATA2 = numpy.power(numpy.e, _PREVIEW_XDATA2)


class PythonStyleEditor(Graphs.StyleEditor):
    """Graphs Style Editor Window."""

    __gtype_name__ = "GraphsPythonStyleEditor"

    def __init__(self):
        super().__init__()

        self._initialize_test_items()
        self.connect("load_request", self._on_load_request)
        self.connect("save_request", self._on_save_request)

        self.set_editor_box(StyleEditorBox(self))

    def _initialize_test_items(self):
        """Initialize example test items with predefined preview data."""
        preview_data = [
            (_PREVIEW_XDATA1, _PREVIEW_YDATA1, _PREVIEW_XERR1, _PREVIEW_YERR1),
            (_PREVIEW_XDATA2, _PREVIEW_YDATA2, None, None),
        ]
        style_manager = Graphs.StyleManager.get_instance()
        test_style = style_manager.get_system_style_params()
        test_items = self.props.test_items
        for xdata, ydata, xerr, yerr in preview_data:
            test_items.append(
                DataItem.new(
                    test_style,
                    xdata=xdata,
                    ydata=ydata,
                    xerr=xerr,
                    yerr=yerr,
                    name=_("Example Item"),
                    color="#000000",
                    errcolor="#000000",
                ),
            )

    @staticmethod
    def _on_load_request(self, file: Gio.File) -> None:
        """Load a style."""
        style_editor = self.get_editor_box()
        name = style_editor.load_style(file)
        self.set_title(name)

    @staticmethod
    def _on_save_request(self, file: Gio.File) -> None:
        """Save current style."""
        self.get_editor_box().save_style(file)
