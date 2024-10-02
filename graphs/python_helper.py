# SPDX-License-Identifier: GPL-3.0-or-later
"""Python Helper - Python part."""
from gi.repository import Gio, Graphs

from graphs import (
    curve_fitting,
    edit_item,
    export_items,
    file_import,
    utilities,
)
from graphs.item import EquationItem
from graphs.style_editor import StyleEditorWindow
from graphs.window import PythonWindow

_REQUEST_NAMES = (
    "python_method_request",
    "edit_item_dialog_request",
    "curve_fitting_dialog_request",
    "evaluate_string_request",
    "import_from_files_request",
    "export_items_request",
    "add_equation_request",
    "validate_equation_request",
    "open_style_editor_request",
    "create_window_request",
)


class PythonHelper(Graphs.PythonHelper):
    """Python helper for python only calls."""

    def __init__(self, application: Graphs.Application):
        super().__init__(application=application)

        for request_name in _REQUEST_NAMES:
            self.connect(
                request_name,
                getattr(self, "_on_" + request_name),
            )

    @staticmethod
    def _on_python_method_request(self, obj, method: str) -> None:
        getattr(obj, method)()

    @staticmethod
    def _on_edit_item_dialog_request(
        self, window: Graphs.Window, item: Graphs.Item,
    ) -> None:
        return edit_item.EditItemDialog(window, item)

    @staticmethod
    def _on_curve_fitting_dialog_request(
        self, window: Graphs.Window, item: Graphs.Item,
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
    def _on_validate_equation_request(self, equation: str) -> None:
        return utilities.validate_equation(equation)

    @staticmethod
    def _on_import_from_files_request(
        self,
        window: Graphs.Window,
        files: list[Gio.File],
        _n_files: int,
    ) -> None:
        return file_import.import_from_files(window, files)

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
    def _on_add_equation_request(
        self, window: Graphs.Window, name: str,
    ) -> None:
        settings = self.props.application.get_settings_child("add-equation")
        equation = settings.get_string("equation")
        if name == "":
            name = f"Y = {settings.get_string('equation')}"
        data = window.get_data()
        data.add_items([
            EquationItem.new(
                data.get_selected_style_params(),
                equation,
                name=name,
            ),
        ])
        data.optimize_limits()

    @staticmethod
    def _on_open_style_editor_request(self, file: Gio.File) -> None:
        window = StyleEditorWindow(self.props.application)
        window.load_style(file)
        window.present()

    @staticmethod
    def _on_create_window_request(self) -> Graphs.Window:
        return PythonWindow(self.props.application)
