# SPDX-License-Identifier: GPL-3.0-or-later
"""Style editor."""
from gi.repository import Graphs

from graphs.style_editor.editor_box import StyleEditorBox


class PythonStyleEditor(Graphs.StyleEditor):
    """Graphs Style Editor Window."""

    __gtype_name__ = "GraphsPythonStyleEditor"

    def __init__(self):
        super().__init__()
        self.set_editor_box(StyleEditorBox(self))
