# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Gio, Graphs, Gtk

from graphs import (
    curve_fitting,
    export_items,
    file_import,
    operations,
    utilities,
)
from graphs.item import EquationItem, GeneratedDataItem
from graphs.sidebar import edit_item
from graphs.style_editor import PythonStyleEditor
from graphs.window import PythonWindow

_REQUESTS = (
    "add-equation",
    "create-item-settings",
    "create-style-editor",
    "create-window",
    "curve-fitting-dialog",
    "evaluate-string",
    "export-items",
    "generate-data",
    "import-from-files",
    "perform-operation",
    "python-method",
    "validate-equation",
)


class PythonHelper(Graphs.PythonHelper):
    """Python helper for python only calls."""

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)

        for request in _REQUESTS:
            request = request + "-request"
            self.connect(
                request,
                getattr(self, "_on_" + request.replace("-", "_")),
            )

    @staticmethod
    def _on_add_equation_request(
        self,
        window: Graphs.Window,
        name: str,
    ) -> EquationItem:
        settings = self.props.application.get_settings_child("add-equation")
        equation = settings.get_string("equation")
        if name == "":
            name = f"Y = {settings.get_string('equation')}"
        return EquationItem.new(
            window.get_data().get_selected_style_params(),
            equation,
            name=name,
        )

    @staticmethod
    def _on_create_item_settings_request(
        self,
        edit_item_box: Gtk.Box,
        item: Graphs.Item,
    ) -> Gtk.Widget:
        return edit_item.create_item_settings(edit_item_box, item)

    @staticmethod
    def _on_create_style_editor_request(self) -> Graphs.StyleEditor:
        return PythonStyleEditor(self.props.application)

    @staticmethod
    def _on_create_window_request(self) -> Graphs.Window:
        return PythonWindow(self.props.application)

    @staticmethod
    def _on_curve_fitting_dialog_request(
        self,
        window: Graphs.Window,
        item: Graphs.Item,
    ) -> None:
        return curve_fitting.CurveFittingDialog(window, item)

    @staticmethod
    def _on_evaluate_string_request(self, string: str) -> None:
        value = utilities.string_to_float(string)
        if value is None:
            return False
        self.set_evaluate_string_helper(value)
        return True

    @staticmethod
    def _on_export_items_request(
        self,
        window: Graphs.Window,
        mode: str,
        file: Gio.File,
        items: list[Graphs.Item],
        _n_items: int,
    ) -> None:
        figure_settings = window.get_data().get_figure_settings()
        return export_items.export_items(mode, file, items, figure_settings)

    @staticmethod
    def _on_generate_data_request(
        self,
        window: Graphs.Window,
        name: str,
    ) -> GeneratedDataItem:
        settings = self.props.application.get_settings_child("generate-data")
        equation = settings.get_string("equation")
        if name == "":
            name = f"Y = {settings.get_string('equation')}"
        return GeneratedDataItem.new(
            window.get_data().get_selected_style_params(),
            equation,
            settings.get_string("xstart"),
            settings.get_string("xstop"),
            settings.get_int("steps"),
            settings.get_int("scale"),
            name=name,
        )

    @staticmethod
    def _on_import_from_files_request(
        self,
        window: Graphs.Window,
        files: list[Gio.File],
        _n_files: int,
    ) -> None:
        return file_import.import_from_files(window, files)

    @staticmethod
    def _on_perform_operation_request(
        self,
        window: Graphs.Window,
        name: str,
    ) -> None:
        operations.perform_operation(window, name)

    @staticmethod
    def _on_python_method_request(self, obj, method: str) -> None:
        getattr(obj, method)()

    @staticmethod
    def _on_validate_equation_request(self, equation: str) -> None:
        return utilities.validate_equation(equation)
